"""F7 wired into POST /v1/analyze (Plan 5 T7 part B; rulings P3, P5, P5-R17/R18/R21).

- The explanation is generated only with an active `ai_processing` consent, after the scan and
  verdicts are committed, within the 8 s budget, and it never changes or blocks a verdict.
- Any failure degrades to `explanation.source == "unavailable"` (text null, no tips); analyze
  still answers 200.
- `explanation_cache` is keyed by product, anonymised-input hash (prompt version and model
  included) and language. A hit is guarded again for the caller's names and email.
"""

import asyncio
import json
from uuid import NAMESPACE_URL, uuid5

import pytest
from sqlalchemy import func, select

from app.core.security import AccountContext
from app.features.analyze import explain as explain_mod
from app.features.analyze import service as analyze_service
from app.features.analyze.explain import ExplanationLLM, MemberStatusEcho
from app.features.consents.policy import CURRENT_VERSIONS
from app.features.me.service import ensure_account
from app.features.members.service import get_or_create_primary
from app.features.ratelimit.models import ExplanationCache
from app.features.scans.models import Scan
from app.integrations.callmissed import get_llm_provider
from app.integrations.providers import CompletionFailed, ProviderUnavailable
from tests.api.analyze.conftest import EMAIL, OFF_BARCODE, A, B

URL = "/v1/analyze"
TEXT = "member_1 should go easy on this; the label lists sugar."
C = B.__class__("33333333-3333-3333-3333-333333333333")


class EchoLLM:
    """An LLMProvider fake that echoes the statuses it is sent (optionally overridden)."""

    def __init__(self, text: str = TEXT, *, override=None, fail=None, delay=0.0, on_call=None):
        self.text = text
        self.override = override or {}
        self.fail = fail
        self.delay = delay
        self.on_call = on_call
        self.chat_calls: list[dict] = []

    async def extract_label(self, **kwargs):  # pragma: no cover - not used here
        raise AssertionError("extract_label must not be called by analyze")

    async def chat_json(self, **kwargs):
        self.chat_calls.append(kwargs)
        if self.on_call is not None:
            await self.on_call()
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.fail is not None:
            raise self.fail
        members = json.loads(kwargs["user"])["members"]
        return ExplanationLLM(
            members=[
                MemberStatusEcho(ref=m["ref"], status=self.override.get(m["ref"], m["status"]))
                for m in members
            ],
            text=self.text,
            tips=["Compare the sugar line with similar packs."],
        )


@pytest.fixture
def use_llm(app):
    def _use(fake):
        app.dependency_overrides[get_llm_provider] = lambda: fake
        return fake

    return _use


@pytest.fixture
def fake_llm(use_llm):
    return use_llm(EchoLLM())


@pytest.fixture
async def consented(grant):
    await grant(A)


async def _post(client, product, **extra):
    r = await client.post(URL, json={"product_id": str(product.id), **extra})
    assert r.status_code == 200, r.text
    return r.json()


def _unavailable(body: dict, language: str = "en") -> bool:
    return body["explanation"] == {
        "text": None,
        "tips": [],
        "language": language,
        "source": "unavailable",
        "prompt_version": "explanation_v3",
        "member_refs": {},
    }


async def _cache_rows(db_session) -> list[ExplanationCache]:
    rows = await db_session.scalars(
        select(ExplanationCache).execution_options(populate_existing=True)
    )
    return list(rows)


# --- happy path --------------------------------------------------------------------------------


async def test_explanation_with_member_refs(
    auth_client, consented, seeded_family, sf_biscuit_product, fake_llm
):
    body = await _post(auth_client, sf_biscuit_product, language="hi")
    exp = body["explanation"]
    assert exp["source"] == "llm" and exp["text"] == TEXT  # member_N tokens kept for clients
    assert exp["tips"] == ["Compare the sugar line with similar packs."]
    assert exp["language"] == "hi" and exp["prompt_version"] == "explanation_v3"
    assert exp["member_refs"] == {
        "member_1": str(seeded_family["Me"].id),
        "member_2": str(seeded_family["Dad"].id),
        "member_3": str(seeded_family["Riya"].id),
    }
    assert "tips" not in body  # tips live inside the explanation (P5-R17)
    assert len(fake_llm.chat_calls) == 1


async def test_prompt_sent_has_no_names_ids_or_email(
    auth_client, consented, seeded_family, sf_biscuit_product, fake_llm
):
    await _post(auth_client, sf_biscuit_product, language="mr")
    (call,) = fake_llm.chat_calls
    sent = json.dumps({k: str(v) for k, v in call.items()}, ensure_ascii=False)
    for forbidden in ("Dad", "Riya", '"Me"', EMAIL, str(A), sf_biscuit_product.name):
        assert forbidden not in sent, forbidden
    for member in seeded_family.values():
        assert str(member.id) not in sent
    assert json.loads(call["user"])["language"] == "mr"
    assert call["prompt_version"] == "explanation_v3"


# --- never changes a verdict -------------------------------------------------------------------


async def test_explanation_never_changes_verdict(
    auth_client, consented, seeded_family, sf_biscuit_product, use_llm
):
    use_llm(EchoLLM(override={"member_2": "ok"}))  # the model claims Dad is ok
    with_llm = await _post(auth_client, sf_biscuit_product)
    assert {v["member_name"]: v["status"] for v in with_llm["verdicts"]}["Dad"] == "avoid"
    assert _unavailable(with_llm)  # the claim is dropped, never shown

    fake = use_llm(EchoLLM(fail=AssertionError("must not be called")))
    await auth_client.post(
        "/v1/consents",
        json={"purpose": "ai_processing", "version": CURRENT_VERSIONS["ai_processing"],
              "granted": False},
    )  # fmt: skip
    without_llm = await _post(auth_client, sf_biscuit_product)
    assert fake.chat_calls == []
    assert with_llm["verdicts"] == without_llm["verdicts"]
    assert with_llm["report"] == without_llm["report"]


async def test_valid_explanation_leaves_verdicts_identical(
    auth_client, grant, seeded_family, sf_biscuit_product, use_llm
):
    use_llm(EchoLLM(fail=AssertionError("no consent yet")))
    before = await _post(auth_client, sf_biscuit_product)
    await grant(A, ["ai_processing"])
    use_llm(EchoLLM())
    after = await _post(auth_client, sf_biscuit_product)
    assert after["explanation"]["source"] == "llm"
    assert after["verdicts"] == before["verdicts"] and after["report"] == before["report"]


async def test_email_in_text_is_dropped(
    auth_client, consented, seeded_family, sf_biscuit_product, use_llm
):
    """The router passes the account email to the guard."""
    use_llm(EchoLLM(text=f"member_1: write to {EMAIL.upper()} for help."))
    assert _unavailable(await _post(auth_client, sf_biscuit_product))


# --- consent gate ------------------------------------------------------------------------------


async def test_no_ai_consent_no_call(auth_client, grant, seeded_family, cola_product, fake_llm):
    await grant(A, ["terms", "health_data"])
    body = await _post(auth_client, cola_product, language="hi")
    assert fake_llm.chat_calls == []
    assert _unavailable(body, "hi")
    assert len(body["verdicts"]) == 3


async def test_withdrawn_ai_consent_no_call(
    auth_client, consented, seeded_family, cola_product, fake_llm
):
    r = await auth_client.post(
        "/v1/consents",
        json={"purpose": "ai_processing", "version": CURRENT_VERSIONS["ai_processing"],
              "granted": False},
    )  # fmt: skip
    assert r.status_code == 200
    assert _unavailable(await _post(auth_client, cola_product))
    assert fake_llm.chat_calls == []


async def test_unknown_member_404_makes_no_call(
    auth_client, consented, seeded_family, sf_biscuit_product, fake_llm, other_account_member
):
    r = await auth_client.post(
        URL,
        json={
            "product_id": str(sf_biscuit_product.id),
            "member_ids": [str(other_account_member.id)],
        },
    )
    assert r.status_code == 404 and fake_llm.chat_calls == []


# --- failures degrade --------------------------------------------------------------------------


async def test_llm_timeout_still_200(
    auth_client, consented, seeded_family, sf_biscuit_product, use_llm, monkeypatch, db_session
):
    monkeypatch.setattr(explain_mod, "EXPLANATION_BUDGET_S", 0.05)
    use_llm(EchoLLM(delay=5))
    body = await _post(auth_client, sf_biscuit_product)
    assert [v["status"] for v in body["verdicts"]] == ["caution", "avoid", "avoid"]
    assert body["explanation"]["text"] is None and _unavailable(body)
    assert await db_session.scalar(select(func.count()).select_from(Scan)) == 1
    assert await _cache_rows(db_session) == []


@pytest.mark.parametrize(
    "error",
    [
        ProviderUnavailable("insufficient_credits"),
        ProviderUnavailable("not_configured"),
        CompletionFailed(),
        RuntimeError("boom"),
        TimeoutError(),
    ],
)
async def test_provider_errors_degrade(
    auth_client, consented, seeded_family, sf_biscuit_product, use_llm, error
):
    use_llm(EchoLLM(fail=error))
    body = await _post(auth_client, sf_biscuit_product)
    assert _unavailable(body) and len(body["verdicts"]) == 3


async def test_cache_write_failure_still_200(
    auth_client, consented, seeded_family, sf_biscuit_product, fake_llm, monkeypatch
):
    async def broken(*args, **kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr(analyze_service, "_store_explanation", broken)
    body = await _post(auth_client, sf_biscuit_product)
    assert body["explanation"]["source"] == "llm"


async def test_no_transaction_held_during_llm_call(
    auth_client, consented, seeded_family, sf_biscuit_product, use_llm, db_session
):
    """R16(3): the scan and verdicts are committed before the LLM call starts."""
    seen = {}

    async def check():
        seen["in_transaction"] = db_session.in_transaction()
        seen["scans"] = await db_session.scalar(select(func.count()).select_from(Scan))
        await db_session.commit()  # end the probe's own read

    use_llm(EchoLLM(on_call=check))
    await _post(auth_client, sf_biscuit_product)
    assert seen == {"in_transaction": False, "scans": 1}


# --- cache -------------------------------------------------------------------------------------


async def test_cache_hit_makes_no_second_call(
    auth_client, consented, seeded_family, sf_biscuit_product, fake_llm, db_session
):
    first = await _post(auth_client, sf_biscuit_product, language="hi")
    second = await _post(auth_client, sf_biscuit_product, language="hi")
    assert len(fake_llm.chat_calls) == 1
    assert second["explanation"] == first["explanation"]
    (row,) = await _cache_rows(db_session)
    assert row.product_id == sf_biscuit_product.id and row.language == "hi"
    assert len(row.profile_hash) == 64
    stored = json.dumps(row.payload, ensure_ascii=False)
    for forbidden in ("Dad", "Riya", EMAIL, str(A), *(str(m.id) for m in seeded_family.values())):
        assert forbidden not in stored


async def test_cache_is_per_language(
    auth_client, consented, seeded_family, sf_biscuit_product, fake_llm, db_session
):
    await _post(auth_client, sf_biscuit_product, language="en")
    await _post(auth_client, sf_biscuit_product, language="mr")
    assert len(fake_llm.chat_calls) == 2
    assert sorted(r.language for r in await _cache_rows(db_session)) == ["en", "mr"]


async def test_cache_changes_with_the_family(
    auth_client, consented, seeded_family, sf_biscuit_product, fake_llm
):
    await _post(auth_client, sf_biscuit_product)
    await _post(auth_client, sf_biscuit_product, member_ids=[str(seeded_family["Riya"].id)])
    assert len(fake_llm.chat_calls) == 2


async def test_dropped_explanation_is_not_cached(
    auth_client, consented, seeded_family, sf_biscuit_product, use_llm, db_session
):
    use_llm(EchoLLM(override={"member_3": "ok"}))
    await _post(auth_client, sf_biscuit_product)
    assert await _cache_rows(db_session) == []


async def _primary_only_account(db_session, grant, account_id, name):
    await ensure_account(db_session, AccountContext(account_id, None))
    await grant(account_id)
    primary = await get_or_create_primary(db_session, account_id)
    primary.name = name
    await db_session.flush()
    return primary


async def test_cache_shared_across_accounts_is_guarded_again(
    auth_client, login, grant, cola_product, fake_llm, db_session
):
    """Same anonymised family in another account: a cache hit (no call), but the guard runs
    again with that account's names, and member_refs point at that account's own ids."""
    a = await _primary_only_account(db_session, grant, A, "Asha")
    first = await _post(auth_client, cola_product)
    assert first["explanation"]["member_refs"] == {"member_1": str(a.id)}

    await _primary_only_account(db_session, grant, B, "Easy")  # "easy" is in the cached text
    login(B)
    second = await _post(auth_client, cola_product)
    assert _unavailable(second)

    c = await _primary_only_account(db_session, grant, C, "Kavya")
    login(C)
    third = await _post(auth_client, cola_product)
    assert third["explanation"]["source"] == "llm" and third["explanation"]["text"] == TEXT
    assert third["explanation"]["member_refs"] == {"member_1": str(c.id)}
    assert len(fake_llm.chat_calls) == 1


async def test_off_product_cache_key(auth_client, consented, fake_llm, db_session):
    r = await auth_client.post(URL, json={"barcode": OFF_BARCODE})
    assert r.status_code == 200 and r.json()["explanation"]["source"] == "llm"
    (row,) = await _cache_rows(db_session)
    assert row.product_id == uuid5(NAMESPACE_URL, f"off:{OFF_BARCODE}")
