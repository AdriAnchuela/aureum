import pytest

from aureum.ingest.fred import parse_fred_csv

CSV = """DATE,DGS10
2026-08-25,4.21
2026-08-26,.
2026-08-27,4.18
"""


def test_parse_drops_missing_dot_values():
    df = parse_fred_csv(CSV, "DGS10", "us_10y_yield")
    assert len(df) == 2
    assert df["value"].tolist() == [4.21, 4.18]
    assert set(df.columns) == {"date", "series_id", "name", "value"}


def test_parse_rejects_unexpected_shape():
    with pytest.raises(ValueError):
        parse_fred_csv("a,b,c\n1,2,3\n", "DGS10", "x")
