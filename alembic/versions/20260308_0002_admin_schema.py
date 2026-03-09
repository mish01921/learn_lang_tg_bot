"""admin schema and audit tables

Revision ID: 20260308_0002
Revises: 20260308_0001
Create Date: 2026-03-08 12:15:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from alembic.runtime.migration import MigrationContext


revision: str = "20260308_0002"
down_revision: Union[str, None] = "20260308_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    ctx = MigrationContext.configure(bind)
    dialect = ctx.dialect.name

    if dialect == "postgresql":
        op.execute("CREATE SCHEMA IF NOT EXISTS admin")
        op.create_table(
            "audit_log",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column("actor_user_id", sa.BigInteger(), nullable=False),
            sa.Column("target_user_id", sa.BigInteger(), nullable=True),
            sa.Column("action", sa.Text(), nullable=False),
            sa.Column("details", sa.Text(), nullable=True),
            sa.Column("metadata_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.Text(), nullable=False),
            schema="admin",
        )
        op.create_index("idx_admin_audit_created", "audit_log", ["created_at"], schema="admin")
    else:
        op.create_table(
            "admin_audit_log",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column("actor_user_id", sa.BigInteger(), nullable=False),
            sa.Column("target_user_id", sa.BigInteger(), nullable=True),
            sa.Column("action", sa.Text(), nullable=False),
            sa.Column("details", sa.Text(), nullable=True),
            sa.Column("metadata_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.Text(), nullable=False),
        )
        op.create_index("idx_admin_audit_created", "admin_audit_log", ["created_at"])

    if dialect == "postgresql":
        op.create_table(
            "settings",
            sa.Column("key", sa.Text(), primary_key=True),
            sa.Column("value", sa.Text(), nullable=False),
            sa.Column("updated_at", sa.Text(), nullable=False),
            schema="admin",
        )
    else:
        op.create_table(
            "admin_settings",
            sa.Column("key", sa.Text(), primary_key=True),
            sa.Column("value", sa.Text(), nullable=False),
            sa.Column("updated_at", sa.Text(), nullable=False),
        )


def downgrade() -> None:
    bind = op.get_bind()
    ctx = MigrationContext.configure(bind)
    dialect = ctx.dialect.name

    if dialect == "postgresql":
        op.drop_table("settings", schema="admin")
        op.drop_index("idx_admin_audit_created", table_name="audit_log", schema="admin")
        op.drop_table("audit_log", schema="admin")
    else:
        op.drop_table("admin_settings")
        op.drop_index("idx_admin_audit_created", table_name="admin_audit_log")
        op.drop_table("admin_audit_log")
