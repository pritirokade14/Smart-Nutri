"""Seed a diary fixture input (packages/test-fixtures/diary/inputs) as `meal_logs` rows.

Rows are inserted directly (not through POST /v1/meals): a quick add leaves sugars, salt and
saturated fat unknown, and the fixtures give entries every value they need.
"""

import json
from datetime import date, datetime, time
from uuid import uuid4

from app.core.time import zone
from app.features.meals.models import MealLog
from tests.fixtures.loader import FIXTURES

OFF_BARCODE = "8900000000000"
# Keys that differ between a seeded database and a fixture (generated ids and timestamps).
# `weight_source` (slice 6) is not in the day goldens (they have no weigh-ins); `normalise`
# asserts it is "latest" (or null when hidden) and drops it. The "trend" case is the shared
# target golden g5_taper_trend.
DROP = {
    "id",
    "member_id",
    "slot_id",
    "meal_slot_id",
    "product_id",
    "updated_at",
    "client_id",
}


def load_input(stem: str) -> dict:
    return json.loads((FIXTURES / "diary" / "inputs" / f"{stem}.json").read_text(encoding="utf-8"))


def load_expected(stem: str) -> dict:
    return json.loads(
        (FIXTURES / "diary" / "expected" / f"{stem}.json").read_text(encoding="utf-8")
    )


def seed_entries(
    db_session, account_id, member_id, slot_ids: dict[str, str], day: str, items, tz, product_id
):
    """Insert the entries of one day. ``slot_ids`` maps a slot key (breakfast, lunch, ...) to
    its id; ``product_id`` is any existing product (the rows of kind `product` need one)."""
    d = date.fromisoformat(day)
    for item in items:
        hh, mm = item["local_time"].split(":")
        at = datetime.combine(d, time(int(hh), int(mm)), tzinfo=zone(tz))
        kind = item["source_kind"]
        db_session.add(
            MealLog(
                id=uuid4(),
                account_id=account_id,
                member_id=member_id,
                meal_slot_id=slot_ids[item["slot"]],
                local_date=d,
                eaten_at=at,
                source_kind=kind,
                product_id=product_id if kind == "product" else None,
                off_barcode=OFF_BARCODE if kind == "off" else None,
                product_name=item["name"],
                grams=item["grams"],
                nutrients=dict(item["nutrients"]),
            )
        )


def _instant(value: str) -> str:
    """The same instant in UTC (the fixture keeps the +05:30 offset, the database returns Z)."""
    return datetime.fromisoformat(value).astimezone(zone("UTC")).isoformat()


def normalise(node):
    """The response without ids and update times, with instants in UTC, for comparing with an
    expected file."""
    if isinstance(node, dict):
        if "weight_source" in node:
            assert node["weight_source"] in ("latest", None), node["weight_source"]
        return {
            k: _instant(v)
            if k in ("eaten_at", "last_eaten_at") and isinstance(v, str)
            else normalise(v)
            for k, v in node.items()
            if k not in DROP and k != "weight_source"
        }
    if isinstance(node, list):
        return [normalise(v) for v in node]
    return node
