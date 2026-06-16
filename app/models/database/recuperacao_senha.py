"""
Modelo ORM para a tabela de tokens de recuperação de senha.
"""

from datetime import datetime
from sqlalchemy import (
    String, DateTime, Integer, Boolean, ForeignKey, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.banco_dados import Base


class RecuperacaoSenha(Base):
    __tablename__ = "recuperacao_senha"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id"), nullable=False
    )
    token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expira_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    utilizado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relacionamentos
    usuario = relationship("Usuario", back_populates="tokens_recuperacao")

    def __repr__(self) -> str:
        return f"<RecuperacaoSenha(id={self.id}, usuario_id={self.usuario_id}, utilizado={self.utilizado})>"
