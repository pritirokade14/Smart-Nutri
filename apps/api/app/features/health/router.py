import asyncio
import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from psycopg.errors import UndefinedTable
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schema import EXPECTED_ALEMBIC_HEAD
from app.db.session import get_session
from app.features.health.schemas import HealthOut

logger = logging.getLogger(__name__)

DB_CHECK_TIMEOUT_S = 3.0

router = APIRouter(prefix="/v1/health", tags=["health"])


def _out(status_code: int, status: str, database: str) -> JSONResponse:
    body = HealthOut(status=status, database=database)  # type: ignore[arg-type]
    return JSONResponse(status_code=status_code, content=body.model_dump())


@router.get(
    "",
    operation_id="health_get",
    response_model=HealthOut,
    responses={200: {"model": HealthOut}, 503: {"model": HealthOut}},
)
async def health_get(session: Annotated[AsyncSession, Depends(get_session)]) -> JSONResponse:
    try:
        result = await asyncio.wait_for(
            session.execute(text("SELECT version_num FROM alembic_version")),
            timeout=DB_CHECK_TIMEOUT_S,
        )
        versions = list(result.scalars().all())
    except ProgrammingError as exc:
        if isinstance(exc.orig, UndefinedTable):
            logger.error("health check: alembic_version is missing (schema never migrated)")
            return _out(503, "unavailable", "schema_behind")
        logger.warning("health check: database error (%s)", type(exc).__name__)
        return _out(503, "degraded", "error")
    except Exception as exc:  # noqa: BLE001 - any failure means degraded; never leak details
        logger.warning("health check: database unreachable (%s)", type(exc).__name__)
        return _out(503, "degraded", "error")
    if versions != [EXPECTED_ALEMBIC_HEAD]:
        # Revision ids are not secret; they help spot a deploy that ran before its migration.
        logger.error(
            "health check: schema at %s, this build expects %s", versions, EXPECTED_ALEMBIC_HEAD
        )
        return _out(503, "unavailable", "schema_behind")
    return _out(200, "ok", "ok")
