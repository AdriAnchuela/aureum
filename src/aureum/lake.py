"""Parquet lake writer with two landing patterns, both idempotent.

- Snapshot: full-history sources (Stooq, FRED, COT) are cheap to re-pull, so
  each run lands a dated snapshot (audit trail) and atomically replaces a
  `latest.parquet` pointer that the warehouse reads. Re-running a day
  overwrites that day's snapshot — no duplicates.
- Increment: append-only sources (GDELT) land one partition file keyed by the
  publisher's file id. If the file already exists the write is a no-op, so a
  crashed job can always be retried blindly.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from .config import LAKE_DIR

log = logging.getLogger(__name__)


def _write_atomic(df: pd.DataFrame, dest: Path) -> None:
    tmp = dest.with_suffix(".tmp.parquet")
    df.to_parquet(tmp, index=False)
    tmp.replace(dest)


def write_snapshot(df: pd.DataFrame, source: str, table: str, source_url: str = "") -> Path:
    root = LAKE_DIR / "raw" / source / table
    snap_dir = root / f"snapshot_date={datetime.now(tz=UTC).date().isoformat()}"
    snap_dir.mkdir(parents=True, exist_ok=True)
    _write_atomic(df, snap_dir / "data.parquet")
    _write_atomic(df, root / "latest.parquet")
    meta = {
        "fetched_at": datetime.now(tz=UTC).isoformat(),
        "rows": len(df),
        "source_url": source_url,
    }
    (root / "_meta.json").write_text(json.dumps(meta, indent=2))
    log.info("snapshot %s/%s: %d rows", source, table, len(df))
    return root / "latest.parquet"


def write_increment(
    df: pd.DataFrame, source: str, table: str, partition: str, file_id: str
) -> Path | None:
    dest_dir = LAKE_DIR / "raw" / source / table / f"date={partition}"
    dest = dest_dir / f"{file_id}.parquet"
    if dest.exists():
        log.info("increment %s/%s/%s already landed, skipping", source, table, file_id)
        return None
    dest_dir.mkdir(parents=True, exist_ok=True)
    _write_atomic(df, dest)
    log.info("increment %s/%s/%s: %d rows", source, table, file_id, len(df))
    return dest
