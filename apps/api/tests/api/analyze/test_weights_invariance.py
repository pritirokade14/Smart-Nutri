"""Weights never touch verdicts (Plan 12 Task 23): `analyze` is byte-identical with and
without a weight log."""

from decimal import Decimal

from app.core import time as core_time
from app.features.members import service as members_service
from app.features.weights import store
from tests.api.analyze.conftest import A


async def test_verdict_invariance_with_weights(auth_client, own_member, cola_product, db_session):
    body = {"product_id": str(cola_product.id), "language": "en"}
    before = await auth_client.post("/v1/analyze", json=body)
    assert before.status_code == 200, before.text
    primary = await members_service.get_or_create_primary(db_session, A)
    for i in range(5):
        day = core_time.local_today("Asia/Kolkata").replace(day=1 + i)
        await store.upsert_weigh_in(
            db_session, own_member, day, Decimal(60 + i), core_time.now_utc()
        )
        await store.upsert_weigh_in(db_session, primary, day, Decimal(90 - i), core_time.now_utc())
    own_member.weight_kg = 200
    primary.weight_kg = 35
    await db_session.flush()
    after = await auth_client.post("/v1/analyze", json=body)
    assert after.status_code == 200

    def verdicts(r) -> bytes:
        v = r.json()["verdicts"]
        return repr(sorted((x["member_id"], x["status"], str(x["reasons"])) for x in v)).encode()

    assert verdicts(before) == verdicts(after)
