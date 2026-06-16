"""
Modelos ORM para SessaoGeracao e PlanoAlimentar — SPEC-040.

Representam o histórico de gerações do usuário autenticado.
Cada SessaoGeracao contém 3 PlanoAlimentar (um por eixo).
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Integer, String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.banco_dados import Base


class SessaoGeracao(Base):
    """Sessão de geração de planos de um usuário."""

    __tablename__ = "sessoes_geracao"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id"), nullable=False, index=True,
    )
    data_geracao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    objetivo: Mapped[str] = mapped_column(String(30), nullable=False)
    get_calorico: Mapped[float] = mapped_column(Float, nullable=False)
    tmb: Mapped[float] = mapped_column(Float, nullable=False)
    pdf_uuid: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    data_expiracao_pdf: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # Relacionamento: cascade delete nos planos associados
    planos = relationship(
        "PlanoAlimentar",
        back_populates="sessao",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<SessaoGeracao(id={self.id}, usuario_id={self.usuario_id}, "
            f"objetivo={self.objetivo})>"
        )


class PlanoAlimentar(Base):
    """Um plano alimentar dentro de uma sessão de geração."""

    __tablename__ = "planos_alimentares"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sessao_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("sessoes_geracao.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    eixo: Mapped[str] = mapped_column(String(20), nullable=False)
    get_calorico: Mapped[float] = mapped_column(Float, nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False)

    sessao = relationship("SessaoGeracao", back_populates="planos")

    def __repr__(self) -> str:
        return (
            f"<PlanoAlimentar(id={self.id}, sessao_id={self.sessao_id}, "
            f"eixo={self.eixo})>"
        )
