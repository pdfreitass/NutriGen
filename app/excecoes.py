"""
Exceções customizadas do NutriGen.

Centraliza todas as exceções específicas do domínio para
tratamento padronizado nos endpoints (HTTP status codes).
"""


class NutriGenException(Exception):
    """Exceção base do NutriGen."""


# ─── LLM / DeepSeek ──────────────────────────────────

class DeepSeekError(NutriGenException):
    """Erro base para falhas na API DeepSeek."""


class DeepSeekUnavailableError(DeepSeekError):
    """API DeepSeek está offline ou inacessível após retries."""


class DeepSeekInvalidResponseError(DeepSeekError):
    """Resposta da DeepSeek não pôde ser parseada como JSON válido."""


class DeepSeekTimeoutError(DeepSeekError):
    """Timeout excedido ao chamar a API DeepSeek."""


# ─── Extração NL→JSON ───────────────────────────────

class ExtractionError(NutriGenException):
    """Erro na extração de perfil a partir do texto do usuário."""


class CamposObrigatoriosAusentesError(ExtractionError):
    """Campos obrigatórios (sexo, idade, peso, altura) não encontrados no texto."""

    def __init__(self, campos_faltantes: list[str], mensagem: str | None = None):
        self.campos_faltantes = campos_faltantes
        super().__init__(mensagem or self._gerar_mensagem())

    def _gerar_mensagem(self) -> str:
        campos = ", ".join(self.campos_faltantes)
        return (
            f"Não consegui identificar: {campos}. "
            f"Tente incluir essas informações na sua descrição."
        )


class ValorFisiologicoInvalidoError(ExtractionError):
    """Valor extraído fora do intervalo fisiologicamente plausível."""


# ─── Validação de Planos ────────────────────────────

class PlanValidationError(NutriGenException):
    """Planos gerados não passaram na validação após correções e retries."""


class GETForaDoIntervaloSeguroError(NutriGenException):
    """GET calculado fora de 1200-4000 kcal/dia."""


# ─── Banco de Dados ─────────────────────────────────

class DatabaseError(NutriGenException):
    """Erro de persistência no banco de dados."""


# ─── Rate Limiting ───────────────────────────────────

class RateLimitError(NutriGenException):
    """Rate limit excedido."""
