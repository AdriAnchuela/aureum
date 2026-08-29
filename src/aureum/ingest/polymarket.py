"""Prediction-market odds from Polymarket's Gamma API (keyless REST).

The order book's top markets are mostly sports; AUREUM cares about macro.
Markets are pulled by 24h volume and filtered by macro keywords, landing a
daily snapshot of implied probabilities. The WebSocket streaming consumer
(aureum.stream) covers the tick-level view; this batch snapshot is what the
dashboard and the marts read.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime

import pandas as pd

from ..http import fetch_text
from ..lake import write_snapshot

log = logging.getLogger(__name__)

URL = (
    "https://gamma-api.polymarket.com/markets"
    "?closed=false&order=volume24hr&ascending=false&limit=100&offset={offset}"
)
PAGES = 5

# A market qualifies if its question matches any macro keyword (lowercase).
MACRO_KEYWORDS = [
    "fed", "rate cut", "rate hike", "interest rate", "recession", "inflation",
    "cpi", "gdp", "tariff", "gold", "treasury", "dollar", "election",
    "war", "ceasefire", "invasion", "nuclear", "sanction", "opec", "oil",
    "china", "taiwan", "ukraine", "russia", "iran", "israel", "shutdown",
    "debt ceiling", "default", "central bank", "ecb", "stock market", "s&p",
]


# Word boundaries matter: plain substring matching lets "Borussia" qualify
# as macro news because bo-RUSSIA-. Found the hard way, kept as a test.
_MACRO_RE = re.compile("|".join(rf"\b{re.escape(k)}\b" for k in MACRO_KEYWORDS))


def is_macro(question: str) -> bool:
    return bool(_MACRO_RE.search(question.lower()))


def parse_markets(payload: str) -> pd.DataFrame:
    rows = []
    fetched_at = datetime.now(tz=UTC)
    for m in json.loads(payload):
        question = m.get("question") or ""
        if not is_macro(question):
            continue
        try:
            outcomes = json.loads(m.get("outcomes") or "[]")
            prices = [float(p) for p in json.loads(m.get("outcomePrices") or "[]")]
            token_ids = json.loads(m.get("clobTokenIds") or "[]")
        except (ValueError, TypeError):
            continue
        for i, outcome in enumerate(outcomes):
            if i >= len(prices):
                continue
            rows.append(
                {
                    "fetched_at": fetched_at,
                    "market_id": str(m.get("id")),
                    "question": question,
                    "slug": m.get("slug"),
                    "outcome": outcome,
                    "implied_prob": prices[i],
                    "token_id": token_ids[i] if i < len(token_ids) else None,
                    "volume_24h": float(m.get("volume24hr") or 0),
                    "liquidity": float(m.get("liquidity") or 0),
                    "end_date": m.get("endDate"),
                }
            )
    return pd.DataFrame(rows)


def run() -> dict[str, int]:
    frames = []
    for page in range(PAGES):
        try:
            frames.append(parse_markets(fetch_text(URL.format(offset=page * 100))))
        except Exception:
            log.exception("polymarket page %d failed, continuing", page)
    if not frames:
        return {"rows": 0}
    df = pd.concat(frames, ignore_index=True)
    if df.empty:
        return {"rows": 0}
    df = df.drop_duplicates(["market_id", "outcome"])
    write_snapshot(df, "polymarket", "macro_odds", source_url=URL)
    return {"rows": len(df), "markets": df["market_id"].nunique()}
