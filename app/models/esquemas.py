import re
from typing import Any, Dict, List, Optional, Literal
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


# ─── SPEC-003: Extração NL→JSON ─────────────────────

class Perfil(BaseModel):
    """Perfil demográfico extraído do texto do usuário."""
    sexo: Optional[Literal["masculino", "feminino"]] = Field(
        None, description="Sexo biológico"
    )
    idade: Optional[int] = Field(
        None, ge=1, le=120, description="Idade em anos (1-120)"
    )
    peso_kg: Optional[float] = Field(
        None, ge=20, le=500, description="Peso em quilogramas (20-500)"
    )
    altura_cm: Optional[float] = Field(
        None, ge=50, le=280, description="Altura em centímetros (50-280)"
    )


class RotinaExtraida(BaseModel):
    """Rotina e objetivo extraídos do texto do usuário."""
    nivel_atividade: Optional[Literal["sedentario", "moderado", "ativo"]] = Field(
        None, description="Nível de atividade física"
    )
    objetivo: Optional[Literal["perda_de_peso", "manutencao", "ganho_de_massa"]] = Field(
        None, description="Objetivo da dieta"
    )
    detalhes: Optional[str] = Field(
        None, description="Detalhes adicionais da rotina"
    )


class PerfilExtraido(BaseModel):
    """Resultado da extração NL→JSON — perfil completo do usuário."""
    perfil: Perfil = Field(default_factory=Perfil, description="Dados demográficos")
    rotina: RotinaExtraida = Field(default_factory=RotinaExtraida, description="Rotina e objetivo")
    preferencias: List[str] = Field(default_factory=list, description="Alimentos que o usuário gosta")
    restricoes: List[str] = Field(default_factory=list, description="Alimentos que o usuário NÃO come / tem alergia")
    condicoes: List[str] = Field(default_factory=list, description="Condições especiais detectadas")
    extra: Dict[str, Any] = Field(default_factory=dict, description="Dados adicionais extraídos")


# ─── SPEC-004: Geração de Planos via IA ─────────────────────

class MetasNutricionais(BaseModel):
    """Metas nutricionais calculadas deterministicamente (TMB, GET, macros)."""
    tmb: float = Field(..., description="Taxa Metabólica Basal em kcal")
    get_calorico: float = Field(..., description="Gasto Energético Total em kcal")
    proteina_g: float = Field(..., description="Meta de proteína em gramas")
    carboidrato_g: float = Field(..., description="Meta de carboidrato em gramas")
    gordura_g: float = Field(..., description="Meta de gordura em gramas")


class ItemGerado(BaseModel):
    """Alimento individual dentro de uma refeição gerada pela IA."""
    nome: str = Field(..., description="Nome do alimento (deve existir no catálogo)")
    quantidade_g: float = Field(..., ge=30, le=500, description="Quantidade em gramas")
    proteina_g: float = Field(..., ge=0, description="Proteína calculada para esta porção")
    carboidrato_g: float = Field(..., ge=0, description="Carboidrato calculado para esta porção")
    gordura_g: float = Field(..., ge=0, description="Gordura calculada para esta porção")
    calorias_kcal: float = Field(..., ge=0, description="Calorias calculadas para esta porção")


class RefeicaoGerada(BaseModel):
    """Refeição gerada pela IA, contendo alimentos e horário sugerido."""
    nome: str = Field(default="Refeição", description="Nome da refeição (ex: Café da Manhã)")
    horario: Optional[str] = Field(None, description="Horário sugerido (ex: 07:00)")
    alimentos: List[ItemGerado] = Field(
        default_factory=list, description="Alimentos desta refeição"
    )


class PlanoGerado(BaseModel):
    """Um plano alimentar completo gerado pela IA."""
    nome: str = Field(..., description="Nome do plano (ex: Tradicional Brasileiro)")
    descricao: str = Field(..., min_length=10, description="Descrição do plano (2-4 frases)")
    eixo: Literal["tradicional", "funcional", "pratico"] = Field(
        ..., description="Eixo de diferenciação"
    )
    objetivo: str = Field(..., description="Objetivo da dieta")
    calorias_estimadas: float = Field(..., description="Calorias totais estimadas pelo modelo")
    refeicoes: List[RefeicaoGerada] = Field(
        default_factory=list, description="Refeições do plano (validado pelo PlanValidator)"
    )


class PlanosGerados(BaseModel):
    """Container para os 3 planos gerados pela IA."""
    planos: List[PlanoGerado] = Field(
        ..., min_length=3, max_length=3, description="Exatamente 3 planos gerados"
    )


# ─── SPEC-005: Validação de Planos ─────────────────────

class ValidationResult(BaseModel):
    """Resultado da validação pós-geração dos planos."""
    planos_corrigidos: PlanosGerados = Field(..., description="Planos após correções")
    correcoes_aplicadas: List[str] = Field(
        default_factory=list,
        description="Lista de correções aplicadas (para log, não exibidas ao usuário)",
    )
    aprovado: bool = Field(..., description="True se os planos passaram em todas as validações")


# ─── SPEC-007: Endpoint de Geração (formulário + texto) ──

class DietGenerateRequestV2(BaseModel):
    """Requisição de geração com dados estruturados + descrição da rotina."""
    sexo: Literal["masculino", "feminino"] = Field(
        ..., description="Sexo biológico"
    )
    idade: int = Field(..., ge=1, le=120, description="Idade em anos")
    peso_kg: float = Field(..., ge=20, le=500, description="Peso em quilogramas")
    altura_cm: float = Field(..., ge=50, le=280, description="Altura em centímetros")
    nivel_atividade: Literal["sedentario", "moderado", "ativo"] = Field(
        ..., description="Nível de atividade física"
    )
    texto: str = Field(
        ...,
        min_length=10,
        max_length=1500,
        description="Descrição da rotina, objetivos, preferências e restrições",
    )
    evitar_alimentos: List[str] = Field(
        default_factory=list,
        max_length=50,
        description="Alimentos a evitar na regeneração (SPEC-042). Cada item deve ser um nome de alimento.",
    )


class DietGenerateResponseV2(BaseModel):
    """Resposta da geração de planos (schema SPEC-007)."""
    paciente: dict = Field(..., description="Dados do paciente extraídos")
    tmb: float = Field(..., description="Taxa Metabólica Basal em kcal")
    get_calorico: float = Field(..., description="Gasto Energético Total em kcal")
    objetivo: str = Field(..., description="Objetivo inferido da dieta")
    planos: List[PlanoGerado] = Field(..., description="3 planos alimentares gerados")
    pdf_url: Optional[str] = Field(None, description="URL para download do PDF")
    request_id: str = Field(..., description="UUID da requisição para suporte")
    sessao_id: Optional[int] = Field(
        None, description="ID da sessão no banco (null se usuário anônimo)"
    )
    avisos: List[str] = Field(
        default_factory=list,
        description="Avisos de segurança e recomendações (RN-070, RN-021, etc.)",
    )
    severidade_restricoes: str = Field(
        default="preferencia",
        description="Nível de severidade das restrições detectadas",
    )


# ─── SPEC-008: Expansão de Restrições ────────────────────

class ExpandedRestrictions(BaseModel):
    """Restrições expandidas com classificação de severidade e avisos."""
    alimentos_proibidos: list[str] = Field(
        default_factory=list,
        description="Lista concreta de alimentos proibidos (nomes exatos)",
    )
    severidade: str = Field(
        default="preferencia",
        description="Nível de severidade: alergia, conviccao, preferencia",
    )
    avisos: list[str] = Field(
        default_factory=list,
        description="Avisos obrigatórios para o usuário (RN-021, RN-022, RN-023, RN-070-072)",
    )
    bloqueado: bool = Field(
        default=False,
        description="True se a geração deve ser bloqueada (ex: transtorno alimentar)",
    )
    motivo_bloqueio: str = Field(
        default="",
        description="Motivo do bloqueio, se aplicável",
    )


# ─── SPEC-040: Histórico de Gerações ────────────────────

class PlanoResumo(BaseModel):
    """Resumo leve de um plano no histórico (sem refeições)."""
    nome: str = Field(..., description="Nome do plano")
    eixo: str = Field(..., description="Eixo de diferenciação")
    calorias_estimadas: float = Field(..., description="Calorias estimadas do plano")


class HistoricoItem(BaseModel):
    """Um item do histórico de gerações do usuário."""
    sessao_id: int = Field(..., description="ID da sessão de geração")
    data_geracao: Optional[str] = Field(None, description="Data de geração (ISO 8601)")
    objetivo: str = Field(..., description="Objetivo da dieta")
    get_calorico: float = Field(..., description="GET em kcal")
    tmb: float = Field(..., description="TMB em kcal")
    pdf_disponivel: bool = Field(..., description="True se PDF ainda disponível (7 dias)")
    pdf_url: Optional[str] = Field(None, description="URL relativa do PDF, se disponível")
    resumo: dict = Field(
        default_factory=lambda: {"planos": []},
        description="Resumo dos planos: { planos: [{ nome, eixo, calorias_estimadas }] }",
    )


class HistoricoResponse(BaseModel):
    """Resposta paginada do histórico de gerações."""
    items: List[HistoricoItem] = Field(..., description="Itens do histórico")
    total: int = Field(..., description="Total de registros")
    page: int = Field(..., description="Página atual")
    pages: int = Field(..., description="Total de páginas")


# ─── SPEC-041: Feedback de Planos ──────────────────

_MOTIVOS_NEGATIVOS = [
    "alimentos_repetidos",
    "quantidades_irreais",
    "combinacoes_ruins",
    "alimentos_indesejados",
    "outro",
]


class FeedbackRequest(BaseModel):
    """Requisição de feedback sobre um plano gerado."""
    sessao_id: Optional[int] = Field(
        None, description="ID da sessão de geração (null se anônimo)"
    )
    plano_idx: int = Field(
        ..., ge=0, le=2, description="Índice do plano (0, 1, 2)"
    )
    positivo: bool = Field(
        ..., description="True = 👍 positivo, False = 👎 negativo"
    )
    motivo: Optional[str] = Field(
        None,
        description=f"Motivo da insatisfação. Opções: {_MOTIVOS_NEGATIVOS}",
    )
    comentario: Optional[str] = Field(
        None, max_length=500, description="Comentário livre (opcional)"
    )

    @model_validator(mode="after")
    def validate_motivo(self):
        if self.motivo is not None and self.motivo not in _MOTIVOS_NEGATIVOS:
            raise ValueError(
                f"Motivo inválido. Opções: {_MOTIVOS_NEGATIVOS}"
            )
        return self


class FeedbackResponse(BaseModel):
    """Resposta ao envio de feedback."""
    mensagem: str = Field(..., description="Mensagem de confirmação")
