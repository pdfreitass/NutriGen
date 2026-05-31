"""
Módulo de distribuição de macronutrientes com base no GET e objetivo da dieta.
Converte percentuais para gramas de proteína, carboidrato e gordura.
"""

from typing import Dict, Optional, Literal

# Valores calóricos por grama de macronutriente
CALORIAS_POR_GRAMA = {
    "proteina": 4,
    "carboidrato": 4,
    "gordura": 9,
}

# Distribuições sugeridas conforme o objetivo
DISTRIBUICAO_SUGERIDA = {
    "perda_de_peso": {"proteina_pct": 35, "carboidrato_pct": 35, "gordura_pct": 30},
    "manutencao": {"proteina_pct": 25, "carboidrato_pct": 50, "gordura_pct": 25},
    "ganho_de_massa": {"proteina_pct": 30, "carboidrato_pct": 45, "gordura_pct": 25},
}


def distribuir_macros(
    get_calorico: float,
    objetivo: Literal["perda_de_peso", "manutencao", "ganho_de_massa"],
    macros_personalizados: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """
    Distribui os macronutrientes em gramas com base no GET e objetivo.

    Se macros_personalizados for fornecido, usa os percentuais do usuário.
    Caso contrário, usa os valores sugeridos para o objetivo.

    Args:
        get_calorico: Gasto Energético Total em kcal
        objetivo: "perda_de_peso", "manutencao" ou "ganho_de_massa"
        macros_personalizados: Dict opcional com proteina_pct, carboidrato_pct, gordura_pct

    Returns:
        Dict com proteina_g, carboidrato_g, gordura_g
    """
    if macros_personalizados:
        pcts = macros_personalizados
    else:
        pcts = DISTRIBUICAO_SUGERIDA.get(objetivo, DISTRIBUICAO_SUGERIDA["manutencao"])

    proteina_g = round((get_calorico * pcts["proteina_pct"] / 100) / CALORIAS_POR_GRAMA["proteina"], 1)
    carboidrato_g = round(
        (get_calorico * pcts["carboidrato_pct"] / 100) / CALORIAS_POR_GRAMA["carboidrato"], 1
    )
    gordura_g = round((get_calorico * pcts["gordura_pct"] / 100) / CALORIAS_POR_GRAMA["gordura"], 1)

    return {
        "proteina_g": proteina_g,
        "carboidrato_g": carboidrato_g,
        "gordura_g": gordura_g,
    }
