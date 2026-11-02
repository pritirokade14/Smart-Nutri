import base64
import hashlib
import hmac
import json
import logging
import time
from typing import Annotated
from uuid import UUID

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from fastapi import Depends

from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.core.security import (
    MAX_STALE_SECONDS,
    AccountContext,
    JwksCache,
    current_account,
    get_jwks_cache,
)

SUPABASE_URL = "https://proj.supabase.co"
JWKS_URL = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
SUB = "6f1c2b9e-1d2a-4c3b-9a8e-0f1e2d3c4b5a"
EC_KID = "ec-key-1"
RSA_KID = "rsa-key-1"

settings = Settings(
    _env_file=None,
    environment="test",
    supabase_url=SUPABASE_URL,
    supabase_jwks_url=JWKS_URL,
)


def _public_jwk(private_key, kid: str, alg: str) -> dict:
    algo = jwt.algorithms.ECAlgorithm if alg == "ES256" else jwt.algorithms.RSAAlgorithm
    jwk = json.loads(algo.to_jwk(private_key.public_key()))
    jwk.update({"kid": kid, "alg": alg, "use": "sig"})
    return jwk


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _claims(**override) -> dict:
    now = int(time.time())
    claims = {
        "sub": SUB,
        "email": "a@b.c",
        "aud": "authenticated",
        "iss": f"{SUPABASE_URL}/auth/v1",
        "role": "authenticated",
        "iat": now,
        "exp": now + 3600,
    }
    for name in ("exp", "nbf"):
        if name in override and isinstance(override[name], int):
            override[name] = now + override[name]
    claims.update(override)
    return {k: v for k, v in claims.items() if v is not None}


@pytest.fixture(scope="module")
def ec_key():
    return ec.generate_private_key(ec.SECP256R1())


@pytest.fixture(scope="module")
def rsa_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def jwks_doc(ec_key, rsa_key):
    return {"keys": [_public_jwk(ec_key, EC_KID, "ES256"), _public_jwk(rsa_key, RSA_KID, "RS256")]}


class CountingFetch:
    def __init__(self, *docs) -> None:
        self.docs = list(docs)
        self.calls = 0

    async def __call__(self, url: str) -> dict:
        assert url == JWKS_URL
        self.calls += 1
        doc = self.docs[min(self.calls, len(self.docs)) - 1]
        if isinstance(doc, Exception):
            raise doc
        return doc


@pytest.fixture
def jwks(jwks_doc):
    return JwksCache(JWKS_URL, fetch=CountingFetch(jwks_doc))


@pytest.fixture
def make_token(ec_key):
    def _make(*, key=None, kid=EC_KID, alg="ES256", headers=None, **override) -> str:
        hdrs = {"kid": kid} if kid is not None else {}
        hdrs.update(headers or {})
        return jwt.encode(_claims(**override), key or ec_key, algorithm=alg, headers=hdrs)

    return _make


async def _expect(code: str, authorization, jwks, cfg=settings) -> None:
    with pytest.raises(ApiError) as e:
        await current_account(authorization=authorization, jwks=jwks, settings=cfg)
    assert (e.value.code, e.value.status) == (code, 401)


# --- happy paths ---------------------------------------------------------------------


async def test_valid_token(make_token, jwks):
    ctx = await current_account(
        authorization=f"Bearer {make_token()}", jwks=jwks, settings=settings
    )
    assert isinstance(ctx, AccountContext)
    assert ctx.account_id == UUID(SUB) and ctx.email == "a@b.c"


async def test_valid_rs256_token(make_token, rsa_key, jwks):
    token = make_token(key=rsa_key, kid=RSA_KID, alg="RS256")
    ctx = await current_account(authorization=f"bearer {token}", jwks=jwks, settings=settings)
    assert ctx.account_id == UUID(SUB)


async def test_email_optional(make_token, jwks):
    ctx = await current_account(
        authorization=f"Bearer {make_token(email=None)}", jwks=jwks, settings=settings
    )
    assert ctx.email is None


async def test_expiry_within_leeway_accepted(make_token, jwks):
    ctx = await current_account(
        authorization=f"Bearer {make_token(exp=-10)}", jwks=jwks, settings=settings
    )
    assert ctx.account_id == UUID(SUB)


# --- claim validation ----------------------------------------------------------------


@pytest.mark.parametrize(
    "override",
    [
        {"aud": "anon"},
        {"aud": None},
        {"iss": "https://evil/auth/v1"},
        {"iss": None},
        {"exp": -60},
        {"exp": None},
        {"nbf": 120},
        {"sub": "not-a-uuid"},
        {"sub": None},
    ],
)
async def test_bad_claims_rejected(make_token, jwks, override):
    await _expect("auth_invalid", f"Bearer {make_token(**override)}", jwks)


async def test_unconfigured_supabase_url_rejects(make_token, jwks):
    cfg = Settings(_env_file=None, environment="test", supabase_jwks_url=JWKS_URL)
    await _expect("auth_invalid", f"Bearer {make_token(iss='/auth/v1')}", jwks, cfg)


# --- header handling -----------------------------------------------------------------


async def test_missing_header(jwks):
    await _expect("auth_required", None, jwks)


@pytest.mark.parametrize("value", ["", "Basic abc", "Bearer", "Bearer    ", "abc.def.ghi"])
async def test_non_bearer_header(jwks, value):
    await _expect("auth_required", value, jwks)


@pytest.mark.parametrize("token", ["garbage", "a.b.c", "x" * 50])
async def test_garbled_token(jwks, token):
    await _expect("auth_invalid", f"Bearer {token}", jwks)


async def test_missing_kid_rejected(make_token, jwks):
    await _expect("auth_invalid", f"Bearer {make_token(kid=None)}", jwks)


# --- signature and algorithm ---------------------------------------------------------


async def test_forged_signature_rejected(make_token, jwks):
    attacker = ec.generate_private_key(ec.SECP256R1())
    await _expect("auth_invalid", f"Bearer {make_token(key=attacker)}", jwks)


async def test_tampered_payload_rejected(make_token, jwks):
    header, _, sig = make_token().split(".")
    forged = _b64(json.dumps(_claims(sub="00000000-0000-0000-0000-000000000000")).encode())
    await _expect("auth_invalid", f"Bearer {header}.{forged}.{sig}", jwks)


async def test_hs256_token_rejected(ec_key, jwks):
    # Classic alg confusion: HMAC-sign with the server's *public* key as the secret.
    public_pem = ec_key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    for secret in (public_pem, json.dumps(_public_jwk(ec_key, EC_KID, "ES256")).encode()):
        header = _b64(json.dumps({"alg": "HS256", "typ": "JWT", "kid": EC_KID}).encode())
        payload = _b64(json.dumps(_claims()).encode())
        sig = _b64(hmac.new(secret, f"{header}.{payload}".encode(), hashlib.sha256).digest())
        await _expect("auth_invalid", f"Bearer {header}.{payload}.{sig}", jwks)


@pytest.mark.parametrize("alg", ["none", "None", "NONE"])
async def test_alg_none_rejected(jwks, alg):
    header = _b64(json.dumps({"alg": alg, "typ": "JWT", "kid": EC_KID}).encode())
    payload = _b64(json.dumps(_claims()).encode())
    await _expect("auth_invalid", f"Bearer {header}.{payload}.", jwks)


async def test_alg_must_match_key(make_token, rsa_key, jwks):
    # RS256 token that points at the EC key's kid.
    token = make_token(key=rsa_key, kid=EC_KID, alg="RS256")
    await _expect("auth_invalid", f"Bearer {token}", jwks)


async def test_symmetric_keys_in_jwks_ignored(make_token):
    oct_key = {"kty": "oct", "kid": "hs", "alg": "HS256", "k": _b64(b"shared-secret-" * 3)}
    cache = JwksCache(JWKS_URL, fetch=CountingFetch({"keys": [oct_key]}))
    token = jwt.encode(_claims(), "shared-secret-" * 3, algorithm="HS256", headers={"kid": "hs"})
    await _expect("auth_invalid", f"Bearer {token}", cache)


# --- JWKS cache ----------------------------------------------------------------------


async def test_jwks_cached_between_requests(make_token, jwks):
    for _ in range(3):
        await current_account(authorization=f"Bearer {make_token()}", jwks=jwks, settings=settings)
    assert jwks._fetch.calls == 1


@pytest.fixture
def rotating_fetch(ec_key):
    new_key = ec.generate_private_key(ec.SECP256R1())
    old = {"keys": [_public_jwk(ec_key, EC_KID, "ES256")]}
    new = {"keys": [_public_jwk(ec_key, EC_KID, "ES256"), _public_jwk(new_key, "ec-2", "ES256")]}
    return CountingFetch(old, new), new_key


async def test_unknown_kid_refetches_once(make_token, rotating_fetch):
    fetch, new_key = rotating_fetch
    cache = JwksCache(JWKS_URL, fetch=fetch)
    await current_account(authorization=f"Bearer {make_token()}", jwks=cache, settings=settings)
    assert fetch.calls == 1
    token = make_token(key=new_key, kid="ec-2")
    ctx = await current_account(authorization=f"Bearer {token}", jwks=cache, settings=settings)
    assert ctx.account_id == UUID(SUB)
    assert fetch.calls == 2
    await current_account(authorization=f"Bearer {token}", jwks=cache, settings=settings)
    assert fetch.calls == 2


async def test_unknown_kid_still_unknown_after_refetch(make_token, jwks):
    await current_account(authorization=f"Bearer {make_token()}", jwks=jwks, settings=settings)
    await _expect("auth_invalid", f"Bearer {make_token(kid='nope-1')}", jwks)
    assert jwks._fetch.calls == 2
    # A flood of random kids must not turn into a flood of JWKS fetches.
    for i in range(5):
        await _expect("auth_invalid", f"Bearer {make_token(kid=f'nope-{i + 2}')}", jwks)
    assert jwks._fetch.calls == 2


async def test_first_load_does_not_double_fetch(make_token, jwks):
    await _expect("auth_invalid", f"Bearer {make_token(kid='nope')}", jwks)
    assert jwks._fetch.calls == 1


async def test_ttl_expiry_refetches(make_token, jwks_doc):
    fetch = CountingFetch(jwks_doc)
    now = [1000.0]
    cache = JwksCache(JWKS_URL, ttl_seconds=600, fetch=fetch, clock=lambda: now[0])
    await current_account(authorization=f"Bearer {make_token()}", jwks=cache, settings=settings)
    now[0] += 599
    await current_account(authorization=f"Bearer {make_token()}", jwks=cache, settings=settings)
    assert fetch.calls == 1
    now[0] += 2
    await current_account(authorization=f"Bearer {make_token()}", jwks=cache, settings=settings)
    assert fetch.calls == 2


async def test_fetch_failure_is_auth_invalid(make_token):
    cache = JwksCache(JWKS_URL, fetch=CountingFetch(httpx.ConnectError("dns secret-host")))
    await _expect("auth_invalid", f"Bearer {make_token()}", cache)


async def test_malformed_jwks_is_auth_invalid(make_token):
    cache = JwksCache(JWKS_URL, fetch=CountingFetch({"nope": []}))
    await _expect("auth_invalid", f"Bearer {make_token()}", cache)


async def test_failed_refresh_keeps_last_good_keys(make_token, jwks_doc):
    fetch = CountingFetch(jwks_doc, httpx.ConnectError("down"))
    now = [1000.0]
    cache = JwksCache(JWKS_URL, ttl_seconds=600, fetch=fetch, clock=lambda: now[0])
    await current_account(authorization=f"Bearer {make_token()}", jwks=cache, settings=settings)
    now[0] += 601
    ctx = await current_account(
        authorization=f"Bearer {make_token()}", jwks=cache, settings=settings
    )
    assert ctx.account_id == UUID(SUB) and fetch.calls == 2


async def test_default_fetch_uses_httpx(monkeypatch, jwks_doc, make_token):
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200, json=jwks_doc)

    real_client = httpx.AsyncClient

    def fake_client(*args, **kwargs):
        assert kwargs.get("timeout") == 5
        return real_client(*args, transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr("app.core.security.httpx.AsyncClient", fake_client)
    cache = JwksCache(JWKS_URL)
    ctx = await current_account(
        authorization=f"Bearer {make_token()}", jwks=cache, settings=settings
    )
    assert ctx.account_id == UUID(SUB) and seen == [JWKS_URL]


def test_get_jwks_cache_is_process_cached(monkeypatch):
    get_jwks_cache.cache_clear()
    get_settings.cache_clear()
    monkeypatch.setenv("SUPABASE_JWKS_URL", JWKS_URL)
    try:
        cache = get_jwks_cache()
        assert cache is get_jwks_cache()
        assert cache._jwks_url == JWKS_URL
    finally:
        get_jwks_cache.cache_clear()
        get_settings.cache_clear()


# --- through the app: error envelope -------------------------------------------------


async def test_endpoint_error_envelope(app, client, make_token, jwks):
    @app.get("/whoami")
    async def _(account: Annotated[AccountContext, Depends(current_account)]):
        return {"account_id": str(account.account_id)}

    app.dependency_overrides[get_jwks_cache] = lambda: jwks
    app.dependency_overrides[get_settings] = lambda: settings

    r = await client.get("/whoami")
    assert r.status_code == 401
    assert r.json() == {
        "error": {"code": "auth_required", "message_key": "error.auth_required", "details": {}}
    }

    r = await client.get("/whoami", headers={"Authorization": f"Bearer {make_token(aud='x')}"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "auth_invalid"
    assert "aud" not in r.text.lower().replace("auth_invalid", "")

    r = await client.get("/whoami", headers={"Authorization": f"Bearer {make_token()}"})
    assert r.status_code == 200 and r.json() == {"account_id": SUB}


# --- hardening (R14) -----------------------------------------------------------------


def _raw_token(header: dict, claims: dict | None = None) -> str:
    h = _b64(json.dumps(header).encode())
    p = _b64(json.dumps(claims or _claims()).encode())
    return f"{h}.{p}.{_b64(b'sig')}"


@pytest.mark.parametrize(
    "header",
    [
        {"alg": [], "kid": EC_KID},
        {"alg": {}, "kid": EC_KID},
        {"alg": ["ES256"], "kid": EC_KID},
        {"alg": None, "kid": EC_KID},
        {"alg": "ES256", "kid": 5},
        {"alg": "ES256", "kid": ["a"]},
        {"alg": "ES256", "kid": {}},
    ],
)
async def test_non_string_alg_or_kid_is_401_through_app(app, client, jwks, header):
    @app.get("/whoami")
    async def _(account: Annotated[AccountContext, Depends(current_account)]):
        return {}

    app.dependency_overrides[get_jwks_cache] = lambda: jwks
    app.dependency_overrides[get_settings] = lambda: settings
    r = await client.get("/whoami", headers={"Authorization": f"Bearer {_raw_token(header)}"})
    assert r.status_code == 401 and r.json()["error"]["code"] == "auth_invalid"


@pytest.mark.parametrize("role", ["service_role", "anon", None, ["authenticated"]])
async def test_role_must_be_authenticated(make_token, jwks, role):
    await _expect("auth_invalid", f"Bearer {make_token(role=role)}", jwks)


@pytest.mark.parametrize("value", [True])
async def test_anonymous_rejected(make_token, jwks, value):
    await _expect("auth_invalid", f"Bearer {make_token(is_anonymous=value)}", jwks)


async def test_is_anonymous_false_accepted(make_token, jwks):
    ctx = await current_account(
        authorization=f"Bearer {make_token(is_anonymous=False)}", jwks=jwks, settings=settings
    )
    assert ctx.account_id == UUID(SUB)


@pytest.mark.parametrize(
    "sub",
    [SUB.upper(), SUB.replace("-", ""), "{" + SUB + "}", "urn:uuid:" + SUB],
)
async def test_non_canonical_sub_rejected(make_token, jwks, sub):
    await _expect("auth_invalid", f"Bearer {make_token(sub=sub)}", jwks)


async def test_stale_keys_served_within_cap_then_fail_closed(make_token, jwks_doc, caplog):
    fetch = CountingFetch(jwks_doc, httpx.ConnectError("down"))
    now = [1000.0]
    cache = JwksCache(JWKS_URL, ttl_seconds=600, fetch=fetch, clock=lambda: now[0])
    auth = f"Bearer {make_token()}"
    await current_account(authorization=auth, jwks=cache, settings=settings)
    now[0] += MAX_STALE_SECONDS - 1
    with caplog.at_level(logging.WARNING, logger="app.core.security"):
        await current_account(authorization=auth, jwks=cache, settings=settings)
    assert any(r.levelno == logging.WARNING for r in caplog.records)
    assert not any(r.levelno >= logging.ERROR for r in caplog.records)
    now[0] += 11  # backoff elapsed, keys now older than the cap
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="app.core.security"):
        await _expect("auth_invalid", auth, cache)
    errors = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert errors and auth not in caplog.text and EC_KID not in caplog.text
    assert "down" not in caplog.text


async def test_recovers_after_stale_cap_when_fetch_succeeds(make_token, jwks_doc):
    fetch = CountingFetch(jwks_doc, httpx.ConnectError("down"), jwks_doc)
    now = [1000.0]
    cache = JwksCache(JWKS_URL, ttl_seconds=600, fetch=fetch, clock=lambda: now[0])
    auth = f"Bearer {make_token()}"
    await current_account(authorization=auth, jwks=cache, settings=settings)
    now[0] += MAX_STALE_SECONDS + 1
    await _expect("auth_invalid", auth, cache)
    now[0] += 11
    ctx = await current_account(authorization=auth, jwks=cache, settings=settings)
    assert ctx.account_id == UUID(SUB)


async def test_key_ops_without_verify_dropped(ec_key, make_token):
    entry = _public_jwk(ec_key, EC_KID, "ES256")
    cache = JwksCache(JWKS_URL, fetch=CountingFetch({"keys": [{**entry, "key_ops": ["sign"]}]}))
    await _expect("auth_invalid", f"Bearer {make_token()}", cache)


async def test_key_ops_with_verify_kept(ec_key, make_token):
    entry = _public_jwk(ec_key, EC_KID, "ES256")
    cache = JwksCache(JWKS_URL, fetch=CountingFetch({"keys": [{**entry, "key_ops": ["verify"]}]}))
    ctx = await current_account(
        authorization=f"Bearer {make_token()}", jwks=cache, settings=settings
    )
    assert ctx.account_id == UUID(SUB)


async def test_oversized_token_rejected_without_parsing(jwks, monkeypatch):
    def boom(_):
        raise AssertionError("must not parse")

    monkeypatch.setattr("app.core.security.jwt.get_unverified_header", boom)
    await _expect("auth_invalid", "Bearer " + "a" * 8193, jwks)
