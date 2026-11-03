"""F7: an LLM explanation of the engine's verdicts that can never change them (Plan 5 T7a).

Pure building blocks plus one async orchestrator; no DB, no cache (those come with the
analyze wiring in part B).

- `build_explanation_input` anonymises the family: members become `member_1..N` (verdict
  order) with relation, age band and diet only. No names, ids, emails, product name, brand or
  raw ingredient text; free-text params (a typed-in allergen or condition) become "other".
- `ExplanationLLM` is the strict schema the model must fill. It echoes every member's status.
- `guard` drops the explanation when an echoed status differs from the engine's, a member is
  missing or extra, the text names an unknown `member_N` or uses any other form of a member
  token ("member 2", "Member-2"), contains a denied word ("safe", "healthy" and their hi/mr
  forms; also "fine" and "okay" when any member is not `ok`), or contains a member name or
  the account email. It never edits the text: clients substitute the `member_N` tokens
  (via `member_refs`) and show the disclaimer.
- `explain` calls the provider within an 8 s budget and returns None on any failure. It never
  raises, and it never touches the `AnalysisResult`, which is frozen and only read here.
"""

from __future__ import annotations

import asyncio
import logging
import re
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime
from enum import Enum
from typing import Annotated, Any, Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field

from app import scoring
from app.core.config import Settings
from app.features.analyze.schemas import VerdictStatus
from app.features.members.models import Member
from app.integrations.providers import LLMProvider, ProviderUnavailable
from app.prompts import EXPLANATION_PROMPT_VERSION, load_prompt

logger = logging.getLogger(__name__)

EXPLANATION_BUDGET_S = 8.0  # total, retries included (P3 / P5-R21)
LANGUAGES = ("en", "hi", "mr")
Language = Literal["en", "hi", "mr"]
AgeBand = Literal["under_2", "2_12", "13_17", "18_59", "60_plus", "unknown"]

MAX_TEXT_CHARS = 900
MAX_TIPS = 3
MAX_TIP_CHARS = 140
MAX_MEMBERS = 10

# Params whose values can be user free text (P5-R18). Anything not canonical becomes "other".
_ALLERGEN_PARAM = "allergen"
_FREE_TEXT_PARAMS = frozenset({"condition"})
OTHER = "other"

# Anything that looks like a member token: "member_2", "Member 2", "member-2", "member2",
# "member_०२". Only the exact `member_N` form (no leading zero, ASCII digits) is accepted
# (Ruling P7), because clients substitute only that form. Not preceded by an ASCII letter, so
# "remember 2" is not a token.
_TOKEN_LIKE_RE = re.compile(r"(?<![a-z])member[\s_-]*(\d+)", re.IGNORECASE)
_EXACT_TOKEN_RE = re.compile(r"member_[1-9][0-9]*")

# Words the explanation must never use, for any status (Ruling P7). Latin words match as
# whole words; Devanagari words also match as a word prefix (case endings attach).
DENY_WORDS: tuple[str, ...] = (
    "safe",
    "safely",
    "healthy",
    "सुरक्षित",
    "सुरक्षित आहे",
    "सेहतमंद",
    "हेल्दी",
)
# Also denied when any member's status is not `ok`.
DENY_WORDS_NOT_ALL_OK: tuple[str, ...] = ("fine", "okay")
_IST = ZoneInfo("Asia/Kolkata")


# --- input (what the model sees) -----------------------------------------------------------


class ReasonIn(BaseModel):
    code: str
    severity: VerdictStatus
    params: dict[str, Any]


class MemberIn(BaseModel):
    ref: str
    relation: str
    age_band: AgeBand
    diet: str
    status: VerdictStatus
    reasons: list[ReasonIn]


class AllergenFactIn(BaseModel):
    allergen: str
    state: str


class ClaimIn(BaseModel):
    claim: str
    verdict: str
    reason_code: str
    params: dict[str, Any]


class ProductFactsIn(BaseModel):
    nutriscore_grade: str | None
    high_in: list[str]
    allergens: list[AllergenFactIn]
    ingredients_known: bool
    hidden_sugars: list[str]
    sodium_additives: list[str]
    veg_mark_mismatch: bool
    claims: list[ClaimIn]


class ExplanationIn(BaseModel):
    language: Language
    members: list[MemberIn]
    product: ProductFactsIn


# --- output (what the model must return) ---------------------------------------------------


class MemberStatusEcho(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ref: str
    status: VerdictStatus


class ExplanationLLM(BaseModel):
    """The strict schema for the model. `members` comes first so the model commits to the
    engine's statuses before it writes any prose."""

    model_config = ConfigDict(extra="forbid")

    members: list[MemberStatusEcho] = Field(max_length=MAX_MEMBERS)
    text: str = Field(max_length=MAX_TEXT_CHARS)
    tips: list[Annotated[str, Field(max_length=MAX_TIP_CHARS)]] = Field(max_length=MAX_TIPS)


class Explanation(BaseModel):
    """A guarded explanation. `text` and `tips` keep the `member_N` tokens; `member_refs`
    maps each token to the engine's member id so clients substitute the display name."""

    model_config = ConfigDict(frozen=True)

    text: str
    tips: list[str]
    language: Language
    prompt_version: str
    member_refs: dict[str, str]


# --- input builder -------------------------------------------------------------------------


def age_band(birth_year: int | None, today: date) -> AgeBand:
    """Band of the YOUNGEST age the birth year allows (same rule as to_scoring_member)."""
    if birth_year is None or birth_year > today.year:
        return "unknown"
    age = max(0, today.year - birth_year - 1)
    if age < 2:
        return "under_2"
    if age < 13:
        return "2_12"
    if age < 18:
        return "13_17"
    if age < 60:
        return "18_59"
    return "60_plus"


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_jsonable(v) for v in value]
    return value


def _canonical_allergens() -> frozenset[str]:
    return frozenset(k.lower() for k in scoring.load_config().allergens)


def _allergen(value: Any, canonical: frozenset[str]) -> str:
    return value if isinstance(value, str) and value in canonical else OTHER


def _clean_params(params: Mapping[str, Any], canonical: frozenset[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in params.items():
        if key == _ALLERGEN_PARAM:
            out[key] = _allergen(value, canonical)
        elif key in _FREE_TEXT_PARAMS:
            out[key] = OTHER
        else:
            out[key] = _jsonable(value)
    return out


def _product_facts(report: scoring.ProductReport, canonical: frozenset[str]) -> ProductFactsIn:
    allergens: dict[tuple[str, str], AllergenFactIn] = {}
    for key, state in report.allergens.items():
        fact = AllergenFactIn(allergen=_allergen(key, canonical), state=str(_jsonable(state)))
        allergens.setdefault((fact.allergen, fact.state), fact)
    return ProductFactsIn(
        nutriscore_grade=report.nutriscore.grade,
        high_in=list(report.high_in),
        allergens=list(allergens.values()),
        ingredients_known=report.ingredients_known,
        hidden_sugars=list(report.hidden_sugars),
        sodium_additives=list(report.sodium_additives),
        veg_mark_mismatch=report.veg_mark_mismatch,
        claims=[
            ClaimIn(
                claim=c.claim,
                verdict=str(_jsonable(c.verdict)),
                reason_code=c.reason_code,
                params=_clean_params(c.params, canonical),
            )
            for c in report.claims
        ],
    )


def today_ist() -> date:
    return datetime.now(_IST).date()


def build_explanation_input(
    result: scoring.AnalysisResult,
    members: Sequence[Member],
    language: str,
    *,
    today: date | None = None,
) -> ExplanationIn:
    """The anonymised model input. `members` must be in verdict order (ValueError if not)."""
    if len(members) != len(result.verdicts):
        raise ValueError("members do not match verdicts")
    today = today or today_ist()
    canonical = _canonical_allergens()
    items: list[MemberIn] = []
    for i, (member, verdict) in enumerate(zip(members, result.verdicts, strict=True), start=1):
        if verdict.member_id != str(member.id):
            raise ValueError("verdict order does not match member order")
        items.append(
            MemberIn(
                ref=f"member_{i}",
                relation=member.relation,
                age_band=age_band(member.birth_year, today),
                diet=member.diet,
                status=verdict.status.value,
                reasons=[
                    ReasonIn(
                        code=r.code,
                        severity=r.severity.value,
                        params=_clean_params(r.params, canonical),
                    )
                    for r in verdict.reasons
                ],
            )
        )
    return ExplanationIn(
        language=language,  # type: ignore[arg-type]  # validated by the model
        members=items,
        product=_product_facts(result.report, canonical),
    )


# --- guard ---------------------------------------------------------------------------------


def _normalise(text: str) -> str:
    """NFKC, drop invisible format characters (ZWJ, ZWNJ, soft hyphen...), casefold."""
    text = unicodedata.normalize("NFKC", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Cf")
    return text.casefold()


def _is_word_char(c: str) -> bool:
    return c == "_" or unicodedata.category(c)[0] in "LMN"


def _contains_word(text: str, needle: str) -> bool:
    """`needle` starts a word in `text`. Latin needles must also end a word ("Al" is not in
    "also"); other scripts match as a word prefix, because Marathi attaches case endings
    ("रियाला"). A false positive only costs the explanation."""
    prefix_ok = not needle.isascii() and len(needle) >= 3
    start = text.find(needle)
    while start != -1:
        end = start + len(needle)
        left = start == 0 or not _is_word_char(text[start - 1])
        right = prefix_ok or end == len(text) or not _is_word_char(text[end])
        if left and right:
            return True
        start = text.find(needle, start + 1)
    return False


def _name_needles(names: Iterable[str]) -> set[str]:
    needles: set[str] = set()
    for name in names:
        full = _normalise(name).strip()
        if len(full) >= 2:
            needles.add(full)
        # Split on spaces and punctuation only: Devanagari vowel signs are not `\w`.
        part = ""
        for c in f"{full} ":
            if _is_word_char(c):
                part += c
                continue
            if len(part) >= 2:
                needles.add(part)
            part = ""
    return needles


def _drop_reason(
    out: ExplanationLLM,
    result: scoring.AnalysisResult,
    member_names: Sequence[str],
    emails: Sequence[str],
) -> str | None:
    expected = {f"member_{i}": v.status.value for i, v in enumerate(result.verdicts, start=1)}
    echoed = {m.ref: m.status for m in out.members}
    if len(out.members) != len(expected) or echoed != expected:
        return "status_mismatch"
    if not out.text.strip():
        return "empty"
    combined = "\n".join([out.text, *out.tips])
    for m in _TOKEN_LIKE_RE.finditer(combined):
        token = m.group(0)
        if not _EXACT_TOKEN_RE.fullmatch(token):
            return "member_token_variant"
        if token not in expected:
            return "unknown_member_token"
    haystack = _normalise(combined)
    deny = DENY_WORDS
    if any(v.status is not scoring.Status.OK for v in result.verdicts):
        deny = (*deny, *DENY_WORDS_NOT_ALL_OK)
    if any(_contains_word(haystack, _normalise(w)) for w in deny):
        return "denied_word"
    if any(_contains_word(haystack, n) for n in _name_needles(member_names)):
        return "member_name"
    for email in emails:
        e = _normalise(email).strip()
        if e and e in haystack:
            return "email"
    return None


def guard(
    out: ExplanationLLM,
    result: scoring.AnalysisResult,
    member_names: Sequence[str],
    emails: Sequence[str],
    *,
    language: Language,
    prompt_version: str,
) -> Explanation | None:
    """The explanation, or None when it disagrees with the engine or leaks identity."""
    reason = _drop_reason(out, result, member_names, emails)
    if reason is not None:
        logger.info("explanation_dropped reason=%s prompt_version=%s", reason, prompt_version)
        return None
    return Explanation(
        text=out.text,
        tips=list(out.tips),
        language=language,
        prompt_version=prompt_version,
        member_refs={f"member_{i}": v.member_id for i, v in enumerate(result.verdicts, start=1)},
    )


# --- orchestrator --------------------------------------------------------------------------


async def explain(
    provider: LLMProvider,
    settings: Settings,
    result: scoring.AnalysisResult,
    members: Sequence[Member],
    language: str,
    *,
    emails: Sequence[str] = (),
    today: date | None = None,
) -> Explanation | None:
    """A guarded explanation, or None. Never raises (cancellation aside); never blocks the
    verdicts for more than EXPLANATION_BUDGET_S."""
    if language not in LANGUAGES:
        return None
    lang: Language = language  # type: ignore[assignment]
    budget = EXPLANATION_BUDGET_S
    try:
        data = build_explanation_input(result, members, lang, today=today)
        system, version = load_prompt(EXPLANATION_PROMPT_VERSION)
        async with asyncio.timeout(budget):
            out = await provider.chat_json(
                model=settings.callmissed_explanation_model,
                system=system,
                user=data.model_dump_json(),
                schema=ExplanationLLM,
                prompt_version=version,
                timeout_s=budget,
            )
        if not isinstance(out, ExplanationLLM):
            logger.warning("explanation_unavailable reason=wrong_type")
            return None
        return guard(
            out,
            result,
            [m.name for m in members],
            emails,
            language=lang,
            prompt_version=version,
        )
    except ProviderUnavailable as exc:
        logger.warning("explanation_unavailable reason=%s", exc.reason)
        return None
    except Exception as exc:  # noqa: BLE001 - degrade to None, never fail the analysis
        logger.warning("explanation_unavailable reason=%s", type(exc).__name__)
        return None
