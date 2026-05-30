# SPEC-002: Catálogo de Alimentos (FoodCatalog)

**Status:** ✅ Concluído
**Fase:** 1 — MVP
**Data de conclusão:** 2026-05-30

---

## User Story

Como serviço de geração de planos, quero um catálogo de alimentos carregado em memória com busca por nome, categoria e valores nutricionais, para que os planos gerados usem apenas alimentos reais e validados.

---

## Critérios de Aceite

- [x] `FoodCatalog` implementado em `app/infrastructure/food_catalog.py`
- [x] Carrega `data/foods.json` em memória na inicialização do módulo
- [x] Método `buscar_por_nome(nome: str) → Alimento | None` com match por tokens (3 fases)
- [x] Método `buscar_por_categoria(categoria: str) → list[Alimento]`
- [x] Método `listar_todos() → list[Alimento]`
- [x] Método `expandir_restricao(restricao: str) → list[str]` — mapeia categoria genérica para lista de alimentos
- [x] Método `categorias_disponiveis() → list[str]`
- [x] `Alimento` como dataclass com: nome, categoria, proteina_g, carboidrato_g, gordura_g, calorias_kcal
- [x] Catálogo atual com 68 alimentos em 8 categorias

---

## Arquivos Implementados

| Arquivo | Descrição |
|---------|-----------|
| `app/models/food.py` | Dataclass `Alimento` (frozen, slots) + `macros_por_porcao(gramas)` |
| `app/infrastructure/food_catalog.py` | Classe `FoodCatalog` + singleton `food_catalog` |
| `app/infrastructure/__init__.py` | Exporta `FoodCatalog` e `food_catalog` |
| `data/foods.json` | Fonte autoritativa — 68 alimentos em 8 categorias |

---

## Algoritmo de Busca (3 fases)

1. **Match exato:** nome em lowercase bate direto no índice
2. **Match por tokens:** cada token da busca está contido no nome do alimento (ex: `"frango"` encontra `"Peito de Frango Grelhado"`)
3. **Desempate por especificidade:** entre múltiplos candidatos, retorna o nome mais curto (match mais específico)

---

## Mapeamento de Restrições (`expandir_restricao`)

| Restrição | Expansão |
|-----------|----------|
| `peixe` / `frutos do mar` | Salmão Grelhado, Atum em Lata (água), Tilápia Grelhada, Camarão Cozido |
| `carne vermelha` | Carne Moída Magra, Filé Mignon, Costela Bovina, Lombo Suíno |
| `glúten` | Pão Francês, Pão Integral, Macarrão Cozido |
| `laticínios` | Todos da categoria "Laticínios" (8 alimentos) |
| `vegetariano` / `ovolactovegetariano` | Todos da categoria "Carnes e Peixes" (12 alimentos) |
| `vegano` | Carnes e Peixes (12) + Laticínios (8) + Ovo Cozido + Ovo Mexido (22 total) |

---

## Notas Técnicas

- `FoodCatalog` é um singleton carregado uma vez no módulo (`food_catalog = FoodCatalog()`)
- A busca por nome usa o algoritmo documentado em `food_suggester.py`
- A expansão de restrições usa mapeamento fixo para restrições comuns e consulta dinâmica ao catálogo para categorias
- O arquivo `foods.json` continua como fonte autoritativa
- `Alimento` é frozen (imutável) e usa `__slots__` para eficiência de memória

## Categorias

1. Carnes e Peixes (12 alimentos)
2. Grãos e Cereais (10)
3. Leguminosas (6)
4. Laticínios (8)
5. Frutas (10)
6. Vegetais (10)
7. Gorduras e Oleaginosas (7)
8. Bebidas (5)
