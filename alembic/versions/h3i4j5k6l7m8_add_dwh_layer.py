"""add dwh layer tables

Revision ID: h3i4j5k6l7m8
Revises: g2h3i4j5k6l7
Create Date: 2026-02-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'h3i4j5k6l7m8'
down_revision: Union[str, None] = 'g2h3i4j5k6l7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============ Create Enums ============

    dwhtablesourcetype = postgresql.ENUM(
        'staging_copy', 'custom', 'staging_modified',
        name='dwhtablesourcetype', create_type=False
    )
    dwhtablesourcetype.create(op.get_bind(), checkfirst=True)

    dwhloadstrategy = postgresql.ENUM(
        'full', 'incremental', 'append',
        name='dwhloadstrategy', create_type=False
    )
    dwhloadstrategy.create(op.get_bind(), checkfirst=True)

    dwhtransferstatus = postgresql.ENUM(
        'pending', 'running', 'success', 'failed',
        name='dwhtransferstatus', create_type=False
    )
    dwhtransferstatus.create(op.get_bind(), checkfirst=True)

    dwhschedulefrequency = postgresql.ENUM(
        'manual', 'hourly', 'daily', 'weekly', 'monthly', 'cron',
        name='dwhschedulefrequency', create_type=False
    )
    dwhschedulefrequency.create(op.get_bind(), checkfirst=True)

    # ============ Create Tables ============

    # 1. dwh_tables
    op.create_table(
        'dwh_tables',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uuid', sa.String(36), nullable=False),
        sa.Column('code', sa.String(100), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('source_type', sa.Enum('staging_copy', 'custom', 'staging_modified', name='dwhtablesourcetype', create_type=False), nullable=False),
        sa.Column('source_query_id', sa.Integer(), nullable=True),
        sa.Column('table_name', sa.String(100), nullable=False),
        sa.Column('table_created', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_date', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        sa.UniqueConstraint('code'),
        sa.UniqueConstraint('table_name'),
        sa.ForeignKeyConstraint(['source_query_id'], ['data_connection_queries.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_dwh_tables_code', 'dwh_tables', ['code'])

    # 2. dwh_columns
    op.create_table(
        'dwh_columns',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('dwh_table_id', sa.Integer(), nullable=False),
        sa.Column('column_name', sa.String(200), nullable=False),
        sa.Column('data_type', sa.Enum('string', 'integer', 'decimal', 'boolean', 'date', 'datetime', name='columndatatype', create_type=False), nullable=False, server_default='string'),
        sa.Column('is_nullable', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_primary_key', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_incremental_key', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('max_length', sa.Integer(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_date', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['dwh_table_id'], ['dwh_tables.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('dwh_table_id', 'column_name', name='uq_dwh_table_column'),
    )

    # 3. dwh_transfers
    op.create_table(
        'dwh_transfers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uuid', sa.String(36), nullable=False),
        sa.Column('dwh_table_id', sa.Integer(), nullable=False),
        sa.Column('source_query_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('load_strategy', sa.Enum('full', 'incremental', 'append', name='dwhloadstrategy', create_type=False), nullable=False, server_default='full'),
        sa.Column('incremental_column', sa.String(200), nullable=True),
        sa.Column('last_incremental_value', sa.String(500), nullable=True),
        sa.Column('column_mapping', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_date', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        sa.ForeignKeyConstraint(['dwh_table_id'], ['dwh_tables.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_query_id'], ['data_connection_queries.id'], ondelete='SET NULL'),
    )

    # 4. dwh_schedules
    op.create_table(
        'dwh_schedules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('transfer_id', sa.Integer(), nullable=False),
        sa.Column('frequency', sa.Enum('manual', 'hourly', 'daily', 'weekly', 'monthly', 'cron', name='dwhschedulefrequency', create_type=False), nullable=False, server_default='manual'),
        sa.Column('cron_expression', sa.String(100), nullable=True),
        sa.Column('hour', sa.Integer(), nullable=True),
        sa.Column('minute', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('day_of_week', sa.Integer(), nullable=True),
        sa.Column('day_of_month', sa.Integer(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_run_at', sa.DateTime(), nullable=True),
        sa.Column('next_run_at', sa.DateTime(), nullable=True),
        sa.Column('created_date', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['transfer_id'], ['dwh_transfers.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('transfer_id'),
    )

    # 5. dwh_transfer_logs
    op.create_table(
        'dwh_transfer_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uuid', sa.String(36), nullable=False),
        sa.Column('transfer_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'success', 'failed', name='dwhtransferstatus', create_type=False), nullable=False, server_default='pending'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('total_rows', sa.Integer(), nullable=True),
        sa.Column('inserted_rows', sa.Integer(), nullable=True),
        sa.Column('updated_rows', sa.Integer(), nullable=True),
        sa.Column('deleted_rows', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('triggered_by', sa.String(100), nullable=True),
        sa.Column('created_date', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        sa.ForeignKeyConstraint(['transfer_id'], ['dwh_transfers.id'], ondelete='CASCADE'),
    )

    # 6. dwh_mappings
    op.create_table(
        'dwh_mappings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uuid', sa.String(36), nullable=False),
        sa.Column('dwh_table_id', sa.Integer(), nullable=False),
        sa.Column('target_type', sa.Enum('master_data', 'system_version', 'system_period', 'system_parameter', 'budget_entry', name='mappingtargettype', create_type=False), nullable=False),
        sa.Column('target_entity_id', sa.Integer(), nullable=True),
        sa.Column('target_definition_id', sa.Integer(), nullable=True),
        sa.Column('target_version_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_date', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        sa.ForeignKeyConstraint(['dwh_table_id'], ['dwh_tables.id'], ondelete='CASCADE'),
    )

    # 7. dwh_field_mappings
    op.create_table(
        'dwh_field_mappings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('mapping_id', sa.Integer(), nullable=False),
        sa.Column('source_column', sa.String(200), nullable=False),
        sa.Column('target_field', sa.String(200), nullable=False),
        sa.Column('transform_type', sa.String(50), nullable=True, server_default='none'),
        sa.Column('transform_config', postgresql.JSONB(), nullable=True),
        sa.Column('is_key_field', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sort_order', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_date', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['mapping_id'], ['dwh_mappings.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('mapping_id', 'target_field', name='uq_dwh_mapping_target_field'),
    )


def downgrade() -> None:
    op.drop_table('dwh_field_mappings')
    op.drop_table('dwh_mappings')
    op.drop_table('dwh_transfer_logs')
    op.drop_table('dwh_schedules')
    op.drop_table('dwh_transfers')
    op.drop_table('dwh_columns')
    op.drop_table('dwh_tables')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS dwhschedulefrequency")
    op.execute("DROP TYPE IF EXISTS dwhtransferstatus")
    op.execute("DROP TYPE IF EXISTS dwhloadstrategy")
    op.execute("DROP TYPE IF EXISTS dwhtablesourcetype")
