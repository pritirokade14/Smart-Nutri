import asyncio
import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.features.health.schemas import HealthOut

logger = logging.getLogger(__name__)

DB_CHECK_TIMEOUT_S = 3.0

router = APIRouter(prefix="/v1/health", tags=["health"])


@router.get(
    "",
    operation_id="health_get",
    response_model=HealthOut,
    responses={200: {"model": HealthOut}, 503: {"model": HealthOut}},
)
async def health_get(session: Annotated[AsyncSession, Depends(get_session)]) -> JSONResponse:
    try:
        await asyncio.wait_for(session.execute(text("SELECT 1")), timeout=DB_CHECK_TIMEOUT_S)
    except Exception as exc:  # noqa: BLE001 - any failure means degraded; never leak details
        logger.warning("health check: database unreachable (%s)", type(exc).__name__)
        return JSONResponse(status_code=503, content={"status": "degraded", "database": "error"})
    return JSONResponse({"status": "ok", "database": "ok"})
