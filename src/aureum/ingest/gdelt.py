"""GDELT 2.0 event firehose: one new file every 15 minutes, keyless.

Each run lands the latest export file as an incremental partition keyed by
GDELT's own file id, so the Dagster 15-min schedule (or a cron) accumulates
history and re-runs are no-ops. Only the columns AUREUM needs are kept.
"""

from __future__ import annotations

import io
import logging
import zipfile

import pandas as pd

from ..http import fetch_bytes, fetch_text
from ..lake import write_increment

log = logging.getLogger(__name__)

LASTUPDATE_URL = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"

# GDELT 2.0 event table: 61 tab-separated columns, no header.
# 0-indexed positions per the official codebook.
N_COLUMNS = 61
_KEEP = {
    0: "event_id",
    1: "event_date",          # YYYYMMDD
    26: "event_code",         # CAMEO
    28: "event_root_code",
    29: "quad_class",         # 1/2 cooperation, 3/4 conflict
    30: "goldstein",          # -10 (destabilising) .. +10
    33: "num_articles",
    34: "avg_tone",
    53: "action_country",     # ISO country of the action
    60: "source_url",
}


def parse_events(blob: bytes) -> pd.DataFrame:
    df = pd.read_csv(
        io.BytesIO(blob),
        sep="\t",
        header=None,
        dtype=str,
        quoting=3,  # QUOTE_NONE: raw news URLs contain stray quotes
        encoding="utf-8",
        encoding_errors="replace",
    )
    if df.shape[1] != N_COLUMNS:
        raise ValueError(f"expected {N_COLUMNS} columns, got {df.shape[1]}")
    df = df[list(_KEEP)].rename(columns=_KEEP)
    for col in ["quad_class", "num_articles"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in ["goldstein", "avg_tone"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def latest_export_url() -> str:
    # lastupdate.txt: three lines (size, hash, url) — export, mentions, gkg.
    for line in fetch_text(LASTUPDATE_URL).splitlines():
        parts = line.split()
        if parts and parts[-1].endswith(".export.CSV.zip"):
            return parts[-1]
    raise ValueError("no export file listed in lastupdate.txt")


def run() -> dict[str, int]:
    url = latest_export_url()
    file_id = url.rsplit("/", 1)[-1].split(".")[0]  # e.g. 20260829171500
    blob = fetch_bytes(url)
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        df = parse_events(zf.read(zf.namelist()[0]))
    dest = write_increment(df, "gdelt", "events", partition=file_id[:8], file_id=file_id)
    return {"rows": len(df) if dest else 0, "file_id": file_id, "skipped": dest is None}
