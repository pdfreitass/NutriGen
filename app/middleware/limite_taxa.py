"""
Middleware de rate limiting simples (in-memory) — SPEC-007.

Limita requisições por IP para o endpoint de geração de planos.
- Anônimos: 10 req/min
- Autenticados: 30 req/min

Implementação leve sem dependências externas. Para produção,
substituir por slowapi ou Redis-based rate limiter (SPEC-019).
"""

import time
import threading
from typing import Optional

from fastapi import Request, HTTPException

from app.configuracao import RATE_LIMIT_ANON as _CFG_ANON, RATE_LIMIT_AUTH as _CFG_AUTH

# ─── Configuração ──────────────────────────────────────────

RATE_LIMIT_ANON = _CFG_ANON      # do .env (default 10)
RATE_LIMIT_AUTH = _CFG_AUTH      # do .env (default 30)
WINDOW_SECONDS = 60              # janela de tempo em segundos


# ─── Armazenamento em memória ──────────────────────────────

class _RateLimitStore:
    """Armazena timestamps de requisições por IP com limpeza periódica."""

    def __init__(self) -> None:
        self._store: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def is_rate_limited(self, key: str, limit: int) -> bool:
        """Verifica se a chave excedeu o limite na janela atual.

        Args:
            key: Identificador (IP ou IP+user).
            limit: Número máximo de requisições na janela.

        Returns:
            True se o limite foi excedido.
        """
        agora = time.monotonic()
        janela_inicio = agora - WINDOW_SECONDS

        with self._lock:
            timestamps = self._store.get(key, [])

            # Remover timestamps antigos (fora da janela)
            timestamps = [t for t in timestamps if t > janela_inicio]

            if len(timestamps) >= limit:
                # Calcular tempo restante até reset
                tempo_restante = WINDOW_SECONDS - (agora - timestamps[0])
                self._store[key] = timestamps
                return True, max(1, int(tempo_restante))

            # Registrar nova requisição
            timestamps.append(agora)
            self._store[key] = timestamps

            # Limpeza periódica: remover entradas muito antigas
            if len(self._store) > 10000:
                self._cleanup(agora)

            return False, 0

    def _cleanup(self, agora: float) -> None:
        """Remove entradas expiradas do store."""
        janela_inicio = agora - WINDOW_SECONDS * 2
        expired = [
            k for k, v in self._store.items()
            if not any(t > janela_inicio for t in v)
        ]
        for k in expired:
            del self._store[k]


_store = _RateLimitStore()


# ─── Middleware ────────────────────────────────────────────

def get_client_ip(request: Request) -> str:
    """Extrai o IP real do cliente, considerando proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def rate_limit_middleware(request: Request):
    """Middleware de rate limiting aplicado apenas a POST /api/diet/generate.

    Se o limite for excedido, retorna HTTP 429 com tempo de espera.
    """
    if request.url.path != "/api/diet/generate" or request.method != "POST":
        return None  # sem rate limit para outras rotas

    ip = get_client_ip(request)
    # TODO SPEC-019: Detectar usuário autenticado via JWT para limite maior
    is_authenticated = False
    limit = RATE_LIMIT_AUTH if is_authenticated else RATE_LIMIT_ANON

    exceeded, retry_after = _store.is_rate_limited(ip, limit)

    if exceeded:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Muitas requisições. Aguarde {retry_after} segundos "
                f"antes de tentar novamente."
            ),
            headers={"Retry-After": str(retry_after)},
        )

    return None
