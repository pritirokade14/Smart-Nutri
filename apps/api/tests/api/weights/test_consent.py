"""The consent gate on the weights routes (Plan 12 Task 23; Q13)."""

import pytest

from tests.api.weights.conftest import ACC_A, ACC_B, TREND, URL, body


def _err(r) -> dict:
    return r.json()["error"]


@pytest.mark.parametrize(
    ("method", "path", "kwargs"),
    [
        ("put", f"{URL}/2026-11-07", {"json": body(80)}),
        ("get", URL, {}),
        ("get", TREND, {}),
    ],
)
async def test_put_list_trend_need_health_data(client, login, grant, method, path, kwargs):
    await grant(ACC_B, ["terms"])
    login(ACC_B)
    r = await getattr(client, method)(path, **kwargs)
    assert r.status_code == 403, r.text
    assert _err(r)["code"] == "consent_required"
    assert _err(r)["details"]["purposes"] == ["health_data"]


async def test_no_consent_lists_both(client, login, grant):
    await grant(ACC_B, [])
    login(ACC_B)
    r = await client.get(URL)
    assert _err(r)["details"]["purposes"] == ["terms", "health_data"]


async def test_delete_needs_only_terms(client, login, grant, seed_weights):
    await grant(ACC_A, ["terms"])
    login(ACC_A)
    await seed_weights([("2026-11-07", 80)])
    assert (await client.delete(f"{URL}/2026-11-07")).status_code == 204
    r = await client.delete(f"{URL}/2026-11-07")
    assert r.status_code == 404  # past the gate: the row is gone


async def test_delete_without_terms_is_refused(client, login, grant):
    await grant(ACC_B, [])
    login(ACC_B)
    r = await client.delete(f"{URL}/2026-11-07")
    assert r.status_code == 403 and _err(r)["details"]["purposes"] == ["terms"]


async def test_gate_before_rate_limit(client, app, login, grant, db_session, monkeypatch):
    from sqlalchemy import text

    monkeypatch.setattr(app.state.settings, "rate_limit_weights_per_day", 1)
    await grant(ACC_B, ["terms"])
    login(ACC_B)
    for _ in range(3):
        r = await client.put(f"{URL}/2026-11-07", json=body(80))
        assert r.status_code == 403  # never 429: a refused call costs no quota
    n = (
        await db_session.execute(
            text("select count(*) from rate_limit_counters where key = :k"),
            {"k": f"acct:{ACC_B}"},
        )
    ).scalar()
    assert n == 0
