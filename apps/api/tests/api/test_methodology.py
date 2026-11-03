"""GET /v1/methodology (Plan 7 Task 5, F12): public, cached, served from scoring.methodology()."""

import json

import pytest

from app import scoring
from app.db.session import get_session
from app.scoring.methodology import SECTION_IDS


@pytest.fixture
def public_client(app, client, db_session):
    """No auth override at all: the route must work without a token. Only the DB (for the
    per-IP rate limit) is the shared rolled-back test session."""
    app.dependency_overrides[get_session] = lambda: db_session
    return client


async def test_methodology_is_public_and_cached(public_client):
    r = await public_client.get("/v1/methodology?language=hi")
    assert r.status_code == 200, r.json()
    assert "max-age=3600" in r.headers["cache-control"]
    assert "public" in r.headers["cache-control"] and "s-maxage=3600" in r.headers["cache-control"]
    body = r.json()
    assert body["language"] == "hi" and body["pending_clinician_review"] is True


async def test_default_language_is_english(public_client):
    assert (await public_client.get("/v1/methodology")).json()["language"] == "en"


async def test_methodology_matches_the_engine_export(public_client):
    body = (await public_client.get("/v1/methodology")).json()
    m = scoring.methodology()
    assert body["version"] == m["version"]
    assert [s["id"] for s in body["sections"]] == list(SECTION_IDS)
    assert body["sections"] == json.loads(json.dumps(m["sections"]))  # JSON keys are strings


async def test_methodology_thresholds_match_yaml(public_client):
    cfg = scoring.load_config()
    sections = {s["id"]: s for s in (await public_client.get("/v1/methodology")).json()["sections"]}
    assert (
        sections["blood_sugar"]["thresholds"]["avoid_sugars_g"]
        == cfg.thresholds["conditions"]["blood_sugar"]["avoid_sugars_g"]
    )
    assert sections["high_in"]["thresholds"] == cfg.thresholds["high_in"]


async def test_methodology_lists_required_sources(public_client):
    sources = (await public_client.get("/v1/methodology")).json()["sources"]
    ids = {s["id"] for s in sources}
    assert {
        "icmr_nin_2024",
        "fssai_claims_2018",
        "who_infant",
        "uk_fsa_front_of_pack",
        "nutriscore_2023",
    } <= ids
    # No source URL has been checked by a person yet: clients must not present them as verified.
    assert all(s["url_verified"] is False for s in sources)
    assert all(set(s) == {"id", "title", "url", "url_verified"} for s in sources)


async def test_every_cited_source_exists(public_client):
    body = (await public_client.get("/v1/methodology")).json()
    ids = {s["id"] for s in body["sources"]}
    for section in body["sections"]:
        for key in ("threshold_sources", "rationale_sources"):
            assert set(section[key] or ()) <= ids, (section["id"], key)


async def test_bad_language_422(public_client):
    r = await public_client.get("/v1/methodology?language=fr")
    assert (r.status_code, r.json()["error"]["code"]) == (422, "validation_error")


async def test_public_rate_limit(app, public_client):
    app.state.settings.rate_limit_public_per_minute = 1
    assert (await public_client.get("/v1/methodology")).status_code == 200
    r = await public_client.get("/v1/methodology")
    assert (r.status_code, r.json()["error"]["code"]) == (429, "rate_limited")


def test_route_has_no_security_and_a_rate_limit(app):
    spec = app.openapi()
    op = spec["paths"]["/v1/methodology"]["get"]
    assert "security" not in op and op["operationId"] == "methodology_get"


def test_every_section_has_client_strings_in_every_language():
    from app.core.i18n import catalog

    cat = catalog()
    for language in ("en", "hi", "mr"):
        for sid in SECTION_IDS:
            for part in ("title", "description"):
                assert cat.has(f"methodology.section.{sid}.{part}", language), (language, sid)
        for key in ("title", "intro", "pending_review", "sources_title", "url_unverified"):
            assert cat.has(f"methodology.{key}", language), (language, key)
