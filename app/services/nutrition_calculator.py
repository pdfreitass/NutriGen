"""
Calculadora nutricional determinística — SPEC-006.

Encapsula os cálculos de TMB, GET e distribuição de macronutrientes
a partir de um PerfilExtraido, retornando MetasNutricionais.

Reusa os módulos existentes:
- tmb_calculator.py (Mifflin-St Jeor)
- macro_distributor.py (distribuição por objetivo)

Uso:
    from app.services.nutrition_calculator import NutritionCalculator

    calc = NutritionCalculator()
    metas = calc.calcular(perfil_extraido)
"""

import logging

from app.models.schemas import MetasNutricionais, PerfilExtraido
from app.services.tmb_calculator import calcular_tmb, calcular_get
from app.services.macro_distributor import distribuir_macros
from app.exceptions import GETForaDoIntervaloSeguroError

logger = logging.getLogger(__name__)

# Intervalo seguro de GET (RN-042)
_GET_MINIMO = 1200.0
_GET_MAXIMO = 4000.0


class NutritionCalculator:
    """Calculadora de metas nutricionais a partir de perfil extraído.

    Fluxo determinístico (sem IA):
    1. TMB via Mifflin-St Jeor
    2. GET via fator de atividade
    3. Distribuição de macros conforme objetivo
    """

    def calcular(self, perfil: PerfilExtraido) -> MetasNutricionais:
        """Calcula metas nutricionais a partir do perfil extraído.

        Args:
            perfil: PerfilExtraido com dados demográficos, rotina e objetivo.

        Returns:
            MetasNutricionais com TMB, GET e macros em gramas.

        Raises:
            GETForaDoIntervaloSeguroError: Se GET < 1200 ou > 4000 kcal.
        """
        p = perfil.perfil
        r = perfil.rotina

        # 1. TMB (Mifflin-St Jeor)
        tmb = calcular_tmb(
            sexo=p.sexo or "masculino",
            peso_kg=p.peso_kg or 70,
            altura_cm=p.altura_cm or 170,
            idade=p.idade or 30,
        )

        # 2. GET (fator de atividade)
        nivel = r.nivel_atividade or "sedentario"
        get_calorico = calcular_get(tmb, nivel)

        # 3. Validar intervalo seguro do GET
        if get_calorico < _GET_MINIMO:
            raise GETForaDoIntervaloSeguroError(
                f"GET calculado: {get_calorico:.0f} kcal. "
                f"O mínimo seguro é {_GET_MINIMO:.0f} kcal."
            )
        if get_calorico > _GET_MAXIMO:
            raise GETForaDoIntervaloSeguroError(
                f"GET calculado: {get_calorico:.0f} kcal. "
                f"O máximo seguro é {_GET_MAXIMO:.0f} kcal."
            )

        # 4. Distribuição de macros
        objetivo = r.objetivo or "manutencao"
        macros = distribuir_macros(
            get_calorico=get_calorico,
            objetivo=objetivo,
        )

        logger.info(
            "Cálculo nutricional | TMB=%.0f | GET=%.0f | objetivo=%s | "
            "P=%.0fg | C=%.0fg | G=%.0fg",
            tmb,
            get_calorico,
            objetivo,
            macros["proteina_g"],
            macros["carboidrato_g"],
            macros["gordura_g"],
        )

        return MetasNutricionais(
            tmb=tmb,
            get_calorico=get_calorico,
            proteina_g=macros["proteina_g"],
            carboidrato_g=macros["carboidrato_g"],
            gordura_g=macros["gordura_g"],
        )


# ─── Singleton ───────────────────────────────────────────

nutrition_calculator = NutritionCalculator()
