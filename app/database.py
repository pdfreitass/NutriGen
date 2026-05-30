"""
Configuração do SQLAlchemy síncrono com SQL Server.

Gerencia a conexão com o banco de dados usando pyodbc e SQLAlchemy 2.0.
A conexão usa odbc_connect para compatibilidade com named instances do SQL Server.
"""

import os
import urllib.parse

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()

# String de conexão ODBC direta (funciona com named instances como SQLEXPRESS)
_ODBC_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost\\SQLEXPRESS;"
    "DATABASE=nutrigen;"
    "Trusted_Connection=yes"
)

# Permite sobrescrever a URL completa via .env se necessário
_ENV_URL = os.getenv("DATABASE_URL")
if _ENV_URL:
    DATABASE_URL = _ENV_URL
else:
    params = urllib.parse.quote(_ODBC_STR)
    DATABASE_URL = f"mssql+pyodbc:///?odbc_connect={params}"

engine = create_engine(DATABASE_URL, echo=False, pool_size=5, max_overflow=10)

SessionFactory = sessionmaker(engine, class_=Session, expire_on_commit=False)


class Base(DeclarativeBase):
    """Classe base para todos os modelos ORM."""
    pass


def get_session() -> Session:
    """Cria e retorna uma sessão (usada como generator para FastAPI Depends)."""
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def criar_tabelas():
    """Cria todas as tabelas definidas nos modelos (útil para desenvolvimento)."""
    Base.metadata.create_all(engine)


def fechar_conexao():
    """Fecha a conexão com o banco de dados."""
    engine.dispose()
