import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Proje root'unu path'e ekle
sys.path.insert(0, '.')

from app.config import settings
from app.db.base import Base

# Tüm modelleri import et (metadata için)
from app.models.dynamic.meta_entity import MetaEntity
from app.models.dynamic.meta_attribute import MetaAttribute
from app.models.dynamic.meta_translation import MetaTranslation
from app.models.dynamic.master_data import MasterData
from app.models.dynamic.master_data_value import MasterDataValue
from app.models.dynamic.dim_time import DimTime
from app.models.dynamic.fact_definition import FactDefinition, FactDimension
from app.models.dynamic.fact_measure import FactMeasure
from app.models.dynamic.fact_data import FactData, FactDataValue
from app.models.system_data import BudgetVersion, BudgetPeriod, BudgetParameter, ParameterVersion
from app.models.budget_entry import (
    BudgetType, BudgetTypeMeasure, BudgetDefinition, BudgetDefinitionDimension,
    BudgetEntryRow, BudgetEntryCell, RuleSet, RuleSetItem
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Database URL'i settings'den al
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
