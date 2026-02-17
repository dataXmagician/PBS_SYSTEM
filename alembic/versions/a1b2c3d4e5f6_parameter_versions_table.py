"""add parameter_versions table and remove version_id from budget_parameters

Revision ID: a1b2c3d4e5f6
Revises: fc5ca68fdad2
Create Date: 2026-02-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'fc5ca68fdad2'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create parameter_versions table
    op.create_table('parameter_versions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('parameter_id', sa.Integer(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('value', sa.String(length=500), nullable=True, comment='Bu versiyondaki parametre değeri'),
        sa.ForeignKeyConstraint(['parameter_id'], ['budget_parameters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['version_id'], ['budget_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('parameter_id', 'version_id', name='uq_parameter_version'),
    )

    # 2. Migrate existing data: copy version_id from budget_parameters to parameter_versions
    op.execute("""
        INSERT INTO parameter_versions (parameter_id, version_id)
        SELECT id, version_id FROM budget_parameters WHERE version_id IS NOT NULL
    """)

    # 3. Drop the version_id FK and column from budget_parameters
    op.drop_constraint('budget_parameters_version_id_fkey', 'budget_parameters', type_='foreignkey')
    op.drop_column('budget_parameters', 'version_id')


def downgrade():
    # 1. Re-add version_id column
    op.add_column('budget_parameters',
        sa.Column('version_id', sa.Integer(), nullable=True, comment='Bağlı Versiyon')
    )

    # 2. Migrate data back: take first version_id for each parameter
    op.execute("""
        UPDATE budget_parameters bp
        SET version_id = (
            SELECT pv.version_id FROM parameter_versions pv
            WHERE pv.parameter_id = bp.id
            LIMIT 1
        )
    """)

    # 3. Re-add FK constraint
    op.create_foreign_key('budget_parameters_version_id_fkey', 'budget_parameters', 'budget_versions', ['version_id'], ['id'])

    # 4. Drop parameter_versions table
    op.drop_table('parameter_versions')
