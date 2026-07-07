"""Add level test tracking

Revision ID: cd320fc85d53
Revises: 20260308_0003
Create Date: 2026-07-06 14:25:35.648316
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = 'cd320fc85d53'
down_revision: Union[str, None] = '20260308_0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('last_failed_test_date', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('last_failed_test_level', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'last_failed_test_level')
    op.drop_column('users', 'last_failed_test_date')
