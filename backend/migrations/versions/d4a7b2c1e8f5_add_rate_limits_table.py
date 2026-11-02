"""add rate_limits table

Revision ID: d4a7b2c1e8f5
Revises: 2f18f98c4a20
Create Date: 2026-10-31 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd4a7b2c1e8f5'
down_revision: Union[str, Sequence[str], None] = '2f18f98c4a20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'rate_limits',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('customer_id', sa.Text(), sa.ForeignKey('customers.id'), nullable=True),
        sa.Column('counter_type', sa.Text(), nullable=False),
        sa.Column('window_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "counter_type IN ('customer_hourly', 'global_daily')",
            name='ck_rate_limit_counter_type',
        ),
    )
    op.create_index(
        'ix_rate_limits_lookup',
        'rate_limits',
        ['counter_type', 'customer_id', 'window_start'],
    )


def downgrade() -> None:
    op.drop_index('ix_rate_limits_lookup', table_name='rate_limits')
    op.drop_table('rate_limits')
