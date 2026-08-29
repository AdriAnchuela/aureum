import json

from aureum.ingest.polymarket import is_macro, parse_markets

PAYLOAD = json.dumps(
    [
        {
            "id": "111",
            "question": "Will the Fed cut rates in September?",
            "slug": "fed-cut-september",
            "outcomes": '["Yes", "No"]',
            "outcomePrices": '["0.83", "0.17"]',
            "clobTokenIds": '["tok1", "tok2"]',
            "volume24hr": 250000.5,
            "liquidity": 90000.1,
            "endDate": "2026-09-17T18:00:00Z",
        },
        {
            "id": "222",
            "question": "LoL: Top Esports vs LGD Gaming (BO5)",
            "outcomes": '["TES", "LGD"]',
            "outcomePrices": '["0.6", "0.4"]',
            "clobTokenIds": "[]",
            "volume24hr": 9e9,
        },
    ]
)


def test_parse_keeps_macro_drops_esports():
    df = parse_markets(PAYLOAD)
    assert df["market_id"].unique().tolist() == ["111"]
    assert len(df) == 2  # Yes + No rows
    yes = df[df["outcome"] == "Yes"].iloc[0]
    assert yes["implied_prob"] == 0.83
    assert yes["token_id"] == "tok1"


def test_keyword_filter():
    assert is_macro("Russia-Ukraine ceasefire in 2026?")
    assert not is_macro("Champions League winner")


def test_borussia_is_not_russia():
    # substring matching would see bo-RUSSIA-; word boundaries must not
    assert not is_macro("Will BV Borussia 09 Dortmund win on 2026-08-29?")
    assert not is_macro("Golden State Warriors to win the NBA title?")
