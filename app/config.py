"""
Configuração centralizada do NutriGen.

Lê todas as variáveis de ambiente com validação na inicialização.
Evita chamadas espalhadas de os.getenv() e facilita testes.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _obrigatoria(nome: str) -> str:
    """Lê variável de ambiente obrigatória. Levanta RuntimeError se ausente."""
    valor = os.getenv(nome)
    if not valor:
        raise RuntimeError(
            f"Variável de ambiente '{nome}' não configurada. "
            f"Defina-a no arquivo .env ou no ambiente."
        )
    return valor


# ─── DeepSeek ───────────────────────────────────────

DEEPSEEK_API_KEY = _obrigatoria("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_TIMEOUT = int(os.getenv("DEEPSEEK_TIMEOUT", "90"))
DEEPSEEK_MAX_RETRIES = int(os.getenv("DEEPSEEK_MAX_RETRIES", "2"))

# Timeouts específicos por tarefa
EXTRACTION_TIMEOUT = int(os.getenv("EXTRACTION_TIMEOUT", "15"))
GENERATION_TIMEOUT = int(os.getenv("GENERATION_TIMEOUT", "90"))

# ─── JWT ────────────────────────────────────────────

JWT_SECRET_KEY = _obrigatoria("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# ─── Banco de Dados ─────────────────────────────────

DATABASE_URL = os.getenv("DATABASE_URL", "")

# ─── Rate Limiting ──────────────────────────────────

RATE_LIMIT_ANON = int(os.getenv("RATE_LIMIT_ANON", "10"))
RATE_LIMIT_AUTH = int(os.getenv("RATE_LIMIT_AUTH", "30"))

# ─── Aplicação ──────────────────────────────────────

APP_ENV = os.getenv("APP_ENV", "development")
APP_DEBUG = os.getenv("APP_DEBUG", "true").lower() == "true"
APP_PORT = int(os.getenv("APP_PORT", "8000"))
