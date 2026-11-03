"""POST /v1/analyze: per-member verdicts for one product, plus the AI explanation.

Verdicts come only from ``app.scoring.analyze``; this module resolves inputs, maps the
result to the response and records the scan. ``evaluate`` and ``to_analyze_out`` are pure
(no DB), so scripts/export_fixture_responses.py builds the shared golden responses with
exactly the code the endpoint runs.

The explanation (F7) runs only after the scan and verdicts are committed, only with an
active ``ai_processing`` consent, and only through ``explain`` (8 s budget, guarded). It
can never change a verdict and never fails the request: any problem gives an
"unavailable" explanation. Guarded explanations are cached in ``explanation_cache`` by
product, anonymised-input hash (prompt version and model included) and language; a hit is
guarded again with the caller's member names and email.
"""

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app import scoring
from app.core.config import Settings
from app.core.errors import ApiError
from app.features.analyze import explain
from app.features.analyze.schemas import (
    AnalyzeOut,
    AnalyzeRequest,
    ExplanationOut,
    Language,
    ReasonOut,
    VerdictOut,
)
from app.features.consents import service as consents_service
from app.features.members import service as members_service
from app.features.members.models import Member
from app.features.products import service as products_service
from app.features.products.service import ProductLookup
from app.features.ratelimit.models import ExplanationCache
from app.features.scans import service as scans_service
from app.integrations.openfoodfacts import InvalidBarcode, OffClient, OffUnavailable
from app.integrations.providers import LLMProvider
from app.prompts import EXPLANATION_PROMPT_VERSION, load_prompt

logger = logging.getLogger(__name__)


def evaluate(
    found: ProductLookup, members: Sequence[Member], *, today: date
) -> scoring.AnalysisResult:
    scoring_members = [members_service.to_scoring_member(m, today=today) for m in members]
    return scoring.analyze(found.product, scoring_members)


def scan_analysis(found: ProductLookup, result: scoring.AnalysisResult) -> dict[str, Any]:
    """What the scan row stores: engine output (member ids only, no names) plus the barcode."""
    return result.to_dict() | {"barcode": found.info.barcode or None}


def to_analyze_out(
    found: ProductLookup,
    members: Sequence[Member],
    result: scoring.AnalysisResult,
    *,
    scan_id: UUID,
    language: Language = "en",
) -> AnalyzeOut:
    data = result.to_dict()
    verdicts: list[VerdictOut] = []
    for member, verdict in zip(members, data["verdicts"], strict=True):
        if verdict["member_id"] != str(member.id):
            raise RuntimeError("verdict order does not match member order")
        verdicts.append(
            VerdictOut(
                member_id=member.id,
                member_name=member.name,
                relation=member.relation,
                is_primary=bool(member.is_primary),
                status=verdict["status"],
                reasons=[ReasonOut(**r) for r in verdict["reasons"]],
                profile_set_up=member.birth_year is not None,
            )
        )
    return AnalyzeOut(
        scan_id=scan_id,
        product=products_service.to_product_out(found),
        report=data["report"],
        verdicts=verdicts,
        explanation=unavailable_explanation(language),
    )


def unavailable_explanation(language: Language) -> ExplanationOut:
    return ExplanationOut(
        text=None,
        tips=[],
        language=language,
        source="unavailable",
        prompt_version=EXPLANATION_PROMPT_VERSION,
        member_refs={},
    )


def explanation_product_key(found: ProductLookup) -> UUID | None:
    """`explanation_cache.product_id`: our product id, or a stable id for an OFF barcode."""
    if found.product_id is not None:
        return found.product_id
    if found.info.barcode:
        return uuid5(NAMESPACE_URL, f"off:{found.info.barcode}")
    return None


@dataclass(frozen=True)
class _ExplanationJob:
    """Everything the explanation needs, taken before the commit (no ORM access after it)."""

    data: explain.ExplanationIn
    system: str
    prompt_version: str
    key: str
    product_key: UUID | None
    member_names: tuple[str, ...]
    emails: tuple[str, ...]
    language: Language


def _explanation_job(
    found: ProductLookup,
    members: Sequence[Member],
    result: scoring.AnalysisResult,
    *,
    language: Language,
    email: str | None,
    settings: Settings,
    today: date,
) -> _ExplanationJob | None:
    try:
        data = explain.build_explanation_input(result, members, language, today=today)
        system, version = load_prompt(EXPLANATION_PROMPT_VERSION)
    except Exception as exc:  # noqa: BLE001 - the explanation never fails the analysis
        logger.warning("explanation_unavailable reason=%s", type(exc).__name__)
        return None
    return _ExplanationJob(
        data=data,
        system=system,
        prompt_version=version,
        key=explain.cache_key(data, version, settings.callmissed_explanation_model, system),
        product_key=explanation_product_key(found),
        member_names=tuple(m.name for m in members),
        emails=(email,) if email else (),
        language=language,
    )


async def _load_cached(
    session: AsyncSession, job: _ExplanationJob
) -> explain.ExplanationLLM | None:
    if job.product_key is None:
        return None
    payload = await session.scalar(
        select(ExplanationCache.payload).where(
            ExplanationCache.product_id == job.product_key,
            ExplanationCache.profile_hash == job.key,
            ExplanationCache.language == job.language,
        )
    )
    if payload is None:
        return None
    try:
        return explain.ExplanationLLM.model_validate(payload)
    except ValidationError:
        logger.warning("explanation_cache_invalid prompt_version=%s", job.prompt_version)
        return None


async def _store_explanation(
    session: AsyncSession, job: _ExplanationJob, out: explain.ExplanationLLM
) -> None:
    """Cache a guarded model answer (anonymised: tokens and statuses only) in its own short
    transaction. A concurrent writer of the same key wins; both answers passed the guard."""
    if job.product_key is None:
        return
    await session.execute(
        insert(ExplanationCache)
        .values(
            product_id=job.product_key,
            profile_hash=job.key,
            language=job.language,
            payload=out.model_dump(mode="json"),
        )
        .on_conflict_do_nothing()
    )
    await session.commit()


async def _end_transaction(session: AsyncSession, *, ok: bool) -> None:
    try:
        if ok:
            await session.commit()
        else:
            await session.rollback()
    except Exception as exc:  # noqa: BLE001
        logger.warning("explanation_session_cleanup_failed reason=%s", type(exc).__name__)


def _to_out(guarded: explain.Explanation) -> ExplanationOut:
    return ExplanationOut(
        text=guarded.text,
        tips=list(guarded.tips),
        language=guarded.language,
        source="llm",
        prompt_version=guarded.prompt_version,
        member_refs={ref: UUID(mid) for ref, mid in guarded.member_refs.items()},
    )


async def _explanation(
    session: AsyncSession,
    llm: LLMProvider,
    settings: Settings,
    account_id: UUID,
    result: scoring.AnalysisResult,
    job: _ExplanationJob | None,
    language: Language,
) -> ExplanationOut:
    """Runs after the scan commit. Never raises; every failure is "unavailable"."""
    unavailable = unavailable_explanation(language)
    if job is None:
        return unavailable
    try:
        allowed = await consents_service.has_active_consent(session, account_id, "ai_processing")
        cached = await _load_cached(session, job) if allowed else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("explanation_unavailable reason=%s", type(exc).__name__)
        await _end_transaction(session, ok=False)
        return unavailable
    # End the read transaction: no DB connection is held across the LLM call (R16(3)).
    await _end_transaction(session, ok=True)
    if not allowed:
        return unavailable

    def _guard(out: explain.ExplanationLLM) -> explain.Explanation | None:
        return explain.guard(
            out,
            result,
            job.member_names,
            job.emails,
            language=job.language,
            prompt_version=job.prompt_version,
        )

    if cached is not None:
        guarded = _guard(cached)  # again: this account's names and email
        return unavailable if guarded is None else _to_out(guarded)

    raw = await explain.complete(llm, settings, job.data, job.system, job.prompt_version)
    guarded = None if raw is None else _guard(raw)
    if raw is None or guarded is None:
        return unavailable
    try:
        await _store_explanation(session, job, raw)
    except Exception as exc:  # noqa: BLE001 - a cache miss next time, nothing worse
        logger.warning("explanation_cache_write_failed reason=%s", type(exc).__name__)
        await _end_transaction(session, ok=False)
    return _to_out(guarded)


async def _resolve_product(
    session: AsyncSession,
    off: OffClient,
    request: AnalyzeRequest,
    settings: Settings,
    account_id: UUID,
) -> ProductLookup:
    # Another account's pending (unreviewed) product is never served (CROSS-PLAN 18).
    if request.product_id is not None:
        found = await products_service.lookup_by_id(
            session, request.product_id, account_id=account_id
        )
    else:
        try:
            found = await products_service.lookup_by_barcode(
                session, off, request.barcode or "", settings=settings, account_id=account_id
            )
        except InvalidBarcode as exc:
            raise ApiError("invalid_barcode", 422) from exc
        except OffUnavailable as exc:
            raise ApiError("off_unavailable", 503) from exc
        if found is None:
            await session.commit()  # persist a stale OFF cache delete
    if found is None:
        raise ApiError("product_not_found", 404)
    return found


async def analyze_for_account(
    session: AsyncSession,
    off: OffClient,
    account_id: UUID,
    request: AnalyzeRequest,
    *,
    settings: Settings,
    today: date,
    llm: LLMProvider,
    email: str | None,
) -> AnalyzeOut:
    """Resolve members and product, run the engine, record the scan and commit; then add the
    explanation (see the module docstring), which can only ever be "unavailable" on failure.

    Explicit members are checked before the product lookup, so a request with a foreign or
    unknown member never reaches Open Food Facts. With no ``member_ids`` every member of the
    account is analysed, the primary first (created on first use), so the list is never
    empty. The OFF cache write (barcode path), the primary member (first use) and the scan
    row are committed together at the end.
    """
    members: list[Member] | None = None
    if request.member_ids:
        members = await members_service.get_many(session, account_id, request.member_ids)
        if members is None:  # unknown and foreign ids look the same (no existence leak)
            raise ApiError("member_not_found", 404)
    found = await _resolve_product(session, off, request, settings, account_id)
    if members is None:
        await members_service.get_or_create_primary(session, account_id)
        members = await members_service.list_members(session, account_id)  # primary first

    result = evaluate(found, members, today=today)
    scan_id = uuid4()
    await scans_service.add_scan(
        session,
        scan_id=scan_id,
        account_id=account_id,
        product_id=found.product_id,
        analysis=scan_analysis(found, result),
    )
    out = to_analyze_out(found, members, result, scan_id=scan_id, language=request.language)
    job = _explanation_job(
        found,
        members,
        result,
        language=request.language,
        email=email,
        settings=settings,
        today=today,
    )
    await session.commit()  # the scan and verdicts are final before any LLM call
    explanation = await _explanation(
        session, llm, settings, account_id, result, job, request.language
    )
    return out.model_copy(update={"explanation": explanation})
