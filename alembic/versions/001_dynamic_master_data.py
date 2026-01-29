"""create dynamic master data tables

Revision ID: 001_dynamic_master_data
Revises: 
Create Date: 2025-01-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_dynamic_master_data'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Meta Entities - Anaveri Tipleri
    op.create_table(
        'meta_entities',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uuid', sa.String(36), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('default_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(50), server_default='database', nullable=True),
        sa.Column('color', sa.String(20), server_default='blue', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_system', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=True),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        sa.UniqueConstraint('code')
    )
    op.create_index('ix_meta_entities_code', 'meta_entities', ['code'])

    # Meta Attributes - Anaveri Alanları
    op.create_table(
        'meta_attributes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uuid', sa.String(36), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('default_label', sa.String(100), nullable=False),
        sa.Column('data_type', sa.Enum('string', 'integer', 'decimal', 'boolean', 'date', 'datetime', 'list', 'reference', name='attributetype'), nullable=False),
        sa.Column('options', sa.Text(), nullable=True),
        sa.Column('reference_entity_id', sa.Integer(), nullable=True),
        sa.Column('default_value', sa.String(255), nullable=True),
        sa.Column('is_required', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('is_unique', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('is_code_field', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('is_name_field', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('is_system', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=True),
        sa.Column('min_value', sa.String(50), nullable=True),
        sa.Column('max_value', sa.String(50), nullable=True),
        sa.Column('min_length', sa.Integer(), nullable=True),
        sa.Column('max_length', sa.Integer(), nullable=True),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        sa.ForeignKeyConstraint(['entity_id'], ['meta_entities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reference_entity_id'], ['meta_entities.id'])
    )
    op.create_index('ix_meta_attributes_code', 'meta_attributes', ['code'])
    op.create_index('ix_meta_attributes_entity_id', 'meta_attributes', ['entity_id'])

    # Meta Translations - Çoklu Dil
    op.create_table(
        'meta_translations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('attribute_id', sa.Integer(), nullable=True),
        sa.Column('language_code', sa.String(5), nullable=False),
        sa.Column('translated_name', sa.String(100), nullable=False),
        sa.Column('translated_description', sa.String(500), nullable=True),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['entity_id'], ['meta_entities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['attribute_id'], ['meta_attributes.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('entity_id', 'language_code', name='uq_entity_language'),
        sa.UniqueConstraint('attribute_id', 'language_code', name='uq_attribute_language')
    )
    op.create_index('ix_meta_translations_language_code', 'meta_translations', ['language_code'])

    # Master Data - Anaveri Kayıtları
    op.create_table(
        'master_data',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uuid', sa.String(36), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=True),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        sa.ForeignKeyConstraint(['entity_id'], ['meta_entities.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('entity_id', 'code', name='uq_entity_code')
    )
    op.create_index('ix_master_data_entity_id', 'master_data', ['entity_id'])
    op.create_index('ix_master_data_code', 'master_data', ['code'])

    # Master Data Values - Anaveri Alan Değerleri
    op.create_table(
        'master_data_values',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('master_data_id', sa.Integer(), nullable=False),
        sa.Column('attribute_id', sa.Integer(), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['master_data_id'], ['master_data.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['attribute_id'], ['meta_attributes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reference_id'], ['master_data.id'])
    )
    op.create_index('ix_master_data_attribute', 'master_data_values', ['master_data_id', 'attribute_id'], unique=True)

    # Dim Time - Tarih Boyutu
    op.create_table(
        'dim_time',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('date_key', sa.Integer(), nullable=False),
        sa.Column('full_date', sa.Date(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('quarter', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('month_name', sa.String(20), nullable=False),
        sa.Column('month_name_short', sa.String(3), nullable=False),
        sa.Column('week', sa.Integer(), nullable=False),
        sa.Column('day', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('day_name', sa.String(20), nullable=False),
        sa.Column('day_of_year', sa.Integer(), nullable=False),
        sa.Column('is_weekend', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('is_month_end', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('is_quarter_end', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('is_year_end', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('fiscal_year', sa.Integer(), nullable=True),
        sa.Column('fiscal_quarter', sa.Integer(), nullable=True),
        sa.Column('fiscal_month', sa.Integer(), nullable=True),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date_key'),
        sa.UniqueConstraint('full_date')
    )
    op.create_index('ix_dim_time_date_key', 'dim_time', ['date_key'])
    op.create_index('ix_dim_time_year', 'dim_time', ['year'])
    op.create_index('ix_dim_time_month', 'dim_time', ['month'])

    # Fact Definitions - Veri Giriş Şablonları
    op.create_table(
        'fact_definitions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uuid', sa.String(36), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('include_time_dimension', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('time_granularity', sa.String(20), server_default='month', nullable=True),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        sa.UniqueConstraint('code')
    )
    op.create_index('ix_fact_definitions_code', 'fact_definitions', ['code'])

    # Fact Dimensions - Şablon Boyutları
    op.create_table(
        'fact_dimensions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('fact_definition_id', sa.Integer(), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=True),
        sa.Column('is_required', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['fact_definition_id'], ['fact_definitions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['entity_id'], ['meta_entities.id'])
    )

    # Fact Measures - Şablon Ölçüleri
    op.create_table(
        'fact_measures',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('fact_definition_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('measure_type', sa.Enum('integer', 'decimal', 'currency', 'percentage', name='measuretype'), server_default='decimal', nullable=True),
        sa.Column('aggregation', sa.Enum('sum', 'avg', 'min', 'max', 'count', 'last', name='aggregationtype'), server_default='sum', nullable=True),
        sa.Column('decimal_places', sa.Integer(), server_default='2', nullable=True),
        sa.Column('unit', sa.String(20), nullable=True),
        sa.Column('default_value', sa.String(50), server_default='0', nullable=True),
        sa.Column('is_required', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('is_calculated', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('formula', sa.String(500), nullable=True),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['fact_definition_id'], ['fact_definitions.id'], ondelete='CASCADE')
    )

    # Fact Data - Veri Girişleri
    op.create_table(
        'fact_data',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uuid', sa.String(36), nullable=False),
        sa.Column('fact_definition_id', sa.Integer(), nullable=False),
        sa.Column('dimension_values', sa.String(500), nullable=False),
        sa.Column('time_id', sa.Integer(), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('month', sa.Integer(), nullable=True),
        sa.Column('version', sa.String(50), server_default='BUDGET', nullable=True),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid'),
        sa.ForeignKeyConstraint(['fact_definition_id'], ['fact_definitions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['time_id'], ['dim_time.id'])
    )
    op.create_index('ix_fact_data_fact_definition_id', 'fact_data', ['fact_definition_id'])
    op.create_index('ix_fact_data_time_id', 'fact_data', ['time_id'])
    op.create_index('ix_fact_data_year', 'fact_data', ['year'])
    op.create_index('ix_fact_data_version', 'fact_data', ['version'])
    op.create_index('ix_fact_data_combination', 'fact_data', ['fact_definition_id', 'dimension_values', 'time_id', 'version'])

    # Fact Data Values - Veri Değerleri
    op.create_table(
        'fact_data_values',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('fact_data_id', sa.Integer(), nullable=False),
        sa.Column('measure_id', sa.Integer(), nullable=False),
        sa.Column('value', sa.String(50), nullable=True),
        sa.Column('created_date', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_date', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['fact_data_id'], ['fact_data.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['measure_id'], ['fact_measures.id'], ondelete='CASCADE')
    )
    op.create_index('ix_fact_data_measure', 'fact_data_values', ['fact_data_id', 'measure_id'], unique=True)


def downgrade() -> None:
    op.drop_table('fact_data_values')
    op.drop_table('fact_data')
    op.drop_table('fact_measures')
    op.drop_table('fact_dimensions')
    op.drop_table('fact_definitions')
    op.drop_table('dim_time')
    op.drop_table('master_data_values')
    op.drop_table('master_data')
    op.drop_table('meta_translations')
    op.drop_table('meta_attributes')
    op.drop_table('meta_entities')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS attributetype")
    op.execute("DROP TYPE IF EXISTS measuretype")
    op.execute("DROP TYPE IF EXISTS aggregationtype")
