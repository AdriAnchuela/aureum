"""Streaming consumers: WebSocket sources → micro-batch sinks.

Two paths, chosen per run:
- lake sink (zero infra): events buffer in memory and flush to incremental
  parquet partitions — same idempotent contract as batch ingestion.
- kafka sink (Redpanda via docker compose): events publish to a topic;
  `aureum stream consume` drains topics back into the lake. The broker buys
  replay and fan-out; the lake path keeps `make` targets runnable anywhere.
"""
