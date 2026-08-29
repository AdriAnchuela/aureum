"""Live prediction-market odds: Polymarket CLOB market channel.

Subscribes to the top macro markets (as selected by the batch snapshot in
the lake — the batch layer decides *what* matters, the stream layer watches
it move). Book snapshots, price changes and trades land as tidy rows.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import websockets

from ..config import LAKE_DIR

log = logging.getLogger(__name__)

WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"


def top_macro_tokens(top: int = 25, lake_dir: Path | None = None) -> list[str]:
    """Token ids of the highest-volume macro outcomes from the latest snapshot."""
    path = (lake_dir or LAKE_DIR) / "raw/polymarket/macro_odds/latest.parquet"
    if not path.exists():
        raise FileNotFoundError("run `aureum ingest polymarket` first — the stream follows it")
    df = pd.read_parquet(path).dropna(subset=["token_id"])
    df = df.sort_values("volume_24h", ascending=False).drop_duplicates("market_id")
    return df["token_id"].head(top).tolist()


def _best(levels: list[dict], side: str) -> float | None:
    prices = [float(entry["price"]) for entry in levels or [] if entry.get("price")]
    if not prices:
        return None
    return max(prices) if side == "bid" else min(prices)


def parse_event(raw: str) -> list[dict]:
    doc = json.loads(raw)
    messages = doc if isinstance(doc, list) else [doc]
    ts = datetime.now(tz=UTC)
    rows = []
    for m in messages:
        if not isinstance(m, dict):
            continue
        etype = m.get("event_type")
        base = {"ts_recv": ts, "event_type": etype, "asset_id": m.get("asset_id")}
        if etype == "book":
            rows.append(
                base
                | {
                    "best_bid": _best(m.get("bids") or m.get("buys"), "bid"),
                    "best_ask": _best(m.get("asks") or m.get("sells"), "ask"),
                    "price": None,
                    "size": None,
                }
            )
        elif etype == "price_change":
            for change in m.get("changes") or []:
                rows.append(
                    base
                    | {
                        "best_bid": None,
                        "best_ask": None,
                        "price": float(change["price"]) if change.get("price") else None,
                        "size": float(change["size"]) if change.get("size") else None,
                    }
                )
        elif etype == "last_trade_price":
            rows.append(
                base
                | {
                    "best_bid": None,
                    "best_ask": None,
                    "price": float(m["price"]) if m.get("price") else None,
                    "size": float(m["size"]) if m.get("size") else None,
                }
            )
    return rows


async def stream(sink, minutes: float = 0, top: int = 25) -> None:
    tokens = top_macro_tokens(top)
    log.info("polymarket: subscribing to %d assets", len(tokens))
    deadline = time.monotonic() + minutes * 60 if minutes else None
    while deadline is None or time.monotonic() < deadline:
        try:
            async with websockets.connect(WS_URL, ping_interval=20) as ws:
                await ws.send(json.dumps({"assets_ids": tokens, "type": "market"}))
                log.info("polymarket: connected")
                while deadline is None or time.monotonic() < deadline:
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=5)
                    except TimeoutError:
                        continue
                    for event in parse_event(raw):
                        sink.add(event)
        except Exception:
            if deadline is not None and time.monotonic() >= deadline:
                break
            log.exception("polymarket: connection dropped, reconnecting in 3s")
            await asyncio.sleep(3)
    sink.close()
