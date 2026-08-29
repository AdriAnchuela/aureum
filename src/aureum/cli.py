"""CLI entry point: `aureum ingest [all|prices|fred|cot|gdelt]`."""

from __future__ import annotations

import argparse
import logging
import sys

from .ingest import cot, fred, gdelt, prices

log = logging.getLogger(__name__)

INGESTORS = {"prices": prices.run, "fred": fred.run, "cot": cot.run, "gdelt": gdelt.run}


def main() -> int:
    parser = argparse.ArgumentParser(prog="aureum")
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest", help="run batch ingestors into the lake")
    ingest.add_argument("sources", nargs="+", choices=["all", *INGESTORS])
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    sources = list(INGESTORS) if "all" in args.sources else args.sources
    failed = []
    for name in sources:
        try:
            summary = INGESTORS[name]()
            print(f"{name}: {summary}")
        except Exception as exc:  # one source failing must not sink the rest
            log.exception("%s failed", name)
            failed.append((name, exc))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
