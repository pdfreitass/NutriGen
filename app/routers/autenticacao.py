"""
Router com os endpoints de autenticação e cadastro de usuário.
"""

from fastapi import APIRouter, HTTPException
from app.models.esquemas import (
    UserCreate, UserResponse, LoginRequest,
    ForgotPasswordRequest, ResetPasswordRequest, Endereco,
)
from app.services.servico_autenticacao import (
    registrar_usuario,
    autenticar_usuario,
    gerar_token_jwt,
    solicitar_redefinicao_senha,
    redefinir_senha,
)
from app.services.servico_viacep import buscar_endereco_por_cep

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])


@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate):
    """
    Cadastra um novo usuário.

    - Valida CPF (algoritmo dos dígitos verificadores)
    - Valida senha (8+ chars, 1 maiúscula, 1 número, 1 especial)
    - Busca endereço automaticamente pelo CEP (ViaCEP)
    - Hash bcrypt da senha
    - Armazena em SQL Server
    """
    # 1. Buscar endereço pelo CEP
    endereco_data = buscar_endereco_por_cep(user_data.cep)

    if not endereco_data:
        raise HTTPException(
            status_code=400,
            detail=f"CEP {user_data.cep} inválido ou não encontrado na base dos Correios",
        )

    endereco = Endereco(**endereco_data)

    # 2. Registrar usuário
    try:
        usuario = registrar_usuario(
            nome_completo=user_data.nome_completo,
            cpf=user_data.cpf,
            telefone=user_data.telefone,
            email=user_data.email,
            senha=user_data.senha,
            endereco=endereco,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return usuario


@router.post("/login")
def login(credentials: LoginRequest):
    """
    Autentica um usuário com e-mail e senha.
    """
    usuario = autenticar_usuario(
        email=credentials.email,
        senha=credentials.senha,
    )

    if not usuario:
        raise HTTPException(
            status_code=401,
            detail="E-mail ou senha inválidos",
        )

    # Gerar token JWT
    token = gerar_token_jwt(usuario["id"])

    return {
        "mensagem": "Autenticado com sucesso",
        "token": token,
        "usuario": usuario,
    }


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest):
    """
    Solicita redefinição de senha.

    Gera um token de recuperação e retorna uma mensagem genérica
    (não revela se o e-mail existe ou não por segurança).
    """
    token = solicitar_redefinicao_senha(data.email)

    # Resposta genérica por segurança — não revela se o e-mail existe
    # Em produção, o token é enviado por e-mail, nunca exposto no response
    return {
        "mensagem": (
            "Se o e-mail informado estiver cadastrado, você receberá "
            "instruções para redefinir sua senha em breve."
        ),
    }


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest):
    """
    Redefine a senha do usuário usando um token de recuperação válido.
    """
    sucesso = redefinir_senha(data.token, data.nova_senha)

    if not sucesso:
        raise HTTPException(
            status_code=400,
            detail="Token inválido, expirado ou já utilizado. Solicite um novo token.",
        )

    return {"mensagem": "Senha redefinida com sucesso!"}
