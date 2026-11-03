from dataclasses import dataclass
from uuid import UUID

import pytest

from app.core.security import AccountContext, current_account
from app.db.session import get_session
from app.features.analyze.explain import MemberStatusEcho
from app.features.consents.models import Consent
from app.features.consents.policy import CURRENT_VERSIONS
from app.features.me.service import ensure_account
from app.features.voice.answer import VoiceLLM
from app.integrations.callmissed import get_llm_provider, get_speech_provider
from app.integrations.openfoodfacts import get_off_client
from app.integrations.storage import get_voice_storage
from scripts.export_fixture_responses import fixture_member_record, fixture_product_record
from tests.api.analyze.conftest import OFF_PAYLOAD
from tests.api.products.test_lookup_service import FakeOff
from tests.fakes.llm import FakeLLM
from tests.fakes.speech import FakeSpeech
from tests.fakes.storage import FakeStorage

A = UUID("11111111-1111-1111-1111-111111111111")
B = UUID("22222222-2222-2222-2222-222222222222")
EMAIL = "asha@example.com"


@dataclass
class Fakes:
    speech: FakeSpeech
    llm: FakeLLM
    storage: FakeStorage
    off: FakeOff


def llm_answer(status: str = "avoid", answer: str = "It has a lot of sugar.") -> VoiceLLM:
    return VoiceLLM(members=[MemberStatusEcho(ref="member_1", status=status)], answer=answer)


@pytest.fixture(autouse=True)
def voice_on(app) -> None:
    """Voice is off by default (VOICE_ENABLED, Ruling V1 S3); these tests exercise it on."""
    app.state.settings.voice_enabled = True


@pytest.fixture
def fakes() -> Fakes:
    return Fakes(
        speech=FakeSpeech(),
        llm=FakeLLM(chat_result=llm_answer()),
        storage=FakeStorage(),
        off=FakeOff(OFF_PAYLOAD),
    )


@pytest.fixture
def grant(db_session):
    async def _grant(account_id: UUID, purposes=("terms", "health_data", "ai_processing")):
        await ensure_account(db_session, AccountContext(account_id, None))
        for purpose in purposes:
            db_session.add(
                Consent(account_id=account_id, purpose=purpose, version=CURRENT_VERSIONS[purpose])
            )
        await db_session.flush()

    return _grant


@pytest.fixture
def login(app, db_session, fakes):
    def _login(account_id: UUID = A) -> None:
        app.dependency_overrides[get_session] = lambda: db_session
        app.dependency_overrides[current_account] = lambda: AccountContext(account_id, EMAIL)
        app.dependency_overrides[get_llm_provider] = lambda: fakes.llm
        app.dependency_overrides[get_speech_provider] = lambda: fakes.speech
        app.dependency_overrides[get_voice_storage] = lambda: fakes.storage
        app.dependency_overrides[get_off_client] = lambda: fakes.off

    return _login


@pytest.fixture
async def auth_headers(login, grant):
    """ACC A logged in with every consent granted. Headers are unused (auth is overridden)."""
    await grant(A)
    login(A)
    return {}


async def _add(db_session, row):
    db_session.add(row)
    await db_session.flush()
    await db_session.refresh(row)
    return row


@pytest.fixture
async def seeded_member(db_session, grant) -> UUID:
    """The Plan 1 `diabetic_adult` saved under account A (name "Asha")."""
    await ensure_account(db_session, AccountContext(A, None))
    record = fixture_member_record("diabetic_adult", account_id=A)
    record.name = "Asha"
    return (await _add(db_session, record)).id


@pytest.fixture
async def seeded_biscuit(db_session) -> UUID:
    return (await _add(db_session, fixture_product_record("sf_biscuit"))).id


@pytest.fixture
async def other_accounts_member(db_session) -> UUID:
    await ensure_account(db_session, AccountContext(B, None))
    record = fixture_member_record("diabetic_adult", account_id=B)
    record.id = UUID("0b8f7a52-0000-4000-8000-0000000000b2")
    return (await _add(db_session, record)).id
