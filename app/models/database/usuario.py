"""
Modelo ORM para a tabela de usuários.
"""

from datetime import datetime
from sqlalchemy import String, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome_completo: Mapped[str] = mapped_column(String(150), nullable=False)
    cpf: Mapped[str] = mapped_column(String(11), nullable=False, unique=True)
    telefone: Mapped[str] = mapped_column(String(15), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    cep: Mapped[str] = mapped_column(String(8), nullable=False)
    logradouro: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    bairro: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    cidade: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    estado: Mapped[str] = mapped_column(String(2), nullable=False, default="")
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relacionamentos
    tokens_recuperacao = relationship(
        "RecuperacaoSenha", back_populates="usuario", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Usuario(id={self.id}, email={self.email})>"
