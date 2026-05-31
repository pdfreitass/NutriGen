"""
Middleware de request_id para correlação de logs — SPEC-011.

Gera um UUID único para cada requisição e o propaga via:
- contextvars (acessível por todas as camadas)
- Header X-Request-ID na resposta (para o frontend)

Uso em qualquer módulo:
    from app.middleware.id_requisicao import get_request_id
    rid = get_request_id()
"""

import uuid
import contextvars

from fastapi import Request
from fastapi.responses import Response

# ContextVar thread-safe para propagar o request_id
_request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)


def get_request_id() -> str:
    """Retorna o request_id da requisição atual. Seguro para usar em qualquer módulo."""
    return _request_id_ctx.get()


async def request_id_middleware(request: Request, call_next):
    """Middleware que injeta request_id no contexto e nos headers de resposta.

    Deve ser registrado ANTES do rate_limit_middleware para que
    erros de rate limit também tenham request_id.
    """
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    _request_id_ctx.set(rid)

    response: Response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response
