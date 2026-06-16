"""
Módulo de cálculo da Taxa Metabólica Basal (TMB) usando a equação de Mifflin-St Jeor
e do Gasto Energético Total (GET) baseado no nível de atividade.
"""

from typing import Literal

FATORES_ATIVIDADE = {
    "sedentario": 1.2,
    "moderado": 1.55,
    "ativo": 1.725,
}


def calcular_tmb(sexo: str, peso_kg: float, altura_cm: float, idade: int) -> float:
    """
    Calcula a Taxa Metabólica Basal usando a equação de Mifflin-St Jeor.

    Args:
        sexo: "masculino" ou "feminino"
        peso_kg: Peso em quilogramas
        altura_cm: Altura em centímetros
        idade: Idade em anos

    Returns:
        TMB em kcal (arredondado para 1 casa decimal)
    """
    if sexo == "masculino":
        tmb = 10 * peso_kg + 6.25 * altura_cm - 5 * idade + 5
    else:
        tmb = 10 * peso_kg + 6.25 * altura_cm - 5 * idade - 161

    return round(tmb, 1)


def calcular_get(tmb: float, nivel_atividade: Literal["sedentario", "moderado", "ativo"]) -> float:
    """
    Calcula o Gasto Energético Total com base no nível de atividade.

    Args:
        tmb: Taxa Metabólica Basal em kcal
        nivel_atividade: "sedentario", "moderado" ou "ativo"

    Returns:
        GET em kcal (arredondado para 1 casa decimal)
    """
    fator = FATORES_ATIVIDADE.get(nivel_atividade, 1.2)
    get = tmb * fator
    return round(get, 1)
