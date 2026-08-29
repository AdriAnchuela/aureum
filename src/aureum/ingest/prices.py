"""Daily OHLC from the Yahoo Finance chart API (keyless JSON endpoint).

Stooq was the original source but now serves a JavaScript anti-bot challenge
to non-browser clients; Yahoo's v8 chart endpoint works with a plain UA.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from urllib.parse import quote

import pandas as pd

from ..config import YAHOO_SYMBOLS
from ..http import fetch_text
from ..lake import write_snapshot

log = logging.getLogger(__name__)

URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=10y&interval=1d"


def parse_yahoo_chart(payload: str, symbol: str, name: str) -> pd.DataFrame:
    doc = json.loads(payload)
    result = (doc.get("chart") or {}).get("result")
    if not result:
        error = (doc.get("chart") or {}).get("error")
        raise ValueError(f"yahoo returned no data for {symbol}: {error}")
    node = result[0]
    quotes = node["indicators"]["quote"][0]
    df = pd.DataFrame(
        {
            "date": [
                datetime.fromtimestamp(ts, tz=UTC).date() for ts in node.get("timestamp", [])
            ],
            "open": quotes.get("open"),
            "high": quotes.get("high"),
            "low": quotes.get("low"),
            "close": quotes.get("close"),
            "volume": quotes.get("volume"),
        }
    )
    df = df.dropna(subset=["close"])
    df["symbol"] = symbol
    df["name"] = name
    return df[["date", "symbol", "name", "open", "high", "low", "close", "volume"]]


def run() -> dict[str, int]:
    frames = []
    for symbol, name in YAHOO_SYMBOLS.items():
        url = URL.format(symbol=quote(symbol))
        try:
            frames.append(parse_yahoo_chart(fetch_text(url), symbol, name))
        except Exception:
            log.exception("yahoo %s failed, continuing", symbol)
    if not frames:
        return {"rows": 0}
    df = pd.concat(frames, ignore_index=True)
    write_snapshot(df, "prices", "daily", source_url=URL)
    return {"rows": len(df), "symbols": df["symbol"].nunique()}
