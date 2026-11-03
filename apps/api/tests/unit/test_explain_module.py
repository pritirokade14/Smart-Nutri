"""F7 part A: explanation input builder, guard and orchestrator (Plan 5 T7a).

The LLM only explains. These tests pin that it never sees names, ids, emails, free text
or the product name, that any disagreement with the engine drops the explanation, and that
every failure degrades to None. Nothing calls the real CallMissed API.
"""

import asyncio
import copy
import dataclasses
import json
import uuid
from datetime import date
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from app import scoring
from app.core.config import Settings
from app.features.analyze import explain as explain_mod
from app.features.analyze.explain import (
    EXPLANATION_BUDGET_S,
    Explanation,
    ExplanationLLM,
    MemberStatusEcho,
    build_explanation_input,
    explain,
    guard,
)
from app.features.members.models import Member
from app.features.members.service import to_scoring_member
from app.integrations import callmissed
from app.integrations.callmissed import CallMissedClient
from app.integrations.providers import CompletionFailed, ProviderUnavailable
from app.prompts import load_prompt
from tests.fakes.llm import FakeLLM

TODAY = date(2026, 11, 3)
ACCOUNT_ID = uuid.UUID("0b8f7a52-0000-4000-8000-00000000a001")
DAD_ID = uuid.UUID("0b8f7a52-0000-4000-8000-0000000000d1")
RIYA_ID = uuid.UUID("0b8f7a52-0000-4000-8000-0000000000c2")
EMAIL = "Parent.Sharma@Example.com"
PRODUCT_NAME = "Zorblax Sugar-Free Marie"
SECRET = "cm_test_secret_key"


def _row(**kw) -> Member:
    base = {
        "account_id": ACCOUNT_ID, "sex": None, "height_cm": None, "weight_kg": None,
        "custom_alerts": [], "goal": None, "is_primary": False, "allergens": [],
        "conditions": [], "diet": "non_veg",
    }  # fmt: skip
    return Member(**{**base, **kw})


@pytest.fixture
def family_rows() -> list[Member]:
    return [
        _row(
            id=DAD_ID, name="Dad", relation="parent", birth_year=1960, diet="veg",
            conditions=["diabetes", "Sharma knee thing"],
        ),
        _row(
            id=RIYA_ID, name="रिया", relation="child", birth_year=2018,
            allergens=["milk", "Riyas school paste"],
        ),
    ]  # fmt: skip


@pytest.fixture
def product() -> scoring.Product:
    return scoring.Product(
        name=PRODUCT_NAME,
        per_100g=scoring.Nutrients(
            energy_kcal=480,
            sugars_g=28.0,
            carbs_g=70,
            fat_g=18,
            sat_fat_g=9,
            salt_g=0.9,
            protein_g=7,
            fiber_g=2,
        ),
        ingredients=("refined wheat flour (maida)", "sugar", "milk solids", "invert syrup"),
        claims=("sugar free",),
    )


@pytest.fixture
def family_result(product, family_rows) -> scoring.AnalysisResult:
    return scoring.analyze(product, [to_scoring_member(m, today=TODAY) for m in family_rows])


@pytest.fixture
def settings() -> Settings:
    return Settings(_env_file=None, environment="test", callmissed_explanation_model="expl-model")


def _echo(result: scoring.AnalysisResult, **override: str) -> list[MemberStatusEcho]:
    out = []
    for i, v in enumerate(result.verdicts, start=1):
        ref = f"member_{i}"
        out.append(MemberStatusEcho(ref=ref, status=override.get(ref, v.status.value)))
    return out


def _llm_out(result, text="member_1 should go easy on this.", tips=None, **override):
    return ExplanationLLM(
        members=_echo(result, **override),
        text=text,
        tips=["Check the sugar line first."] if tips is None else tips,
    )


def _names(rows):
    return [r.name for r in rows]


# --- engine sanity for the fixtures ------------------------------------------------------


def test_fixture_engine_statuses(family_result):
    # Dad (diabetes, veg) and Riya (milk allergy) both get avoid for this biscuit.
    assert [v.status.value for v in family_result.verdicts] == ["avoid", "avoid"]


# --- build_explanation_input ---------------------------------------------------------------


def test_input_members_are_tokens_in_verdict_order(family_result, family_rows):
    data = build_explanation_input(family_result, family_rows, "hi", today=TODAY)
    assert data.language == "hi"
    refs = [m.ref for m in data.members]
    assert refs == ["member_1", "member_2"]
    m1, m2 = data.members
    assert (m1.relation, m1.age_band, m1.diet, m1.status) == ("parent", "60_plus", "veg", "avoid")
    assert (m2.relation, m2.age_band, m2.diet, m2.status) == ("child", "2_12", "non_veg", "avoid")
    assert [r.code for r in m1.reasons] == [r.code for r in family_result.verdicts[0].reasons]


def test_free_text_params_become_other(family_result, family_rows):
    data = build_explanation_input(family_result, family_rows, "en", today=TODAY)
    params = [r.params for m in data.members for r in m.reasons]
    conditions = [p["condition"] for p in params if "condition" in p]
    allergens = [p["allergen"] for p in params if "allergen" in p]
    assert conditions == ["other"]
    assert "milk" in allergens and "other" in allergens
    assert set(allergens) <= {"milk", "other"}
    assert {a.allergen for a in data.product.allergens} <= {"milk", "gluten", "wheat", "other"}


def test_age_band_unknown_without_birth_year(product):
    rows = [_row(id=uuid.uuid4(), name="X", relation="self", birth_year=None)]
    result = scoring.analyze(product, [to_scoring_member(m, today=TODAY) for m in rows])
    data = build_explanation_input(result, rows, "en", today=TODAY)
    assert data.members[0].age_band == "unknown"


@pytest.mark.parametrize(
    ("birth_year", "band"),
    [(2026, "under_2"), (2024, "under_2"), (2023, "2_12"), (2013, "2_12"), (2012, "13_17"),
     (2008, "13_17"), (2007, "18_59"), (1966, "18_59"), (1965, "60_plus"), (2027, "unknown")],
)  # fmt: skip
def test_age_bands_use_youngest_age(product, birth_year, band):
    rows = [_row(id=uuid.uuid4(), name="X", relation="other", birth_year=birth_year)]
    result = scoring.analyze(product, [to_scoring_member(m, today=TODAY) for m in rows])
    assert build_explanation_input(result, rows, "en", today=TODAY).members[0].age_band == band


def test_member_order_mismatch_is_an_error(family_result, family_rows):
    with pytest.raises(ValueError):
        build_explanation_input(family_result, list(reversed(family_rows)), "en", today=TODAY)


# --- explain(): what reaches the provider --------------------------------------------------


async def test_prompt_has_no_member_names(family_result, family_rows, settings):
    fake = FakeLLM(chat_result=_llm_out(family_result))
    await explain(fake, settings, family_result, family_rows, "hi", emails=[EMAIL], today=TODAY)
    sent = json.dumps(fake.chat_calls[0], default=str, ensure_ascii=False)
    for forbidden in (
        "Dad", "रिया", str(DAD_ID), str(RIYA_ID), str(ACCOUNT_ID), EMAIL, EMAIL.lower(),
        PRODUCT_NAME, "Zorblax", "Sharma", "Riyas", "school paste", "knee",
    ):  # fmt: skip
        assert forbidden not in sent, forbidden
    call = fake.chat_calls[0]
    assert call["model"] == "expl-model"
    assert call["prompt_version"] == "explanation_v2"
    assert call["schema"] is ExplanationLLM
    assert call["system"] == load_prompt("explanation_v2")[0]
    assert call["timeout_s"] == EXPLANATION_BUDGET_S == 8.0
    assert json.loads(call["user"])["language"] == "hi"


def _wire_client(responses: list[httpx.Response]):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return responses[min(len(seen) - 1, len(responses) - 1)]

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = CallMissedClient(api_key=SECRET, base_url="https://cm.test/v1", http_client=http)
    return client, seen


def _completion(content: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "x", "object": "chat.completion", "created": 0, "model": "expl-model",
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": content}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        },
    )  # fmt: skip


@pytest.fixture
def no_sleep(monkeypatch):
    async def fake_sleep(_s):
        return None

    monkeypatch.setattr(callmissed, "_sleep", fake_sleep)


async def test_wire_request_has_residency_strict_schema_and_no_pii(
    family_result, family_rows, settings
):
    client, seen = _wire_client([_completion(_llm_out(family_result).model_dump_json())])
    out = await explain(
        client, settings, family_result, family_rows, "mr", emails=[EMAIL], today=TODAY
    )
    assert isinstance(out, Explanation)
    raw = seen[0].content.decode()
    body = json.loads(raw)
    assert body["provider"] == {"data_residency": "in"}
    assert body["model"] == "expl-model" and body["temperature"] == 0
    rf = body["response_format"]
    assert rf["type"] == "json_schema" and rf["json_schema"]["strict"] is True
    assert sorted(rf["json_schema"]["schema"]["required"]) == ["members", "text", "tips"]
    decoded = json.dumps(body, ensure_ascii=False)
    for forbidden in ("Dad", "रिया", str(DAD_ID), str(RIYA_ID), str(ACCOUNT_ID), EMAIL,
                      PRODUCT_NAME, "Sharma"):  # fmt: skip
        assert forbidden not in decoded, forbidden


async def test_402_is_none(family_result, family_rows, settings):
    client, seen = _wire_client([httpx.Response(402, json={"error": {"code": "x"}})])
    assert await explain(client, settings, family_result, family_rows, "en", today=TODAY) is None
    assert len(seen) == 1


async def test_5xx_is_none(family_result, family_rows, settings, no_sleep):
    client, _ = _wire_client([httpx.Response(503, json={})])
    assert await explain(client, settings, family_result, family_rows, "en", today=TODAY) is None


@pytest.mark.parametrize(
    "error",
    [ProviderUnavailable("insufficient_credits"), ProviderUnavailable("not_configured"),
     CompletionFailed("x"), RuntimeError("boom"), ValueError("bad"), TimeoutError()],
)  # fmt: skip
async def test_provider_error_is_none(family_result, family_rows, settings, error):
    fake = FakeLLM(chat_result=error)
    assert await explain(fake, settings, family_result, family_rows, "en", today=TODAY) is None


async def test_timeout_is_none(family_result, family_rows, settings, monkeypatch):
    monkeypatch.setattr(explain_mod, "EXPLANATION_BUDGET_S", 0.05)

    class SlowLLM:
        async def chat_json(self, **_kw):
            await asyncio.sleep(5)
            raise AssertionError("budget not enforced")

    loop = asyncio.get_running_loop()
    start = loop.time()
    out = await explain(SlowLLM(), settings, family_result, family_rows, "en", today=TODAY)
    assert out is None
    assert loop.time() - start < 1.0


async def test_unsupported_language_makes_no_call(family_result, family_rows, settings):
    fake = FakeLLM(chat_result=_llm_out(family_result))
    assert await explain(fake, settings, family_result, family_rows, "fr", today=TODAY) is None
    assert fake.chat_calls == []


async def test_member_mismatch_makes_no_call(family_result, family_rows, settings):
    fake = FakeLLM(chat_result=_llm_out(family_result))
    out = await explain(fake, settings, family_result, family_rows[:1], "en", today=TODAY)
    assert out is None and fake.chat_calls == []


async def test_valid_explanation_passes_through(family_result, family_rows, settings):
    fake = FakeLLM(chat_result=_llm_out(family_result, text="member_2 को दूध से बचना है।"))
    out = await explain(
        fake, settings, family_result, family_rows, "hi", emails=[EMAIL], today=TODAY
    )
    assert out == Explanation(
        text="member_2 को दूध से बचना है।",
        tips=["Check the sugar line first."],
        language="hi",
        prompt_version="explanation_v2",
        member_refs={"member_1": str(DAD_ID), "member_2": str(RIYA_ID)},
    )


# --- the verdict is never changed ------------------------------------------------------------


async def test_explanation_never_changes_verdict(family_result, family_rows, settings):
    before = copy.deepcopy(family_result.to_dict())
    verdicts_before = family_result.verdicts
    fake = FakeLLM(chat_result=_llm_out(family_result, member_1="ok"))  # engine says avoid
    out = await explain(fake, settings, family_result, family_rows, "en", today=TODAY)
    assert out is None
    assert len(fake.chat_calls) == 1
    assert family_result.verdicts is verdicts_before
    assert family_result.to_dict() == before
    assert family_result.verdicts[0].status == scoring.Status.AVOID


@pytest.mark.parametrize("wrong", ["ok", "caution", "unknown"])
def test_guard_drops_any_status_mismatch(family_result, family_rows, wrong):
    out = _llm_out(family_result, member_2=wrong)
    assert guard(out, family_result, _names(family_rows), [], language="en",
                 prompt_version="explanation_v2") is None  # fmt: skip


def _guard(out, result, rows, emails=()):
    return guard(out, result, _names(rows), list(emails), language="en",
                 prompt_version="explanation_v2")  # fmt: skip


def test_guard_drops_missing_member(family_result, family_rows):
    out = _llm_out(family_result)
    out = out.model_copy(update={"members": out.members[:1]})
    assert _guard(out, family_result, family_rows) is None


def test_guard_drops_extra_or_duplicate_member(family_result, family_rows):
    out = _llm_out(family_result)
    extra = out.model_copy(
        update={"members": [*out.members, MemberStatusEcho(ref="member_3", status="ok")]}
    )
    dup = out.model_copy(update={"members": [*out.members, out.members[0]]})
    assert _guard(extra, family_result, family_rows) is None
    assert _guard(dup, family_result, family_rows) is None


def test_guard_drops_unknown_member_token(family_result, family_rows):
    out = _llm_out(family_result, text="member_3 can have it.")
    assert _guard(out, family_result, family_rows) is None
    tips = _llm_out(family_result, tips=["Give member_7 less."])
    assert _guard(tips, family_result, family_rows) is None


@pytest.mark.parametrize("text", ["dad should skip it.", "DAD: avoid", "For Dad's tea time"])
def test_guard_drops_latin_name_case_insensitive(family_result, family_rows, text):
    assert _guard(_llm_out(family_result, text=text), family_result, family_rows) is None


@pytest.mark.parametrize(
    "text",
    ["रिया को यह नहीं देना चाहिए।", "रियाला हे देऊ नका.", "र‍िया avoid"],
)
def test_guard_drops_devanagari_name(family_result, family_rows, text):
    assert _guard(_llm_out(family_result, text=text), family_result, family_rows) is None


def test_guard_devanagari_nukta_normalised(product):
    rows = [_row(id=uuid.uuid4(), name="ज़ोया", relation="self", birth_year=1990)]
    result = scoring.analyze(product, [to_scoring_member(m, today=TODAY) for m in rows])
    decomposed = "ज़ोया"  # same name, nukta as a combining mark
    out = _llm_out(result, text=f"{decomposed} को चीनी कम लेनी है।")
    assert _guard(out, result, rows) is None


def test_guard_drops_name_in_tips(family_result, family_rows):
    out = _llm_out(family_result, tips=["Ask Dad to read the label."])
    assert _guard(out, family_result, family_rows) is None


def test_guard_drops_email_case_insensitive(family_result, family_rows):
    out = _llm_out(family_result, text="Write to parent.sharma@example.com for help.")
    assert _guard(out, family_result, family_rows, [EMAIL]) is None


def test_guard_name_needs_a_word_start(family_result, product):
    rows = [_row(id=uuid.uuid4(), name="Al", relation="self", birth_year=1990)]
    result = scoring.analyze(product, [to_scoring_member(m, today=TODAY) for m in rows])
    out = _llm_out(result, text="member_1 should also check the salt.")
    assert _guard(out, result, rows) is not None


@pytest.mark.parametrize(
    "text",
    [
        "member 2 should skip it.",
        "Member-2 should skip it.",
        "Member_1 should skip it.",
        "MEMBER_1 should skip it.",
        "member2 should skip it.",
        "member_01 should skip it.",
        "member_२ को यह नहीं देना चाहिए।",
        "member_1 and member - 2 should skip it.",
    ],
)
def test_guard_drops_member_token_variants(family_result, family_rows, text):
    # Ruling P7: only the exact `member_N` form is substituted by clients.
    assert _guard(_llm_out(family_result, text=text), family_result, family_rows) is None


def test_guard_drops_member_token_variant_in_tips(family_result, family_rows):
    out = _llm_out(family_result, tips=["Member 1 can compare labels."])
    assert _guard(out, family_result, family_rows) is None


def test_guard_ignores_member_inside_another_word(family_result, family_rows):
    out = _llm_out(family_result, text="member_1: remember 2 things on the label.")
    assert _guard(out, family_result, family_rows) is not None


@pytest.fixture
def all_ok():
    rows = [_row(id=uuid.uuid4(), name="Zed", relation="self", birth_year=1990)]
    product = scoring.Product(
        name="plain",
        per_100g=scoring.Nutrients(
            energy_kcal=350, sugars_g=1, carbs_g=60, fat_g=6, sat_fat_g=1, salt_g=0.01,
            protein_g=12, fiber_g=10,
        ),
        ingredients=("rolled oats",),
    )  # fmt: skip
    result = scoring.analyze(product, [to_scoring_member(m, today=TODAY) for m in rows])
    assert [v.status for v in result.verdicts] == [scoring.Status.OK]
    return result, rows


@pytest.mark.parametrize(
    "text",
    [
        # en
        "This is safe for member_1.",
        "SAFE choice.",
        "member_2 can safely eat it.",
        "A healthy snack for member_1.",
        "Healthy!",
        # hi
        "यह member_1 के लिए सुरक्षित है।",
        "यह एक सेहतमंद नाश्ता है।",
        "यह हेल्दी स्नैक है।",
        # mr
        "हे member_2 साठी सुरक्षित आहे.",
        "हा सुरक्षित पर्याय आहे.",
        "हा हेल्दी खाऊ आहे.",
        # controller addition after the c2897fd re-review
        "यह member_1 के लिए स्वस्थ विकल्प है।",
        "हा निरोगी पर्याय आहे.",
        "member_2 साठी निरोगी खाऊ.",
    ],
)
def test_guard_deny_list_for_every_status(family_result, family_rows, all_ok, text):
    assert _guard(_llm_out(family_result, text=text), family_result, family_rows) is None
    ok_result, ok_rows = all_ok
    assert _guard(_llm_out(ok_result, text=text), ok_result, ok_rows) is None


@pytest.mark.parametrize(
    "text", ["member_2 के लिए ठीक है।", "member_2 साठी हे चालेल.", "member_2 साठी ठीक आहे."]
)
def test_guard_drops_hi_mr_okay_for_a_non_ok_member(family_result, family_rows, text):
    """Controller addition: "ठीक" (hi) and "चालेल" (mr) for a member the engine did not mark ok."""
    assert family_result.verdicts[1].status is not scoring.Status.OK
    assert _guard(_llm_out(family_result, text=text), family_result, family_rows) is None


def test_guard_deny_list_applies_to_tips(family_result, family_rows):
    out = _llm_out(family_result, tips=["Pick a healthy version."])
    assert _guard(out, family_result, family_rows) is None


@pytest.mark.parametrize(
    "text",
    [
        "member_1 is fine with this.",
        "It is Okay now and then.",
        "FINE for member_1",
        "member_1 के लिए ठीक है।",
        "यह member_1 के लिए ठीक रहेगा।",
        "member_1 साठी चालेल.",
        "हे member_1 ला चालेल.",
    ],
)
def test_guard_denies_fine_and_okay_when_a_member_is_not_ok(
    family_result, family_rows, all_ok, text
):
    assert _guard(_llm_out(family_result, text=text), family_result, family_rows) is None
    ok_result, ok_rows = all_ok
    assert _guard(_llm_out(ok_result, text=text), ok_result, ok_rows) is not None


@pytest.mark.parametrize(
    "text",
    [
        "member_1 should check the safety seal.",
        "Unhealthy fats are listed; member_2 should skip it.",
        "member_1: the finer print lists sugar.",
        "member_1 को चीनी कम लेनी चाहिए।",
        "member_2 ने हे टाळावे.",
    ],
)
def test_guard_deny_list_matches_whole_latin_words_only(family_result, family_rows, text):
    assert _guard(_llm_out(family_result, text=text), family_result, family_rows) is not None


def test_guard_drops_blank_text(family_result, family_rows):
    assert _guard(_llm_out(family_result, text="   "), family_result, family_rows) is None


def test_guard_keeps_tokens_for_clients(family_result, family_rows):
    out = _guard(_llm_out(family_result), family_result, family_rows)
    assert out is not None and "member_1" in out.text
    assert out.member_refs == {"member_1": str(DAD_ID), "member_2": str(RIYA_ID)}


# --- the strict LLM schema -------------------------------------------------------------------


def test_llm_schema_rejects_extra_fields_and_limits(family_result):
    echo = [m.model_dump() for m in _echo(family_result)]
    with pytest.raises(ValidationError):
        ExplanationLLM.model_validate({"members": echo, "text": "x", "tips": [], "verdict": "ok"})
    with pytest.raises(ValidationError):
        ExplanationLLM.model_validate({"members": echo, "text": "x" * 901, "tips": []})
    with pytest.raises(ValidationError):
        ExplanationLLM.model_validate({"members": echo, "text": "x", "tips": ["a"] * 4})
    with pytest.raises(ValidationError):
        ExplanationLLM.model_validate({"members": echo, "text": "x", "tips": ["a" * 141]})
    with pytest.raises(ValidationError):
        ExplanationLLM.model_validate(
            {"members": [{"ref": "member_1", "status": "safe"}], "text": "x", "tips": []}
        )


# --- the prompt ----------------------------------------------------------------------------


def test_prompt_file_rules():
    text, version = load_prompt("explanation_v2")
    assert version == "explanation_v2"
    assert "Information, not medical advice" in text
    for needle in ("member_N", "en", "hi", "mr", "never change", "members"):
        assert needle in text, needle
    assert "Make no medical claims" in text
    assert "Unknown is NOT safe" in text


def test_prompt_caution_wording_and_forbidden_words_ruling_p7():
    text, _ = load_prompt("explanation_v2")
    assert "fine now and then" not in text and "small portion" not in text
    assert "there is something to watch; see the reasons" in text
    for word in ("safe", "healthy", "सुरक्षित", "सेहतमंद", "हेल्दी", "सुरक्षित आहे"):
        assert f'"{word}"' in text, word
    assert "for every status" in text


def test_prompt_lists_every_denied_word():
    """The model is told about every word the guard drops (so it can avoid them)."""
    text, _ = load_prompt("explanation_v2")
    for word in (
        *explain_mod.DENY_WORDS,
        *explain_mod.DENY_WORDS_NOT_ALL_OK,
        *explain_mod.DENY_WORDS_CLAIMS,
    ):
        assert f'"{word}"' in text, word


def test_deny_lists_include_the_re_review_additions():
    assert {"स्वस्थ", "निरोगी"} <= set(explain_mod.DENY_WORDS)
    assert {"ठीक", "चालेल"} <= set(explain_mod.DENY_WORDS_NOT_ALL_OK)


def test_no_duplicate_today_ist():
    """Ruling P8.2: one IST "today", in app.core.time."""
    from app.core import time as core_time

    assert explain_mod.today_ist is core_time.today_ist
    assert not hasattr(explain_mod, "_IST")


# --- cache key -----------------------------------------------------------------------------


def test_cache_key_is_anonymous_and_versioned(family_result, family_rows, product):
    data = build_explanation_input(family_result, family_rows, "hi", today=TODAY)
    key = explain_mod.cache_key(data, "explanation_v2", "expl-model", "PROMPT")
    assert len(key) == 64 and int(key, 16) >= 0
    assert key == explain_mod.cache_key(
        build_explanation_input(family_result, family_rows, "hi", today=TODAY),
        "explanation_v2",
        "expl-model",
        "PROMPT",
    )
    # Same anonymised family under other names and ids: same key (names never reach it).
    renamed = [copy.copy(m) for m in family_rows]
    for i, m in enumerate(renamed):
        m.name, m.id = f"Other{i}", uuid.uuid4()
    other = scoring.analyze(
        dataclasses.replace(product, name="Another name"),
        [to_scoring_member(m, today=TODAY) for m in renamed],
    )
    assert (
        explain_mod.cache_key(
            build_explanation_input(other, renamed, "hi", today=TODAY),
            "explanation_v2",
            "expl-model",
            "PROMPT",
        )
        == key
    )
    # Language, prompt version and model each change it.
    assert key != explain_mod.cache_key(
        build_explanation_input(family_result, family_rows, "en", today=TODAY),
        "explanation_v2",
        "expl-model",
        "PROMPT",
    )
    assert key != explain_mod.cache_key(data, "explanation_v1", "expl-model", "PROMPT")
    assert key != explain_mod.cache_key(data, "explanation_v2", "other-model", "PROMPT")
    # An in-place prompt edit (same version label) changes the key.
    assert key != explain_mod.cache_key(data, "explanation_v2", "expl-model", "PROMPT edited")


# Plan 9 Task 7 reason codes that the released explanation_v1 cannot list (released prompts
# are never edited in place, P9-R15). v1's "a code you do not recognise: explain it only from
# its params, or leave it out" covers them meanwhile (their params are empty, so they are left
# out). At merge: list them in explanation_v2.md / voice_v2.md (Task 5) and empty this set.
NOT_IN_RELEASED_PROMPT = {"supplement_child", "supplement_infant"}


def test_prompt_lists_every_engine_reason_code():
    text, _ = load_prompt("explanation_v2")
    for code in ("carbs_per_serving_high", "good_protein_density", "custom_alert_unknown"):
        assert f"`{code}`" in text, code
    en = json.loads(
        (Path(__file__).parents[4] / "packages/i18n/messages/en.json").read_text("utf-8")
    )
    missing = [c for c in en["reason"] if f"`{c}`" not in text and c not in NOT_IN_RELEASED_PROMPT]
    assert missing == []


# --- medical-claim and "suitable" deny words ----------------------------------------------

_CLAIM_TEXTS = [
    "This will cure your cough.",
    "It cures acidity.",
    "Helps treat diabetes.",
    "It treats low sugar.",
    "A good treatment option.",
    "It can reverse the condition.",
    "It may prevent spikes.",
    "It prevents cravings.",
    "यह इलाज में मदद करता है।",
    "यह उपचार के लिए अच्छा है।",
    "यामुळे आजार बरा होतो.",
]
_SUITABLE_TEXTS = [
    "It is suitable for member_1.",
    "यह member_1 के लिए योग्य है।",
    "हे member_1 साठी उपयुक्त आहे.",
    "यह उपयुक्त है।",
]


@pytest.mark.parametrize("text", _CLAIM_TEXTS)
def test_guard_always_drops_medical_claim_words(family_result, family_rows, text):
    assert _guard(_llm_out(family_result, text=text), family_result, family_rows) is None
    tips = _llm_out(family_result, tips=[text])
    assert _guard(tips, family_result, family_rows) is None


@pytest.mark.parametrize("text", _CLAIM_TEXTS)
def test_guard_drops_medical_claim_words_when_all_ok(family_result, product, text):
    rows = [_row(id=uuid.uuid4(), name="Solo", relation="self", birth_year=1990)]
    result = scoring.analyze(product, [to_scoring_member(m, today=TODAY) for m in rows])
    assert all(v.status is scoring.Status.OK for v in result.verdicts)
    assert _guard(_llm_out(result, text=text), result, rows) is None


@pytest.mark.parametrize("text", _SUITABLE_TEXTS)
def test_guard_drops_suitable_when_any_member_not_ok(family_result, family_rows, text):
    assert any(v.status is not scoring.Status.OK for v in family_result.verdicts)
    assert _guard(_llm_out(family_result, text=text), family_result, family_rows) is None


@pytest.mark.parametrize("text", _SUITABLE_TEXTS)
def test_guard_allows_suitable_when_all_ok(product, text):
    rows = [_row(id=uuid.uuid4(), name="Solo", relation="self", birth_year=1990)]
    result = scoring.analyze(product, [to_scoring_member(m, today=TODAY) for m in rows])
    assert all(v.status is scoring.Status.OK for v in result.verdicts)
    assert _guard(_llm_out(result, text=text), result, rows) is not None


def test_claim_deny_list_contents():
    assert {
        "cure", "cures", "treat", "treats", "treatment", "reverse", "prevent", "prevents",
        "इलाज", "उपचार", "बरा",
    } <= set(explain_mod.DENY_WORDS_CLAIMS)  # fmt: skip
    assert {"suitable", "योग्य", "उपयुक्त"} <= set(explain_mod.DENY_WORDS_NOT_ALL_OK)


def test_ruling_v1_deny_list_additions():
    """Ruling V1 B1: disease-management claims always; go-ahead phrasing when not all ok."""
    assert {"manage", "manages", "control", "controls"} <= set(explain_mod.DENY_WORDS_CLAIMS)
    assert {
        "acceptable", "go ahead", "खा सकते", "चल जाएगा", "खाऊ शकता", "हरकत नाही",
    } <= set(explain_mod.DENY_WORDS_NOT_ALL_OK)  # fmt: skip


@pytest.mark.parametrize(
    "text",
    ["member_1 can go ahead.", "member_1 के लिए चल जाएगा।", "member_1 साठी हरकत नाही."],
)
def test_guard_drops_go_ahead_for_a_non_ok_family(family_result, family_rows, all_ok, text):
    assert _guard(_llm_out(family_result, text=text), family_result, family_rows) is None
    ok_result, ok_rows = all_ok
    assert _guard(_llm_out(ok_result, text=text), ok_result, ok_rows) is not None


def test_guard_drops_disease_control_claims_for_every_status(family_result, family_rows, all_ok):
    text = "It may help member_1 control blood sugar."
    assert _guard(_llm_out(family_result, text=text), family_result, family_rows) is None
    ok_result, ok_rows = all_ok
    assert _guard(_llm_out(ok_result, text=text), ok_result, ok_rows) is None


# --- Plan 9 T5: protein-guide guard rules (prompt v2) --------------------------------------


def test_explanation_uses_v2():
    from app.prompts import EXPLANATION_PROMPT_VERSION

    assert EXPLANATION_PROMPT_VERSION == "explanation_v2"
    text, version = load_prompt(EXPLANATION_PROMPT_VERSION)
    assert version == "explanation_v2"
    assert "Never recommend a supplement, a brand or a product to buy" in text
    assert "You may repeat protein numbers that are in the input" in text


_ADVICE_TEXTS = [
    "member_1 could try creatine.",
    "Some people take steroids for this.",
    "Skip steroid use.",
    "A fat burner will not help member_1.",
    "Try a protein supplement.",
    "Buy this brand instead.",
    "Take a pre-workout first.",
    "Have 2 scoops a day.",
    "member_1 needs 60 g of protein.",
    "You should eat 40 grams daily.",
    "The dose depends on weight.",
    "member_1 को क्रिएटिन लेना चाहिए।",
    "स्टेरॉयड से बचें।",
    "प्रोटीन सप्लिमेंट लें।",
    "ब्रांड बदलें।",
    "आपको 60 ग्राम प्रोटीन चाहिए।",
    "दिन में 2 स्कूप लें।",
    "member_1 ला क्रिएटिन घ्या.",
    "तुम्हाला ६० ग्रॅम प्रोटीन लागेल.",
    "ब्रँड बदला.",
    "फॅट बर्नर घेऊ नका.",
]


@pytest.mark.parametrize("text", _ADVICE_TEXTS)
def test_guard_drops_supplement_dose_and_creatine_advice_for_every_status(
    family_result, family_rows, all_ok, text
):
    assert _guard(_llm_out(family_result, text=text), family_result, family_rows) is None
    ok_result, ok_rows = all_ok
    assert _guard(_llm_out(ok_result, text=text), ok_result, ok_rows) is None


def test_guard_drops_advice_in_tips(family_result, family_rows):
    out = _llm_out(family_result)
    out.tips = ["Add creatine."]
    assert _guard(out, family_result, family_rows) is None


def test_guard_keeps_protein_numbers_from_the_input(all_ok):
    ok_result, ok_rows = all_ok
    text = "member_1: this has 12 g protein per 100 g, so compare labels."
    assert _guard(_llm_out(ok_result, text=text), ok_result, ok_rows) is not None


def test_advice_deny_list_contents():
    assert {
        "creatine", "steroid", "steroids", "fat burner", "supplement", "brand", "scoop",
        "क्रिएटिन", "स्टेरॉयड",
    } <= set(explain_mod.DENY_WORDS_ADVICE)  # fmt: skip


def test_explanation_prompt_lists_every_advice_word():
    text, _ = load_prompt("explanation_v2")
    for word in explain_mod.DENY_WORDS_ADVICE:
        assert f'"{word}"' in text, word


def test_context_has_no_user_types(family_result, family_rows):
    data = explain_mod.build_explanation_input(family_result, family_rows, "en", today=TODAY)
    keys: set[str] = set()

    def walk(v):
        if isinstance(v, dict):
            for k, x in v.items():
                keys.add(k)
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)

    walk(json.loads(data.model_dump_json()))
    assert not keys & {"user_type", "types", "active_type"}
