"""
Middleware de analytics — SPEC-043.

Registra eventos anonimizados de uso do sistema após cada resposta.
Executa em thread separada (não bloqueante).
"""

import json
import logging
import threading
from datetime import datetime, timezone

from fastapi import Request, Response

from app.banco_dados import SessionFactory
from app.models.database.evento_analytics import EventoAnalytics

logger = logging.getLogger(__name__)


def _salvar_evento(tipo: str, metadados: dict | None = None) -> None:
    """Salva um evento de analytics no banco (thread separada)."""
    try:
        with SessionFactory() as session:
            evento = EventoAnalytics(
                tipo=tipo,
                metadados_json=json.dumps(metadados) if metadados else None,
                criado_em=datetime.now(timezone.utc),
            )
            session.add(evento)
            session.commit()
    except Exception as e:
        logger.warning("Falha ao salvar evento analytics: %s", e)


def registrar_evento(tipo: str, metadados: dict | None = None) -> None:
    """Registra evento de analytics em background (não bloqueante).

    Args:
        tipo: Tipo do evento (plan_gerado, erro_extracao, etc.)
        metadados: Dicionário com metadados anonimizados.
    """
    thread = threading.Thread(
        target=_salvar_evento,
        args=(tipo, metadados),
        daemon=True,
    )
    thread.start()
