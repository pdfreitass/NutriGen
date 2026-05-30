import re
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, model_validator, EmailStr


class Endereco(BaseModel):
    cep: str = Field(..., description="CEP do endereço")
    logradouro: str = Field(..., description="Logradouro (rua, avenida, etc)")
    bairro: str = Field(..., description="Bairro")
    cidade: str = Field(..., description="Cidade")
    estado: str = Field(..., description="Estado (UF)")


class UserCreate(BaseModel):
    nome_completo: str = Field(
        ..., min_length=3, max_length=150, description="Nome completo do usuário"
    )
    cpf: str = Field(
        ..., min_length=11, max_length=11, description="CPF com 11 dígitos (apenas números)"
    )
    telefone: str = Field(
        ..., min_length=10, max_length=15, description="Telefone com DDD (apenas números)"
    )
    email: EmailStr = Field(..., description="E-mail válido")
    cep: str = Field(
        ..., min_length=8, max_length=8, description="CEP com 8 dígitos (apenas números)"
    )
    senha: str = Field(
        ..., min_length=8, max_length=100, description="Senha com 8+ caracteres, 1 maiúscula, 1 número, 1 caractere especial"
    )

    @model_validator(mode="after")
    def validate_cpf(self):
        """Valida CPF com algoritmo dos dígitos verificadores."""
        cpf = self.cpf
        if not cpf.isdigit() or len(cpf) != 11:
            raise ValueError("CPF deve conter exatamente 11 dígitos numéricos")

        # Rejeitar CPFs com todos dígitos iguais
        if cpf == cpf[0] * 11:
            raise ValueError("CPF inválido: todos os dígitos são iguais")

        # Validar 1º dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digito1 = (soma * 10 % 11) % 10
        if digito1 != int(cpf[9]):
            raise ValueError("CPF inválido: primeiro dígito verificador não confere")

        # Validar 2º dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digito2 = (soma * 10 % 11) % 10
        if digito2 != int(cpf[10]):
            raise ValueError("CPF inválido: segundo dígito verificador não confere")

        return self

    @model_validator(mode="after")
    def validate_senha(self):
        """Valida senha: 8+ chars, 1 maiúscula, 1 número, 1 caractere especial."""
        senha = self.senha
        if len(senha) < 8:
            raise ValueError("Senha deve ter no mínimo 8 caracteres")
        if not re.search(r"[A-Z]", senha):
            raise ValueError("Senha deve conter pelo menos uma letra maiúscula")
        if not re.search(r"[0-9]", senha):
            raise ValueError("Senha deve conter pelo menos um número")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?`~]", senha):
            raise ValueError("Senha deve conter pelo menos um caractere especial")
        return self


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="E-mail do usuário")
    senha: str = Field(..., description="Senha do usuário")


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="E-mail do usuário para recuperação de senha")


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1, description="Token de recuperação recebido por e-mail")
    nova_senha: str = Field(
        ..., min_length=8, max_length=100,
        description="Nova senha com 8+ caracteres, 1 maiúscula, 1 número, 1 caractere especial"
    )

    @model_validator(mode="after")
    def validate_nova_senha(self):
        """Valida a nova senha com as mesmas regras do cadastro."""
        senha = self.nova_senha
        if len(senha) < 8:
            raise ValueError("Senha deve ter no mínimo 8 caracteres")
        if not re.search(r"[A-Z]", senha):
            raise ValueError("Senha deve conter pelo menos uma letra maiúscula")
        if not re.search(r"[0-9]", senha):
            raise ValueError("Senha deve conter pelo menos um número")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?`~]", senha):
            raise ValueError("Senha deve conter pelo menos um caractere especial")
        return self


class UserResponse(BaseModel):
    id: int = Field(..., description="ID do usuário")
    nome_completo: str = Field(..., description="Nome completo do usuário")
    cpf: str = Field(..., description="CPF mascarado (XXX.XXX.XXX-XX)")
    telefone: str = Field(..., description="Telefone")
    email: str = Field(..., description="E-mail")
    endereco: Endereco = Field(..., description="Endereço completo")


class PatientData(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100, description="Nome do paciente")
    sexo: Literal["masculino", "feminino"] = Field(..., description="Sexo biológico")
    idade: int = Field(..., ge=1, le=120, description="Idade em anos")
    peso_kg: float = Field(..., ge=20, le=500, description="Peso em quilogramas")
    altura_cm: float = Field(..., ge=50, le=280, description="Altura em centímetros")


class MacrosCustomizados(BaseModel):
    proteina_pct: float = Field(..., ge=0, le=100, description="Percentual de proteína")
    carboidrato_pct: float = Field(..., ge=0, le=100, description="Percentual de carboidrato")
    gordura_pct: float = Field(..., ge=0, le=100, description="Percentual de gordura")

    @model_validator(mode="after")
    def validate_soma_macros(self):
        soma = self.proteina_pct + self.carboidrato_pct + self.gordura_pct
        if abs(soma - 100) > 0.01:
            raise ValueError(f"A soma dos percentuais de macros deve ser 100. Soma atual: {soma}")
        return self


class Routine(BaseModel):
    nome: str = Field(..., min_length=1, max_length=50, description="Nome da rotina (ex: Low Carb)")
    nivel_atividade: Literal["sedentario", "moderado", "ativo"] = Field(
        ..., description="Nível de atividade física"
    )
    objetivo: Literal["perda_de_peso", "manutencao", "ganho_de_massa"] = Field(
        ..., description="Objetivo da dieta"
    )
    alimentos_preferidos: List[str] = Field(
        ..., min_length=1, description="Lista de alimentos preferidos para esta rotina"
    )
    macros_personalizados: Optional[MacrosCustomizados] = Field(
        None, description="Distribuição personalizada de macros (opcional)"
    )


class DietGenerateRequest(BaseModel):
    paciente: PatientData = Field(..., description="Dados do paciente")
    rotinas: List[Routine] = Field(
        ..., min_length=3, description="Lista com pelo menos 3 rotinas alimentares"
    )


class MacrosGramas(BaseModel):
    proteina_g: float = Field(..., description="Quantidade de proteína em gramas")
    carboidrato_g: float = Field(..., description="Quantidade de carboidrato em gramas")
    gordura_g: float = Field(..., description="Quantidade de gordura em gramas")


class AlimentoPlano(BaseModel):
    nome: str = Field(..., description="Nome do alimento")
    quantidade_g: float = Field(..., description="Quantidade em gramas")
    proteina_g: float = Field(..., description="Proteína em gramas")
    carboidrato_g: float = Field(..., description="Carboidrato em gramas")
    gordura_g: float = Field(..., description="Gordura em gramas")
    calorias_kcal: float = Field(..., description="Calorias em kcal")


class Refeicao(BaseModel):
    nome: str = Field(..., description="Nome da refeição (ex: Café da Manhã)")
    alimentos: List[AlimentoPlano] = Field(..., description="Alimentos da refeição")


class PlanoAlimentar(BaseModel):
    nome: str = Field(..., description="Nome da rotina")
    nivel_atividade: str = Field(..., description="Nível de atividade física")
    objetivo: str = Field(..., description="Objetivo da dieta (perda_de_peso, manutencao, ganho_de_massa)")
    get_calorico: float = Field(..., description="Gasto Energético Total em kcal")
    macros: MacrosGramas = Field(..., description="Macronutrientes em gramas")
    refeicoes: List[Refeicao] = Field(..., description="Refeições do plano")


class DietGenerateResponse(BaseModel):
    paciente: PatientData = Field(..., description="Dados do paciente")
    tmb: float = Field(..., description="Taxa Metabólica Basal em kcal")
    planos: List[PlanoAlimentar] = Field(..., description="Planos alimentares gerados")
    pdf_url: str = Field(..., description="URL para download do PDF")
