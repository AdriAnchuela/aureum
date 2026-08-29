from aureum.ingest.cot import parse_cot_csv

CSV = (
    '"Market and Exchange Names","As of Date in Form YYMMDD","As of Date in Form YYYY-MM-DD",'
    '"Open Interest (All)","Noncommercial Positions-Long (All)",'
    '"Noncommercial Positions-Short (All)",'
    '"Commercial Positions-Long (All)","Commercial Positions-Short (All)"\n'
    '"GOLD - COMMODITY EXCHANGE INC.",260825,2026-08-25,500000,300000,80000,120000,340000\n'
    '"UST 10Y NOTE - CHICAGO BOARD OF TRADE",'
    '260825,2026-08-25,4000000,900000,1400000,2000000,1500000\n'
    '"WHEAT-SRW - CHICAGO BOARD OF TRADE",260825,2026-08-25,1,1,1,1,1\n'
)


def test_parse_selects_configured_markets_and_computes_nets():
    df = parse_cot_csv(CSV)
    assert set(df["instrument"]) == {"gold", "us_treasury_10y"}
    gold = df[df["instrument"] == "gold"].iloc[0]
    assert gold["net_noncommercial"] == 220000
    assert gold["net_commercial"] == -220000
    # wheat is not a configured market and must not leak through
    assert "WHEAT" not in " ".join(df["market_name"])
