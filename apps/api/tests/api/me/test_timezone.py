from tests.api.me.conftest import ACC_A


async def test_me_has_default_timezone(client, consented):
    r = await client.get("/v1/me")
    assert r.status_code == 200
    assert r.json()["timezone"] == "Asia/Kolkata"


async def test_put_timezone_valid(client, consented):
    r = await client.put("/v1/me/timezone", json={"timezone": "America/New_York"})
    assert r.status_code == 200
    assert r.json()["timezone"] == "America/New_York"
    assert (await client.get("/v1/me")).json()["timezone"] == "America/New_York"


async def test_put_timezone_invalid_422(client, consented):
    for bad in ("IST", "Mars/Base", "../etc/passwd"):
        r = await client.put("/v1/me/timezone", json={"timezone": bad})
        assert r.status_code == 422, bad
        assert r.json()["error"]["code"] == "timezone_invalid"
    r = await client.put("/v1/me/timezone", json={"timezone": ""})
    assert r.status_code == 422
    assert (await client.get("/v1/me")).json()["timezone"] == "Asia/Kolkata"


async def test_put_timezone_needs_only_sign_in(client, login):
    login(ACC_A)  # no consents at all
    r = await client.put("/v1/me/timezone", json={"timezone": "Asia/Kolkata"})
    assert r.status_code == 200


async def test_put_timezone_rate_limited(client, app, consented, monkeypatch):
    monkeypatch.setattr(app.state.settings, "rate_limit_diary_settings_per_day", 2)
    for _ in range(2):
        assert (
            await client.put("/v1/me/timezone", json={"timezone": "Asia/Kolkata"})
        ).status_code == 200
    r = await client.put("/v1/me/timezone", json={"timezone": "Asia/Kolkata"})
    assert r.status_code == 429
    assert r.json()["error"]["code"].startswith("rate_limited")
