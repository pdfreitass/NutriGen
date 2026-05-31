"""
Serviço de expansão de restrições alimentares — SPEC-008.

Converte restrições genéricas do usuário ("não como peixe", "sou vegano")
em listas concretas de alimentos proibidos, classifica a severidade e
gera avisos obrigatórios conforme regras de negócio.

Também detecta menções a transtornos alimentares e bloqueia a geração
nesses casos (RN-073).

Uso:
    from app.services.expansor_restricoes import RestrictionExpander

    expander = RestrictionExpander()
    result = expander.expandir(restricoes, condicoes, food_catalog)
    if result.bloqueado:
        raise HTTPException(400, result.motivo_bloqueio)
"""

import logging
from typing import Optional

from app.infrastructure.catalogo_alimentos import FoodCatalog
from app.models.esquemas import ExpandedRestrictions

logger = logging.getLogger(__name__)

# ─── Palavras-chave de transtorno alimentar (RN-073) ──────

_TRANSTORNO_ALIMENTAR_KEYWORDS = [
    "anorexia",
    "bulimia",
    "compulsão alimentar",
    "compulsao alimentar",
    "transtorno alimentar",
    "não como há",
    "nao como ha",
    "vômito",
    "vomito",
    "vomitar",
    "purgar",
    "restrição extrema",
    "restricao extrema",
]

# ─── Avisos por condição médica ───────────────────────────

_AVISOS_CONDICOES = {
    "diabetes": (
        "Este plano não substitui orientação médica para diabetes. "
        "Consulte seu endocrinologista antes de seguir qualquer dieta."
    ),
    "hipertensao": (
        "Este plano não substitui orientação médica para hipertensão. "
        "Consulte seu cardiologista. Alimentos com alto teor de sódio devem ser evitados."
    ),
    "gravidez": (
        "Este plano NÃO é adequado para gestantes. "
        "Consulte seu obstetra e um nutricionista especializado em gestação."
    ),
    "hipotireoidismo": (
        "Este plano não substitui orientação médica para hipotireoidismo. "
        "Consulte seu endocrinologista."
    ),
    "colesterol_alto": (
        "Este plano não substitui orientação médica para colesterol alto. "
        "Consulte seu cardiologista ou nutricionista."
    ),
    "celiaco": (
        "Este plano considera restrição total a glúten. "
        "Verifique sempre os rótulos dos alimentos industrializados."
    ),
}

# ─── Aviso geral obrigatório (RN-070) ─────────────────────

_AVISO_GERAL = (
    "Este plano alimentar é gerado por inteligência artificial e tem caráter "
    "informativo. Não substitui consulta com nutricionista ou médico. "
    "Consulte um profissional de saúde antes de iniciar qualquer dieta."
)

# ─── Mapeamento de severidade ──────────────────────────────

_PADROES_ALERGIA = [
    "alergia", "alérgico", "alergica", "alérgica",
    "intolerancia", "intolerância", "intolerante",
]

_PADROES_CONVICCAO = [
    "vegano", "vegana", "vegetariano", "vegetariana",
    "ovolactovegetariano", "ovolactovegetariana",
]

_PADROES_PREFERENCIA = [
    "não gosto", "nao gosto", "não como", "nao como",
    "evito", "detesto", "odeio",
]


# ═══════════════════════════════════════════════════════════
# RestrictionExpander
# ═══════════════════════════════════════════════════════════

class RestrictionExpander:
    """Expansor de restrições alimentares com classificação de severidade.

    Converte termos genéricos em listas concretas de alimentos proibidos,
    classifica o nível de severidade (alergia > conviccao > preferencia)
    e gera avisos obrigatórios por condição médica detectada.
    """

    def expandir(
        self,
        restricoes: list[str],
        condicoes: list[str],
        catalogo: FoodCatalog,
        texto_original: str = "",
    ) -> ExpandedRestrictions:
        """Expande restrições genéricas para listas concretas de alimentos.

        Args:
            restricoes: Lista de restrições em linguagem natural.
            condicoes: Condições especiais detectadas.
            catalogo: Catálogo de alimentos (FoodCatalog).
            texto_original: Texto original do usuário (para detecção de transtornos).

        Returns:
            ExpandedRestrictions com alimentos proibidos, severidade, avisos.
        """
        # 1. Detectar transtorno alimentar (RN-073) — BLOQUEIO TOTAL
        if texto_original:
            bloqueio = self._detectar_transtorno_alimentar(texto_original)
            if bloqueio:
                return ExpandedRestrictions(
                    alimentos_proibidos=[],
                    severidade="bloqueado",
                    avisos=[],
                    bloqueado=True,
                    motivo_bloqueio=bloqueio,
                )

        # 2. Expandir restrições para alimentos concretos
        proibidos: set[str] = set()
        for restricao in restricoes:
            expandidos = catalogo.expandir_restricao(restricao)
            for nome in expandidos:
                proibidos.add(nome)

        # 3. Expandir condições para restrições de categoria
        for condicao in condicoes:
            expandidos = catalogo.expandir_restricao(condicao)
            for nome in expandidos:
                proibidos.add(nome)

        # 4. Classificar severidade
        severidade = self._classificar_severidade(
            restricoes, condicoes, texto_original
        )

        # 5. Gerar avisos
        avisos = self._gerar_avisos(condicoes, severidade)

        return ExpandedRestrictions(
            alimentos_proibidos=sorted(proibidos),
            severidade=severidade,
            avisos=avisos,
            bloqueado=False,
            motivo_bloqueio="",
        )

    # ─── Detecção de transtorno alimentar ──────────────

    def _detectar_transtorno_alimentar(self, texto: str) -> Optional[str]:
        """Detecta menções a transtornos alimentares no texto (RN-073).

        Args:
            texto: Texto original do usuário.

        Returns:
            Mensagem de bloqueio se detectado, None caso contrário.
        """
        texto_lower = texto.lower()

        for keyword in _TRANSTORNO_ALIMENTAR_KEYWORDS:
            if keyword in texto_lower:
                logger.warning(
                    "Transtorno alimentar detectado: keyword='%s'",
                    keyword,
                )
                return (
                    "Identificamos menções a transtorno alimentar no seu texto. "
                    "O NutriGen não substitui acompanhamento médico ou psicológico. "
                    "Recomendamos fortemente que você busque ajuda profissional. "
                    "Se precisar de apoio, o CVV (Centro de Valorização da Vida) "
                    "oferece atendimento 24h pelo telefone 188."
                )

        return None

    # ─── Classificação de severidade ──────────────────

    def _classificar_severidade(
        self,
        restricoes: list[str],
        condicoes: list[str],
        texto_original: str = "",
    ) -> str:
        """Classifica a severidade das restrições.

        Ordem de prioridade: alergia > conviccao > preferencia.

        Returns:
            'alergia', 'conviccao', ou 'preferencia'.
        """
        todas = [r.lower() for r in restricoes] + [c.lower() for c in condicoes]
        texto_lower = texto_original.lower() if texto_original else ""

        # Verificar alergia primeiro (mais grave)
        for padrao in _PADROES_ALERGIA:
            if any(padrao in t for t in todas) or padrao in texto_lower:
                return "alergia"

        # Verificar convicção
        for padrao in _PADROES_CONVICCAO:
            if any(padrao in t for t in todas) or padrao in texto_lower:
                return "conviccao"

        # Verificar preferência
        for padrao in _PADROES_PREFERENCIA:
            if any(padrao in t for t in todas) or padrao in texto_lower:
                return "preferencia"

        # Default: preferencia (sem restrições fortes)
        return "preferencia"

    # ─── Geração de avisos ────────────────────────────

    def _gerar_avisos(
        self,
        condicoes: list[str],
        severidade: str,
    ) -> list[str]:
        """Gera avisos obrigatórios com base nas condições detectadas.

        Args:
            condicoes: Condições especiais detectadas.
            severidade: Nível de severidade classificado.

        Returns:
            Lista de avisos para exibição ao usuário.
        """
        avisos: list[str] = []

        # Aviso geral sempre presente (RN-070)
        avisos.append(_AVISO_GERAL)

        # RN-021: Aviso para alergias
        if severidade == "alergia":
            avisos.append(
                "ALERTA: Você indicou alergia ou intolerância alimentar. "
                "Verifique atentamente todos os ingredientes antes de consumir. "
                "Em caso de dúvida, consulte um alergista."
            )

        # RN-022: Aviso para condições médicas
        for condicao in condicoes:
            cond_lower = condicao.lower().strip()
            if cond_lower in _AVISOS_CONDICOES:
                avisos.append(_AVISOS_CONDICOES[cond_lower])

        # RN-023: Aviso para dietas restritivas
        if severidade == "conviccao":
            if any(c in condicoes for c in ("vegano", "vegetariano")):
                avisos.append(
                    "ATENÇÃO: Dietas veganas/vegetarianas exigem atenção especial "
                    "à vitamina B12, ferro, zinco e ômega-3. Considere suplementação "
                    "sob orientação profissional."
                )

        # RN-071: Alerta de segurança para GET muito baixo é tratado no NutritionCalculator
        # RN-072: Alerta de meta agressiva é tratado no NutritionCalculator

        return avisos


# ─── Singleton ───────────────────────────────────────────

restriction_expander = RestrictionExpander()
