"""add budget_parameters table

Revision ID: fc5ca68fdad2
Revises: d11dda6a7ae3
Create Date: 2026-02-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fc5ca68fdad2'
down_revision = 'd11dda6a7ae3'
branch_labels = None
depends_on = None

# Define the enum outside of create_table to control creation
parametervaluetype = postgresql.ENUM('tutar', 'miktar', 'sayi', 'yuzde', name='parametervaluetype', create_type=False)


def upgrade():
    # Create enum type if not exists
    parametervaluetype.create(op.get_bind(), checkfirst=True)

    op.create_table('budget_parameters',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False, comment='Parametre Kodu'),
        sa.Column('name', sa.String(length=200), nullable=False, comment='Parametre Adı'),
        sa.Column('description', sa.String(length=500), nullable=True, comment='Açıklama'),
        sa.Column('value_type', parametervaluetype, nullable=False, comment='Değer Tipi (tutar, miktar, sayi, yuzde)'),
        sa.Column('version_id', sa.Integer(), nullable=False, comment='Bağlı Versiyon'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_date', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_date', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['version_id'], ['budget_versions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        sa.UniqueConstraint('code'),
    )
    op.create_index('ix_budget_parameters_code', 'budget_parameters', ['code'])


def downgrade():
    op.drop_index('ix_budget_parameters_code', table_name='budget_parameters')
    op.drop_table('budget_parameters')
    parametervaluetype.drop(op.get_bind(), checkfirst=True)
