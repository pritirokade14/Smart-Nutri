"""SupabaseAuthAdmin over httpx.MockTransport: never calls real Supabase."""

import logging
from uuid import UUID

import httpx
import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.integrations.supabase_admin import (
    AdminUnavailable,
    SupabaseAuthAdmin,
    get_supabase_admin,
)

URL = "https://proj.supabase.co"
KEY = "sb_secret_test_value"
USER = UUID("11111111-1111-1111-1111-111111111111")


def make(handler) -> tuple[SupabaseAuthAdmin, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def _h(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    http = httpx.AsyncClient(transport=httpx.MockTransport(_h))
    return SupabaseAuthAdmin(http, url=URL + "/", secret_key=SecretStr(KEY)), seen


async def test_delete_user_calls_the_admin_api():
    admin, seen = make(lambda r: httpx.Response(200, json={}))
    await admin.delete_user(USER)
    [req] = seen
    assert req.method == "DELETE"
    assert str(req.url) == f"{URL}/auth/v1/admin/users/{USER}"
    assert req.headers["authorization"] == f"Bearer {KEY}"
    assert req.headers["apikey"] == KEY


async def test_404_counts_as_already_deleted():
    admin, _ = make(lambda r: httpx.Response(404, json={"msg": "User not found"}))
    await admin.delete_user(USER)


@pytest.mark.parametrize("status", [400, 401, 500, 503])
async def test_other_errors_raise_without_leaking(status, caplog):
    admin, _ = make(lambda r: httpx.Response(status, text=f"secret body {KEY}"))
    with caplog.at_level(logging.DEBUG), pytest.raises(AdminUnavailable) as exc:
        await admin.delete_user(USER)
    assert KEY not in str(exc.value) and KEY not in caplog.text
    assert "secret body" not in caplog.text


async def test_network_error_raises():
    def boom(request):
        raise httpx.ConnectError("down")

    admin, _ = make(boom)
    with pytest.raises(AdminUnavailable):
        await admin.delete_user(USER)


def test_repr_hides_the_key():
    admin, _ = make(lambda r: httpx.Response(200))
    assert KEY not in repr(admin)


async def test_dependency_without_config_refuses():
    gen = get_supabase_admin(Settings(_env_file=None, environment="test"))
    admin = await gen.__anext__()
    with pytest.raises(AdminUnavailable):
        await admin.delete_user(USER)
    await gen.aclose()
