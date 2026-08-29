"""Central configuration: paths and source registries.

Everything the ingestors pull is declared here, so adding an instrument or a
FRED series is a one-line change reviewed in one place.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

LAKE_DIR = Path(os.getenv("AUREUM_LAKE_DIR") or REPO_ROOT / "lake")
DATA_DIR = Path(os.getenv("AUREUM_DATA_DIR") or REPO_ROOT / "data")

# Yahoo Finance chart API. symbol -> canonical name landed in the lake.
# (Stooq was the first choice but now sits behind a JS anti-bot challenge.)
YAHOO_SYMBOLS: dict[str, str] = {
    "GC=F": "gold_futures",
    "SI=F": "silver_futures",
    "^GSPC": "sp500",
}

# FRED series pulled through the keyless fredgraph.csv endpoint.
FRED_SERIES: dict[str, str] = {
    "DGS10": "us_10y_yield",
    "DGS2": "us_2y_yield",
    "T10Y2Y": "curve_10y_2y",
    "DFII10": "us_10y_real_yield",
    "DTWEXBGS": "usd_broad_index",
    "VIXCLS": "vix",
}

# CFTC COT legacy report: instrument -> substrings that identify its market row.
# Market names drift across years ("10-YEAR U.S. TREASURY NOTES" became
# "UST 10Y NOTE"), hence a list of historical aliases per instrument.
COT_MARKETS: dict[str, list[str]] = {
    "gold": ["GOLD - COMMODITY EXCHANGE"],
    "us_treasury_10y": ["10-YEAR U.S. TREASURY NOTES", "UST 10Y NOTE"],
}
COT_YEARS_BACK = 5
