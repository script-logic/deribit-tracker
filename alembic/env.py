"""
Alembic environment configuration using synchronous engine.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context  # type: ignore

sys.path.append(str(Path(__file__).parent.parent))

from app.core import get_settings
from app.database import Base
from app.database.models import PriceTick  # type: ignore  # noqa: F401

config = context.config
settings = get_settings()

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

db_password = settings.database.password.get_secret_value()
db_host = settings.database.host
config.set_main_option(
    "sqlalchemy.url",
    f"postgresql://{settings.database.user}:{db_password}@"
    f"{db_host}:{settings.database.port}/{settings.database.db}",
)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")

    if url and url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://")

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

    url = configuration.get("sqlalchemy.url", "")
    if url.startswith("postgresql+asyncpg://"):
        configuration["sqlalchemy.url"] = url.replace(
            "postgresql+asyncpg://", "postgresql://"
        )

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
