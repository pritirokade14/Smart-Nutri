from fastapi import APIRouter, Depends, Response

from app import scoring
from app.core.ratelimit import limit
from app.features.methodology.schemas import (
    Methodology,
    MethodologyLanguage,
    MethodologySection,
    MethodologySource,
)

router = APIRouter(prefix="/v1/methodology", tags=["methodology"])

CACHE_CONTROL = "public, max-age=3600, s-maxage=3600"


def build_methodology(language: MethodologyLanguage) -> Methodology:
    data = scoring.methodology()
    return Methodology(
        version=data["version"],
        language=language,
        pending_clinician_review=data["pending_clinician_review"],
        sections=[MethodologySection(**s) for s in data["sections"]],
        sources=[MethodologySource(id=sid, **src) for sid, src in data["sources"].items()],
    )


@router.get(
    "",
    operation_id="methodology_get",
    response_model=Methodology,
    dependencies=[Depends(limit("public"))],  # per client IP; no auth
)
async def methodology_get(
    response: Response, language: MethodologyLanguage = MethodologyLanguage.EN
) -> Methodology:
    """How SmartNutri scores products: every rule's live thresholds and their sources.

    Public (no token). The values come from the rules engine config, never written by hand;
    `pending_clinician_review` stays true until a clinician signs the thresholds off.
    Section titles and descriptions are client strings (`methodology.section.<id>.*`).
    """
    response.headers["Cache-Control"] = CACHE_CONTROL
    return build_methodology(language)
