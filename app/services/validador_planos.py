"""
Pipeline de validação determinística pós-geração — SPEC-005.

Valida e corrige automaticamente os planos gerados pela IA antes de
mostrá-los ao usuário. 100% determinístico, sem chamadas à IA.

Fluxo (6 fases em ordem fixa):
1. Estrutural — 3 planos, 4-6 refeições cada
2. Restrições — TOLERÂNCIA ZERO a alimentos proibidos
3. Catálogo — todos os alimentos existem no FoodCatalog
4. Quantidades — 30g a 500g por alimento
5. Nutricional — macros ±10%, calorias 95%-105% do GET
6. Diversidade — máximo 60% de sobreposição entre planos

Se aprovado=False após correções, o orquestrador re-solicita geração (máx 1x).
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from app.models.esquemas import (
    ItemGerado,
    MetasNutricionais,
    PlanoGerado,
    PlanosGerados,
    RefeicaoGerada,
    ValidationResult,
)
from app.infrastructure.catalogo_alimentos import FoodCatalog

logger = logging.getLogger(__name__)

# ─── Constantes ──────────────────────────────────────────

_QUANTIDADE_MINIMA_G = 30
_QUANTIDADE_MAXIMA_G = 500
_MACRO_TOLERANCIA = 0.10       # ±10%
_CALORIA_TOLERANCIA_MIN = 0.95  # 95% do GET
_CALORIA_TOLERANCIA_MAX = 1.05  # 105% do GET
_SOBREPOSICAO_MAXIMA = 0.60     # máximo 60% de alimentos iguais entre planos
_MIN_REFEICOES = 4
_MAX_REFEICOES = 7


# ─── ValidationResult interno (mutável durante validação) ─

@dataclass
class _CorrecoesAcumuladas:
    """Acumula correções durante o pipeline de validação."""
    correcoes: list[str] = field(default_factory=list)
    erros_graves: list[str] = field(default_factory=list)

    def adicionar(self, msg: str) -> None:
        self.correcoes.append(msg)

    def adicionar_grave(self, msg: str) -> None:
        self.erros_graves.append(msg)
        self.correcoes.append(f"[GRAVE] {msg}")

    @property
    def tem_erros_graves(self) -> bool:
        return len(self.erros_graves) > 0


# ═══════════════════════════════════════════════════════════
# PlanValidator
# ═══════════════════════════════════════════════════════════

class PlanValidator:
    """Validador determinístico de planos alimentares gerados por IA.

    Aplica 6 fases de validação em ordem fixa, corrigindo o que for
    possível e sinalizando o que exigir re-geração.

    Uso:
        validator = PlanValidator()
        result = validator.validar(planos, metas, restricoes, catalogo)
        if not result.aprovado:
            # re-solicitar geração com mensagem de erro
    """

    # ─── Método principal ─────────────────────────────

    def validar(
        self,
        planos: PlanosGerados,
        metas: MetasNutricionais,
        restricoes: list[str],
        catalogo: FoodCatalog,
    ) -> ValidationResult:
        """Executa o pipeline completo de validação.

        Args:
            planos: PlanosGerados com exatamente 3 planos.
            metas: MetasNutricionais com TMB, GET e macros calculados.
            restricoes: Lista de alimentos proibidos (nomes exatos).
            catalogo: Catálogo de alimentos (FoodCatalog singleton).

        Returns:
            ValidationResult com planos corrigidos, correções e status.
        """
        acum = _CorrecoesAcumuladas()

        # Trabalhamos com uma cópia mutável (listas de dicts)
        planos_dicts = [p.model_dump() for p in planos.planos]

        # Fase 1: Estrutural
        self._validar_estrutural(planos_dicts, acum)

        # Fase 2: Restrições (TOLERÂNCIA ZERO)
        self._validar_restricoes(planos_dicts, restricoes, catalogo, acum)

        # Fase 3: Catálogo
        self._validar_catalogo(planos_dicts, catalogo, acum)

        # Fase 4: Quantidades
        self._validar_quantidades(planos_dicts, acum)

        # Fase 5: Nutricional
        self._validar_nutricional(planos_dicts, metas, acum)

        # Fase 6: Diversidade
        self._validar_diversidade(planos_dicts, acum)

        # Reconstruir PlanosGerados
        planos_corrigidos = PlanosGerados(
            planos=[PlanoGerado(**p) for p in planos_dicts]
        )

        aprovado = not acum.tem_erros_graves

        logger.info(
            "Validação concluída | aprovado=%s | correcoes=%d | graves=%d",
            aprovado,
            len(acum.correcoes),
            len(acum.erros_graves),
        )

        return ValidationResult(
            planos_corrigidos=planos_corrigidos,
            correcoes_aplicadas=acum.correcoes,
            aprovado=aprovado,
        )

    # ═══════════════════════════════════════════════════════
    # Fase 1 — Estrutural
    # ═══════════════════════════════════════════════════════

    def _validar_estrutural(
        self,
        planos: list[dict],
        acum: _CorrecoesAcumuladas,
    ) -> None:
        """RN-001, RN-005: 3 planos, 4-6 refeições cada."""
        if len(planos) != 3:
            acum.adicionar_grave(
                f"Esperados 3 planos, recebidos {len(planos)}. Rejeitando."
            )
            return

        for i, plano in enumerate(planos):
            refeicoes = plano.get("refeicoes", [])
            num_ref = len(refeicoes)

            if num_ref < _MIN_REFEICOES:
                # Auto-corrigir: adicionar refeições padrão até atingir o mínimo
                faltantes = _MIN_REFEICOES - num_ref
                refeicoes_padrao = [
                    {"nome": "Lanche da Tarde", "horario": "16:00", "alimentos": [
                        {"nome": "Iogurte Natural", "quantidade_g": 150,
                         "proteina_g": 6.0, "carboidrato_g": 8.0,
                         "gordura_g": 4.5, "calorias_kcal": 97}
                    ]},
                    {"nome": "Lanche da Manhã", "horario": "10:00", "alimentos": [
                        {"nome": "Banana", "quantidade_g": 100,
                         "proteina_g": 1.3, "carboidrato_g": 22.0,
                         "gordura_g": 0.3, "calorias_kcal": 89}
                    ]},
                    {"nome": "Ceia", "horario": "21:00", "alimentos": [
                        {"nome": "Aveia em Flocos", "quantidade_g": 30,
                         "proteina_g": 4.1, "carboidrato_g": 19.9,
                         "gordura_g": 2.0, "calorias_kcal": 114}
                    ]},
                ]
                for idx in range(faltantes):
                    ref_default = refeicoes_padrao[min(idx, len(refeicoes_padrao) - 1)]
                    refeicoes.append(ref_default)
                plano["refeicoes"] = refeicoes
                acum.adicionar(
                    f"Plano {i + 1} '{plano.get('nome', '?')}': "
                    f"apenas {num_ref} refeições → {faltantes} refeição(ões) " 
                    f"padrão adicionada(s) para atingir o mínimo de {_MIN_REFEICOES}."
                )

            elif num_ref > _MAX_REFEICOES:
                removidas = num_ref - _MAX_REFEICOES
                plano["refeicoes"] = refeicoes[:_MAX_REFEICOES]
                acum.adicionar(
                    f"Plano {i + 1} '{plano.get('nome', '?')}': "
                    f"{removidas} refeições excedentes removidas "
                    f"({num_ref} → {_MAX_REFEICOES})."
                )

    # ═══════════════════════════════════════════════════════
    # Fase 2 — Restrições (TOLERÂNCIA ZERO)
    # ═══════════════════════════════════════════════════════

    def _validar_restricoes(
        self,
        planos: list[dict],
        restricoes: list[str],
        catalogo: FoodCatalog,
        acum: _CorrecoesAcumuladas,
    ) -> None:
        """RN-020: Nenhum alimento proibido pode aparecer nos planos."""
        if not restricoes:
            return

        proibidos_lower = set(r.lower().strip() for r in restricoes)

        for i, plano in enumerate(planos):
            for j, refeicao in enumerate(plano.get("refeicoes", [])):
                alimentos = refeicao.get("alimentos", [])
                removidos = []

                alimentos_filtrados = []
                for alimento in alimentos:
                    nome = alimento.get("nome", "")
                    if nome.lower() in proibidos_lower:
                        removidos.append(nome)
                        # Tentar substituir por similar da mesma categoria
                        substituto = self._encontrar_substituto(
                            nome, proibidos_lower, catalogo
                        )
                        if substituto:
                            alimentos_filtrados.append(substituto)
                            acum.adicionar(
                                f"Plano {i + 1}, '{refeicao.get('nome', '?')}': "
                                f"'{nome}' (proibido) → '{substituto['nome']}'"
                            )
                        else:
                            acum.adicionar(
                                f"Plano {i + 1}, '{refeicao.get('nome', '?')}': "
                                f"'{nome}' (proibido) removido — sem substituto disponível."
                            )
                    else:
                        alimentos_filtrados.append(alimento)

                refeicao["alimentos"] = alimentos_filtrados

                if removidos and not alimentos_filtrados:
                    acum.adicionar(
                        f"Plano {i + 1}, '{refeicao.get('nome', '?')}': "
                        f"todos os alimentos eram proibidos e foram removidos. "
                        f"Refeição ficou vazia."
                    )

    def _encontrar_substituto(
        self,
        nome_proibido: str,
        proibidos_lower: set[str],
        catalogo: FoodCatalog,
    ) -> dict | None:
        """Encontra substituto para alimento proibido na mesma categoria."""
        alimento_original = catalogo.buscar_por_nome(nome_proibido)
        if not alimento_original:
            return None

        categoria = alimento_original.categoria
        candidatos = catalogo.buscar_por_categoria(categoria)

        for candidato in candidatos:
            if candidato.nome.lower() not in proibidos_lower:
                # Retornar com valores proporcionais (default 100g)
                return {
                    "nome": candidato.nome,
                    "quantidade_g": 100.0,
                    "proteina_g": candidato.proteina_g,
                    "carboidrato_g": candidato.carboidrato_g,
                    "gordura_g": candidato.gordura_g,
                    "calorias_kcal": candidato.calorias_kcal,
                }

        return None

    # ═══════════════════════════════════════════════════════
    # Fase 3 — Catálogo
    # ═══════════════════════════════════════════════════════

    def _validar_catalogo(
        self,
        planos: list[dict],
        catalogo: FoodCatalog,
        acum: _CorrecoesAcumuladas,
    ) -> None:
        """LL-002: Todo alimento deve existir no FoodCatalog."""
        for i, plano in enumerate(planos):
            for j, refeicao in enumerate(plano.get("refeicoes", [])):
                alimentos = refeicao.get("alimentos", [])
                alimentos_validados = []

                for alimento in alimentos:
                    nome = alimento.get("nome", "")
                    encontrado = catalogo.buscar_por_nome(nome)

                    if encontrado:
                        # Corrigir valores nutricionais com base no catálogo
                        qtd = alimento.get("quantidade_g", 100.0)
                        fator = qtd / 100.0
                        alimento["proteina_g"] = round(encontrado.proteina_g * fator, 1)
                        alimento["carboidrato_g"] = round(encontrado.carboidrato_g * fator, 1)
                        alimento["gordura_g"] = round(encontrado.gordura_g * fator, 1)
                        alimento["calorias_kcal"] = round(encontrado.calorias_kcal * fator, 1)
                        alimentos_validados.append(alimento)
                    else:
                        # Tentar fuzzy match
                        similar = self._buscar_similar(nome, catalogo)
                        if similar:
                            qtd = alimento.get("quantidade_g", 100.0)
                            fator = qtd / 100.0
                            acum.adicionar(
                                f"Plano {i + 1}, '{refeicao.get('nome', '?')}': "
                                f"'{nome}' não encontrado → substituído por '{similar.nome}'"
                            )
                            alimentos_validados.append({
                                "nome": similar.nome,
                                "quantidade_g": qtd,
                                "proteina_g": round(similar.proteina_g * fator, 1),
                                "carboidrato_g": round(similar.carboidrato_g * fator, 1),
                                "gordura_g": round(similar.gordura_g * fator, 1),
                                "calorias_kcal": round(similar.calorias_kcal * fator, 1),
                            })
                        else:
                            acum.adicionar(
                                f"Plano {i + 1}, '{refeicao.get('nome', '?')}': "
                                f"'{nome}' não encontrado no catálogo e sem similar — removido."
                            )

                refeicao["alimentos"] = alimentos_validados

    def _buscar_similar(self, nome: str, catalogo: FoodCatalog):
        """Busca alimento similar usando matching parcial por tokens."""
        nome_lower = nome.lower().strip()
        tokens = set(nome_lower.split())

        if not tokens:
            return None

        todos = catalogo.listar_todos()
        candidatos: list[tuple[int, object]] = []

        for alimento in todos:
            nome_alimento_lower = alimento.nome.lower()
            score = sum(1 for t in tokens if t in nome_alimento_lower)
            if score > 0:
                candidatos.append((score, alimento))

        if candidatos:
            candidatos.sort(key=lambda x: x[0], reverse=True)
            return candidatos[0][1]

        return None

    # ═══════════════════════════════════════════════════════
    # Fase 4 — Quantidades
    # ═══════════════════════════════════════════════════════

    def _validar_quantidades(
        self,
        planos: list[dict],
        acum: _CorrecoesAcumuladas,
    ) -> None:
        """RN-014: Quantidades entre 30g e 500g. Fora → clampar."""
        for i, plano in enumerate(planos):
            for j, refeicao in enumerate(plano.get("refeicoes", [])):
                for alimento in refeicao.get("alimentos", []):
                    qtd = alimento.get("quantidade_g", 100.0)

                    if qtd < _QUANTIDADE_MINIMA_G:
                        fator = _QUANTIDADE_MINIMA_G / qtd if qtd > 0 else 1.0
                        alimento["quantidade_g"] = float(_QUANTIDADE_MINIMA_G)
                        self._reescalar_macros(alimento, fator)
                        acum.adicionar(
                            f"Plano {i + 1}, '{refeicao.get('nome', '?')}': "
                            f"'{alimento['nome']}' quantidade {qtd:.0f}g → "
                            f"{_QUANTIDADE_MINIMA_G}g (mínimo)."
                        )

                    elif qtd > _QUANTIDADE_MAXIMA_G:
                        fator = _QUANTIDADE_MAXIMA_G / qtd
                        alimento["quantidade_g"] = float(_QUANTIDADE_MAXIMA_G)
                        self._reescalar_macros(alimento, fator)
                        acum.adicionar(
                            f"Plano {i + 1}, '{refeicao.get('nome', '?')}': "
                            f"'{alimento['nome']}' quantidade {qtd:.0f}g → "
                            f"{_QUANTIDADE_MAXIMA_G}g (máximo)."
                        )

    @staticmethod
    def _reescalar_macros(alimento: dict, fator: float) -> None:
        """Reescala os macros de um alimento por um fator multiplicativo."""
        alimento["proteina_g"] = round(alimento.get("proteina_g", 0) * fator, 1)
        alimento["carboidrato_g"] = round(alimento.get("carboidrato_g", 0) * fator, 1)
        alimento["gordura_g"] = round(alimento.get("gordura_g", 0) * fator, 1)
        alimento["calorias_kcal"] = round(alimento.get("calorias_kcal", 0) * fator, 1)

    # ═══════════════════════════════════════════════════════
    # Fase 5 — Nutricional
    # ═══════════════════════════════════════════════════════

    def _validar_nutricional(
        self,
        planos: list[dict],
        metas: MetasNutricionais,
        acum: _CorrecoesAcumuladas,
    ) -> None:
        """RN-010, RN-015: Macros ±10% e calorias 95%-105% do GET."""
        for i, plano in enumerate(planos):
            totais = self._somar_macros_plano(plano)

            # RN-010: Cada macro ±10%
            proteina_ok = self._dentro_da_tolerancia(
                totais["proteina_g"], metas.proteina_g, _MACRO_TOLERANCIA
            )
            carbo_ok = self._dentro_da_tolerancia(
                totais["carboidrato_g"], metas.carboidrato_g, _MACRO_TOLERANCIA
            )
            gordura_ok = self._dentro_da_tolerancia(
                totais["gordura_g"], metas.gordura_g, _MACRO_TOLERANCIA
            )

            if not proteina_ok:
                self._ajustar_macro(plano, "proteina_g", metas.proteina_g, totais["proteina_g"])
                acum.adicionar(
                    f"Plano {i + 1} '{plano.get('nome', '?')}': "
                    f"proteína ajustada de {totais['proteina_g']:.0f}g → "
                    f"~{metas.proteina_g:.0f}g (meta)."
                )

            if not carbo_ok:
                self._ajustar_macro(plano, "carboidrato_g", metas.carboidrato_g, totais["carboidrato_g"])
                acum.adicionar(
                    f"Plano {i + 1} '{plano.get('nome', '?')}': "
                    f"carboidrato ajustado de {totais['carboidrato_g']:.0f}g → "
                    f"~{metas.carboidrato_g:.0f}g (meta)."
                )

            if not gordura_ok:
                self._ajustar_macro(plano, "gordura_g", metas.gordura_g, totais["gordura_g"])
                acum.adicionar(
                    f"Plano {i + 1} '{plano.get('nome', '?')}': "
                    f"gordura ajustada de {totais['gordura_g']:.0f}g → "
                    f"~{metas.gordura_g:.0f}g (meta)."
                )

            # RN-015: Calorias totais 95%-105% do GET
            totais_apos = self._somar_macros_plano(plano)
            calorias_totais = totais_apos["calorias_kcal"]

            if calorias_totais < metas.get_calorico * _CALORIA_TOLERANCIA_MIN:
                acum.adicionar_grave(
                    f"Plano {i + 1} '{plano.get('nome', '?')}': "
                    f"calorias totais ({calorias_totais:.0f} kcal) abaixo de "
                    f"95% do GET ({metas.get_calorico:.0f} kcal)."
                )
            elif calorias_totais > metas.get_calorico * _CALORIA_TOLERANCIA_MAX:
                acum.adicionar_grave(
                    f"Plano {i + 1} '{plano.get('nome', '?')}': "
                    f"calorias totais ({calorias_totais:.0f} kcal) acima de "
                    f"105% do GET ({metas.get_calorico:.0f} kcal)."
                )

    def _ajustar_macro(
        self,
        plano: dict,
        macro_key: str,
        meta: float,
        atual: float,
    ) -> None:
        """Ajusta quantidades proporcionalmente para aproximar macro da meta."""
        if atual <= 0:
            return

        fator = meta / atual
        for refeicao in plano.get("refeicoes", []):
            for alimento in refeicao.get("alimentos", []):
                nova_qtd = alimento["quantidade_g"] * fator
                nova_qtd = max(_QUANTIDADE_MINIMA_G, min(nova_qtd, _QUANTIDADE_MAXIMA_G))
                fator_real = nova_qtd / alimento["quantidade_g"] if alimento["quantidade_g"] > 0 else 1.0
                alimento["quantidade_g"] = round(nova_qtd, 1)
                self._reescalar_macros(alimento, fator_real)

    @staticmethod
    def _somar_macros_plano(plano: dict) -> dict[str, float]:
        """Soma os macros totais de um plano."""
        totais = {
            "proteina_g": 0.0,
            "carboidrato_g": 0.0,
            "gordura_g": 0.0,
            "calorias_kcal": 0.0,
        }
        for refeicao in plano.get("refeicoes", []):
            for alimento in refeicao.get("alimentos", []):
                for key in totais:
                    totais[key] += alimento.get(key, 0.0)
        return totais

    @staticmethod
    def _dentro_da_tolerancia(valor: float, meta: float, tolerancia: float) -> bool:
        """Verifica se valor está dentro de ±tolerancia da meta."""
        if meta == 0:
            return valor == 0
        return abs(valor - meta) / meta <= tolerancia

    # ═══════════════════════════════════════════════════════
    # Fase 6 — Diversidade
    # ═══════════════════════════════════════════════════════

    def _validar_diversidade(
        self,
        planos: list[dict],
        acum: _CorrecoesAcumuladas,
    ) -> None:
        """RN-004: Máximo 60% de sobreposição de alimentos entre planos."""
        if len(planos) < 2:
            return

        for i in range(len(planos)):
            alimentos_i = self._extrair_nomes_alimentos(planos[i])
            if not alimentos_i:
                continue

            for j in range(i + 1, len(planos)):
                alimentos_j = self._extrair_nomes_alimentos(planos[j])
                if not alimentos_j:
                    continue

                intersecao = alimentos_i & alimentos_j
                uniao = alimentos_i | alimentos_j

                if not uniao:
                    continue

                sobreposicao = len(intersecao) / len(uniao)

                if sobreposicao > _SOBREPOSICAO_MAXIMA:
                    acum.adicionar_grave(
                        f"Sobreposição de {sobreposicao:.0%} entre "
                        f"Plano {i + 1} e Plano {j + 1} "
                        f"(máximo {_SOBREPOSICAO_MAXIMA:.0%}). "
                        f"Alimentos em comum: {', '.join(sorted(intersecao))}."
                    )

    @staticmethod
    def _extrair_nomes_alimentos(plano: dict) -> set[str]:
        """Extrai conjunto de nomes de alimentos (lowercase) de um plano."""
        nomes: set[str] = set()
        for refeicao in plano.get("refeicoes", []):
            for alimento in refeicao.get("alimentos", []):
                nome = alimento.get("nome", "").lower().strip()
                if nome:
                    nomes.add(nome)
        return nomes


# ─── Singleton ───────────────────────────────────────────

plan_validator = PlanValidator()
