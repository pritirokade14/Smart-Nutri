import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/health", tags=["health"])


@router.get("", operation_id="health_get")
async def health_get(session: Annotated[AsyncSession, Depends(get_session)]) -> JSONResponse:
    try:
        await session.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 - any failure means degraded; never leak details
        logger.warning("health check: database unreachable")
        return JSONResponse(status_code=503, content={"status": "degraded", "database": "error"})
    return JSONResponse({"status": "ok", "database": "ok"})
