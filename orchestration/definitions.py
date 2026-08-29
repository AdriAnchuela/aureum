"""Dagster definitions: each ingestor is an asset; two schedules drive them.

Run locally with `make dagster` — the UI shows lineage, runs and failures.
"""

from __future__ import annotations

import dagster as dg

from aureum.ingest import cot, fred, gdelt, prices


@dg.asset(group_name="batch")
def prices_daily() -> dg.MaterializeResult:
    return dg.MaterializeResult(metadata=prices.run())


@dg.asset(group_name="batch")
def fred_series() -> dg.MaterializeResult:
    return dg.MaterializeResult(metadata=fred.run())


@dg.asset(group_name="batch")
def cot_positioning() -> dg.MaterializeResult:
    return dg.MaterializeResult(metadata=cot.run())


@dg.asset(group_name="near_real_time")
def gdelt_events() -> dg.MaterializeResult:
    return dg.MaterializeResult(metadata=gdelt.run())


batch_job = dg.define_asset_job(
    "batch_daily", selection=[prices_daily, fred_series, cot_positioning]
)
gdelt_job = dg.define_asset_job("gdelt_15min", selection=[gdelt_events])

defs = dg.Definitions(
    assets=[prices_daily, fred_series, cot_positioning, gdelt_events],
    schedules=[
        dg.ScheduleDefinition(
            job=batch_job, cron_schedule="0 7 * * *", execution_timezone="Europe/Madrid"
        ),
        dg.ScheduleDefinition(job=gdelt_job, cron_schedule="*/15 * * * *"),
    ],
)
