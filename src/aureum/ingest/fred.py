"""Macro series from FRED via the keyless fredgraph.csv endpoint.

The official API (with key) is a drop-in upgrade; phase 1 favours
zero-setup reproducibility. fredgraph is served behind a WAF that drops
some python clients, hence curl_fallback=True (see aureum.http).
"""

from __future__ import annotations

import io
import logging

import pandas as pd

from ..config import FRED_SERIES
from ..http import fetch_text
from ..lake import write_snapshot

log = logging.getLogger(__name__)

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"


def parse_fred_csv(text: str, series_id: str, name: str) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(text))
    if df.shape[1] != 2:
        raise ValueError(f"unexpected fredgraph payload for {series_id}: {df.shape[1]} columns")
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"]).dt.date
    # FRED encodes missing observations as "."
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])
    df["series_id"] = series_id
    df["name"] = name
    return df[["date", "series_id", "name", "value"]]


def run() -> dict[str, int]:
    frames = []
    for series_id, name in FRED_SERIES.items():
        url = URL.format(series=series_id)
        try:
            frames.append(parse_fred_csv(fetch_text(url, curl_fallback=True), series_id, name))
        except Exception:
            log.exception("fred %s failed, continuing", series_id)
    if not frames:
        return {"rows": 0}
    df = pd.concat(frames, ignore_index=True)
    write_snapshot(df, "fred", "series", source_url=URL)
    return {"rows": len(df), "series": df["series_id"].nunique()}
