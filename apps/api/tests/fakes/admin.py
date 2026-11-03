"""FakeAdmin: a SupabaseAdmin for tests. Never calls Supabase."""

from __future__ import annotations

from uuid import UUID

from app.integrations.supabase_admin import AdminUnavailable


class FakeAdmin:
    """Deletes auth users; fails the next `failures` calls (or every call for ids in
    `failing`) with AdminUnavailable."""

    def __init__(self, failures: int = 0, failing: set[UUID] | None = None) -> None:
        self.failures = failures
        self.failing = set(failing or ())
        self.calls: list[UUID] = []
        self.deleted: list[UUID] = []
        self.gone: set[UUID] = set()

    async def delete_user(self, user_id: UUID) -> None:
        self.calls.append(user_id)
        if self.failures or user_id in self.failing:
            self.failures = max(0, self.failures - 1)
            raise AdminUnavailable("fake outage")
        self.deleted.append(user_id)
        self.gone.add(user_id)
