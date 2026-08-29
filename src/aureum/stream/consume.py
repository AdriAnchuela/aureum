"""Drain Redpanda topics back into the lake (the kafka→lake leg)."""

from __future__ import annotations

import json
import logging
import time

log = logging.getLogger(__name__)

TOPIC_TABLES = {
    "aureum.paxg.trades": ("paxg", "trades"),
    "aureum.polymarket.market": ("polymarket", "market_events"),
}


def consume(topic: str, sink, minutes: float = 1.0, bootstrap: str = "localhost:9092") -> None:
    from confluent_kafka import Consumer  # optional dependency, import here

    consumer = Consumer(
        {
            "bootstrap.servers": bootstrap,
            "group.id": "aureum-lake-writer",
            "auto.offset.reset": "earliest",
        }
    )
    consumer.subscribe([topic])
    deadline = time.monotonic() + minutes * 60
    try:
        while time.monotonic() < deadline:
            msg = consumer.poll(1.0)
            if msg is None or msg.error():
                continue
            sink.add(json.loads(msg.value()))
    finally:
        consumer.close()
        sink.close()
