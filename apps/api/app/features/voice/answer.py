"""The spoken answer to a voice question (Plan 7 F10): the engine decides, the LLM explains.

The answer always starts with `verdict_sentence(status)`, built from the engine's status. The
LLM text after it is used only if it passes every check; otherwise the rule-based fallback
(`fallback.fallback_answer`) is spoken instead:

- the F7 guard from `analyze.explain` (status echo matches the engine; no denied words such
  as "safe"/"healthy" and, for a non-`ok` status, "fine"/"okay"; no member name or email);
- no `member_N`-like token at all (it would be read aloud);
- the verdict lock (`fallback.violates_verdict_lock`): no other status label, no "safe".

The member is anonymised exactly as for F7 (`build_explanation_input`: relation, age band,
diet, reason codes; no name, id or email). The transcribed question goes in only inside
`<user_question>`, with every account member's name replaced by "this member" (Ruling V1 S2),
truncated, and with angle brackets removed so it can't close the tag. Every
call goes through `LLMProvider.chat_json`, which always sends data residency "in".

Logs carry the prompt version, status and why an answer was dropped, never the question or
any answer text.
"""

from __future__ import annotations

import asyncio
import logging
import re
import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app import scoring
from app.core.config import Settings
from app.core.i18n import Catalog, catalog
from app.features.analyze.explain import (
    ExplanationLLM,
    MemberStatusEcho,
    _is_word_char,
    _name_needles,
    build_explanation_input,
    guard,
)
from app.features.members.models import Member
from app.features.voice.fallback import (
    fallback_answer,
    verdict_sentence,
    violates_verdict_lock,
)
from app.integrations.providers import LLMProvider, ProviderUnavailable
from app.prompts import VOICE_PROMPT_VERSION, load_prompt

logger = logging.getLogger(__name__)

VOICE_LLM_BUDGET_S = 8.0
MAX_QUESTION_CHARS = 500
MAX_ANSWER_CHARS = 600
LANGUAGE_NAMES = {"en": "English", "hi": "Hindi", "mr": "Marathi"}
_TOKEN_LIKE_RE = re.compile(r"(?<![a-z])member[\s_-]*\d", re.IGNORECASE)
NAME_REPLACEMENT = "this member"


class VoiceLLM(BaseModel):
    """Strict schema for the model. `members` first, so it commits to the engine's status."""

    model_config = ConfigDict(extra="forbid")

    members: list[MemberStatusEcho] = Field(max_length=1)
    answer: str = Field(max_length=MAX_ANSWER_CHARS)


@dataclass(frozen=True)
class VoiceText:
    text: str
    status: scoring.Status
    source: Literal["llm", "fallback"]
    prompt_version: str | None


def redact_names(text: str, names: Iterable[str]) -> str:
    """`text` with every member name (the full name and each part of two or more characters)
    replaced by "this member" (Ruling V1 S2).

    Matching is case-insensitive, after NFKC and with invisible format characters removed (as
    the guard does). Latin names match whole words only ("Asha" is not in "Ashanti"); other
    scripts also take the rest of the word, because Hindi and Marathi attach case endings
    ("आशाला"). Longer names are tried first.
    """
    text = unicodedata.normalize("NFKC", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Cf")
    needles = sorted(_name_needles(names), key=len, reverse=True)
    if not needles:
        return text
    # Fold per character so indexes still line up with `text`.
    folded = "".join(f if len(f := c.casefold()) == 1 else c for c in text)
    out: list[str] = []
    i = 0
    while i < len(text):
        end = None
        if i == 0 or not _is_word_char(text[i - 1]):
            for needle in needles:
                if not folded.startswith(needle, i):
                    continue
                stop = i + len(needle)
                if not needle.isascii():
                    while stop < len(text) and _is_word_char(text[stop]):
                        stop += 1
                elif stop < len(text) and _is_word_char(text[stop]):
                    continue
                end = stop
                break
        if end is None:
            out.append(text[i])
            i += 1
        else:
            out.append(NAME_REPLACEMENT)
            i = end
    return "".join(out)


def _clean_question(question: str, names: Iterable[str]) -> str:
    question = redact_names(question, names)
    return question.replace("<", " ").replace(">", " ")[:MAX_QUESTION_CHARS]


def build_user_message(
    result: scoring.AnalysisResult,
    member: Member,
    language: str,
    question: str,
    *,
    member_names: Sequence[str] = (),
    today: date | None = None,
) -> str:
    """The anonymised engine result, then the question inside `<user_question>`, with the
    member's name and every name in `member_names` replaced by "this member"."""
    data = build_explanation_input(result, [member], language, today=today)
    names = [member.name, *member_names]
    return (
        f"{data.model_dump_json()}\n\n"
        f"<user_question>{_clean_question(question, names)}</user_question>"
    )


def _drop_reason(
    out: VoiceLLM,
    result: scoring.AnalysisResult,
    member: Member,
    language: str,
    member_names: Sequence[str],
    emails: Sequence[str],
    cat: Catalog,
) -> str | None:
    text = out.answer.strip()
    if not text:
        return "empty"
    guarded = guard(
        ExplanationLLM(members=out.members, text=text, tips=[]),
        result,
        [member.name, *member_names],
        emails,
        language=language,  # type: ignore[arg-type]
        prompt_version=VOICE_PROMPT_VERSION,
    )
    if guarded is None:
        return "explanation_guard"
    if _TOKEN_LIKE_RE.search(text):
        return "member_token"
    if violates_verdict_lock(text, result.verdicts[0].status, language, cat):
        return "verdict_lock"
    return None


async def answer_question(
    provider: LLMProvider,
    settings: Settings,
    result: scoring.AnalysisResult,
    member: Member,
    language: str,
    question: str,
    *,
    member_names: Sequence[str] = (),
    emails: Sequence[str] = (),
    today: date | None = None,
    cat: Catalog | None = None,
) -> VoiceText:
    """The spoken answer for ONE member's verdict. Never changes the verdict.

    `member_names` are the names of every member of the account: each is replaced by "this
    member" in the question before it reaches the model, and an answer that says one is
    dropped (as is one that says `member.name`).

    Raises ProviderUnavailable (no credits, no key) so the route can answer 503 without a
    TTS call; any other failure or rejection gives the fallback answer.
    """
    if language not in LANGUAGE_NAMES:
        raise ValueError("language must be en, hi or mr")
    if len(result.verdicts) != 1:
        raise ValueError("a voice answer is about exactly one member")
    c = cat or catalog(settings.i18n_messages_dir)
    status = result.verdicts[0].status
    fallback = VoiceText(
        text=fallback_answer(result.verdicts[0], language, c),
        status=status,
        source="fallback",
        prompt_version=None,
    )
    try:
        system, version = load_prompt(VOICE_PROMPT_VERSION)
        system = f"{system}\nAnswer language: {LANGUAGE_NAMES[language]}.\n"
        user = build_user_message(
            result, member, language, question, member_names=member_names, today=today
        )
        async with asyncio.timeout(VOICE_LLM_BUDGET_S):
            out = await provider.chat_json(
                model=settings.callmissed_explanation_model,
                system=system,
                user=user,
                schema=VoiceLLM,
                prompt_version=version,
                timeout_s=VOICE_LLM_BUDGET_S,
            )
    except ProviderUnavailable:
        raise
    except Exception as exc:  # noqa: BLE001 - degrade to the fallback, never fail the answer
        logger.warning("voice_answer_fallback reason=%s", type(exc).__name__)
        return fallback
    if not isinstance(out, VoiceLLM):
        logger.warning("voice_answer_fallback reason=wrong_type")
        return fallback
    dropped = _drop_reason(out, result, member, language, member_names, emails, c)
    if dropped is not None:
        logger.info("voice_answer_dropped reason=%s prompt_version=%s", dropped, version)
        return fallback
    text = f"{verdict_sentence(status, language, c)} {out.answer.strip()}"
    return VoiceText(text=text, status=status, source="llm", prompt_version=version)
