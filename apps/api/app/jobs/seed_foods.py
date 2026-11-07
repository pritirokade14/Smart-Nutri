"""Seed the generic foods, household portions, densities and documented Indian dishes
(Plan 12 Task 3; ADR 0024). Idempotent: an upsert by (source, source_code), so food ids stay
stable across reseeds and old diary entries keep their `food_id`.

    python -m app.jobs.seed_foods [--check]

`--check` reads and validates the data files and prints the report; it does not connect to the
database and writes nothing. Without it the rows are upserted. Logs and output carry counts
and dish codes only, never connection details.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from collections.abc import Sequence

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import build_engine, build_sessionmaker
from app.features.foods.seed import SeedReport, load_seed_data, report_for, seed_foods

logger = logging.getLogger("app.jobs.seed_foods")


def format_report(report: SeedReport) -> str:
    lines = [
        f"{report.foods} foods",
        f"{report.dishes_seeded} dishes seeded",
        f"{len(report.dishes_excluded)} dishes excluded",
        *(f"  - {code}: {why}" for code, why in sorted(report.dishes_excluded.items())),
        f"{report.portions} portions",
        f"{report.densities} densities",
    ]
    return "\n".join(lines)


async def _run() -> SeedReport:
    engine = build_engine(get_settings())
    try:
        async with build_sessionmaker(engine)() as session:
            return await seed_foods(session)
    finally:
        await engine.dispose()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.jobs.seed_foods")
    parser.add_argument("--check", action="store_true", help="validate and report; write nothing")
    args = parser.parse_args(argv)
    configure_logging(get_settings().log_level)
    if args.check:
        print(format_report(report_for(load_seed_data())))
        return 0
    report = asyncio.run(_run())
    logger.info(
        "foods seeded",
        extra={"foods": report.foods, "dishes": report.dishes_seeded, "portions": report.portions},
    )
    print(format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
