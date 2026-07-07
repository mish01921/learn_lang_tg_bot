"""add word_audio_cache table

Revision ID: 20260308_0003
Revises: 20260308_0002
Create Date: 2026-03-08 14:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20260308_0003"
down_revision: Union[str, None] = "20260308_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "word_audio_cache",
        sa.Column("word", sa.Text(), primary_key=True),
        sa.Column("file_id", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("word_audio_cache")
