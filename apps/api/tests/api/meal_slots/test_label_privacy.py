"""Custom meal labels are user text: exact bytes, never in analytics, errors, logs or prompts."""

import json
import logging
import subprocess
import sys

from app.integrations import posthog
from tests.api.meal_slots.helpers import URL, add, listing, log_quick

LABEL = "संध्याकाळचा चहा ☕"


class _Spy:
    def __init__(self):
        self.captured: list = []

    def capture(self, *args, **kwargs):
        self.captured.append((args, kwargs))


async def test_label_round_trip_exact_bytes(client, consented, db_session):
    r = await add(client, LABEL)
    assert r.status_code == 201
    assert r.json()["custom_label"] == LABEL
    got = next(i for i in await listing(client) if i["id"] == r.json()["id"])
    assert got["custom_label"].encode() == LABEL.encode()
    from sqlalchemy import text

    stored = await db_session.scalar(
        text("select custom_label from meal_slots where id = :i"), {"i": r.json()["id"]}
    )
    assert stored.encode() == LABEL.encode()


async def test_label_never_in_analytics(client, consented, monkeypatch):
    spy = _Spy()
    monkeypatch.setattr(posthog, "_client", spy)
    r = await add(client, LABEL)
    sid = r.json()["id"]
    await client.patch(f"{URL}/{sid}", json={"custom_label": LABEL + "2"})
    await log_quick(client, sid)
    await client.delete(f"{URL}/{sid}")
    assert "संध्या" not in json.dumps(spy.captured, ensure_ascii=False, default=str)


async def test_label_never_in_error_details(client, consented):
    await add(client, LABEL)
    dup = await add(client, LABEL.upper())
    long = await add(client, LABEL * 3)
    for r in (dup, long):
        assert r.status_code == 422
        assert "संध्या" not in r.text


async def test_label_not_in_logs(client, consented, caplog):
    with caplog.at_level(logging.DEBUG):
        r = await add(client, LABEL)
        sid = r.json()["id"]
        await add(client, LABEL)  # a refused duplicate
        await client.patch(f"{URL}/{sid}", json={"custom_label": LABEL + "2"})
        await log_quick(client, sid)
        await client.delete(f"{URL}/{sid}")
    assert "संध्या" not in caplog.text
    assert "संध्या" not in "".join(str(r.args) + r.getMessage() for r in caplog.records)


def test_prompt_modules_never_import_meal_slots():
    code = (
        "import sys, importlib\n"
        "for m in ('app.prompts', 'app.features.voice', 'app.features.analyze'):\n"
        "    try: importlib.import_module(m)\n"
        "    except ModuleNotFoundError as e:\n"
        "        if e.name != m: raise\n"
        "bad = sorted(n for n in sys.modules if n.startswith('app.features.meal_slots'))\n"
        "print(bad)\n"
        "sys.exit(1 if bad else 0)\n"
    )
    done = subprocess.run([sys.executable, "-c", code], check=False, capture_output=True, text=True)
    assert done.returncode == 0, done.stdout + done.stderr
