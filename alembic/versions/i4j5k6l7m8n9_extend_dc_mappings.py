"""extend data_connection_mappings with target_definition_id and target_version_id

Revision ID: i4j5k6l7m8n9
Revises: h3i4j5k6l7m8
Create Date: 2026-02-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'i4j5k6l7m8n9'
down_revision: Union[str, None] = 'h3i4j5k6l7m8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('data_connection_mappings', sa.Column('target_definition_id', sa.Integer(), nullable=True))
    op.add_column('data_connection_mappings', sa.Column('target_version_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('data_connection_mappings', 'target_version_id')
    op.drop_column('data_connection_mappings', 'target_definition_id')
