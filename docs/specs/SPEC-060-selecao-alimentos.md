# SPEC-060: Seleção de Alimentos pelo Usuário + Geração Determinística

**Status:** ⚪ Pendente
**Fase:** 2
**Tipo:** Principal
**Depende de:** SPEC-020 (Extração), SPEC-030 (Frontend Input)
**Data de criação:** 2026-06-04

---

## 1. User Story

Como usuário, quero selecionar os alimentos que eu realmente como no dia a dia a partir de um catálogo organizado por categorias, para receber planos alimentares 100% baseados na minha realidade — sem alimentos que eu não conheço, não gosto ou não cabem no meu bolso.

---

## 2. Critérios de Aceite

### 2.1 Frontend — Tela de Seleção de Alimentos

- [ ] **SEL-01:** Nova tela "Selecionar Alimentos" aparece após o formulário de perfil (antes de gerar planos).
  - **Input:** Usuário já preencheu sexo, idade, peso, altura, nível de atividade.
  - **Output esperado:** Grid de categorias com checkboxes, barra de busca, contador de selecionados.
  - **Regras relacionadas:** RN-033
  - **RF relacionado:** Novo RF-073

- [ ] **SEL-02:** Alimentos organizados em 7 categorias: 🍗 Proteínas, 🍚 Carboidratos, 🥗 Legumes/Verduras, 🍌 Frutas, 🥛 Laticínios, 🥑 Gorduras, 🥤 Bebidas.
  - **Input:** `data/foods.json` (68 alimentos)
  - **Output esperado:** Cada categoria é um card expansível com ícone e contador de selecionados (ex: "Proteínas 🍗 (3/12 selecionados)").
  - **RF relacionado:** Novo RF-074

- [ ] **SEL-03:** Campo de busca por nome em tempo real (filtra enquanto digita).
  - **Input:** Texto de busca (mínimo 2 caracteres para ativar filtro).
  - **Output esperado:** Apenas alimentos cujo nome contém o termo são exibidos; categorias sem resultados são ocultadas.
  - **RF relacionado:** Novo RF-075

- [ ] **SEL-04:** Indicador de "Cesta" com resumo: total de alimentos selecionados, distribuição por categoria, alerta se faltar categoria essencial.
  - **Input:** Estado dos checkboxes.
  - **Output esperado:** Badge flutuante: "🛒 12 alimentos selecionados | ⚠️ Falta Proteína" (se nenhuma proteína selecionada).
  - **Regras relacionadas:** Nova RN-143
  - **RF relacionado:** Novo RF-076

- [ ] **SEL-05:** Mínimo de 5 alimentos selecionados para habilitar o botão "Gerar Planos".
  - **Input:** Estado dos checkboxes.
  - **Output esperado:** Botão desabilitado com tooltip "Selecione pelo menos 5 alimentos" até atingir o mínimo.
  - **Regras relacionadas:** Nova RN-144

### 2.2 Backend — Algoritmo de Distribuição

- [ ] **DIST-01:** `MealDistributor` em `app/services/distribuidor_refeicoes.py` recebe lista de alimentos + metas e gera 3 planos com 4-6 refeições cada.
  - **Input:** `list[AlimentoSelecionado]` (nome, qtd_max_dia_g opcional) + `MetasNutricionais` + `int` (número de planos = 3).
  - **Output esperado:** `PlanosGerados` com 3 planos, cada um com refeições e alimentos distribuídos.
  - **Regras relacionadas:** RN-001, RN-005, RN-010, RN-015
  - **RF relacionado:** Novo RF-077

- [ ] **DIST-02:** Distribuição calórica entre refeições segue os 3 eixos temáticos (ADR-006):
  - **Input:** GET calculado + eixo (tradicional/functional/pratico).
  - **Output esperado:**
    - Tradicional: Café 20%, Almoço 35%, Lanche 15%, Jantar 30%
    - Funcional: Café 25%, Almoço 30%, Lanche 20%, Jantar 25%
    - Prático: Café 15%, Almoço 30%, Lanche 25%, Jantar 30%
  - **Regras relacionadas:** RN-006

- [ ] **DIST-03:** Cada alimento selecionado aparece em pelo menos 1 dos 3 planos. Alimentos "preferidos" (marcados com ⭐ pelo usuário) aparecem em 2+ planos.
  - **Input:** Lista de alimentos com flag `preferido`.
  - **Output esperado:** Alimentos preferidos têm frequência >= 2 entre os 3 planos.
  - **RF relacionado:** Novo RF-078

- [ ] **DIST-04:** Quantidades ajustadas automaticamente para atingir metas de macros (±10%) e calorias (95-105% GET).
  - **Input:** Plano bruto com alimentos distribuídos.
  - **Output esperado:** Quantidades escaladas proporcionalmente até convergir nas metas (máx 3 iterações).
  - **Regras relacionadas:** RN-010, RN-015

- [ ] **DIST-05:** Variedade entre planos: no máximo 50% de sobreposição de alimentos entre qualquer par de planos. Alimentos "coringa" (arroz, feijão, ovo) podem repetir.
  - **Input:** 3 planos gerados.
  - **Output esperado:** Pelo menos 50% dos alimentos diferentes entre cada par.
  - **Regras relacionadas:** RN-004 (adaptado: 50% em vez de 40%)

### 2.3 IA — Montagem e Descrição (Opcional)

- [ ] **IA-01:** A IA (DeepSeek) é usada apenas para gerar nomes criativos e descrições dos planos, e sugerir combinações de alimentos por refeição. Não escolhe alimentos.
  - **Input:** Lista de alimentos já selecionados + distribuição de macros por refeição.
  - **Output esperado:** JSON com `nome`, `descricao` para cada plano + `alimentos` organizados por refeição.
  - **RF relacionado:** Novo RF-079

- [ ] **IA-02:** Se a IA estiver indisponível, fallback determinístico: nomes padrão ("Tradicional Brasileiro", etc.) e distribuição gulosa de alimentos por refeição.
  - **Input:** Sem IA disponível.
  - **Output esperado:** Planos gerados deterministicamente, sem chamada à API DeepSeek.
  - **RF relacionado:** Novo RNF-052

---

## 3. Contratos de Dados

### 3.1 Input — Seleção de Alimentos

```json
{
  "perfil": {
    "sexo": "masculino",
    "idade": 21,
    "peso_kg": 88.0,
    "altura_cm": 184,
    "nivel_atividade": "ativo",
    "objetivo": "perda_de_peso"
  },
  "alimentos_selecionados": [
    {"nome": "Peito de Frango Grelhado", "preferido": true, "qtd_max_dia_g": null},
    {"nome": "Arroz Branco Cozido", "preferido": false, "qtd_max_dia_g": 300},
    {"nome": "Batata Doce Cozida", "preferido": true, "qtd_max_dia_g": null},
    {"nome": "Ovo Cozido", "preferido": false, "qtd_max_dia_g": 4},
    {"nome": "Brócolis Cozido", "preferido": false, "qtd_max_dia_g": null},
    {"nome": "Banana", "preferido": false, "qtd_max_dia_g": null},
    {"nome": "Aveia em Flocos", "preferido": true, "qtd_max_dia_g": 100},
    {"nome": "Azeite de Oliva", "preferido": false, "qtd_max_dia_g": 30},
    {"nome": "Iogurte Natural", "preferido": false, "qtd_max_dia_g": null}
  ],
  "texto_rotina": "Treino crossfit 5x por semana, café da manhã rápido"
}
```

| Campo | Tipo | Obrigatório | Validação | Exemplo |
|-------|------|:----------:|-----------|---------|
| `perfil.sexo` | `string` | Sim | "masculino" ou "feminino" | `"masculino"` |
| `perfil.idade` | `int` | Sim | 1-120 | `21` |
| `perfil.peso_kg` | `float` | Sim | 20-500 | `88.0` |
| `perfil.altura_cm` | `float` | Sim | 50-280 | `184` |
| `perfil.nivel_atividade` | `string` | Sim | "sedentario"/"moderado"/"ativo" | `"ativo"` |
| `alimentos_selecionados` | `array` | Sim | min 5 itens | `[{...}]` |
| `alimentos_selecionados[].nome` | `string` | Sim | deve existir em foods.json | `"Peito de Frango Grelhado"` |
| `alimentos_selecionados[].preferido` | `bool` | Não | default false | `true` |
| `alimentos_selecionados[].qtd_max_dia_g` | `float/null` | Não | null = sem limite | `300` |
| `texto_rotina` | `string` | Não | 10-2000 chars | `"Treino crossfit..."` |

### 3.2 Output — Planos Gerados

Mesmo schema do `DietGenerateResponseV2` atual, sem alterações. A diferença é que os alimentos vêm 100% da lista selecionada pelo usuário.

### 3.3 Erros Possíveis

| HTTP | Código de erro | Gatilho | Mensagem (PT-BR) |
|:----:|---------------|---------|-------------------|
| 400 | `poucos_alimentos` | < 5 alimentos selecionados | "Selecione pelo menos 5 alimentos para gerar os planos." |
| 400 | `categoria_faltante` | Nenhuma proteína selecionada | "Inclua pelo menos 1 fonte de proteína (frango, ovo, carne, peixe...)." |
| 400 | `alimento_invalido` | Nome não existe no catálogo | "Alimento 'X' não encontrado no catálogo." |
| 422 | `validacao_pydantic` | Schema inválido | Detalhes automáticos do Pydantic. |
| 500 | `distribuicao_falha` | Algoritmo não convergiu | "Erro interno ao distribuir os alimentos. Tente com mais opções." |
| 502 | `ia_falha` | DeepSeek indisponível + fallback desligado | "IA temporariamente indisponível. Usando plano determinístico." |

---

## 4. Fluxo de Implementação

```
Passo 1 — Frontend: renderiza tela de seleção
  Recebe: foods.json (GET /api/foods/catalog)
  Faz: Exibe grid de categorias com checkboxes
  Retorna: Lista de alimentos selecionados + perfil

Passo 2 — POST /api/diet/generate-v2 (novo endpoint)
  Recebe: FoodSelectionRequest (perfil + alimentos + texto_rotina)
  Faz: Valida mínimo de 5 alimentos, categoria proteína obrigatória
  Retorna: 400 se inválido, ou prossegue

Passo 3 — NutritionCalculator.calcular()
  Recebe: Perfil (sexo, idade, peso, altura, atividade)
  Faz: TMB → GET → distribuição de macros por objetivo
  Retorna: MetasNutricionais

Passo 4 — MealDistributor.distribuir() (NOVO)
  Recebe: alimentos_selecionados + metas + eixos (3)
  Faz: 
    a) Para cada eixo, calcula meta calórica por refeição
    b) Distribui alimentos entre refeições priorizando preferidos
    c) Ajusta quantidades para atingir metas de macros (±10%)
    d) Garante variedade entre planos (≤50% sobreposição)
  Retorna: PlanosGerados (3 planos com alimentos e quantidades)
  Se falhar após 3 iterações: lança DistribuicaoFalhaError

Passo 5 — PlanValidator.validar() (existente, adaptado)
  Recebe: PlanosGerados + metas + restrições (vazias)
  Faz: Validação estrutural + quantidades + nutricional + diversidade
  Retorna: ValidationResult com planos corrigidos

Passo 6 — PDF + resposta (existente)
  Recebe: PlanosGerados validados
  Faz: Gera PDF consolidado com os 3 planos
  Retorna: DietGenerateResponseV2
```

### 4.1 Diagrama de Sequência

```
USUÁRIO → FRONTEND → /api/foods/catalog → foods.json
  │          │
  │ seleciona alimentos nas categorias
  │          │
  │──POST /api/diet/generate-v2──▶ ROUTER
  │                                 │
  │                           valida mínimo 5 alimentos
  │                           verifica proteína presente
  │                                 │
  │                           NutritionCalculator
  │                           TMB → GET → macros
  │                                 │
  │                           MealDistributor (NOVO)
  │                           distribui alimentos por refeição
  │                           ajusta quantidades → 3 planos
  │                                 │
  │                           PlanValidator (adaptado)
  │                           valida + corrige
  │                                 │
  │                           PDF Generator
  │                                 │
  │◀── JSON + pdf_url ──────────────│
  │
  ▼ exibe 3 planos + download PDF
```

---

## 5. Regras de Negócio Novas ou Modificadas

| ID | Regra | Tipo |
|----|-------|:----:|
| RN-143 | O sistema **DEVE** exigir pelo menos 1 alimento da categoria "Carnes e Peixes" ou "Ovos" ou "Laticínios" entre os selecionados (fonte de proteína obrigatória). | Nova |
| RN-144 | O sistema **DEVE** exigir no mínimo 5 alimentos selecionados para habilitar a geração. | Nova |
| RN-145 | O sistema **DEVE** oferecer fallback determinístico se a IA estiver indisponível, gerando planos sem chamada à API DeepSeek. | Nova |
| RN-004 | _(Modificada)_ Pelo menos 50% dos alimentos de cada plano **DEVEM** ser diferentes dos outros dois (era 40%). | Modificada |

---

## 6. Requisitos Atendidos

| ID | Requisito | Como esta SPEC atende |
|----|-----------|----------------------|
| RF-073 | Selecionar alimentos de um catálogo categorizado | Novo — UI de checkboxes por categoria |
| RF-074 | Categorias visuais com ícones e contagem | Novo — 7 categorias com cards expansíveis |
| RF-075 | Busca em tempo real por nome do alimento | Novo — Filtro com 2+ caracteres |
| RF-076 | Indicador de cesta com resumo e alertas | Novo — Badge flutuante |
| RF-077 | Algoritmo de distribuição de alimentos em refeições | Novo — `MealDistributor` |
| RF-078 | Alimentos preferidos aparecem em mais planos | Novo — Frequência >= 2 nos 3 planos |
| RF-079 | IA usada apenas para nomes/descrições (não escolhe alimentos) | Novo — Escopo reduzido da IA |
| RNF-052 | Fallback determinístico se DeepSeek offline | Novo — Planos gerados sem IA |

---

## 7. Arquivos Previstos

| Arquivo | Camada | Tipo | Descrição |
|---------|:------:|:----:|-----------|
| `frontend/js/selecao-alimentos.js` | Frontend | Novo | Lógica de UI da tela de seleção |
| `frontend/css/selecao-alimentos.css` | Frontend | Novo | Estilos da grade de categorias |
| `app/routers/alimentos.py` | API | Novo | `GET /api/foods/catalog` |
| `app/models/esquemas.py` | Domain | Modificado | Adicionar `FoodSelectionRequest`, `AlimentoSelecionado` |
| `app/services/distribuidor_refeicoes.py` | Application | Novo | `MealDistributor` — algoritmo de distribuição |
| `app/routers/dieta.py` | API | Modificado | Novo endpoint `POST /api/diet/generate-v2` |
| `frontend/index.html` | Frontend | Modificado | Nova seção `#page-select-foods` |
| `frontend/js/app.js` | Frontend | Modificado | Navegação para tela de seleção |

---

## 8. Notas Técnicas e Restrições

- **Performance:** Distribuição determinística < 100ms. Com IA para nomes/descrições, adicionar ~10s (1 chamada DeepSeek, não 2 como atualmente).
- **Segurança:** Validar que `alimentos_selecionados[].nome` existe em `foods.json` antes de processar. Rejeitar nomes injetados.
- **Compatibilidade:** Manter endpoint atual `POST /api/diet/generate` funcionando (modo texto livre legado). Novo endpoint é `/generate-v2`.
- **Premissas:** O catálogo `foods.json` continua sendo fonte autoritativa. O usuário seleciona apenas alimentos que existem no catálogo — sem digitação livre de nomes.
- **Decisões de design:**
  - **Checkboxes em vez de texto livre:** Evita o problema de matching de nomes que causa `correcoes=60` e alimentos removidos.
  - **Fallback determinístico:** Se DeepSeek offline, planos ainda são gerados. A IA é melhoria, não dependência.
  - **Orçamento:** Na v1, o campo `qtd_max_dia_g` permite limitar quantidades. Na v2, adicionar preço médio por alimento e meta de orçamento diário.
- **Referências:** SPEC-012 (FoodCatalog), SPEC-030 (Frontend Input), ADR-006 (Eixos temáticos)
