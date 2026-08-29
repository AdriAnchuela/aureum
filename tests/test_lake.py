import pandas as pd

from aureum import lake


def test_snapshot_writes_dated_copy_and_latest(tmp_path, monkeypatch):
    monkeypatch.setattr(lake, "LAKE_DIR", tmp_path)
    df = pd.DataFrame({"date": ["2026-08-28"], "close": [3350.0]})

    dest = lake.write_snapshot(df, "prices", "daily", source_url="http://x")

    assert dest.name == "latest.parquet"
    snapshots = list((tmp_path / "raw/prices/daily").glob("snapshot_date=*/data.parquet"))
    assert len(snapshots) == 1
    assert pd.read_parquet(dest).equals(df)


def test_snapshot_rerun_same_day_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(lake, "LAKE_DIR", tmp_path)
    df = pd.DataFrame({"a": [1]})
    lake.write_snapshot(df, "s", "t")
    lake.write_snapshot(df, "s", "t")
    assert len(list((tmp_path / "raw/s/t").glob("snapshot_date=*"))) == 1


def test_increment_skips_already_landed_file(tmp_path, monkeypatch):
    monkeypatch.setattr(lake, "LAKE_DIR", tmp_path)
    df = pd.DataFrame({"a": [1]})
    first = lake.write_increment(df, "gdelt", "events", "20260829", "20260829171500")
    second = lake.write_increment(df, "gdelt", "events", "20260829", "20260829171500")
    assert first is not None
    assert second is None  # no-op: safe blind retries
