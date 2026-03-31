"""Alembic environment – reads DB URL from environment variables."""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import the ORM metadata so Alembic can autogenerate migrations
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models import Base  # noqa: E402

config = context.config

# Apply logging config from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_url() -> str:
    """Build the synchronous SQLAlchemy URL from environment variables."""
    user = os.environ.get("POSTGRES_USER", "workhorse")
    password = os.environ.get("POSTGRES_PASSWORD", "workhorse_secure_pw")
    host = os.environ.get("POSTGRES_HOST", "db")
    db = os.environ.get("POSTGRES_DB", "workhorse_db")
    return f"postgresql://{user}:{password}@{host}:5432/{db}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no live DB connection needed)."""
    context.configure(
        url=_get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (live DB connection)."""
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = _get_url()

    connectable = engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
