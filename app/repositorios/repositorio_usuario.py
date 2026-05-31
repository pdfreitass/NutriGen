"""
Repositório para operações de banco de dados relacionadas ao usuário.

Abstrai o acesso ao SQL Server usando SQLAlchemy síncrono.
Fornece métodos para criar, buscar e atualizar usuários e tokens de recuperação.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modelos.banco import Usuario, RecuperacaoSenha


def _mascarar_cpf(cpf: str) -> str:
    """Formata CPF como XXX.XXX.XXX-XX."""
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


class UsuarioRepository:
    """Repositório para manipulação de usuários no banco de dados."""

    def __init__(self, session: Session):
        self.session = session

    # ─── Buscas ──────────────────────────────────────

    def buscar_por_email(self, email: str) -> Optional[Usuario]:
        """Retorna um usuário pelo e-mail."""
        stmt = select(Usuario).where(Usuario.email == email)
        return self.session.scalar(stmt)

    def buscar_por_cpf(self, cpf: str) -> Optional[Usuario]:
        """Retorna um usuário pelo CPF."""
        stmt = select(Usuario).where(Usuario.cpf == cpf)
        return self.session.scalar(stmt)

    # ─── Criação ─────────────────────────────────────

    def criar(
        self,
        nome_completo: str,
        cpf: str,
        telefone: str,
        email: str,
        senha_hash: str,
        cep: str,
        logradouro: str,
        bairro: str,
        cidade: str,
        estado: str,
    ) -> Usuario:
        """Cria um novo usuário no banco."""
        usuario = Usuario(
            nome_completo=nome_completo,
            cpf=cpf,
            telefone=telefone,
            email=email,
            senha_hash=senha_hash,
            cep=cep,
            logradouro=logradouro,
            bairro=bairro,
            cidade=cidade,
            estado=estado,
        )
        self.session.add(usuario)
        self.session.flush()
        return usuario

    # ─── Atualização ─────────────────────────────────

    def atualizar_senha(self, usuario_id: int, nova_senha_hash: str) -> None:
        """Atualiza o hash da senha do usuário."""
        usuario = self.session.get(Usuario, usuario_id)
        if usuario:
            usuario.senha_hash = nova_senha_hash

    # ─── Token de Recuperação ────────────────────────

    def criar_token_recuperacao(
        self, usuario_id: int, expiracao_horas: int = 1
    ) -> str:
        """Cria um token de recuperação de senha."""
        token = secrets.token_urlsafe(32)
        agora = datetime.now(timezone.utc)
        registro = RecuperacaoSenha(
            usuario_id=usuario_id,
            token=token,
            criado_em=agora,
            expira_em=agora + timedelta(hours=expiracao_horas),
            utilizado=False,
        )
        self.session.add(registro)
        self.session.flush()
        return token

    def validar_token_recuperacao(self, token: str) -> Optional[RecuperacaoSenha]:
        """Valida se um token de recuperação é válido, não expirado e não utilizado."""
        agora = datetime.now(timezone.utc)
        stmt = select(RecuperacaoSenha).where(
            RecuperacaoSenha.token == token,
            RecuperacaoSenha.utilizado == False,  # noqa: E712
            RecuperacaoSenha.expira_em > agora,
        )
        return self.session.scalar(stmt)

    def marcar_token_utilizado(self, token_id: int) -> None:
        """Marca um token como utilizado."""
        registro = self.session.get(RecuperacaoSenha, token_id)
        if registro:
            registro.utilizado = True

    # ─── Conversão ───────────────────────────────────

    @staticmethod
    def usuario_para_dict(usuario: Usuario) -> Dict:
        """Converte um objeto Usuario em dicionário (sem senha)."""
        return {
            "id": usuario.id,
            "nome_completo": usuario.nome_completo,
            "cpf": _mascarar_cpf(usuario.cpf),
            "telefone": usuario.telefone,
            "email": usuario.email,
            "endereco": {
                "cep": usuario.cep,
                "logradouro": usuario.logradouro,
                "bairro": usuario.bairro,
                "cidade": usuario.cidade,
                "estado": usuario.estado,
            },
        }
