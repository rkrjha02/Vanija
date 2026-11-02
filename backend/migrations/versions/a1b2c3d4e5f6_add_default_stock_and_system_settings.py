"""add default_stock column and system_settings table

Revision ID: a1b2c3d4e5f6
Revises: d4a7b2c1e8f5
Create Date: 2026-11-02 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'd4a7b2c1e8f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add default_stock column with a temporary default so existing rows pass NOT NULL
    op.add_column('products', sa.Column('default_stock', sa.Integer(), nullable=False, server_default='0'))

    # Data migration: set default_stock = stock for all existing products
    op.execute('UPDATE products SET default_stock = stock')

    # Remove the server default now that existing rows are filled
    op.alter_column('products', 'default_stock', server_default=None)

    # Create system_settings table for tracking daily reset
    op.create_table(
        'system_settings',
        sa.Column('key', sa.Text(), primary_key=True),
        sa.Column('value', sa.Text(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('system_settings')
    op.drop_column('products', 'default_stock')
