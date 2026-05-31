"""
Middleware de headers de segurança — SPEC-012.

Adiciona headers HTTP de proteção contra ataques comuns:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block (legado, mantido para compatibilidade)
- Strict-Transport-Security (apenas em produção)
"""

from fastapi import Request
from fastapi.responses import Response

from app.configuracao import APP_ENV


async def security_headers_middleware(request: Request, call_next):
    """Adiciona headers de segurança em todas as respostas."""
    response: Response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # HSTS apenas em produção
    if APP_ENV == "production":
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

    return response
