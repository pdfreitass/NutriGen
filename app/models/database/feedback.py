"""
Modelo ORM para Feedback de Planos — SPEC-041.

Armazena avaliações dos usuários sobre planos gerados.
Anti-spam: 1 feedback por (sessao_id, plano_idx, ip_hash) a cada 24h.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.banco_dados import Base


class Feedback(Base):
    """Feedback de um usuário sobre um plano gerado."""

    __tablename__ = "feedback_planos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sessao_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True,
        comment="ID da sessão de geração (null se anônimo)",
    )
    plano_idx: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="Índice do plano avaliado (0, 1, 2)",
    )
    positivo: Mapped[bool] = mapped_column(
        Boolean, nullable=False,
        comment="True = 👍, False = 👎",
    )
    motivo: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
        comment="Motivo da insatisfação (apenas quando positivo=false)",
    )
    comentario: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Comentário livre do usuário",
    )
    ip_hash: Mapped[str] = mapped_column(
        String(64), nullable=False,
        comment="Hash SHA-256 do IP para anti-spam (não armazenamos IP real)",
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="Data/hora do feedback",
    )

    def __repr__(self) -> str:
        return (
            f"<Feedback(id={self.id}, sessao_id={self.sessao_id}, "
            f"plano_idx={self.plano_idx}, positivo={self.positivo})>"
        )
