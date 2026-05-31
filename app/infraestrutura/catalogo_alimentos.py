"""
Catálogo de alimentos carregado em memória.

Singleton que carrega `data/foods.json` uma única vez na inicialização
do módulo e oferece métodos de busca por nome, categoria e expansão
de restrições alimentares genéricas.

Uso:
    from app.infraestrutura.catalogo_alimentos import food_catalog

    alimento = food_catalog.buscar_por_nome("frango")
    proteinas = food_catalog.buscar_por_categoria("Carnes e Peixes")
    proibidos = food_catalog.expandir_restricao("laticínios")
"""

import json
import os
from typing import Optional

from app.modelos.alimento import Alimento

# ─── Mapeamentos fixos para expandir_restricao ──────────────
# Restrições genéricas → lista de alimentos concretos do catálogo.
# Nomes devem corresponder exatamente aos nomes no foods.json.
_RESTRICOES_FIXAS: dict[str, list[str]] = {
    "peixe": [
        "Salmão Grelhado",
        "Atum em Lata (água)",
        "Tilápia Grelhada",
        "Camarão Cozido",
    ],
    "frutos do mar": [
        "Salmão Grelhado",
        "Atum em Lata (água)",
        "Tilápia Grelhada",
        "Camarão Cozido",
    ],
    "carne vermelha": [
        "Carne Moída Magra",
        "Filé Mignon",
        "Costela Bovina",
        "Lombo Suíno",
    ],
    "glúten": [
        "Pão Francês",
        "Pão Integral",
        "Macarrão Cozido",
    ],
}

# Restrições que mapeiam para categorias inteiras do catálogo.
# A chave é o termo de restrição; o valor é a categoria cujos
# alimentos DEVEM ser excluídos.
_RESTRICOES_POR_CATEGORIA: dict[str, list[str]] = {
    "laticínios": ["Laticínios"],
    "vegetariano": ["Carnes e Peixes"],
    "ovolactovegetariano": ["Carnes e Peixes"],
}

# Restrições que mapeiam para categorias + alimentos pontuais.
_RESTRICOES_MISTAS: dict[str, tuple[list[str], list[str]]] = {
    "vegano": (
        ["Carnes e Peixes", "Laticínios"],
        ["Ovo Cozido", "Ovo Mexido"],
    ),
}


class FoodCatalog:
    """Catálogo de alimentos com índices por nome e categoria."""

    def __init__(self) -> None:
        self._alimentos: list[Alimento] = []
        self._por_nome: dict[str, Alimento] = {}        # chave: nome.lower()
        self._por_categoria: dict[str, list[Alimento]] = {}
        self._carregar()

    # ─── Carregamento ──────────────────────────────

    def _carregar(self) -> None:
        """Carrega data/foods.json e popula os índices em memória."""
        caminho = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "foods.json"
        )
        caminho = os.path.abspath(caminho)

        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)

        for cat in dados["categorias"]:
            nome_categoria: str = cat["nome"]
            alimentos_cat: list[Alimento] = []

            for item in cat["alimentos"]:
                alimento = Alimento(
                    nome=item["nome"],
                    categoria=nome_categoria,
                    proteina_g=float(item["proteina_g"]),
                    carboidrato_g=float(item["carboidrato_g"]),
                    gordura_g=float(item["gordura_g"]),
                    calorias_kcal=float(item["calorias_kcal"]),
                )
                self._alimentos.append(alimento)
                alimentos_cat.append(alimento)
                self._por_nome[alimento.nome.lower()] = alimento

            self._por_categoria[nome_categoria] = alimentos_cat

    # ─── Busca por nome (algoritmo de 3 fases) ─────

    def buscar_por_nome(self, nome: str) -> Optional[Alimento]:
        """Busca um alimento pelo nome com 3 fases progressivas.

        Fase 1: Match exato (case-insensitive).
        Fase 2: Cada token da busca está contido no nome do alimento.
        Fase 3: Entre múltiplos candidatos, retorna o nome mais curto
                (match mais específico).

        Args:
            nome: Nome (ou parte do nome) do alimento.

        Returns:
            Alimento encontrado ou None.
        """
        nome_lower = nome.lower().strip()
        tokens = set(nome_lower.split())

        # Fase 1: match exato
        if nome_lower in self._por_nome:
            return self._por_nome[nome_lower]

        # Fase 2: cada token da busca está contido no nome do alimento
        candidatos: list[tuple[str, Alimento]] = []
        for chave, alimento in self._por_nome.items():
            if all(tok in chave for tok in tokens):
                candidatos.append((chave, alimento))

        # Fase 3: retorna o match mais curto (mais específico)
        if candidatos:
            candidatos.sort(key=lambda x: len(x[0]))
            return candidatos[0][1]

        return None

    # ─── Busca por categoria ───────────────────────

    def buscar_por_categoria(self, categoria: str) -> list[Alimento]:
        """Retorna todos os alimentos de uma categoria.

        A busca é case-insensitive.

        Args:
            categoria: Nome da categoria (ex: "Carnes e Peixes").

        Returns:
            Lista de alimentos (vazia se categoria não encontrada).
        """
        # Tenta match exato primeiro
        if categoria in self._por_categoria:
            return list(self._por_categoria[categoria])

        # Tenta case-insensitive
        cat_lower = categoria.lower()
        for nome_cat, alimentos in self._por_categoria.items():
            if nome_cat.lower() == cat_lower:
                return list(alimentos)

        return []

    # ─── Listagem completa ─────────────────────────

    def listar_todos(self) -> list[Alimento]:
        """Retorna a lista completa de alimentos do catálogo."""
        return list(self._alimentos)

    # ─── Categorias disponíveis ────────────────────

    def categorias_disponiveis(self) -> list[str]:
        """Retorna os nomes de todas as categorias do catálogo."""
        return list(self._por_categoria.keys())

    # ─── Expansão de restrições ────────────────────

    def expandir_restricao(self, restricao: str) -> list[str]:
        """Mapeia uma restrição genérica para uma lista concreta de alimentos.

        Suporta restrições fixas (ex: "peixe", "glúten"), restrições
        por categoria (ex: "laticínios", "vegetariano") e restrições
        mistas (ex: "vegano").

        Se a restrição não for reconhecida, retorna a própria string
        como uma lista de um elemento, para que o validador tente
        um match por nome posteriormente.

        Args:
            restricao: Termo genérico de restrição (ex: "peixe", "laticínios").

        Returns:
            Lista de nomes de alimentos afetados pela restrição.
        """
        termo = restricao.lower().strip()

        # 1. Restrições fixas (mapeamento direto)
        if termo in _RESTRICOES_FIXAS:
            return list(_RESTRICOES_FIXAS[termo])

        # 2. Restrições por categoria (todos os alimentos da categoria)
        if termo in _RESTRICOES_POR_CATEGORIA:
            proibidos: list[str] = []
            for cat_nome in _RESTRICOES_POR_CATEGORIA[termo]:
                proibidos.extend(
                    a.nome for a in self.buscar_por_categoria(cat_nome)
                )
            return proibidos

        # 3. Restrições mistas (categorias + alimentos pontuais)
        if termo in _RESTRICOES_MISTAS:
            categorias, pontuais = _RESTRICOES_MISTAS[termo]
            proibidos = list(pontuais)
            for cat_nome in categorias:
                proibidos.extend(
                    a.nome for a in self.buscar_por_categoria(cat_nome)
                )
            return proibidos

        # 4. Restrição não reconhecida — tenta buscar como nome de alimento
        alimento = self.buscar_por_nome(termo)
        if alimento:
            return [alimento.nome]

        # 5. Restrição não mapeada — retorna como está para match textual posterior
        return [restricao]


# ─── Singleton ─────────────────────────────────────
# Carregado uma única vez na importação do módulo.
food_catalog = FoodCatalog()
