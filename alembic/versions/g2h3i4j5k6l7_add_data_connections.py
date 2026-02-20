"""add data connections tables

Revision ID: g2h3i4j5k6l7
Revises: f1a2b3c4d5e6
Create Date: 2026-02-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'g2h3i4j5k6l7'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create PostgreSQL enums via raw SQL with IF NOT EXISTS
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'connectiontype') THEN CREATE TYPE connectiontype AS ENUM ('sap_odata', 'hana_db', 'file_upload'); END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'syncstatus') THEN CREATE TYPE syncstatus AS ENUM ('pending', 'running', 'success', 'failed'); END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'columndatatype') THEN CREATE TYPE columndatatype AS ENUM ('string', 'integer', 'decimal', 'boolean', 'date', 'datetime'); END IF; END $$;")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mappingtargettype') THEN CREATE TYPE mappingtargettype AS ENUM ('master_data', 'system_version', 'system_period', 'system_parameter', 'budget_entry'); END IF; END $$;")

    # 1. data_connections
    op.create_table('data_connections',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uuid', sa.String(length=36), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('connection_type', postgresql.ENUM('sap_odata', 'hana_db', 'file_upload', name='connectiontype', create_type=False), nullable=False),
        sa.Column('host', sa.String(length=500), nullable=True),
        sa.Column('port', sa.Integer(), nullable=True),
        sa.Column('database_name', sa.String(length=200), nullable=True),
        sa.Column('username', sa.String(length=200), nullable=True),
        sa.Column('password', sa.String(length=500), nullable=True),
        sa.Column('sap_client', sa.String(length=10), nullable=True),
        sa.Column('sap_service_path', sa.String(length=500), nullable=True),
        sa.Column('extra_config', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        sa.UniqueConstraint('code'),
    )
    op.create_index('ix_data_connections_code', 'data_connections', ['code'])

    # 2. data_connection_queries
    op.create_table('data_connection_queries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uuid', sa.String(length=36), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('query_text', sa.Text(), nullable=True),
        sa.Column('odata_entity', sa.String(length=500), nullable=True),
        sa.Column('odata_select', sa.String(length=1000), nullable=True),
        sa.Column('odata_filter', sa.String(length=1000), nullable=True),
        sa.Column('odata_top', sa.Integer(), nullable=True),
        sa.Column('file_parse_config', postgresql.JSONB(), nullable=True),
        sa.Column('staging_table_name', sa.String(length=100), nullable=True),
        sa.Column('staging_table_created', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        sa.ForeignKeyConstraint(['connection_id'], ['data_connections.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('connection_id', 'code', name='uq_connection_query_code'),
    )

    # 3. data_connection_columns
    op.create_table('data_connection_columns',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('query_id', sa.Integer(), nullable=False),
        sa.Column('source_name', sa.String(length=200), nullable=False),
        sa.Column('target_name', sa.String(length=200), nullable=False),
        sa.Column('data_type', postgresql.ENUM('string', 'integer', 'decimal', 'boolean', 'date', 'datetime', name='columndatatype', create_type=False), nullable=False, server_default='string'),
        sa.Column('is_nullable', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_primary_key', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_included', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('max_length', sa.Integer(), nullable=True),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['query_id'], ['data_connection_queries.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('query_id', 'target_name', name='uq_query_column_target'),
    )

    # 4. data_sync_logs
    op.create_table('data_sync_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uuid', sa.String(length=36), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=False),
        sa.Column('query_id', sa.Integer(), nullable=True),
        sa.Column('status', postgresql.ENUM('pending', 'running', 'success', 'failed', name='syncstatus', create_type=False), nullable=False, server_default='pending'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('total_rows', sa.Integer(), nullable=True),
        sa.Column('inserted_rows', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('triggered_by', sa.String(length=100), nullable=True),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        sa.ForeignKeyConstraint(['connection_id'], ['data_connections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['query_id'], ['data_connection_queries.id'], ondelete='SET NULL'),
    )

    # 5. data_connection_mappings
    op.create_table('data_connection_mappings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uuid', sa.String(length=36), nullable=False),
        sa.Column('query_id', sa.Integer(), nullable=False),
        sa.Column('target_type', postgresql.ENUM('master_data', 'system_version', 'system_period', 'system_parameter', 'budget_entry', name='mappingtargettype', create_type=False), nullable=False),
        sa.Column('target_entity_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        sa.ForeignKeyConstraint(['query_id'], ['data_connection_queries.id'], ondelete='CASCADE'),
    )

    # 6. data_connection_field_mappings
    op.create_table('data_connection_field_mappings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('mapping_id', sa.Integer(), nullable=False),
        sa.Column('source_column', sa.String(length=200), nullable=False),
        sa.Column('target_field', sa.String(length=200), nullable=False),
        sa.Column('transform_type', sa.String(length=50), nullable=True, server_default='none'),
        sa.Column('transform_config', postgresql.JSONB(), nullable=True),
        sa.Column('is_key_field', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['mapping_id'], ['data_connection_mappings.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('mapping_id', 'target_field', name='uq_mapping_target_field'),
    )


def downgrade() -> None:
    op.drop_table('data_connection_field_mappings')
    op.drop_table('data_connection_mappings')
    op.drop_table('data_sync_logs')
    op.drop_table('data_connection_columns')
    op.drop_table('data_connection_queries')
    op.drop_table('data_connections')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS mappingtargettype")
    op.execute("DROP TYPE IF EXISTS columndatatype")
    op.execute("DROP TYPE IF EXISTS syncstatus")
    op.execute("DROP TYPE IF EXISTS connectiontype")
