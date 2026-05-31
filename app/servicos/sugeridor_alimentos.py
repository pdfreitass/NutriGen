"""
Módulo de sugestão automática de alimentos baseado no banco de dados JSON.
Combina os alimentos preferidos do paciente com sugestões do banco de dados
e monta refeições com quantidades aproximadas.
"""

import json
import os
import random
from typing import Dict, List


def _carregar_alimentos() -> Dict[str, List[Dict]]:
    """
    Carrega o banco de dados de alimentos do arquivo JSON.

    Returns:
        Dict com categorias e suas listas de alimentos
    """
    caminho = os.path.join(os.path.dirname(__file__), "..", "..", "data", "foods.json")
    caminho = os.path.abspath(caminho)

    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)

    return dados


def _buscar_alimento_por_nome(
    nome: str, alimentos_por_nome: Dict[str, Dict]
) -> Dict | None:
    """
    Busca um alimento pelo nome com critérios progressivos:
    1. Match exato (case-insensitive)
    2. Cada token da busca está contido no nome do alimento (ex: "Frango" match "Peito de Frango Grelhado")
    3. Retorna o match mais curto (mais específico) em caso de múltiplos resultados

    Args:
        nome: Nome do alimento a buscar
        alimentos_por_nome: Dict com nome do alimento (lowercase) como chave

    Returns:
        Dict do alimento ou None se não encontrado
    """
    nome_lower = nome.lower().strip()
    tokens = set(nome_lower.split())

    # Fase 1: match exato
    if nome_lower in alimentos_por_nome:
        return alimentos_por_nome[nome_lower]

    # Fase 2: match por tokens — cada token da busca deve estar no nome do alimento
    candidatos = []
    for chave, alimento in alimentos_por_nome.items():
        # Separa o nome do alimento em tokens também
        chave_tokens = set(chave.split())
        # Verifica se TODOS os tokens da busca estão contidos nos tokens do alimento
        if all(any(tok_busca in tok_alimento for tok_alimento in chave_tokens) for tok_busca in tokens):
            # Também conta matches parciais onde o token está contido em um token maior
            pass  # fall through to add candidate
        else:
            # Verifica se cada token da busca é substring de algum lugar do nome completo
            if all(tok in chave for tok in tokens):
                candidatos.append((chave, alimento, len(chave)))
                continue
            continue

        candidatos.append((chave, alimento, len(chave)))

    # Fase 3: se houver múltiplos candidatos, retorna o mais curto (match mais específico)
    if candidatos:
        candidatos.sort(key=lambda x: x[2])  # ordena por tamanho do nome
        return candidatos[0][1]

    return None


def _montar_alimentos_por_nome(dados: Dict[str, List[Dict]]) -> Dict[str, Dict]:
    """
    Cria um dicionário com nome do alimento como chave para busca rápida.

    Args:
        dados: Dados completos do JSON de alimentos (já carregados)

    Returns:
        Dict com nome do alimento (lowercase) como chave
    """
    alimentos_por_nome = {}
    for categoria in dados["categorias"]:
        for alimento in categoria["alimentos"]:
            alimentos_por_nome[alimento["nome"].lower()] = {
                **alimento,
                "categoria": categoria["nome"],
            }
    return alimentos_por_nome


# Carrega o JSON uma única vez e reaproveita para ambas as estruturas
DADOS_ALIMENTOS = _carregar_alimentos()
ALIMENTOS_POR_NOME = _montar_alimentos_por_nome(DADOS_ALIMENTOS)


def _calcular_quantidade_para_macros(
    alimento: Dict, proteina_alvo: float, carb_alvo: float, gordura_alvo: float,
    num_alimentos_na_refeicao: int = 2
) -> float:
    """
    Calcula a quantidade ideal de um alimento em gramas para atingir as metas de macros.

    Usa o macronutriente mais denso do alimento como referência principal
    e divide pela quantidade de alimentos na refeição para distribuição equilibrada.

    Args:
        alimento: Dict com dados nutricionais do alimento (por 100g)
        proteina_alvo: Meta de proteína em gramas
        carb_alvo: Meta de carboidrato em gramas
        gordura_alvo: Meta de gordura em gramas
        num_alimentos_na_refeicao: Quantidade de alimentos nesta refeição

    Returns:
        Quantidade em gramas (entre 50 e 300)
    """
    proporcoes = []
    if alimento["proteina_g"] > 0:
        proporcoes.append(proteina_alvo / alimento["proteina_g"] * 100)
    if alimento["carboidrato_g"] > 0:
        proporcoes.append(carb_alvo / alimento["carboidrato_g"] * 100)
    if alimento["gordura_g"] > 0:
        proporcoes.append(gordura_alvo / alimento["gordura_g"] * 100)

    if not proporcoes:
        return 100

    # Usa a mediana das proporções para ser mais robusto que min ou max
    proporcoes_ordenadas = sorted(proporcoes)
    mediana = proporcoes_ordenadas[len(proporcoes_ordenadas) // 2]

    # Divide pelo número de alimentos na refeição para distribuir as metas
    quantidade = mediana / max(num_alimentos_na_refeicao, 1)
    quantidade = max(50, min(quantidade, 300))  # Entre 50g e 300g
    return round(quantidade, 1)


def _calcular_macros_por_porcao(alimento: Dict, quantidade_g: float) -> Dict:
    """
    Calcula os macros para uma porção específica de um alimento.

    Args:
        alimento: Dict com dados nutricionais (por 100g)
        quantidade_g: Quantidade em gramas

    Returns:
        Dict com macros calculados para a porção
    """
    fator = quantidade_g / 100
    return {
        "proteina_g": round(alimento["proteina_g"] * fator, 1),
        "carboidrato_g": round(alimento["carboidrato_g"] * fator, 1),
        "gordura_g": round(alimento["gordura_g"] * fator, 1),
        "calorias_kcal": round(alimento["calorias_kcal"] * fator, 1),
    }


def _sugerir_alimentos_complementares(
    alimentos_preferidos_encontrados: List[Dict],
    macros_necessarios: Dict[str, float],
    num_sugestoes: int = 3,
) -> List[Dict]:
    """
    Sugere alimentos do banco de dados para complementar a dieta.

    Args:
        alimentos_preferidos_encontrados: Alimentos preferidos que foram encontrados
        macros_necessarios: Metas de macros em gramas
        num_sugestoes: Número de sugestões a retornar

    Returns:
        Lista de alimentos sugeridos
    """
    # Categorias já contempladas pelos alimentos preferidos
    categorias_usadas = set(a.get("categoria", "") for a in alimentos_preferidos_encontrados)

    # Priorizar categorias não usadas ainda
    sugestoes = []
    for categoria in DADOS_ALIMENTOS["categorias"]:
        if categoria["nome"] in categorias_usadas:
            continue
        for alimento in categoria["alimentos"]:
            # Evitar duplicatas com preferidos
            if any(
                a["nome"].lower() == alimento["nome"].lower()
                for a in alimentos_preferidos_encontrados
            ):
                continue
            sugestoes.append({**alimento, "categoria": categoria["nome"]})

    # Embaralhar e pegar algumas sugestões
    random.shuffle(sugestoes)

    # Calcular score de adequação do alimento ao perfil de macros
    # Quanto menor a soma das diferenças normalizadas, mais adequado
    total_macros = (
        macros_necessarios["proteina_g"]
        + macros_necessarios["carboidrato_g"]
        + macros_necessarios["gordura_g"]
    )

    def _score_adequacao(alimento: Dict) -> float:
        """Calcula quão bem um alimento se adequa ao perfil de macros necessário."""
        macro_alimento = (
            alimento["proteina_g"]
            + alimento["carboidrato_g"]
            + alimento["gordura_g"]
        )
        if macro_alimento == 0:
            return float("inf")

        # Proporção de cada macro no alimento
        p_ali = alimento["proteina_g"] / macro_alimento
        c_ali = alimento["carboidrato_g"] / macro_alimento
        g_ali = alimento["gordura_g"] / macro_alimento

        # Proporção alvo de cada macro
        p_alvo = macros_necessarios["proteina_g"] / total_macros if total_macros > 0 else 0.33
        c_alvo = macros_necessarios["carboidrato_g"] / total_macros if total_macros > 0 else 0.33
        g_alvo = macros_necessarios["gordura_g"] / total_macros if total_macros > 0 else 0.34

        # Distância Euclidiana entre as proporções (menor = mais adequado)
        return ((p_ali - p_alvo) ** 2 + (c_ali - c_alvo) ** 2 + (g_ali - g_alvo) ** 2) ** 0.5

    # Ordenar por adequação ao perfil de macros
    sugestoes.sort(key=_score_adequacao)

    return sugestoes[:num_sugestoes]


def sugerir_alimentos(
    alimentos_preferidos: List[str],
    macros_necessarios: Dict[str, float],
) -> List[Dict]:
    """
    Função principal: combina alimentos preferidos com sugestões do banco de dados
    e monta refeições com quantidades.

    Args:
        alimentos_preferidos: Lista de nomes de alimentos preferidos
        macros_necessarios: Dict com proteina_g, carboidrato_g, gordura_g

    Returns:
        Lista de refeições com alimentos e quantidades
    """
    # 1. Buscar alimentos preferidos no banco de dados
    alimentos_encontrados = []
    alimentos_nao_encontrados = []

    for nome in alimentos_preferidos:
        alimento = _buscar_alimento_por_nome(nome, ALIMENTOS_POR_NOME)
        if alimento:
            alimentos_encontrados.append(alimento)
        else:
            alimentos_nao_encontrados.append(nome)

    # 2. Sugerir alimentos complementares
    sugestoes = _sugerir_alimentos_complementares(
        alimentos_encontrados, macros_necessarios
    )

    # 3. Combinar e distribuir em refeições
    todos_alimentos = alimentos_encontrados + sugestoes

    # 4. Calcular metas por refeição (dividir macros em 4 refeições)
    refeicoes_config = [
        {"nome": "Café da Manhã", "fracao": 0.2},
        {"nome": "Almoço", "fracao": 0.35},
        {"nome": "Lanche da Tarde", "fracao": 0.2},
        {"nome": "Jantar", "fracao": 0.25},
    ]

    refeicoes = []
    idx_alimento = 0

    for config in refeicoes_config:
        alimentos_refeicao = []
        meta_proteina = macros_necessarios["proteina_g"] * config["fracao"]
        meta_carb = macros_necessarios["carboidrato_g"] * config["fracao"]
        meta_gordura = macros_necessarios["gordura_g"] * config["fracao"]

        # Distribuir 1-2 alimentos por refeição
        num_alimentos = min(2, len(todos_alimentos) - idx_alimento)
        if num_alimentos <= 0:
            break

        for _ in range(num_alimentos):
            if idx_alimento >= len(todos_alimentos):
                break

            alimento = todos_alimentos[idx_alimento]
            idx_alimento += 1

            quantidade = _calcular_quantidade_para_macros(
                alimento, meta_proteina, meta_carb, meta_gordura,
                num_alimentos_na_refeicao=num_alimentos
            )
            macros_porcao = _calcular_macros_por_porcao(alimento, quantidade)

            alimentos_refeicao.append({
                "nome": alimento["nome"],
                "quantidade_g": quantidade,
                **macros_porcao,
            })

        refeicoes.append({
            "nome": config["nome"],
            "alimentos": alimentos_refeicao,
        })

    return refeicoes
