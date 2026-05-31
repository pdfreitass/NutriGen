"""
Configuração de logging estruturado — SPEC-013.

Formata logs em JSON com campos padronizados e propaga o request_id
do middleware para todas as camadas via logging filter.

Uso:
    from app.configuracao_logs import setup_logging
    setup_logging()

Campos no JSON:
    - timestamp: ISO 8601 com timezone
    - level: DEBUG, INFO, WARNING, ERROR
    - module: nome do módulo (ex: app.servicos.servico_geracao_planos)
    - request_id: UUID da requisição (do contextvars)
    - message: descrição do evento
    - metadata: dados extras (latência, tokens, etc.)
"""

import json
import logging
import sys
from datetime import datetime, timezone


# ─── JSON Formatter ──────────────────────────────────────

class JSONFormatter(logging.Formatter):
    """Formata registros de log como JSON estruturado."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }

        # Incluir request_id se disponível (via contextvars filter)
        request_id = getattr(record, "request_id", "")
        if request_id:
            log_entry["request_id"] = request_id

        # Incluir metadados extras (do extra={} no log call)
        for key in ("latency", "tokens_in", "tokens_out", "tokens_total",
                    "texto_len", "planos_count", "correcoes", "status_code"):
            val = getattr(record, key, None)
            if val is not None:
                log_entry.setdefault("metadata", {})[key] = val

        # Incluir exception info se presente
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
            }

        return json.dumps(log_entry, ensure_ascii=False, default=str)


# ─── Request ID Filter ───────────────────────────────────

class RequestIDFilter(logging.Filter):
    """Injeta request_id do contextvars em cada log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            from app.middleware.id_requisicao import get_request_id
            rid = get_request_id()
            if rid:
                record.request_id = rid
        except Exception:
            pass
        return True


# ─── Setup ───────────────────────────────────────────────

def setup_logging(level: int = logging.INFO) -> None:
    """Configura logging estruturado JSON para toda a aplicação.

    Args:
        level: Nível mínimo de log (default INFO).
    """
    # Handler: stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    handler.addFilter(RequestIDFilter())

    # Configurar root logger
    root = logging.getLogger()
    root.setLevel(level)

    # Remover handlers existentes para evitar duplicação
    root.handlers.clear()
    root.addHandler(handler)

    # Ajustar níveis para bibliotecas ruidosas
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Log de inicialização
    root.info("Logging configurado [JSON estruturado, stdout]")
