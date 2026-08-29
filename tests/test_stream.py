import json

import pandas as pd

from aureum.stream import sink as sink_mod
from aureum.stream.paxg import parse_trade
from aureum.stream.polymarket_ws import parse_event
from aureum.stream.sink import LakeSink


def test_paxg_parse_trade():
    raw = json.dumps(
        {"e": "trade", "T": 1787950000000, "t": 42, "p": "4461.2", "q": "0.5", "m": True}
    )
    event = parse_trade(raw)
    assert event["price"] == 4461.2
    assert event["trade_id"] == 42
    assert parse_trade(json.dumps({"e": "ping"})) is None


def test_polymarket_parse_book_and_price_change():
    book = json.dumps(
        [
            {
                "event_type": "book",
                "asset_id": "tok1",
                "bids": [{"price": "0.80", "size": "100"}, {"price": "0.82", "size": "50"}],
                "asks": [{"price": "0.85", "size": "70"}, {"price": "0.84", "size": "20"}],
            },
            {
                "event_type": "price_change",
                "asset_id": "tok1",
                "changes": [{"price": "0.83", "size": "10", "side": "BUY"}],
            },
        ]
    )
    rows = parse_event(book)
    assert len(rows) == 2
    assert rows[0]["best_bid"] == 0.82
    assert rows[0]["best_ask"] == 0.84
    assert rows[1]["price"] == 0.83


def test_lake_sink_flushes_on_max_buffer(tmp_path, monkeypatch):
    monkeypatch.setattr(sink_mod, "write_increment", _spy := _WriteSpy())
    s = LakeSink("paxg", "trades", flush_seconds=9999, max_buffer=3)
    for i in range(3):
        s.add({"trade_id": i, "price": 4000.0 + i})
    assert _spy.calls == 1
    assert s.flushed_rows == 3
    s.add({"trade_id": 9, "price": 4009.0})
    s.close()
    assert _spy.calls == 2


class _WriteSpy:
    def __init__(self):
        self.calls = 0

    def __call__(self, df, source, table, partition, file_id):
        assert isinstance(df, pd.DataFrame)
        self.calls += 1
