import pytest

from aureum.ingest.gdelt import N_COLUMNS, parse_events


def _row(event_id="1", quad_class="4", goldstein="-8.0", articles="12"):
    cols = [""] * N_COLUMNS
    cols[0] = event_id
    cols[1] = "20260829"
    cols[26] = "190"
    cols[28] = "19"
    cols[29] = quad_class
    cols[30] = goldstein
    cols[33] = articles
    cols[34] = "-4.5"
    cols[53] = "UA"
    cols[60] = "https://example.com/article"
    return "\t".join(cols)


def test_parse_keeps_named_subset_with_types():
    blob = (_row("1") + "\n" + _row("2", quad_class="1", goldstein="5.0")).encode()
    df = parse_events(blob)
    assert len(df) == 2
    assert df["quad_class"].tolist() == [4, 1]
    assert df["goldstein"].tolist() == [-8.0, 5.0]
    assert df["action_country"].iloc[0] == "UA"


def test_parse_rejects_wrong_column_count():
    with pytest.raises(ValueError):
        parse_events(b"a\tb\tc\n")
