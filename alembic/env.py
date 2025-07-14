"""Alembic environment configuration."""
from logging.config import fileConfig
import os
import sys
from alembic import context
from sqlalchemy import engine_from_config
from sqlalchemy import pool

# Add parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.models.database import Base
from app.core.config import Settings

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    settings = Settings()
    if settings.env == "production":
        return settings.database_url
    else:
        db_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, "analyzer.db")
        return f"sqlite:///{db_path}"

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
