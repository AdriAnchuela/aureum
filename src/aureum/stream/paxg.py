"""Tokenised gold, tick by tick: Binance PAXG/USDT trade stream.

Gold's spot market closes on weekends; PAXG trades 24/7, which makes it the
only live window into gold repricing while COMEX sleeps — exactly when
geopolitical shocks tend to land.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import UTC, datetime

import websockets

log = logging.getLogger(__name__)

STREAM_URL = "wss://stream.binance.com:9443/ws/paxgusdt@trade"


def parse_trade(raw: str) -> dict | None:
    d = json.loads(raw)
    if d.get("e") != "trade":
        return None
    return {
        "ts_exchange": datetime.fromtimestamp(d["T"] / 1000, tz=UTC),
        "trade_id": int(d["t"]),
        "price": float(d["p"]),
        "qty": float(d["q"]),
        "buyer_is_maker": bool(d["m"]),
    }


async def stream(sink, minutes: float = 0) -> None:
    """Consume trades into `sink`; minutes=0 means run until interrupted."""
    deadline = time.monotonic() + minutes * 60 if minutes else None
    while deadline is None or time.monotonic() < deadline:
        try:
            async with websockets.connect(STREAM_URL, ping_interval=20) as ws:
                log.info("paxg: connected")
                while deadline is None or time.monotonic() < deadline:
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=5)
                    except TimeoutError:
                        continue
                    event = parse_trade(raw)
                    if event:
                        sink.add(event)
        except Exception:
            if deadline is not None and time.monotonic() >= deadline:
                break
            log.exception("paxg: connection dropped, reconnecting in 3s")
            await asyncio.sleep(3)
    sink.close()
