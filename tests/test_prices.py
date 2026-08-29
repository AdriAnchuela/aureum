import json

import pytest

from aureum.ingest.prices import parse_yahoo_chart

PAYLOAD = json.dumps(
    {
        "chart": {
            "result": [
                {
                    "timestamp": [1787918400, 1788004800],
                    "indicators": {
                        "quote": [
                            {
                                "open": [3340.1, 3355.0],
                                "high": [3361.0, 3372.9],
                                "low": [3333.2, 3350.1],
                                "close": [3355.4, None],
                                "volume": [120000, 90000],
                            }
                        ]
                    },
                }
            ],
            "error": None,
        }
    }
)


def test_parse_tidies_tags_symbol_and_drops_null_closes():
    df = parse_yahoo_chart(PAYLOAD, "GC=F", "gold_futures")
    assert len(df) == 1  # the None close is dropped
    assert df["symbol"].iloc[0] == "GC=F"
    assert df["close"].iloc[0] == 3355.4


def test_parse_raises_on_yahoo_error_envelope():
    payload = json.dumps({"chart": {"result": None, "error": {"code": "Not Found"}}})
    with pytest.raises(ValueError):
        parse_yahoo_chart(payload, "XAUUSD=X", "gold_spot")
