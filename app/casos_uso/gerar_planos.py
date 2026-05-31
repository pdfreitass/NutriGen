"""
Orquestrador do fluxo completo de geração de planos — SPEC-006.

Coordena o pipeline: extração → cálculo → geração → validação → PDF,
com tratamento de erros granular em cada etapa e retry automático.

Fluxo (Fluxo 1 do fluxos.md):
1. ExtractorService.extrair(texto)        → PerfilExtraido
2. NutritionCalculator.calcular(perfil)   → MetasNutricionais
3. PlanGeneratorService.gerar(p, m)       → PlanosGerados
4. PlanValidator.validar(planos, ...)     → ValidationResult
5. Se !aprovado → retry step 3 (máx 1x)
6. PdfGeneratorService.gerar(response)    → UUID do PDF (degradável)
7. Montar e retornar DietGenerateResponse

Uso:
    from app.casos_uso.gerar_planos import GerarPlanosUseCase

    use_case = GerarPlanosUseCase()
    response = use_case.executar("Tenho 28 anos, 72kg...")
"""

import logging
import uuid
from dataclasses import dataclass, field
from typing import Optional

from fastapi import HTTPException

from app.excecoes import (
    CamposObrigatoriosAusentesError,
    DeepSeekError,
    DeepSeekInvalidResponseError,
    DeepSeekTimeoutError,
    DeepSeekUnavailableError,
    GETForaDoIntervaloSeguroError,
    NutriGenException,
    PlanValidationError,
    ValorFisiologicoInvalidoError,
)
from app.infraestrutura.catalogo_alimentos import food_catalog
from app.modelos.esquemas import (
    DietGenerateResponse,
    MetasNutricionais,
    PerfilExtraido,
    PlanosGerados,
    ValidationResult,
)
from app.servicos.servico_extracao import ExtractorService
from app.servicos.calculadora_nutricional import NutritionCalculator
from app.servicos.servico_geracao_planos import PlanGeneratorService
from app.servicos.validador_planos import PlanValidator
from app.servicos.expansor_restricoes import RestrictionExpander
from app.utilitarios.gerador_pdf import gerar_pdf_adaptado

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# GerarPlanosUseCase
# ═══════════════════════════════════════════════════════════

class GerarPlanosUseCase:
    """Orquestrador do fluxo completo de geração de planos alimentares.

    Coordena 4 serviços especializados (extração, cálculo, geração, validação)
    com retry automático na geração se a validação falhar (máx 1 retry).
    O PDF é gerado de forma degradável — se falhar, o response retorna sem PDF.
    """

    def __init__(self) -> None:
        self._extractor = ExtractorService()
        self._calculator = NutritionCalculator()
        self._generator = PlanGeneratorService()
        self._validator = PlanValidator()
        self._expander = RestrictionExpander()

    # ─── Método principal ─────────────────────────────

    def executar(self, texto: str) -> dict:
        """Executa o fluxo completo de geração de planos.

        Args:
            texto: Descrição em linguagem natural do usuário.

        Returns:
            Dict com paciente, tmb, planos, pdf_url e metadados.

        Raises:
            CamposObrigatoriosAusentesError: Dados insuficientes no texto.
            ValorFisiologicoInvalidoError: Valores fora do intervalo.
            GETForaDoIntervaloSeguroError: GET fora de 1200-4000 kcal.
            DeepSeekUnavailableError: API DeepSeek offline.
            DeepSeekInvalidResponseError: Resposta inválida da IA.
            DeepSeekTimeoutError: Timeout da API.
            PlanValidationError: Falha na validação após retry.
        """
        request_id = str(uuid.uuid4())
        logger.info("[%s] Iniciando geração de planos | texto_len=%d", request_id, len(texto))

        # ── Etapa 1: Extração NL→JSON ─────────────────
        try:
            perfil = self._extrair(texto, request_id)
        except CamposObrigatoriosAusentesError as e:
            logger.warning("[%s] Campos obrigatórios ausentes: %s", request_id, e.campos_faltantes)
            raise
        except ValorFisiologicoInvalidoError:
            logger.warning("[%s] Valores fisiológicos inválidos", request_id)
            raise
        except DeepSeekError:
            logger.error("[%s] DeepSeek falhou na extração", request_id)
            raise

        # ── Etapa 2: Cálculo nutricional ──────────────
        try:
            metas = self._calcular(perfil, request_id)
        except GETForaDoIntervaloSeguroError:
            logger.warning("[%s] GET fora do intervalo seguro", request_id)
            raise

        # ── Etapa 2.5: Expandir restrições ──────────────
        expanded = self._expander.expandir(
            perfil.restricoes, perfil.condicoes, food_catalog, texto
        )

        # RN-073: Bloquear se transtorno alimentar detectado
        if expanded.bloqueado:
            logger.warning("[%s] Geração bloqueada: %s", request_id, expanded.motivo_bloqueio)
            raise HTTPException(status_code=400, detail=expanded.motivo_bloqueio)

        # ── Etapa 3: Geração IA ───────────────────────
        planos = self._gerar_com_retry(perfil, metas, texto, request_id)

        # ── Etapa 4: Validação ────────────────────────
        result = self._validar(planos, metas, expanded.alimentos_proibidos, request_id)

        # ── Etapa 5: Retry se necessário ──────────────
        if not result.aprovado:
            logger.warning(
                "[%s] Validação rejeitou planos. Correções graves: %s. "
                "Re-solicitando geração (1ª retentativa).",
                request_id,
                [c for c in result.correcoes_aplicadas if "[GRAVE]" in c],
            )
            try:
                planos = self._gerar(perfil, metas, texto, request_id)
                result = self._validar(planos, metas, expanded.alimentos_proibidos, request_id)

                if not result.aprovado:
                    raise PlanValidationError(
                        "Não foi possível gerar planos válidos após 2 tentativas. "
                        "Tente descrever sua rotina com outras palavras."
                    )
            except PlanValidationError:
                raise
            except Exception as e:
                logger.error("[%s] Falha no retry de geração: %s", request_id, e)
                raise PlanValidationError(
                    "Não foi possível gerar planos válidos. "
                    "Tente novamente com uma descrição mais detalhada."
                )

        # ── Etapa 6: PDF (degradável) ─────────────────
        pdf_url = self._gerar_pdf(planos, perfil, metas, request_id)

        # ── Etapa 7: Montar resposta ──────────────────
        logger.info(
            "[%s] Geração concluída com sucesso | planos=%d | pdf=%s",
            request_id,
            len(planos.planos),
            pdf_url or "não gerado",
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

    def _extrair(self, texto: str, request_id: str) -> PerfilExtraido:
        """Etapa 1: Extração NL→JSON."""
        logger.info("[%s] Etapa 1/7: Extraindo perfil do texto...", request_id)
        perfil = self._extractor.extrair(texto)
        logger.info(
            "[%s] Perfil extraído: sexo=%s idade=%s peso=%s altura=%s objetivo=%s",
            request_id,
            perfil.perfil.sexo,
            perfil.perfil.idade,
            perfil.perfil.peso_kg,
            perfil.perfil.altura_cm,
            perfil.rotina.objetivo,
        )
        return perfil

    def _calcular(
        self, perfil: PerfilExtraido, request_id: str
    ) -> MetasNutricionais:
        """Etapa 2: Cálculo nutricional determinístico."""
        logger.info("[%s] Etapa 2/7: Calculando metas nutricionais...", request_id)
        metas = self._calculator.calcular(perfil)
        return metas

    def _gerar(
        self,
        perfil: PerfilExtraido,
        metas: MetasNutricionais,
        texto: str,
        request_id: str,
    ) -> PlanosGerados:
        """Etapa 3: Geração de planos via IA."""
        logger.info("[%s] Etapa 3/7: Gerando 3 planos via DeepSeek...", request_id)
        planos = self._generator.gerar(perfil, metas, texto_original=texto)
        logger.info("[%s] Planos gerados: %d planos", request_id, len(planos.planos))
        return planos

    def _gerar_com_retry(
        self,
        perfil: PerfilExtraido,
        metas: MetasNutricionais,
        texto: str,
        request_id: str,
    ) -> PlanosGerados:
        """Etapa 3 com retry em caso de falha da IA."""
        try:
            return self._gerar(perfil, metas, texto, request_id)
        except DeepSeekError:
            logger.error("[%s] DeepSeek falhou na geração", request_id)
            raise

    def _validar(
        self,
        planos: PlanosGerados,
        metas: MetasNutricionais,
        restricoes: list[str],
        request_id: str,
    ) -> ValidationResult:
        """Etapa 4: Validação determinística."""
        logger.info("[%s] Etapa 4/7: Validando planos...", request_id)
        result = self._validator.validar(planos, metas, restricoes, food_catalog)
        logger.info(
            "[%s] Validação: aprovado=%s correções=%d",
            request_id,
            result.aprovado,
            len(result.correcoes_aplicadas),
        )
        return result

    def _gerar_pdf(
        self,
        planos: PlanosGerados,
        perfil: PerfilExtraido,
        metas: MetasNutricionais,
        request_id: str,
    ) -> str | None:
        """Etapa 6: Geração de PDF (degradável)."""
        logger.info("[%s] Etapa 6/7: Gerando PDF...", request_id)
        try:
            pdf_url = gerar_pdf_adaptado(planos, perfil, metas)
            logger.info("[%s] PDF gerado: %s", request_id, pdf_url)
            return pdf_url
        except Exception as e:
            logger.error("[%s] Falha ao gerar PDF (não-bloqueante): %s", request_id, e)
            return None
