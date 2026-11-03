from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ERROR_RESPONSES, ErrorEnvelope
from app.db.session import get_session
from app.features.me.dependencies import CurrentAccount, current_account_row
from app.features.members import service
from app.features.members.models import Member
from app.features.members.schemas import MemberIn, MemberOut, MemberPatch

router = APIRouter(prefix="/v1/members", tags=["members"])

_WRITE_RESPONSES = {
    **ERROR_RESPONSES,
    403: {
        "model": ErrorEnvelope,
        "description": "Consent required: saving health fields needs the health_data consent",
    },
}

Current = Annotated[CurrentAccount, Depends(current_account_row)]
Session = Annotated[AsyncSession, Depends(get_session)]


def _out(member: Member) -> MemberOut:
    return MemberOut.model_validate(member, from_attributes=True)


@router.get("", operation_id="members_list", response_model=list[MemberOut])
async def members_list(current: Current, session: Session) -> list[MemberOut]:
    """The account's members, the primary (account holder) first. Creates the primary if new."""
    await service.get_or_create_primary(session, current.account.id)
    members = await service.list_members(session, current.account.id)
    await session.commit()
    return [_out(m) for m in members]


@router.post(
    "",
    operation_id="members_create",
    response_model=MemberOut,
    status_code=201,
    responses=_WRITE_RESPONSES,
)
async def members_create(body: MemberIn, current: Current, session: Session) -> MemberOut:
    member = await service.create_member(session, current.account.id, body)
    out = _out(member)
    await session.commit()
    return out


@router.get("/{member_id}", operation_id="members_get", response_model=MemberOut)
async def members_get(member_id: UUID, current: Current, session: Session) -> MemberOut:
    return _out(await service.get_member(session, current.account.id, member_id))


@router.patch(
    "/{member_id}",
    operation_id="members_update",
    response_model=MemberOut,
    responses=_WRITE_RESPONSES,
)
async def members_update(
    member_id: UUID, body: MemberPatch, current: Current, session: Session
) -> MemberOut:
    member = await service.update_member(session, current.account.id, member_id, body)
    out = _out(member)
    await session.commit()
    return out


@router.delete("/{member_id}", operation_id="members_delete", status_code=204)
async def members_delete(member_id: UUID, current: Current, session: Session) -> Response:
    await service.delete_member(session, current.account.id, member_id)
    await session.commit()
    return Response(status_code=204)
