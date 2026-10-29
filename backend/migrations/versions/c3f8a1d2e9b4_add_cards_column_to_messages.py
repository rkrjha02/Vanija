"""add cards column to messages

Revision ID: c3f8a1d2e9b4
Revises: b5c921d0e6bb
Create Date: 2026-10-29 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c3f8a1d2e9b4'
down_revision: Union[str, Sequence[str], None] = 'b5c921d0e6bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('messages', sa.Column('cards', postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column('messages', 'cards')
