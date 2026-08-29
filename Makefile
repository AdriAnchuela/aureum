PY := .venv/bin/python
PIP := .venv/bin/pip

setup:            ## Create venv and install the package with dev tools
	python3 -m venv .venv
	$(PIP) install -e ".[dev]"

ingest:           ## Run all batch ingestors (prices, FRED, COT, GDELT)
	$(PY) -m aureum.cli ingest all

test:             ## Run unit tests (offline: parsers are tested against fixtures)
	.venv/bin/pytest -q

lint:             ## Ruff static checks
	.venv/bin/ruff check src tests

warehouse:        ## Build dbt models into the DuckDB warehouse
	$(PIP) install -q -e ".[warehouse]"
	cd warehouse && ../.venv/bin/dbt build --profiles-dir .

dagster:          ## Launch the Dagster UI with the daily/15-min schedules
	$(PIP) install -q -e ".[orchestration]"
	.venv/bin/dagster dev -f orchestration/definitions.py

help:
	@grep -E '^[a-z]+:.*##' Makefile | sed 's/:.*##/ —/'
