"""enable pgvector, add policy_documents and policy_chunks

Revision ID: a1c4e9f2b7d3
Revises: 7730550d363a
Create Date: 2026-10-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import pgvector.sqlalchemy
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c4e9f2b7d3'
down_revision: Union[str, Sequence[str], None] = '7730550d363a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table('policy_documents',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('title', sa.Text(), nullable=False),
    sa.Column('source_file', sa.Text(), nullable=False),
    sa.Column('content_hash', sa.Text(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('source_file')
    )
    op.create_table('policy_chunks',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('chunk_index', sa.Integer(), nullable=False),
    sa.Column('section', sa.Text(), nullable=False),
    sa.Column('chunk_text', sa.Text(), nullable=False),
    sa.Column('embedding', pgvector.sqlalchemy.Vector(dim=768), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['policy_documents.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('document_id', 'chunk_index', name='uq_policy_chunk_index')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('policy_chunks')
    op.drop_table('policy_documents')
    op.execute("DROP EXTENSION IF EXISTS vector")
