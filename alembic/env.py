"""
Configuração do Alembic para migrações síncronas com SQL Server.

Utiliza o DATABASE_URL do arquivo .env e o metadata do SQLAlchemy Base
para gerar e executar migrações automaticamente.
"""

import os
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import create_engine, pool

from alembic import context

# Carregar variáveis do .env ANTES de qualquer outra configuração
load_dotenv()

# Importar metadados e models para autogenerate
from app.banco_dados import Base  # noqa: E402
from app.modelos.banco import Usuario, RecuperacaoSenha  # noqa: E402, F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Obter URL do banco diretamente do .env (evita ConfigParser interpolation com %)
DATABASE_URL = os.getenv("DATABASE_URL", "")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with just a URL and not an Engine.
    Calls to context.execute() emit the given string to the script output.
    """
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using a sync SQLAlchemy engine."""
    connectable = create_engine(DATABASE_URL, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
