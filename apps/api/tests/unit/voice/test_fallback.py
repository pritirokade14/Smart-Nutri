"""Server-side i18n and the rule-based spoken fallback (Plan 7 Task 3).

The fallback is built only from engine reason codes and the packages/i18n strings the
clients use. It must render each reason exactly as the clients do (reason-text fixtures).
"""

import json
from pathlib import Path

import pytest

from app import scoring
from app.core.i18n import Catalog, catalog, format_icu, format_number, t
from app.features.voice.fallback import (
    FALLBACK_TIP_KEYS,
    MAX_FALLBACK_REASONS,
    fallback_answer,
    fallback_explanation,
    reason_key,
    reason_sentence,
    verdict_sentence,
    violates_verdict_lock,
)

REASON_TEXT = Path(__file__).parents[5] / "packages" / "test-fixtures" / "reason-text"
S = scoring.Status


# --- i18n ------------------------------------------------------------------------------------


def test_t_falls_back_to_english_then_key():
    cat = Catalog({"en": {"a": "A {x}"}, "hi": {}, "mr": {}})
    assert cat.t("a", "hi", x=1) == "A 1"
    assert cat.t("missing.key", "mr") == "missing.key"


def test_t_reads_repo_messages():
    assert t("voice.verdict_sentence.avoid", "en") == "For this member, avoid this product."
    assert t("status.ok", "hi") == "ठीक है"


def test_icu_select_plural_and_hash():
    msg = "{basis, select, per_serving {One serving} other {100 g}}: {n, plural, =0 {none} one {# item} other {# items}}"
    assert format_icu(msg, "en", basis="per_serving", n=1) == "One serving: 1 item"
    assert format_icu(msg, "en", basis="x", n=3) == "100 g: 3 items"
    assert format_icu(msg, "en", basis="x", n=0) == "100 g: none"


def test_icu_missing_param_raises():
    with pytest.raises(KeyError):
        format_icu("Hello {name}", "en")


@pytest.mark.parametrize(
    ("value", "text"),
    [(10.6, "10.6"), (24, "24"), (10.0, "10"), (1 / 3, "0.333"), (132.5, "132.5")],
)
def test_format_number(value, text):
    assert format_number(value) == text


def test_every_message_parses_in_every_language():
    cat = catalog()
    for language, messages in cat.messages.items():
        for key, message in messages.items():
            try:
                format_icu(message, language, **_dummy_params(message))
            except KeyError:
                pass  # needs a param we didn't guess; parsing succeeded
            except ValueError as exc:  # pragma: no cover - shows which message
                raise AssertionError(f"{language}:{key}: {exc}") from exc


def _dummy_params(message: str) -> dict:
    return {}


# --- reasons, rendered exactly like the clients ------------------------------------------------


@pytest.mark.parametrize("language", ["en", "hi", "mr"])
def test_reason_sentences_match_client_golden_text(language):
    entries = json.loads((REASON_TEXT / f"{language}.json").read_text(encoding="utf-8"))
    assert entries
    for e in entries:
        r = e["reason"]
        reason = scoring.Reason(code=r["code"], severity=S(r["severity"]), params=r["params"])
        assert reason_key(reason.code, reason.params) == e["key"]
        assert reason_sentence(reason, language) == e["text"], e["key"]


def test_unrenderable_reason_is_skipped_not_spoken_broken():
    reason = scoring.Reason(code="sugar_high", severity=S.AVOID, params={})  # no sugars_g
    assert reason_sentence(reason, "en") is None


def test_unknown_code_is_skipped():
    reason = scoring.Reason(code="not_a_code", severity=S.AVOID, params={})
    assert reason_sentence(reason, "en") is None


# --- verdict sentences and the fallback answer ---------------------------------------------------


@pytest.mark.parametrize("language", ["en", "hi", "mr"])
@pytest.mark.parametrize("status", list(S))
def test_verdict_sentence_for_every_status_and_language(status, language):
    text = verdict_sentence(status, language)
    assert text == t(f"voice.verdict_sentence.{status.value}", language)
    assert text != f"voice.verdict_sentence.{status.value}"


def test_avoid_fallback_starts_with_engine_verdict_and_lists_reasons(avoid_case):
    text = fallback_answer(avoid_case.verdict, "en")
    assert text.startswith("For this member, avoid this product.")
    first = reason_sentence(avoid_case.verdict.reasons[0], "en")
    assert first and first in text


def test_unknown_verdict_fallback_says_label_unclear(unknown_case):
    e = fallback_explanation(unknown_case.verdict, "mr")
    assert e.text.startswith(t("voice.verdict_sentence.unknown", "mr"))
    assert "सुरक्षित" not in e.text


def test_unknown_fallback_never_implies_safety_in_any_language(unknown_case):
    for language in ("en", "hi", "mr"):
        text = fallback_answer(unknown_case.verdict, language)
        assert not violates_verdict_lock(text, S.UNKNOWN, language)


def test_fallback_has_at_most_three_reasons_most_severe_first():
    reasons = (
        scoring.Reason("good_protein_density", S.OK, {}),
        scoring.Reason("salt_moderate", S.CAUTION, {"salt_g": 1.0}),
        scoring.Reason("allergen_contains", S.AVOID, {"allergen": "peanut"}),
        scoring.Reason("hidden_sugars", S.CAUTION, {"ingredients": ["dextrose"]}),
        scoring.Reason("sugar_high", S.AVOID, {"sugars_g": 30}),
    )
    verdict = scoring.MemberVerdict(member_id="m", status=S.AVOID, reasons=reasons)
    text = fallback_answer(verdict, "en")
    assert MAX_FALLBACK_REASONS == 3
    assert text == (
        "For this member, avoid this product. "
        "Contains Peanut, which is on your avoid list. "
        "High in sugar: 30 g per 100 g/ml. "
        "Moderate salt: 1 g per 100 g/ml."
    )


def test_fallback_explanation_has_three_tips(avoid_case):
    e = fallback_explanation(avoid_case.verdict, "hi")
    assert len(e.tips) == 3 == len(FALLBACK_TIP_KEYS)
    assert e.tips == tuple(t(k, "hi") for k in FALLBACK_TIP_KEYS)
    assert e.source == "fallback"


def test_fallback_is_pure_and_uses_the_given_catalog(avoid_case):
    cat = Catalog(
        {
            "en": {"voice.verdict_sentence.avoid": "AVOID!", "reason.misleading_sugar_claim": "R."},
            "hi": {},
            "mr": {},
        }
    )
    assert fallback_answer(avoid_case.verdict, "en", cat).startswith("AVOID!")


# --- verdict lock ------------------------------------------------------------------------------


def test_violates_verdict_lock_in_hindi():
    assert violates_verdict_lock(t("verdict.status.ok", "hi"), S.AVOID, "hi")


def test_violates_verdict_lock_english_label_in_other_language():
    assert violates_verdict_lock("यह OK है", S.AVOID, "hi")


@pytest.mark.parametrize("language", ["en", "hi", "mr"])
def test_safe_word_always_rejected(language):
    word = t("voice.word_safe", language)
    for status in S:
        assert violates_verdict_lock(f"x {word} x", status, language)
    assert violates_verdict_lock("This is safe for you.", S.OK, language)
    assert violates_verdict_lock("यह सेफ है", S.OK, language)


def test_own_status_label_is_allowed():
    assert not violates_verdict_lock("Avoid it: it has a lot of sugar.", S.AVOID, "en")
    assert violates_verdict_lock("Avoid it.", S.CAUTION, "en")


def test_lock_matches_whole_words_only_for_latin():
    assert not violates_verdict_lock("The bookshelf of cautious tokens.", S.AVOID, "en")
    assert violates_verdict_lock("It is ok.", S.AVOID, "en")


def test_lock_ignores_case_and_invisible_characters():
    assert violates_verdict_lock("It is O\u200bK.", S.AVOID, "en")
    assert violates_verdict_lock("SAFE", S.AVOID, "en")
