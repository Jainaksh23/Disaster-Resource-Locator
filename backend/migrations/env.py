"""
migrations/env.py — Alembic environment configuration.
Reads DATABASE_URL from pydantic-settings (environment variable).
Uses synchronous psycopg2 URL for Alembic (Alembic does not support asyncpg natively).
"""
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ── Add backend/ to sys.path so models can be imported ───────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import get_settings
from core.database import Base

# Import ALL models so Alembic can detect them for autogenerate
import models  # noqa: F401 — triggers __init__.py which imports all models

# ── Alembic Config object ─────────────────────────────────────────────────────
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# ── Build a synchronous DATABASE_URL from the async one ──────────────────────
def get_sync_url() -> str:
    """
    Convert asyncpg URL to psycopg2 URL for Alembic.
    postgresql+asyncpg://... → postgresql+psycopg2://...
    """
    settings = get_settings()
    url = settings.DATABASE_URL
    return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)


def run_migrations_offline() -> None:
    url = get_sync_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_sync_url()
    connectable = engine_from_config(
        configuration,
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
