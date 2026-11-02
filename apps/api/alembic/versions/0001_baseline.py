"""Baseline schema: all v1 tables with row-level security on every table.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-11-03

Order:
1. Supabase compatibility shim (roles, ``auth`` schema, ``auth.uid()``). Guarded, so it is
   a no-op on Supabase, where these already exist. Never dropped on downgrade.
2. Tables, with check constraints for every enum.
3. Grants matching Supabase defaults for ``authenticated``/``service_role``; ``anon`` gets
   nothing. RLS (not grants) is what isolates accounts.
4. ENABLE + FORCE ROW LEVEL SECURITY on all ten tables.
5. Policies, all ``TO authenticated``. ``off_product_cache``, ``rate_limit_counters`` and
   ``explanation_cache`` get none, so they are server-only.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0001_baseline"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = (
    "accounts",
    "members",
    "consents",
    "products",
    "off_product_cache",
    "scans",
    "meal_logs",
    "product_reports",
    "rate_limit_counters",
    "explanation_cache",
)

SHIM = """
DO $shim$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        CREATE ROLE anon NOLOGIN NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        CREATE ROLE authenticated NOLOGIN NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
        CREATE ROLE service_role NOLOGIN NOINHERIT BYPASSRLS;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'auth') THEN
        CREATE SCHEMA auth;
        GRANT USAGE ON SCHEMA auth TO anon, authenticated, service_role;
    END IF;

    IF to_regprocedure('auth.uid()') IS NULL THEN
        -- Same semantics as Supabase's auth.uid(): legacy per-claim GUC first,
        -- then the JSON claims set by PostgREST / the API.
        EXECUTE $fn$
            CREATE FUNCTION auth.uid() RETURNS uuid
            LANGUAGE sql STABLE
            AS $body$
                SELECT coalesce(
                    nullif(current_setting('request.jwt.claim.sub', true), ''),
                    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub')
                )::uuid
            $body$
        $fn$;
    END IF;
END
$shim$;
"""

OWNER = "account_id = (SELECT auth.uid())"
MEAL_OWNER = (
    "account_id = (SELECT auth.uid()) AND EXISTS ("
    "SELECT 1 FROM members m "
    "WHERE m.id = meal_logs.member_id AND m.account_id = (SELECT auth.uid()))"
)

POLICIES = (
    (
        "CREATE POLICY accounts_select_own ON accounts FOR SELECT TO authenticated "
        "USING (id = (SELECT auth.uid()))"
    ),
    (
        "CREATE POLICY accounts_update_own ON accounts FOR UPDATE TO authenticated "
        "USING (id = (SELECT auth.uid())) WITH CHECK (id = (SELECT auth.uid()))"
    ),
    *(
        f"CREATE POLICY {t}_owner ON {t} FOR ALL TO authenticated "
        f"USING ({OWNER}) WITH CHECK ({OWNER})"
        for t in ("members", "consents", "scans", "product_reports")
    ),
    (
        "CREATE POLICY meal_logs_owner ON meal_logs FOR ALL TO authenticated "
        f"USING ({MEAL_OWNER}) WITH CHECK ({MEAL_OWNER})"
    ),
    "CREATE POLICY products_read ON products FOR SELECT TO authenticated USING (true)",
)


def _ts(name: str, *, nullable: bool = False, default: bool = True) -> sa.Column:
    return sa.Column(
        name,
        sa.DateTime(timezone=True),
        nullable=nullable,
        server_default=sa.text("now()") if default else None,
    )


def _uuid_pk() -> sa.Column:
    return sa.Column(
        "id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")
    )


def _text_array(name: str) -> sa.Column:
    return sa.Column(name, pg.ARRAY(sa.Text()), nullable=False, server_default="{}")


def upgrade() -> None:
    # 1. Supabase compatibility shim.
    op.execute(SHIM)

    # 2. Tables.
    op.create_table(
        "accounts",
        sa.Column("id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=True),
        sa.Column("language", sa.Text(), nullable=False, server_default="en"),
        _ts("created_at"),
        _ts("deleted_at", nullable=True, default=False),
        sa.PrimaryKeyConstraint("id", name="pk_accounts"),
        sa.CheckConstraint("language in ('en', 'hi', 'mr')", name="ck_accounts_language"),
    )

    op.create_table(
        "members",
        _uuid_pk(),
        sa.Column("account_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("relation", sa.Text(), nullable=False),
        sa.Column("birth_year", sa.Integer(), nullable=True),
        sa.Column("sex", sa.Text(), nullable=True),
        sa.Column("height_cm", sa.Numeric(), nullable=True),
        sa.Column("weight_kg", sa.Numeric(), nullable=True),
        sa.Column("diet", sa.Text(), nullable=False, server_default="non_veg"),
        _text_array("allergens"),
        _text_array("conditions"),
        _text_array("custom_alerts"),
        sa.Column("goal", sa.Text(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        _ts("created_at"),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("id", name="pk_members"),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_members_account_id_accounts",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "relation in ('self', 'child', 'parent', 'spouse', 'other')",
            name="ck_members_relation",
        ),
        sa.CheckConstraint(
            "diet in ('veg', 'eggetarian', 'vegan', 'jain', 'non_veg')", name="ck_members_diet"
        ),
        sa.CheckConstraint("sex in ('female', 'male', 'other')", name="ck_members_sex"),
    )
    op.create_index("ix_members_account_id", "members", ["account_id"])

    op.create_table(
        "consents",
        _uuid_pk(),
        sa.Column("account_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False),
        _ts("granted_at"),
        _ts("withdrawn_at", nullable=True, default=False),
        sa.PrimaryKeyConstraint("id", name="pk_consents"),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_consents_account_id_accounts",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "purpose in ('terms', 'health_data', 'ai_processing')", name="ck_consents_purpose"
        ),
    )
    op.create_index("ix_consents_account_id_purpose", "consents", ["account_id", "purpose"])

    op.create_table(
        "products",
        _uuid_pk(),
        sa.Column("barcode", sa.Text(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("brand", sa.Text(), nullable=True),
        sa.Column("category", sa.Text(), nullable=False, server_default="general"),
        sa.Column("per_100g", pg.JSONB(), nullable=False, server_default="{}"),
        sa.Column("serving_size_g", sa.Double(), nullable=True),
        sa.Column("ingredients_text", sa.Text(), nullable=True),
        sa.Column("allergen_statement", sa.Text(), nullable=True),
        sa.Column("may_contain_statement", sa.Text(), nullable=True),
        _text_array("claims"),
        sa.Column("veg_mark", sa.Text(), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("extraction_confidence", sa.Double(), nullable=True),
        sa.Column("verification_status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("created_by", pg.UUID(as_uuid=True), nullable=True),
        _ts("created_at"),
        sa.PrimaryKeyConstraint("id", name="pk_products"),
        sa.UniqueConstraint("barcode", name="uq_products_barcode"),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["accounts.id"],
            name="fk_products_created_by_accounts",
            ondelete="SET NULL",
        ),
        sa.CheckConstraint(
            "category in ('general', 'beverage', 'water', 'cheese', 'fat')",
            name="ck_products_category",
        ),
        sa.CheckConstraint("source in ('label', 'user')", name="ck_products_source"),
        sa.CheckConstraint(
            "verification_status in ('pending', 'verified', 'rejected')",
            name="ck_products_verification_status",
        ),
        sa.CheckConstraint("veg_mark in ('veg', 'non_veg')", name="ck_products_veg_mark"),
        sa.CheckConstraint(
            "extraction_confidence >= 0 and extraction_confidence <= 1",
            name="ck_products_extraction_confidence",
        ),
    )

    op.create_table(
        "off_product_cache",
        sa.Column("barcode", sa.Text(), nullable=False),
        sa.Column("payload", pg.JSONB(), nullable=False),
        _ts("fetched_at"),
        sa.PrimaryKeyConstraint("barcode", name="pk_off_product_cache"),
    )

    op.create_table(
        "scans",
        _uuid_pk(),
        sa.Column("account_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("image_path", sa.Text(), nullable=True),
        sa.Column("image_sha256", sa.Text(), nullable=True),
        sa.Column("analysis", pg.JSONB(), nullable=True),
        _ts("created_at"),
        sa.PrimaryKeyConstraint("id", name="pk_scans"),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_scans_account_id_accounts",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_scans_product_id_products",
            ondelete="SET NULL",
        ),
    )
    op.create_index("ix_scans_account_id", "scans", ["account_id"])
    op.create_index("ix_scans_image_sha256", "scans", ["image_sha256"])

    op.create_table(
        "meal_logs",
        _uuid_pk(),
        sa.Column("account_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("member_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("grams", sa.Numeric(), nullable=False),
        _ts("eaten_at"),
        sa.Column("nutrients", pg.JSONB(), nullable=False),
        sa.Column("client_id", pg.UUID(as_uuid=True), nullable=True),
        _ts("created_at"),
        sa.PrimaryKeyConstraint("id", name="pk_meal_logs"),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_meal_logs_account_id_accounts",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["member_id"],
            ["members.id"],
            name="fk_meal_logs_member_id_members",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.id"], name="fk_meal_logs_product_id_products"
        ),
        sa.UniqueConstraint("account_id", "client_id", name="uq_meal_logs_account_id_client_id"),
        sa.CheckConstraint("grams > 0 and grams <= 5000", name="ck_meal_logs_grams"),
    )
    op.create_index(
        "ix_meal_logs_member_id_eaten_at", "meal_logs", ["member_id", sa.text("eaten_at DESC")]
    )

    op.create_table(
        "product_reports",
        _uuid_pk(),
        sa.Column("product_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="open"),
        _ts("created_at"),
        sa.PrimaryKeyConstraint("id", name="pk_product_reports"),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name="fk_product_reports_product_id_products",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_product_reports_account_id_accounts",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "reason in ('wrong_values', 'wrong_ingredients', 'wrong_product', 'other')",
            name="ck_product_reports_reason",
        ),
        sa.CheckConstraint("status in ('open', 'resolved')", name="ck_product_reports_status"),
    )
    op.create_index("ix_product_reports_product_id", "product_reports", ["product_id"])
    op.create_index("ix_product_reports_account_id", "product_reports", ["account_id"])

    op.create_table(
        "rate_limit_counters",
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("bucket", sa.Text(), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("key", "bucket", "window_start", name="pk_rate_limit_counters"),
    )

    op.create_table(
        "explanation_cache",
        sa.Column("product_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_hash", sa.Text(), nullable=False),
        sa.Column("language", sa.Text(), nullable=False),
        sa.Column("payload", pg.JSONB(), nullable=False),
        _ts("created_at"),
        sa.PrimaryKeyConstraint(
            "product_id", "profile_hash", "language", name="pk_explanation_cache"
        ),
        sa.CheckConstraint("language in ('en', 'hi', 'mr')", name="ck_explanation_cache_language"),
    )

    # 3. Grants: match Supabase's defaults for authenticated/service_role so that RLS is
    #    the only thing isolating accounts; anon (unauthenticated PostgREST) gets nothing.
    tables = ", ".join(TABLES)
    op.execute(f"REVOKE ALL ON {tables} FROM anon")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {tables} TO authenticated")
    op.execute(f"GRANT ALL ON {tables} TO service_role")

    # 4. Row-level security on every table, forced for the table owner too.
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")

    # 5. Policies.
    for policy in POLICIES:
        op.execute(policy)


def downgrade() -> None:
    # Dropping a table drops its policies and grants. The shim is left in place.
    for table in reversed(TABLES):
        op.drop_table(table)
