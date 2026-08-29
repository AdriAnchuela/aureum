"""CLI entry point.

    aureum ingest [all|prices|fred|cot|gdelt|polymarket]
    aureum stream [paxg|polymarket] --minutes N --sink lake|kafka
    aureum stream consume --topic aureum.paxg.trades --minutes N
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from .ingest import cot, fred, gdelt, polymarket, prices

log = logging.getLogger(__name__)

INGESTORS = {
    "prices": prices.run,
    "fred": fred.run,
    "cot": cot.run,
    "gdelt": gdelt.run,
    "polymarket": polymarket.run,
}


def _run_ingest(args: argparse.Namespace) -> int:
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


def _make_sink(kind: str, source: str):
    from .stream.sink import KafkaSink, LakeSink

    if kind == "kafka":
        return KafkaSink(topic=f"aureum.{source}.{'trades' if source == 'paxg' else 'market'}")
    table = "trades" if source == "paxg" else "market_events"
    return LakeSink(source=source, table=table)


def _run_stream(args: argparse.Namespace) -> int:
    if args.source == "consume":
        from .stream.consume import TOPIC_TABLES, consume
        from .stream.sink import LakeSink

        source, table = TOPIC_TABLES[args.topic]
        sink = LakeSink(source=source, table=table)
        consume(args.topic, sink, minutes=args.minutes)
    else:
        sink = _make_sink(args.sink, args.source)
        if args.source == "paxg":
            from .stream import paxg

            asyncio.run(paxg.stream(sink, minutes=args.minutes))
        else:
            from .stream import polymarket_ws

            asyncio.run(polymarket_ws.stream(sink, minutes=args.minutes, top=args.top))
    print(f"{args.source}: {sink.flushed_rows} events")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="aureum")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="run batch ingestors into the lake")
    ingest.add_argument("sources", nargs="+", choices=["all", *INGESTORS])
    ingest.set_defaults(func=_run_ingest)

    stream = sub.add_parser("stream", help="run streaming consumers")
    stream.add_argument("source", choices=["paxg", "polymarket", "consume"])
    stream.add_argument("--minutes", type=float, default=0, help="0 = run until interrupted")
    stream.add_argument("--sink", choices=["lake", "kafka"], default="lake")
    stream.add_argument("--top", type=int, default=25, help="polymarket: top-N macro assets")
    stream.add_argument("--topic", default="aureum.paxg.trades", help="consume: source topic")
    stream.set_defaults(func=_run_stream)

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
