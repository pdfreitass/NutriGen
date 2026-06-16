"""
Middleware de rate limiting robusto — SPEC-045.

Features:
- Rate limiting hierárquico: anônimos 10/min 50/h, autenticados 30/min 200/h
- Headers X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset, Retry-After
- Bloqueio progressivo: 3 violações em 1h → bloqueio 15 min
- Lista de IPs banidos via BANNED_IPS
- Verificação de custo diário via CostTracker
- Log de toda violação
"""

import logging
import time
import threading

from fastapi import Request, HTTPException

from app.configuracao import (
    RATE_LIMIT_ANON,
    RATE_LIMIT_AUTH,
    RATE_LIMIT_HOUR_ANON,
    RATE_LIMIT_HOUR_AUTH,
    BANNED_IPS,
)
from app.infrastructure.cost_tracker import cost_tracker

logger = logging.getLogger(__name__)

# ─── Configuração ──────────────────────────────────────────

VIOLATION_BLOCK_MINUTES = 15
VIOLATION_THRESHOLD = 3
VIOLATION_WINDOW_HOURS = 1


# ─── Armazenamento em memória ──────────────────────────────

class _RateLimitStore:
    """Armazena estado de rate limiting com janelas minuto e hora."""

    def __init__(self) -> None:
        self._minute: dict[str, list[float]] = {}     # IP → timestamps (janela 60s)
        self._hour: dict[str, list[float]] = {}        # IP → timestamps (janela 3600s)
        self._violations: dict[str, list[float]] = {}  # IP → timestamps de violações
        self._blocked_until: dict[str, float] = {}     # IP → timestamp de desbloqueio
        self._lock = threading.Lock()

    def _prune(self, store: dict, window: float, agora: float) -> None:
        inicio = agora - window
        for k in list(store):
            store[k] = [t for t in store[k] if t > inicio]
            if not store[k]:
                del store[k]

    def is_blocked(self, ip: str) -> tuple[bool, int]:
        """Verifica se IP está em bloqueio progressivo."""
        agora = time.monotonic()
        with self._lock:
            if ip in self._blocked_until:
                if agora < self._blocked_until[ip]:
                    remaining = int(self._blocked_until[ip] - agora) + 1
                    return True, remaining
                del self._blocked_until[ip]
        return False, 0

    def is_rate_limited(
        self, ip: str, limit_minute: int, limit_hour: int,
    ) -> tuple[bool, int, int]:
        """Verifica limites por minuto e hora.

        Returns:
            (exceeded, retry_after_seconds, remaining)
        """
        agora = time.monotonic()

        with self._lock:
            # Limpar janelas antigas
            self._prune(self._minute, 60, agora)
            self._prune(self._hour, 3600, agora)

            # Verificar janela horária primeiro
            timestamps_hora = self._hour.get(ip, [])
            if len(timestamps_hora) >= limit_hour:
                retry = int(3600 - (agora - timestamps_hora[0])) + 1
                return True, max(1, retry), 0

            # Verificar janela de minuto
            timestamps_min = self._minute.get(ip, [])
            if len(timestamps_min) >= limit_minute:
                retry = int(60 - (agora - timestamps_min[0])) + 1
                remaining = max(0, limit_minute - len(timestamps_min))
                return True, max(1, retry), remaining

            # Registrar requisição
            self._minute.setdefault(ip, []).append(agora)
            self._hour.setdefault(ip, []).append(agora)

            remaining = limit_minute - len(self._minute[ip])
            return False, 0, remaining

    def record_violation(self, ip: str) -> None:
        """Registra violação para bloqueio progressivo."""
        agora = time.monotonic()
        with self._lock:
            self._violations.setdefault(ip, []).append(agora)
            # Limpar violações antigas
            cutoff = agora - VIOLATION_WINDOW_HOURS * 3600
            self._violations[ip] = [t for t in self._violations[ip] if t > cutoff]

            if len(self._violations[ip]) >= VIOLATION_THRESHOLD:
                self._blocked_until[ip] = agora + VIOLATION_BLOCK_MINUTES * 60
                logger.warning(
                    "IP %s bloqueado por %d min — %d violações em %dh",
                    ip, VIOLATION_BLOCK_MINUTES, VIOLATION_THRESHOLD, VIOLATION_WINDOW_HOURS,
                )


_store = _RateLimitStore()


# ─── Helpers ────────────────────────────────────────────

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _get_auth_key(request: Request) -> str:
    """Extrai chave de rate limit: IP ou IP+user_id."""
    ip = get_client_ip(request)
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            from app.services.servico_autenticacao import verificar_token_jwt
            uid = verificar_token_jwt(auth[7:])
            if uid:
                return f"{ip}:user:{uid}"
        except Exception:
            pass
    return ip


# ─── Middleware ──────────────────────────────────────────

async def rate_limit_middleware(request: Request):
    """Middleware de rate limiting aplicado a POST /api/diet/generate e /generate-v2."""
    if request.method != "POST":
        return None
    if request.url.path not in ("/api/diet/generate", "/api/diet/generate-v2"):
        return None

    ip = get_client_ip(request)
    key = _get_auth_key(request)
    is_auth = ":user:" in key

    # 1. Verificar IPs banidos
    if BANNED_IPS and ip in BANNED_IPS:
        logger.warning("IP banido tentou acessar: %s", ip)
        raise HTTPException(status_code=403, detail="Acesso negado.")

    # 2. Verificar bloqueio progressivo
    blocked, retry = _store.is_blocked(ip)
    if blocked:
        logger.warning("IP bloqueado progressivamente: %s (%ds restantes)", ip, retry)
        raise HTTPException(
            status_code=429,
            detail=f"Bloqueado temporariamente. Aguarde {retry} segundos.",
            headers={"Retry-After": str(retry)},
        )

    # 3. Verificar custo diário
    if cost_tracker.limite_excedido():
        logger.warning("Custo diário excedido: R$ %.2f", cost_tracker.custo_atual())
        raise HTTPException(
            status_code=503,
            detail="Limite diário de processamento atingido. Tente novamente amanhã.",
        )

    # 4. Rate limiting
    limit_min = RATE_LIMIT_AUTH if is_auth else RATE_LIMIT_ANON
    limit_hour = RATE_LIMIT_HOUR_AUTH if is_auth else RATE_LIMIT_HOUR_ANON

    exceeded, retry, remaining = _store.is_rate_limited(key, limit_min, limit_hour)

    if exceeded:
        _store.record_violation(ip)
        logger.warning(
            "Rate limit excedido | ip=%s | auth=%s | retry=%ds",
            ip, is_auth, retry,
        )
        raise HTTPException(
            status_code=429,
            detail=f"Muitas requisições. Aguarde {retry} segundos.",
            headers={
                "Retry-After": str(retry),
                "X-RateLimit-Limit": str(limit_min),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.monotonic() + retry)),
            },
        )

    return None
