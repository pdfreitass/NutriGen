"""
Entidades do domínio de alimentos.

Define a dataclass `Alimento` usada pelo `FoodCatalog` e por todos
os serviços que manipulam alimentos (geração, validação, PDF).
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Alimento:
    """Representa um alimento do catálogo com seus valores nutricionais por 100g.

    É imutável (frozen=True) para segurança em operações de catálogo.
    Usa __slots__ para menor consumo de memória com 68+ instâncias.
    """

    nome: str
    categoria: str
    proteina_g: float
    carboidrato_g: float
    gordura_g: float
    calorias_kcal: float

    def macros_por_porcao(self, quantidade_g: float) -> dict[str, float]:
        """Calcula os macros para uma porção específica (quantidade em gramas)."""
        fator = quantidade_g / 100.0
        return {
            "proteina_g": round(self.proteina_g * fator, 1),
            "carboidrato_g": round(self.carboidrato_g * fator, 1),
            "gordura_g": round(self.gordura_g * fator, 1),
            "calorias_kcal": round(self.calorias_kcal * fator, 1),
        }
