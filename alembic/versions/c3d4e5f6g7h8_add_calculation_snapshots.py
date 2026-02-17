"""add calculation_snapshots table

Revision ID: c3d4e5f6g7h8
Revises: b1c2d3e4f5g6
Create Date: 2026-02-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, None] = 'b1c2d3e4f5g6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'calculation_snapshots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('budget_definition_id', sa.Integer(), nullable=False),
        sa.Column('snapshot_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, comment='Pre-calculation cell values'),
        sa.Column('rule_set_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Applied rule set IDs'),
        sa.Column('created_date', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['budget_definition_id'], ['budget_definitions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_calculation_snapshots_budget_definition_id', 'calculation_snapshots', ['budget_definition_id'])


def downgrade() -> None:
    op.drop_index('ix_calculation_snapshots_budget_definition_id', table_name='calculation_snapshots')
    op.drop_table('calculation_snapshots')
