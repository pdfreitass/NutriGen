"""
Módulo de autenticação e gerenciamento de usuários.

Usa SQL Server via SQLAlchemy síncrono + bcrypt para hash de senha.
"""

import bcrypt
import jwt as pyjwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict

from sqlalchemy.exc import IntegrityError
from app.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_HOURS
from app.database import SessionFactory
from app.repositories.usuario_repository import UsuarioRepository
from app.models.schemas import Endereco

SECRET_KEY = JWT_SECRET_KEY
RESET_TOKEN_EXPIRATION_HOURS = 1


# ─── Password Hashing ──────────────────────────────

def _hash_senha(senha: str) -> str:
    """
    Gera hash bcrypt da senha.

    Args:
        senha: Senha em texto puro

    Returns:
        Hash bcrypt (contém salt embutido)
    """
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verificar_senha(senha: str, senha_hash: str) -> bool:
    """
    Verifica se a senha corresponde ao hash bcrypt armazenado.

    Args:
        senha: Senha em texto puro
        senha_hash: Hash bcrypt armazenado

    Returns:
        True se a senha estiver correta
    """
    try:
        return bcrypt.checkpw(
            senha.encode("utf-8"), senha_hash.encode("utf-8")
        )
    except (ValueError, AttributeError):
        return False


# ─── CPF Masking ───────────────────────────────────

def _mascarar_cpf(cpf: str) -> str:
    """Formata CPF como XXX.XXX.XXX-XX."""
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


# ─── JWT ───────────────────────────────────────────

def gerar_token_jwt(usuario_id: int) -> str:
    """
    Gera um token JWT para o usuário autenticado.

    Args:
        usuario_id: ID do usuário

    Returns:
        Token JWT como string
    """
    payload = {
        "sub": usuario_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    return pyjwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def verificar_token_jwt(token: str) -> Optional[int]:
    """
    Verifica e decodifica um token JWT.

    Args:
        token: Token JWT

    Returns:
        ID do usuário (sub) se válido, None se inválido/expirado
    """
    try:
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except (pyjwt.ExpiredSignatureError, pyjwt.InvalidTokenError):
        return None


# ─── Usuário ───────────────────────────────────────

def registrar_usuario(
    nome_completo: str,
    cpf: str,
    telefone: str,
    email: str,
    senha: str,
    endereco: Endereco,
) -> Optional[Dict]:
    """
    Registra um novo usuário no banco de dados.

    Args:
        nome_completo: Nome completo do usuário
        cpf: CPF do usuário
        telefone: Telefone do usuário
        email: E-mail do usuário
        senha: Senha em texto puro
        endereco: Endereço validado

    Returns:
        Dict com dados do usuário (sem senha) ou None se CPF/e-mail já existir

    Raises:
        ValueError: Se CPF ou e-mail já estiverem cadastrados
    """
    with SessionFactory() as session:
        try:
            repo = UsuarioRepository(session)

            # Verificar se CPF já existe
            existente = repo.buscar_por_cpf(cpf)
            if existente:
                raise ValueError("CPF já cadastrado no sistema")

            # Verificar se e-mail já existe
            existente = repo.buscar_por_email(email)
            if existente:
                raise ValueError("E-mail já cadastrado no sistema")

            senha_hash = _hash_senha(senha)

            usuario = repo.criar(
                nome_completo=nome_completo,
                cpf=cpf,
                telefone=telefone,
                email=email,
                senha_hash=senha_hash,
                cep=endereco.cep,
                logradouro=endereco.logradouro,
                bairro=endereco.bairro,
                cidade=endereco.cidade,
                estado=endereco.estado,
            )

            session.commit()

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

        except IntegrityError as e:
            session.rollback()
            erro = str(e.orig)
            if "cpf" in erro.lower():
                raise ValueError("CPF já cadastrado no sistema")
            elif "email" in erro.lower():
                raise ValueError("E-mail já cadastrado no sistema")
            raise ValueError("Erro ao cadastrar usuário")


def autenticar_usuario(email: str, senha: str) -> Optional[Dict]:
    """
    Autentica um usuário com e-mail e senha.

    Args:
        email: E-mail do usuário
        senha: Senha em texto puro

    Returns:
        Dict com dados do usuário ou None se inválido
    """
    with SessionFactory() as session:
        repo = UsuarioRepository(session)
        usuario = repo.buscar_por_email(email)

        if not usuario:
            # Mantém tempo constante para evitar timing attack
            _verificar_senha(
                "senha_ficticia_tempo_constante",
                "$2b$12$xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            )
            return None

        if not _verificar_senha(senha, usuario.senha_hash):
            return None

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


# ─── Password Reset ───────────────────────────────

def solicitar_redefinicao_senha(email: str) -> Optional[str]:
    """
    Gera um token de recuperação de senha para o e-mail informado.

    Args:
        email: E-mail do usuário

    Returns:
        Token de recuperação (string) se o e-mail existir, None caso contrário
    """
    with SessionFactory() as session:
        repo = UsuarioRepository(session)
        usuario = repo.buscar_por_email(email)

        if not usuario:
            return None

        token = repo.criar_token_recuperacao(
            usuario.id, expiracao_horas=RESET_TOKEN_EXPIRATION_HOURS
        )
        session.commit()
        return token


def redefinir_senha(token: str, nova_senha: str) -> bool:
    """
    Redefine a senha do usuário usando um token de recuperação válido.

    Args:
        token: Token de recuperação
        nova_senha: Nova senha em texto puro

    Returns:
        True se a senha foi redefinida com sucesso, False caso contrário
    """
    with SessionFactory() as session:
        repo = UsuarioRepository(session)
        registro = repo.validar_token_recuperacao(token)

        if not registro:
            return False

        nova_senha_hash = _hash_senha(nova_senha)

        repo.atualizar_senha(registro.usuario_id, nova_senha_hash)
        repo.marcar_token_utilizado(registro.id)
        session.commit()

        return True
