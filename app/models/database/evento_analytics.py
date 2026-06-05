"""
Modelo ORM para EventoAnalytics — SPEC-043.

Registra eventos anonimizados de uso do sistema para métricas.
Sem IP ou texto original do usuário (LGPD-safe).
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.banco_dados import Base


class EventoAnalytics(Base):
    """Evento anonimizado de analytics."""

    __tablename__ = "eventos_analytics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tipo: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="Tipo do evento: plan_gerado, erro_extracao, erro_geracao, erro_validacao",
    )
    metadados_json: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="JSON com metadados: objetivo, eixo, latencia, tokens, etc.",
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )

    def __repr__(self) -> str:
        return f"<EventoAnalytics(id={self.id}, tipo={self.tipo})>"
