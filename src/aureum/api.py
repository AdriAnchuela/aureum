"""Read-only JSON API over the DuckDB warehouse.

    uvicorn aureum.api:app --port 8000

Each request opens the file read-only, so dbt can rebuild underneath
without coordination — the warehouse is the contract, not the process.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import duckdb
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import DATA_DIR

DB_PATH = Path(os.getenv("AUREUM_DUCKDB_PATH") or DATA_DIR / "aureum.duckdb")

app = FastAPI(title="AUREUM API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("AUREUM_ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _query(sql: str, params: list | None = None) -> list[dict]:
    if not DB_PATH.exists():
        raise HTTPException(503, "warehouse not built yet — run `make ingest && make warehouse`")
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        df: pd.DataFrame = con.execute(sql, params or []).df()
    return json.loads(df.to_json(orient="records", date_format="iso"))


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "warehouse": DB_PATH.exists()}


@app.get("/api/macro/daily")
def macro_daily(days: int = 365) -> list[dict]:
    return _query(
        "SELECT * FROM mart_daily_macro WHERE date >= current_date - ? * INTERVAL 1 DAY "
        "ORDER BY date",
        [days],
    )


@app.get("/api/gold/intraday")
def gold_intraday(hours: int = 48) -> list[dict]:
    return _query(
        "SELECT * FROM mart_gold_intraday WHERE minute >= now() - ? * INTERVAL 1 HOUR "
        "ORDER BY minute",
        [hours],
    )


@app.get("/api/risk/daily")
def risk_daily(days: int = 90) -> list[dict]:
    return _query(
        "SELECT * FROM mart_geopolitical_daily "
        "WHERE event_date >= current_date - ? * INTERVAL 1 DAY ORDER BY event_date",
        [days],
    )


@app.get("/api/positioning")
def positioning(instrument: str = "gold") -> list[dict]:
    if instrument not in {"gold", "us_treasury_10y"}:
        raise HTTPException(422, "instrument must be gold or us_treasury_10y")
    return _query(
        "SELECT * FROM mart_cot_positioning WHERE instrument = ? ORDER BY report_date",
        [instrument],
    )


@app.get("/api/odds")
def odds(limit: int = 15) -> list[dict]:
    return _query(
        "SELECT * FROM mart_event_odds ORDER BY volume_24h DESC LIMIT ?", [min(limit, 100)]
    )
