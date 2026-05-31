"""
Orquestrador do fluxo completo de geração de planos — SPEC-006.

Coordena o pipeline: extração → cálculo → geração → validação → PDF,
com tratamento de erros granular em cada etapa e retry automático.

Dois modos de entrada:
- executar_com_dados(): formulário (dados estruturados + texto da rotina)
- executar(): texto livre (extrai tudo via IA, modo legado)
"""

import logging
import uuid

from fastapi import HTTPException

from app.excecoes import (
    CamposObrigatoriosAusentesError,
    DeepSeekError,
    DeepSeekInvalidResponseError,
    DeepSeekTimeoutError,
    DeepSeekUnavailableError,
    GETForaDoIntervaloSeguroError,
    PlanValidationError,
    ValorFisiologicoInvalidoError,
)
from app.infrastructure.catalogo_alimentos import food_catalog
from app.models.esquemas import (
    MetasNutricionais,
    Perfil,
    PerfilExtraido,
    PlanosGerados,
    RotinaExtraida,
    ValidationResult,
)
from app.services.servico_extracao import ExtractorService
from app.services.calculadora_nutricional import NutritionCalculator
from app.services.servico_geracao_planos import PlanGeneratorService
from app.services.validador_planos import PlanValidator
from app.services.expansor_restricoes import RestrictionExpander
from app.utils.gerador_pdf import gerar_pdf_adaptado

logger = logging.getLogger(__name__)


class GerarPlanosUseCase:
    """Orquestrador do fluxo completo de geração de planos alimentares."""

    def __init__(self) -> None:
        self._extractor = ExtractorService()
        self._calculator = NutritionCalculator()
        self._generator = PlanGeneratorService()
        self._validator = PlanValidator()
        self._expander = RestrictionExpander()

    # ─── Modo formulário (principal) ──────────────────

    def executar_com_dados(
        self,
        sexo: str,
        idade: int,
        peso_kg: float,
        altura_cm: float,
        nivel_atividade: str,
        texto: str,
    ) -> dict:
        """Executa o fluxo com dados do formulário + texto da rotina.

        Usa os dados estruturados diretamente (sem extrair via IA).
        A IA extrai apenas preferências, restrições e condições do texto.
        """
        request_id = str(uuid.uuid4())
        logger.info(
            "[%s] Geracao via formulario | sexo=%s idade=%d peso=%.1f altura=%.0f atividade=%s",
            request_id, sexo, idade, peso_kg, altura_cm, nivel_atividade,
        )

        # Construir perfil com dados do formulário
        perfil = PerfilExtraido(
            perfil=Perfil(sexo=sexo, idade=idade, peso_kg=peso_kg, altura_cm=altura_cm),
            rotina=RotinaExtraida(nivel_atividade=nivel_atividade, objetivo=None),
            preferencias=[],
            restricoes=[],
            condicoes=[],
        )

        # Extrair preferências/restrições/condições do texto via IA
        try:
            extraido = self._extractor.extrair(texto)
            perfil.preferencias = extraido.preferencias
            perfil.restricoes = extraido.restricoes
            perfil.condicoes = extraido.condicoes
            if extraido.rotina.objetivo:
                perfil.rotina.objetivo = extraido.rotina.objetivo
        except CamposObrigatoriosAusentesError:
            logger.info("[%s] IA nao detectou campos (esperado — via form)", request_id)
        except DeepSeekError:
            logger.warning("[%s] IA falhou ao extrair preferencias — seguindo sem", request_id)

        # Inferir objetivo se não detectado
        if not perfil.rotina.objetivo:
            perfil.rotina.objetivo = self._extractor._inferir_objetivo_por_imc(perfil)

        return self._executar_fluxo(perfil, texto, request_id)

    # ─── Modo texto livre (legado) ────────────────────

    def executar(self, texto: str) -> dict:
        """Executa o fluxo completo extraindo tudo do texto (modo legado)."""
        request_id = str(uuid.uuid4())
        logger.info("[%s] Geracao via texto livre | len=%d", request_id, len(texto))

        try:
            perfil = self._extractor.extrair(texto)
        except CamposObrigatoriosAusentesError as e:
            logger.warning("[%s] Campos ausentes: %s", request_id, e.campos_faltantes)
            raise
        except ValorFisiologicoInvalidoError:
            logger.warning("[%s] Valores fisiologicos invalidos", request_id)
            raise
        except DeepSeekError:
            logger.error("[%s] DeepSeek falhou na extracao", request_id)
            raise

        return self._executar_fluxo(perfil, texto, request_id)

    # ═══════════════════════════════════════════════════════
    # Fluxo comum
    # ═══════════════════════════════════════════════════════

    def _executar_fluxo(
        self, perfil: PerfilExtraido, texto: str, request_id: str
    ) -> dict:
        """Executa o fluxo comum: cálculo → restrições → geração → validação → PDF."""

        # Cálculo nutricional
        try:
            metas = self._calculator.calcular(perfil)
        except GETForaDoIntervaloSeguroError:
            logger.warning("[%s] GET fora do intervalo seguro", request_id)
            raise

        # Expandir restrições
        expanded = self._expander.expandir(
            perfil.restricoes, perfil.condicoes, food_catalog, texto
        )
        if expanded.bloqueado:
            logger.warning("[%s] Geracao bloqueada: %s", request_id, expanded.motivo_bloqueio)
            raise HTTPException(status_code=400, detail=expanded.motivo_bloqueio)

        # Geração IA
        planos = self._gerar_com_retry(perfil, metas, texto, request_id)

        # Validação
        result = self._validator.validar(
            planos, metas, expanded.alimentos_proibidos, food_catalog
        )

        # Retry se necessário
        if not result.aprovado:
            logger.warning(
                "[%s] Validacao rejeitou planos. Re-solicitando (1a retentativa).",
                request_id,
            )
            try:
                planos = self._gerar(perfil, metas, texto, request_id)
                result = self._validator.validar(
                    planos, metas, expanded.alimentos_proibidos, food_catalog
                )
                if not result.aprovado:
                    raise PlanValidationError(
                        "Nao foi possivel gerar planos validos apos 2 tentativas."
                    )
            except PlanValidationError:
                raise
            except Exception as e:
                logger.error("[%s] Falha no retry: %s", request_id, e)
                raise PlanValidationError(
                    "Nao foi possivel gerar planos validos."
                )

        # PDF (degradável)
        pdf_url = self._gerar_pdf(planos, perfil, metas, request_id)

        # Resposta
        logger.info(
            "[%s] Geracao concluida | planos=%d | pdf=%s",
            request_id, len(planos.planos), pdf_url or "nao gerado",
        )

        return {
            "paciente": {
                "sexo": perfil.perfil.sexo,
                "idade": perfil.perfil.idade,
                "peso_kg": perfil.perfil.peso_kg,
                "altura_cm": perfil.perfil.altura_cm,
            },
            "tmb": metas.tmb,
            "get_calorico": metas.get_calorico,
            "objetivo": perfil.rotina.objetivo,
            "planos": result.planos_corrigidos.planos,
            "pdf_url": pdf_url,
            "request_id": request_id,
            "avisos": expanded.avisos,
            "severidade_restricoes": expanded.severidade,
        }

    # ═══════════════════════════════════════════════════════
    # Etapas internas
    # ═══════════════════════════════════════════════════════

    def _gerar(
        self, perfil: PerfilExtraido, metas: MetasNutricionais,
        texto: str, request_id: str,
    ) -> PlanosGerados:
        logger.info("[%s] Etapa 3/6: Gerando planos via DeepSeek...", request_id)
        planos = self._generator.gerar(perfil, metas, texto_original=texto)
        logger.info("[%s] Planos gerados: %d", request_id, len(planos.planos))
        return planos

    def _gerar_com_retry(
        self, perfil: PerfilExtraido, metas: MetasNutricionais,
        texto: str, request_id: str,
    ) -> PlanosGerados:
        try:
            return self._gerar(perfil, metas, texto, request_id)
        except DeepSeekError:
            logger.error("[%s] DeepSeek falhou na geracao", request_id)
            raise

    def _gerar_pdf(
        self, planos: PlanosGerados, perfil: PerfilExtraido,
        metas: MetasNutricionais, request_id: str,
    ) -> str | None:
        logger.info("[%s] Etapa 5/6: Gerando PDF...", request_id)
        try:
            pdf_url = gerar_pdf_adaptado(planos, perfil, metas)
            logger.info("[%s] PDF gerado: %s", request_id, pdf_url)
            return pdf_url
        except Exception as e:
            logger.error("[%s] Falha ao gerar PDF: %s", request_id, e)
            return None
