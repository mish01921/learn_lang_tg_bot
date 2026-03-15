"""initial schema for words bot

Revision ID: 20260308_0001
Revises:
Create Date: 2026-03-08 10:30:00
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20260308_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", sa.BigInteger(), primary_key=True),
        sa.Column("username", sa.Text(), nullable=True),
        sa.Column("joined_at", sa.Text(), nullable=True),
        sa.Column("streak", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_active", sa.Text(), nullable=True),
        sa.Column("daily_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("daily_date", sa.Text(), nullable=True),
        sa.Column("user_level", sa.Text(), nullable=True),
        sa.Column("banned", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("ban_reason", sa.Text(), nullable=True),
        sa.Column("placement_done", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("placement_score", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("placement_taken_at", sa.Text(), nullable=True),
    )

    op.create_table(
        "word_progress",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("word", sa.Text(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("seen", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("correct", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("correct_streak", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("wrong", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("learned", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("marked_hard", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("marked_know", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("added_at", sa.Text(), nullable=True),
        sa.Column("learned_at", sa.Text(), nullable=True),
        sa.Column("next_review", sa.Text(), nullable=True),
        sa.Column("ease_factor", sa.Float(), nullable=False, server_default=sa.text("2.5")),
        sa.Column("interval_days", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("repetitions", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_reviewed_at", sa.Text(), nullable=True),
        sa.Column("last_grade", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "word", name="uq_word_progress_user_word"),
    )

    op.create_table(
        "sessions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("word", sa.Text(), nullable=False),
        sa.Column("answered_at", sa.Text(), nullable=False),
        sa.Column("correct", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
    )

    op.create_table(
        "story_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("story_date", sa.Text(), nullable=False),
        sa.Column("genre", sa.Text(), nullable=False),
        sa.Column("words_json", sa.Text(), nullable=False),
        sa.Column("story_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
    )

    op.create_table(
        "memory_palace_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("palace_date", sa.Text(), nullable=False),
        sa.Column("theme", sa.Text(), nullable=False),
        sa.Column("words_json", sa.Text(), nullable=False),
        sa.Column("palace_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
    )

    op.create_index("idx_progress_user", "word_progress", ["user_id"])
    op.create_index("idx_progress_review", "word_progress", ["user_id", "next_review"])
    op.create_index("idx_sessions_user", "sessions", ["user_id"])
    op.create_index("idx_story_user_date", "story_history", ["user_id", "story_date"])
    op.create_index("idx_palace_user_date", "memory_palace_history", ["user_id", "palace_date"])


def downgrade() -> None:
    op.drop_index("idx_palace_user_date", table_name="memory_palace_history")
    op.drop_index("idx_story_user_date", table_name="story_history")
    op.drop_index("idx_sessions_user", table_name="sessions")
    op.drop_index("idx_progress_review", table_name="word_progress")
    op.drop_index("idx_progress_user", table_name="word_progress")

    op.drop_table("memory_palace_history")
    op.drop_table("story_history")
    op.drop_table("sessions")
    op.drop_table("word_progress")
    op.drop_table("users")
