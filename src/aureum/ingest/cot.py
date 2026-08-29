"""CFTC Commitments of Traders, legacy futures-only report.

Weekly positioning of large speculators (non-commercials) and hedgers
(commercials) — the closest public window into "who is pushing this market".
Yearly zips, keyless. Landed tidy: one row per (report_date, instrument).
"""

from __future__ import annotations

import io
import logging
import zipfile
from datetime import UTC, datetime

import pandas as pd

from ..config import COT_MARKETS, COT_YEARS_BACK
from ..http import fetch_bytes
from ..lake import write_snapshot

log = logging.getLogger(__name__)

URL = "https://www.cftc.gov/files/dea/history/deacot{year}.zip"

# Header aliases in the legacy file, matched case-insensitively by prefix
# ("commercial…" as a substring would also hit "Noncommercial…").
_COLUMNS = {
    "market_name": ["market and exchange names"],
    "report_date": ["as of date in form yyyy-mm-dd"],
    "open_interest": ["open interest (all)"],
    "noncomm_long": ["noncommercial positions-long (all)"],
    "noncomm_short": ["noncommercial positions-short (all)"],
    "comm_long": ["commercial positions-long (all)"],
    "comm_short": ["commercial positions-short (all)"],
}


def _find(columns: list[str], aliases: list[str]) -> str:
    for col in columns:
        for alias in aliases:
            if col.strip().lower().startswith(alias):
                return col
    raise KeyError(f"no column matching {aliases!r}")


def parse_cot_csv(text: str) -> pd.DataFrame:
    raw = pd.read_csv(io.StringIO(text), low_memory=False)
    cols = {key: _find(list(raw.columns), aliases) for key, aliases in _COLUMNS.items()}
    df = raw[[cols[k] for k in _COLUMNS]].copy()
    df.columns = list(_COLUMNS)

    frames = []
    upper = df["market_name"].astype(str).str.upper()
    for instrument, patterns in COT_MARKETS.items():
        mask = pd.Series(False, index=df.index)
        for pattern in patterns:
            mask |= upper.str.contains(pattern.upper(), regex=False)
        sub = df[mask].copy()
        sub["instrument"] = instrument
        frames.append(sub)
    out = pd.concat(frames, ignore_index=True)

    out["report_date"] = pd.to_datetime(out["report_date"]).dt.date
    for col in ["open_interest", "noncomm_long", "noncomm_short", "comm_long", "comm_short"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["net_noncommercial"] = out["noncomm_long"] - out["noncomm_short"]
    out["net_commercial"] = out["comm_long"] - out["comm_short"]
    return out[
        [
            "report_date",
            "instrument",
            "market_name",
            "open_interest",
            "noncomm_long",
            "noncomm_short",
            "comm_long",
            "comm_short",
            "net_noncommercial",
            "net_commercial",
        ]
    ].sort_values(["instrument", "report_date"])


def run(years_back: int = COT_YEARS_BACK) -> dict[str, int]:
    this_year = datetime.now(tz=UTC).year
    frames = []
    for year in range(this_year - years_back + 1, this_year + 1):
        try:
            blob = fetch_bytes(URL.format(year=year))
            with zipfile.ZipFile(io.BytesIO(blob)) as zf:
                inner = zf.namelist()[0]
                frames.append(parse_cot_csv(zf.read(inner).decode("utf-8", errors="replace")))
        except Exception:
            log.exception("cot %s failed, continuing", year)
    if not frames:
        return {"rows": 0}
    df = pd.concat(frames, ignore_index=True).drop_duplicates(["report_date", "instrument"])
    write_snapshot(df, "cot", "legacy_futures", source_url=URL)
    return {"rows": len(df), "instruments": df["instrument"].nunique()}
