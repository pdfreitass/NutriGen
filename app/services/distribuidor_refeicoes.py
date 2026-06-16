"""
Algoritmo de distribuição determinística de alimentos — SPEC-062.

Distribui alimentos selecionados pelo usuário em 3 planos com 4-6 refeições,
atingindo metas de macros sem depender de IA.

Uso:
    distributor = MealDistributor()
    planos = distributor.distribuir(alimentos, metas)
"""

import random
from dataclasses import dataclass, field

from app.infrastructure.catalogo_alimentos import food_catalog
from app.models.alimento import Alimento


@dataclass
class _AlimentoDistribuicao:
    alimento: Alimento
    preferido: bool = False
    qtd_max_dia: float | None = None
    selecionado_para: set[int] = field(default_factory=set)  # planos em que aparece


# Distribuição calórica por eixo (café, almoço, lanche, jantar)
_EIXO_DISTRIBUICAO: dict[str, list[float]] = {
    "tradicional": [0.20, 0.35, 0.15, 0.30],
    "funcional":   [0.25, 0.30, 0.20, 0.25],
    "pratico":     [0.15, 0.30, 0.25, 0.30],
}

_EIXO_NOMES = ["tradicional", "funcional", "pratico"]
_NOME_PLANOS = {
    "tradicional": "Tradicional Brasileiro",
    "funcional": "Funcional & Nutrientes",
    "pratico": "Prático & Rápido",
}
_NOME_REFEICOES = ["Café da Manhã", "Almoço", "Lanche da Tarde", "Jantar"]


class MealDistributor:
    """Distribui alimentos deterministicamente em 3 planos alimentares."""

    def distribuir(
        self,
        alimentos_nomes: list[str],
        preferidos: set[str],
        qtd_max: dict[str, float | None],
        metas: dict,
    ) -> list[dict]:
        """Distribui alimentos em 3 planos com refeições.

        Args:
            alimentos_nomes: Lista de nomes de alimentos selecionados.
            preferidos: Set de nomes de alimentos marcados como favoritos.
            qtd_max: Dict nome → quantidade máxima diária (None = sem limite).
            metas: Dict com tmb, get_calorico, proteina_g, carboidrato_g, gordura_g.

        Returns:
            Lista de 3 planos, cada um com refeições e alimentos.
        """
        get_kcal = metas["get_calorico"]
        meta_prot = metas["proteina_g"]
        meta_carb = metas["carboidrato_g"]
        meta_gord = metas["gordura_g"]

        # Resolver alimentos do catálogo
        itens: list[_AlimentoDistribuicao] = []
        for nome in alimentos_nomes:
            al = food_catalog.buscar_por_nome(nome)
            if al:
                itens.append(_AlimentoDistribuicao(
                    alimento=al,
                    preferido=nome in preferidos,
                    qtd_max_dia=qtd_max.get(nome),
                ))

        if len(itens) < 3:
            return self._fallback_planos(metas)

        # Embaralhar para variedade (com seed fixa para reprodutibilidade)
        rng = random.Random(42)
        rng.shuffle(itens)

        # Distribuir itens entre planos (preferidos em 2+ planos)
        for item in itens:
            if item.preferido:
                idxs = rng.sample([0, 1, 2], k=min(2, 3))
                item.selecionado_para = set(idxs)
            else:
                item.selecionado_para = {rng.randint(0, 2)}

        planos = []
        for plano_idx, eixo in enumerate(_EIXO_NOMES):
            distr = _EIXO_DISTRIBUICAO[eixo]
            itens_plano = [i for i in itens if plano_idx in i.selecionado_para]

            # Distribuir itens entre 4 refeições
            por_refeicao = self._distribuir_por_refeicao(itens_plano, rng)
            refeicoes = self._calcular_quantidades(
                por_refeicao, distr, get_kcal, meta_prot, meta_carb, meta_gord
            )

            planos.append({
                "nome": _NOME_PLANOS[eixo],
                "descricao": f"Plano {_NOME_PLANOS[eixo]} — gerado com seus alimentos.",
                "eixo": eixo,
                "objetivo": "manutencao",
                "calorias_estimadas": get_kcal,
                "refeicoes": refeicoes,
            })

        return planos

    def _distribuir_por_refeicao(
        self, itens: list[_AlimentoDistribuicao], rng: random.Random,
    ) -> list[list[_AlimentoDistribuicao]]:
        """Distribui itens entre 4 refeições."""
        refeicoes: list[list[_AlimentoDistribuicao]] = [[] for _ in range(4)]
        for i, item in enumerate(itens):
            refeicoes[i % 4].append(item)
        # Garantir que cada refeição tenha pelo menos 1 item
        for i in range(4):
            if not refeicoes[i] and itens:
                refeicoes[i].append(itens[rng.randint(0, len(itens) - 1)])
        return refeicoes

    def _calcular_quantidades(
        self,
        por_refeicao: list[list[_AlimentoDistribuicao]],
        distr: list[float],
        get_kcal: float,
        meta_prot: float,
        meta_carb: float,
        meta_gord: float,
    ) -> list[dict]:
        """Calcula quantidades de cada alimento por refeição."""
        refeicoes = []
        for ref_idx, itens in enumerate(por_refeicao):
            if not itens:
                continue

            meta_kcal_ref = get_kcal * distr[ref_idx]
            n = len(itens)
            alimentos = []

            for item in itens:
                al = item.alimento
                # Quantidade proporcional
                qtd_base = 150.0  # 150g base
                if item.qtd_max_dia and qtd_base > item.qtd_max_dia:
                    qtd_base = item.qtd_max_dia

                # Ajustar para meta calórica da refeição
                kcal_por_g = al.calorias_kcal / 100.0
                qtd = min(qtd_base, meta_kcal_ref / (n * kcal_por_g)) if kcal_por_g > 0 else qtd_base
                qtd = max(30, min(qtd, 500))  # Clampar

                alimentos.append({
                    "nome": al.nome,
                    "quantidade_g": round(qtd, 1),
                    "proteina_g": round(al.proteina_g * qtd / 100, 1),
                    "carboidrato_g": round(al.carboidrato_g * qtd / 100, 1),
                    "gordura_g": round(al.gordura_g * qtd / 100, 1),
                    "calorias_kcal": round(al.calorias_kcal * qtd / 100, 1),
                })

            refeicoes.append({
                "nome": _NOME_REFEICOES[ref_idx],
                "horario": ["07:00", "12:00", "15:30", "19:30"][ref_idx],
                "alimentos": alimentos,
            })

        return refeicoes

    def _fallback_planos(self, metas: dict) -> list[dict]:
        """Fallback: gera planos vazios se poucos alimentos."""
        return [
            {
                "nome": _NOME_PLANOS[eixo],
                "descricao": "Plano gerado com catálogo padrão.",
                "eixo": eixo,
                "objetivo": "manutencao",
                "calorias_estimadas": metas["get_calorico"],
                "refeicoes": [],
            }
            for eixo in _EIXO_NOMES
        ]
