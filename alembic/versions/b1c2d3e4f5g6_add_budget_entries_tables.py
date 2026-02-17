"""add budget entries tables

Revision ID: b1c2d3e4f5g6
Revises: a1b2c3d4e5f6
Create Date: 2026-02-07 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5g6'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create PostgreSQL enums via raw SQL with IF NOT EXISTS
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'budgetmeasuretype') THEN CREATE TYPE budgetmeasuretype AS ENUM ('input', 'calculated'); END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'measuredatatype') THEN CREATE TYPE measuredatatype AS ENUM ('decimal', 'integer', 'currency', 'percentage'); END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'budgetdefinitionstatus') THEN CREATE TYPE budgetdefinitionstatus AS ENUM ('draft', 'active', 'locked', 'archived'); END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'budgetcelltype') THEN CREATE TYPE budgetcelltype AS ENUM ('input', 'calculated', 'parameter_calculated'); END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ruletype') THEN CREATE TYPE ruletype AS ENUM ('fixed_value', 'parameter_multiplier', 'formula'); END IF; END $$;")

    # 1. budget_types
    op.create_table('budget_types',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        sa.UniqueConstraint('code'),
    )
    op.create_index('ix_budget_types_code', 'budget_types', ['code'])

    # 2. budget_type_measures
    op.create_table('budget_type_measures',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('budget_type_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('measure_type', postgresql.ENUM('input', 'calculated', name='budgetmeasuretype', create_type=False), nullable=False),
        sa.Column('data_type', postgresql.ENUM('decimal', 'integer', 'currency', 'percentage', name='measuredatatype', create_type=False), nullable=False),
        sa.Column('formula', sa.String(length=500), nullable=True),
        sa.Column('decimal_places', sa.Integer(), server_default='2'),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('default_value', sa.String(length=50), server_default='0'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['budget_type_id'], ['budget_types.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('budget_type_id', 'code', name='uq_budget_type_measure'),
    )

    # 3. rule_sets
    op.create_table('rule_sets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('budget_type_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['budget_type_id'], ['budget_types.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        sa.UniqueConstraint('code'),
    )
    op.create_index('ix_rule_sets_code', 'rule_sets', ['code'])

    # 4. budget_definitions
    op.create_table('budget_definitions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('budget_type_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('status', postgresql.ENUM('draft', 'active', 'locked', 'archived', name='budgetdefinitionstatus', create_type=False), nullable=False, server_default='draft'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['version_id'], ['budget_versions.id']),
        sa.ForeignKeyConstraint(['budget_type_id'], ['budget_types.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        sa.UniqueConstraint('code'),
    )
    op.create_index('ix_budget_definitions_code', 'budget_definitions', ['code'])

    # 5. rule_set_items
    op.create_table('rule_set_items',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('rule_set_id', sa.Integer(), nullable=False),
        sa.Column('rule_type', postgresql.ENUM('fixed_value', 'parameter_multiplier', 'formula', name='ruletype', create_type=False), nullable=False),
        sa.Column('target_measure_code', sa.String(length=50), nullable=False),
        sa.Column('condition_entity_id', sa.Integer(), nullable=True),
        sa.Column('condition_attribute_code', sa.String(length=50), nullable=True),
        sa.Column('condition_operator', sa.String(length=20), server_default='eq'),
        sa.Column('condition_value', sa.String(length=500), nullable=True),
        sa.Column('apply_to_period_ids', postgresql.JSONB(), nullable=True),
        sa.Column('fixed_value', sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column('parameter_id', sa.Integer(), nullable=True),
        sa.Column('parameter_operation', sa.String(length=20), server_default='multiply'),
        sa.Column('formula', sa.String(length=500), nullable=True),
        sa.Column('priority', sa.Integer(), server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['rule_set_id'], ['rule_sets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['condition_entity_id'], ['meta_entities.id']),
        sa.ForeignKeyConstraint(['parameter_id'], ['budget_parameters.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # 6. budget_definition_dimensions
    op.create_table('budget_definition_dimensions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('budget_definition_id', sa.Integer(), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('is_required', sa.Boolean(), server_default='true'),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['budget_definition_id'], ['budget_definitions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['entity_id'], ['meta_entities.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('budget_definition_id', 'entity_id', name='uq_budget_def_entity'),
    )

    # 7. budget_entry_rows
    op.create_table('budget_entry_rows',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('budget_definition_id', sa.Integer(), nullable=False),
        sa.Column('dimension_values', postgresql.JSONB(), nullable=False),
        sa.Column('currency_code', sa.String(length=10), server_default='TL'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['budget_definition_id'], ['budget_definitions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
    )
    op.create_index('ix_budget_entry_rows_budget_definition_id', 'budget_entry_rows', ['budget_definition_id'])

    # 8. budget_entry_cells
    op.create_table('budget_entry_cells',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('row_id', sa.Integer(), nullable=False),
        sa.Column('period_id', sa.Integer(), nullable=False),
        sa.Column('measure_code', sa.String(length=50), nullable=False),
        sa.Column('value', sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column('cell_type', postgresql.ENUM('input', 'calculated', 'parameter_calculated', name='budgetcelltype', create_type=False), nullable=False, server_default='input'),
        sa.Column('source_rule_id', sa.Integer(), nullable=True),
        sa.Column('source_param_id', sa.Integer(), nullable=True),
        sa.Column('is_manual_override', sa.Boolean(), server_default='false'),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['row_id'], ['budget_entry_rows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['period_id'], ['budget_periods.id']),
        sa.ForeignKeyConstraint(['source_rule_id'], ['rule_set_items.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['source_param_id'], ['budget_parameters.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('row_id', 'period_id', 'measure_code', name='uq_cell_row_period_measure'),
    )
    op.create_index('ix_cell_row_period', 'budget_entry_cells', ['row_id', 'period_id'])


def downgrade() -> None:
    op.drop_table('budget_entry_cells')
    op.drop_table('budget_entry_rows')
    op.drop_table('budget_definition_dimensions')
    op.drop_table('rule_set_items')
    op.drop_table('budget_definitions')
    op.drop_table('rule_sets')
    op.drop_table('budget_type_measures')
    op.drop_table('budget_types')

    # Drop enums
    sa.Enum(name='ruletype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='budgetcelltype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='budgetdefinitionstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='measuredatatype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='budgetmeasuretype').drop(op.get_bind(), checkfirst=True)
