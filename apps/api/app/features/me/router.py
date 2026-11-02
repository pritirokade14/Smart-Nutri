from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import AccountContext, current_account
from app.db.session import get_session
from app.features.me import service
from app.features.me.schemas import MeOut

router = APIRouter(prefix="/v1/me", tags=["me"])


@router.get("", operation_id="me_get", response_model=MeOut)
async def me_get(
    ctx: Annotated[AccountContext, Depends(current_account)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MeOut:
    account = await service.ensure_account(session, ctx)
    return MeOut(
        id=account.id,
        email=ctx.email,
        display_name=account.display_name,
        language=account.language,  # type: ignore[arg-type]
        created_at=account.created_at,
    )
