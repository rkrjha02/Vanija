"""add_users_refresh_tokens_and_customer_user_id

Revision ID: b5c921d0e6bb
Revises: aa1592dbe777
Create Date: 2026-10-28 17:42:31.496578

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5c921d0e6bb'
down_revision: Union[str, Sequence[str], None] = 'aa1592dbe777'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Create users table
    op.create_table('users',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('email', sa.Text(), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('auth_provider', sa.Text(), nullable=False),
        sa.Column('google_id', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('google_id'),
    )

    # 2. Create refresh_tokens table
    op.create_table('refresh_tokens',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('user_id', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # 3. Add user_id column to customers (nullable for now)
    op.add_column('customers', sa.Column('user_id', sa.Text(), nullable=True))
    op.create_unique_constraint('uq_customers_user_id', 'customers', ['user_id'])
    op.create_foreign_key('fk_customers_user_id', 'customers', 'users', ['user_id'], ['id'])

    # 4. Delete all existing data (children first to respect FKs)
    op.execute("DELETE FROM messages")
    op.execute("DELETE FROM pending_confirmations")
    op.execute("DELETE FROM order_items")
    op.execute("DELETE FROM orders")
    op.execute("DELETE FROM cart_items")
    op.execute("DELETE FROM carts")
    op.execute("DELETE FROM addresses")
    op.execute("DELETE FROM conversations")
    op.execute("DELETE FROM customers")

    # 5. Make user_id NOT NULL now that the table is empty
    op.alter_column('customers', 'user_id', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Make user_id nullable again
    op.alter_column('customers', 'user_id', nullable=True)

    # Drop user_id column and its constraints
    op.drop_constraint('fk_customers_user_id', 'customers', type_='foreignkey')
    op.drop_constraint('uq_customers_user_id', 'customers', type_='unique')
    op.drop_column('customers', 'user_id')

    # Drop new tables
    op.drop_table('refresh_tokens')
    op.drop_table('users')
