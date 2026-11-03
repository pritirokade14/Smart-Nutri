"""POST /v1/analyze: per-member verdicts for one product.

Verdicts come only from ``app.scoring.analyze``; this module resolves inputs, maps the
result to the response and records the scan. ``evaluate`` and ``to_analyze_out`` are pure
(no DB), so scripts/export_fixture_responses.py builds the shared golden responses with
exactly the code the endpoint runs.
"""

from collections.abc import Sequence
from datetime import date
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app import scoring
from app.core.config import Settings
from app.core.errors import ApiError
from app.features.analyze.schemas import AnalyzeOut, AnalyzeRequest, ReasonOut, VerdictOut
from app.features.members import service as members_service
from app.features.members.models import Member
from app.features.products import service as products_service
from app.features.products.service import ProductLookup
from app.features.scans import service as scans_service
from app.integrations.openfoodfacts import InvalidBarcode, OffClient, OffUnavailable


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
    )


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
) -> AnalyzeOut:
    """Resolve members and product, run the engine, record the scan, commit once.

    Explicit members are checked before the product lookup, so a request with a foreign or
    unknown member never reaches Open Food Facts. The OFF cache write (barcode path), the
    primary member (first use) and the scan row are committed together at the end.
    """
    members: list[Member] | None = None
    if request.member_ids:
        members = await members_service.get_many(session, account_id, request.member_ids)
        if members is None:  # unknown and foreign ids look the same (no existence leak)
            raise ApiError("member_not_found", 404)
    found = await _resolve_product(session, off, request, settings, account_id)
    if members is None:
        members = [await members_service.get_or_create_primary(session, account_id)]

    result = evaluate(found, members, today=today)
    scan_id = uuid4()
    await scans_service.add_scan(
        session,
        scan_id=scan_id,
        account_id=account_id,
        product_id=found.product_id,
        analysis=scan_analysis(found, result),
    )
    out = to_analyze_out(found, members, result, scan_id=scan_id)
    await session.commit()
    return out
