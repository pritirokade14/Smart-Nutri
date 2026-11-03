from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.features.consents import service
from app.features.consents.schemas import ConsentIn, ConsentState
from app.features.me.dependencies import CurrentAccount, current_account_row

router = APIRouter(prefix="/v1/consents", tags=["consents"])


@router.post("", operation_id="consents_record", response_model=list[ConsentState])
async def consents_record(
    body: ConsentIn,
    current: Annotated[CurrentAccount, Depends(current_account_row)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ConsentState]:
    states = await service.record_consent(session, current.account.id, body)
    await session.commit()
    return states


@router.get("", operation_id="consents_list", response_model=list[ConsentState])
async def consents_list(
    current: Annotated[CurrentAccount, Depends(current_account_row)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ConsentState]:
    return await service.consent_states(session, current.account.id)
