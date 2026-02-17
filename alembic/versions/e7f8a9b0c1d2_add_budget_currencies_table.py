"""add budget_currencies table

Revision ID: e7f8a9b0c1d2
Revises: c3d4e5f6g7h8
Create Date: 2026-02-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e7f8a9b0c1d2'
down_revision = 'c3d4e5f6g7h8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'budget_currencies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False, comment='Para Birimi Kodu'),
        sa.Column('name', sa.String(length=200), nullable=False, comment='Para Birimi Adi'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_date', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_date', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        sa.UniqueConstraint('code'),
    )
    op.create_index('ix_budget_currencies_code', 'budget_currencies', ['code'])


def downgrade():
    op.drop_index('ix_budget_currencies_code', table_name='budget_currencies')
    op.drop_table('budget_currencies')
