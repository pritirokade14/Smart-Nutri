from typing import Annotated

from fastapi import APIRouter, Depends

from app.features.me.dependencies import CurrentAccount, current_account_row
from app.features.me.schemas import MeOut

router = APIRouter(prefix="/v1/me", tags=["me"])


@router.get("", operation_id="me_get", response_model=MeOut)
async def me_get(current: Annotated[CurrentAccount, Depends(current_account_row)]) -> MeOut:
    account = current.account
    return MeOut(
        id=account.id,
        email=current.ctx.email,
        display_name=account.display_name,
        language=account.language,  # type: ignore[arg-type]
        created_at=account.created_at,
    )
