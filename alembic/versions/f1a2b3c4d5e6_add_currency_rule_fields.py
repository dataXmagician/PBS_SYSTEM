"""add currency rule fields to rule_set_items

Revision ID: f1a2b3c4d5e6
Revises: e7f8a9b0c1d2
Create Date: 2026-02-09
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'e7f8a9b0c1d2'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE ruletype ADD VALUE IF NOT EXISTS 'currency_assign'")
    op.add_column('rule_set_items', sa.Column('currency_code', sa.String(length=10), nullable=True))
    op.add_column('rule_set_items', sa.Column('currency_source_entity_id', sa.Integer(), nullable=True))
    op.add_column('rule_set_items', sa.Column('currency_source_attribute_code', sa.String(length=50), nullable=True))
    op.create_foreign_key(
        'fk_rule_set_items_currency_source_entity',
        'rule_set_items', 'meta_entities',
        ['currency_source_entity_id'], ['id']
    )


def downgrade():
    op.drop_constraint('fk_rule_set_items_currency_source_entity', 'rule_set_items', type_='foreignkey')
    op.drop_column('rule_set_items', 'currency_source_attribute_code')
    op.drop_column('rule_set_items', 'currency_source_entity_id')
    op.drop_column('rule_set_items', 'currency_code')
