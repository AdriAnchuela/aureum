"""Micro-batch sinks for streaming events."""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime

import pandas as pd

from ..lake import write_increment

log = logging.getLogger(__name__)


class LakeSink:
    """Buffers event dicts and flushes them as incremental parquet batches.

    Each flush lands one file keyed by its window-start timestamp, so a
    crashed run can be restarted blindly without duplicating closed windows.
    """

    def __init__(
        self, source: str, table: str, flush_seconds: float = 30.0, max_buffer: int = 5000
    ) -> None:
        self.source = source
        self.table = table
        self.flush_seconds = flush_seconds
        self.max_buffer = max_buffer
        self._buffer: list[dict] = []
        self._window_start = time.monotonic()
        self._window_id = datetime.now(tz=UTC)
        self.flushed_rows = 0

    def add(self, event: dict) -> None:
        self._buffer.append(event)
        age = time.monotonic() - self._window_start
        if len(self._buffer) >= self.max_buffer or age >= self.flush_seconds:
            self.flush()

    def flush(self) -> None:
        if not self._buffer:
            return
        df = pd.DataFrame(self._buffer)
        partition = self._window_id.strftime("%Y%m%d")
        file_id = self._window_id.strftime("%Y%m%d%H%M%S%f")
        write_increment(df, self.source, self.table, partition=partition, file_id=file_id)
        self.flushed_rows += len(self._buffer)
        self._buffer = []
        self._window_start = time.monotonic()
        self._window_id = datetime.now(tz=UTC)

    def close(self) -> None:
        self.flush()


class KafkaSink:
    """Publishes events as JSON to a Redpanda/Kafka topic (optional extra)."""

    def __init__(self, topic: str, bootstrap: str = "localhost:9092") -> None:
        from confluent_kafka import Producer  # optional dependency, import here

        self.topic = topic
        self.producer = Producer({"bootstrap.servers": bootstrap})
        self.flushed_rows = 0

    def add(self, event: dict) -> None:
        self.producer.produce(self.topic, json.dumps(event, default=str).encode())
        self.producer.poll(0)
        self.flushed_rows += 1

    def close(self) -> None:
        self.producer.flush(10)
