"""Check or regenerate the Plan 6 shared fixtures (meal summaries and share texts).

Run from apps/api:
  uv run python scripts/export_meal_fixtures.py          # --check (default): diff, exit 1 if stale
  uv run python scripts/export_meal_fixtures.py --write  # write only the files that differ

Input (hand-written): packages/test-fixtures/meals/week_family.json.
Output (generated, never edited by hand):
  meals/expected/week_family.dad_diabetic.json   GET /v1/meals/summary?period=week for Dad
  share/share_result.sf_biscuit.json             share text for a result, per locale
  share/share_weekly.week_family.json            weekly share text, per locale

The summary comes from the same functions the endpoint runs (snapshot -> summarise with the
engine's daily limits), on in-memory rows with fixed UUIDs, so it cannot drift from the API;
tests/api/meals/test_week_family_fixture.py also inserts the rows and calls the endpoint.
Share texts are built from packages/i18n by the algorithm in each file's "rules", which both
clients implement byte for byte. Format: packages/test-fixtures/README.md.
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

sys.path.insert(0, str(Path(__file__).parents[1]))

from app import scoring
from app.core.config import Settings
from app.core.time import IST
from app.features.meals.models import MealLog
from app.features.meals.service import snapshot
from app.features.meals.summary import summarise
from app.features.members.models import Member
from app.features.members.service import to_scoring_member
from app.features.products import service as products_service
from app.features.products.models import Product
from app.features.products.off_mapping import off_to_info, off_to_product
from scripts.export_fixture_responses import fixture_id, fixture_product_record
from tests.fixtures.loader import FIXTURES, load_member, load_product

MEALS = FIXTURES / "meals"
SHARE = FIXTURES / "share"
MESSAGES = FIXTURES.parents[0] / "i18n" / "messages"
LOCALES = ("en", "hi", "mr")
FORMAT_VERSION = 1
WEEK_FAMILY_ACCOUNT = fixture_id("account", "week_family")
SITE_URL = "https://smartnutri.app"


# --- week_family: rows built exactly as the API stores them ------------------------------


@dataclass(frozen=True)
class WeekFamily:
    end_date: date
    scans: int
    members: dict[str, Member]  # fixture key -> row (fixed ids)
    products: list[Product]  # own catalogue rows (fixed ids)
    meals: list[MealLog]  # every meal in the file, also those outside the week


def _member_id(key: str) -> UUID:
    return fixture_id("member", f"week_family/{key}")


def load_week_family(path: Path = MEALS / "week_family.json") -> WeekFamily:
    data = json.loads(path.read_text(encoding="utf-8"))
    members = {
        key: Member(
            id=_member_id(key),
            account_id=WEEK_FAMILY_ACCOUNT,
            name=m["name"],
            relation=m["relation"],
            birth_year=m["birth_year"],
            weight_kg=m["weight_kg"],
            diet=m["diet"],
            allergens=list(m["allergens"]),
            conditions=list(m["conditions"]),
            custom_alerts=[],
            is_primary=m["relation"] == "self",
        )
        for key, m in data["members"].items()
    }
    settings = Settings(_env_file=None, environment="test")
    records: dict[str, Product] = {}
    meals: list[MealLog] = []
    for i, m in enumerate(data["meals"]):
        if "product" in m:
            record = records.setdefault(m["product"], fixture_product_record(m["product"]))
            found = products_service.lookup_from_record(record)
            product, name, product_id, barcode = found.product, record.name, record.id, None
        else:
            payload = data["off_products"][m["barcode"]]
            product = off_to_product(payload, confidence=settings.off_data_confidence)
            name, product_id, barcode = off_to_info(payload).name, None, m["barcode"]
        grams = float(m["grams"])
        meals.append(
            MealLog(
                id=fixture_id("meal", f"week_family/{i}"),
                account_id=WEEK_FAMILY_ACCOUNT,
                member_id=members[m["member"]].id,
                product_id=product_id,
                off_barcode=barcode,
                product_name=name,
                grade=scoring.analyze(product, []).report.nutriscore.grade,
                grams=grams,
                eaten_at=datetime.fromisoformat(m["eaten_at"]),
                nutrients=snapshot(product.per_100g, grams).model_dump(),
                client_id=None,
            )
        )
    return WeekFamily(
        end_date=date.fromisoformat(data["end_date"]),
        scans=int(data["scans"]),
        members=members,
        products=list(records.values()),
        meals=meals,
    )


def week_summary(family: WeekFamily, member_key: str) -> dict[str, Any]:
    member = family.members[member_key]
    limits = scoring.daily_limits_for(
        to_scoring_member(member, today=family.end_date), member.weight_kg
    )
    own = [m for m in family.meals if m.member_id == member.id]
    s = summarise(own, limits, "week", family.end_date, IST, member_id=member.id)
    return s.model_dump(mode="json")


def logged_in_week(family: WeekFamily) -> int:
    start = family.end_date.toordinal() - 6
    return sum(
        1
        for m in family.meals
        if start <= m.eaten_at.astimezone(IST).date().toordinal() <= family.end_date.toordinal()
    )


# --- share texts -------------------------------------------------------------------------


def _messages(locale: str) -> dict[str, Any]:
    return json.loads((MESSAGES / f"{locale}.json").read_text(encoding="utf-8"))


def _msg(messages: dict[str, Any], key: str) -> str:
    node: Any = messages
    for part in key.split("."):
        node = node[part]
    if not isinstance(node, str):
        raise KeyError(key)
    return node


def _fill(template: str, **params: str) -> str:
    """Plain ICU arguments only ({name}); the share templates have no select or plural."""
    out = template
    for k, v in params.items():
        out = out.replace("{" + k + "}", v)
    if "{" in out or "}" in out:
        raise ValueError(f"unfilled or non-plain ICU argument in {template!r}")
    return out


def who(name: str, relation: str, messages: dict[str, Any]) -> str:
    """First word of the member's name, else the relation label (never more than that)."""
    parts = name.split()
    return parts[0] if parts else _msg(messages, f"share.relation.{relation}")


def share_result_text(
    messages: dict[str, Any],
    *,
    product: str,
    grade: str | None,
    verdicts: list[dict[str, str]],
    url: str,
) -> str:
    joined = ", ".join(
        _fill(
            _msg(messages, "share.result.member"),
            who=who(v["name"], v["relation"], messages),
            status=_msg(messages, f"verdict.status.{v['status']}"),
        )
        for v in verdicts
    )
    if grade is None:
        return _fill(
            _msg(messages, "share.result.ungraded"), product=product, members=joined, url=url
        )
    return _fill(
        _msg(messages, "share.result.text"), product=product, grade=grade, members=joined, url=url
    )


def share_weekly_text(messages: dict[str, Any], *, scans: int, logged: int, url: str) -> str:
    return _fill(_msg(messages, "share.weekly"), scans=str(scans), logged=str(logged), url=url)


def _forbidden(messages: dict[str, Any], locale: str) -> list[str]:
    """Words that must never appear in a share text: condition, allergen and custom alert
    labels (alert.*, Ruling M1 S6)."""
    groups = ("condition", "allergen", "alert")
    words = {v.casefold() for group in groups for v in messages[group].values()}
    if locale == "en":
        words |= {"diabetes", "diabetic", "allergy", "allergic", "allergen", "milk"}
    return sorted(words)


SHARE_RESULT_MEMBERS = (
    # Fixture member (engine verdict) shown under a realistic name; the names never hint at
    # health (the fixture members' own names do, e.g. "Diabetic Adult").
    ("diabetic_adult", "Ravi Patil", "parent"),
    ("milk_allergic_child", "Riya", "child"),
    ("bp_parent", "", "self"),
    ("no_age", "Sushila Devi", "other"),
)
SHARE_RULES = [
    "key = share.result.text, or share.result.ungraded when grade is null",
    (
        "for each verdict in response order: who = first whitespace-separated word of the "
        "member's name; if the name is blank, share.relation.<relation>"
    ),
    "status = verdict.status.<status>; one member = share.result.member(who, status)",
    "members = the member strings joined with ', ' (comma + space) in every locale",
    "product = the product name as returned; grade = the letter; url as given",
    "never interpolate conditions, allergens, reason codes or nutrient totals",
]


def share_result_fixture() -> dict[str, Any]:
    product = load_product("sf_biscuit")
    index = json.loads((FIXTURES / "responses" / "index.json").read_text(encoding="utf-8"))
    verdicts = []
    for key, name, relation in SHARE_RESULT_MEMBERS:
        status = scoring.analyze(product, [load_member(key)]).verdicts[0].status.value
        verdicts.append(
            {
                "fixture_member": key,
                "member_id": index["members"][key],
                "name": name,
                "relation": relation,
                "status": status,
            }
        )
    grade = scoring.analyze(product, []).report.nutriscore.grade
    expected, forbidden = {}, {}
    for locale in LOCALES:
        msgs = _messages(locale)
        url = f"{SITE_URL}/{locale}"
        expected[locale] = share_result_text(
            msgs, product=product.name, grade=grade, verdicts=verdicts, url=url
        )
        forbidden[locale] = _forbidden(msgs, locale)
        hits = [w for w in forbidden[locale] if w in expected[locale].casefold()]
        if hits:
            raise ValueError(f"share text leaks {hits} ({locale})")
    return {
        "format_version": FORMAT_VERSION,
        "description": "Share text for the sf_biscuit result for three members (Plan 6 F17).",
        "input": {
            "product": product.name,
            "grade": grade,
            "urls": {loc: f"{SITE_URL}/{loc}" for loc in LOCALES},
            "verdicts": verdicts,
        },
        "rules": SHARE_RULES,
        "expected": expected,
        "forbidden_substrings": forbidden,
    }


def share_weekly_fixture(family: WeekFamily) -> dict[str, Any]:
    logged = logged_in_week(family)
    expected = {
        loc: share_weekly_text(
            _messages(loc), scans=family.scans, logged=logged, url=f"{SITE_URL}/{loc}"
        )
        for loc in LOCALES
    }
    return {
        "format_version": FORMAT_VERSION,
        "description": "Weekly share text for meals/week_family.json (counts only, Plan 6 F17).",
        "input": {
            "scans": family.scans,
            "logged": logged,
            "urls": {loc: f"{SITE_URL}/{loc}" for loc in LOCALES},
        },
        "rules": [
            "key = share.weekly; scans and logged come from GET /v1/meals/week_counts",
            "pass the counts as plain decimal strings (Latin digits), not locale-formatted",
        ],
        "expected": expected,
    }


# --- check / write -----------------------------------------------------------------------


def _dump(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def compute() -> dict[Path, str]:
    family = load_week_family()
    return {
        MEALS / "expected" / "week_family.dad_diabetic.json": _dump(week_summary(family, "dad")),
        SHARE / "share_result.sf_biscuit.json": _dump(share_result_fixture()),
        SHARE / "share_weekly.week_family.json": _dump(share_weekly_fixture(family)),
    }


def changes() -> dict[Path, tuple[str, str | None]]:
    """{path: (new, old)} for every file whose content differs."""
    out = {}
    for path, new in compute().items():
        old = path.read_text(encoding="utf-8") if path.exists() else None
        if new != old:
            out[path] = (new, old)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="default: diff, exit 1 if stale")
    mode.add_argument("--write", action="store_true", help="write only the files that differ")
    args = ap.parse_args(argv)
    diff = changes()
    if args.write:
        for path, (new, _old) in diff.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(new, encoding="utf-8")
            print(f"wrote {path.relative_to(FIXTURES)}")
        return 0
    for path, (new, old) in diff.items():
        sys.stdout.writelines(
            difflib.unified_diff(
                (old or "").splitlines(keepends=True),
                new.splitlines(keepends=True),
                str(path.relative_to(FIXTURES)),
                str(path.relative_to(FIXTURES)),
            )
        )
    return 1 if diff else 0


if __name__ == "__main__":
    raise SystemExit(main())
