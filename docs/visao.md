# 🔭 Visão do Produto — NutriGen (Diet Plan Generator com IA)

> **Propósito:** Documento de visão canônica em 5 perspectivas + roadmap de especificações. Deve ser usado como contexto por uma IA para gerar código. Seja preciso e sem ambiguidades.
>
> **Última atualização:** 2026-06-04

---

## 0. Estrutura da Documentação e Roadmap

Antes de mergulhar nas 5 perspectivas da visão, este é o mapa completo da documentação do projeto. Todo arquivo listado aqui existe na pasta `docs/` e deve ser lido pela IA antes de gerar código.

### 0.1 Documentos de Referência

| Documento | Conteúdo | Quando consultar |
|-----------|----------|------------------|
| `visao.md` (este) | Visão do produto em 5 perspectivas + resumo do roadmap | **Sempre — leia primeiro** |
| `roadmap.md` | Fonte oficial de acompanhamento: 25 SPECs em 3 fases, progresso, backlog | Para saber o status atual do projeto |
| `requisitos.md` | 46 RFs + 26 RNFs com priorização MoSCoW | Para entender escopo e prioridades |
| `arquitetura.md` | Arquitetura em camadas, stack, modelo de dados, prompts | Para implementar qualquer código backend |
| `fluxos.md` | 5 fluxos completos (happy path, erros, restrições, visualização, regeneração) | Para implementar endpoints e lógica de frontend |
| `regras.md` | 59 regras de negócio (RN-001 a RN-142) | **Sempre — cada regra DEVE ser referenciada no código** |
| `ADR.md` | 6 decisões de arquitetura registradas (ADR-001 a ADR-006) | Para entender escolhas fundamentais já feitas |
| `licoes-aprendidas.md` | 7 lições aprendidas (LL-001 a LL-007) + regras rápidas | **Sempre — evite repetir erros conhecidos** |

### 0.2 Roadmap de Especificações (SPECs)

O projeto está organizado em **25 especificações** agrupadas em **5 famílias** (numeração de 10 em 10). Cada SPEC Principal (múltiplo de 10) define uma feature; subspecs (01-09) estendem a principal da família. Arquivos em `docs/specs/SPEC-0X0-nome.md`.

#### Fase 1 — MVP (13 specs em 3 famílias — ✅ Todas concluídas)

**Família 010 — Infraestrutura & Configuração**

| Spec | Nome | Status | Qualidade | Componente principal |
|:----:|------|:------:|:---------:|----------------------|
| SPEC-010 | **Principal:** Configuração do Cliente DeepSeek | ✅ | ⭐⭐⭐⭐ | `DeepSeekClient` — HTTP, retry, timeout |
| SPEC-011 | Subspec: Configuração de Ambiente e Segurança | ✅ | ⭐⭐⭐⭐ | `.env`, CORS, headers, rate limit config |
| SPEC-012 | Subspec: Catálogo de Alimentos (FoodCatalog) | ✅ | ⭐⭐⭐⭐⭐ | 68 alimentos, 8 categorias, busca por nome |
| SPEC-013 | Subspec: Logs e Observabilidade Básica | ✅ | ⭐⭐⭐ | JSON logs, `request_id`, 8 pontos de log |

**Família 020 — Pipeline de Processamento**

| Spec | Nome | Status | Qualidade | Componente principal |
|:----:|------|:------:|:---------:|----------------------|
| SPEC-020 | **Principal:** Extração NL→JSON | ✅ | ⭐⭐⭐⭐ | `ExtractorService` — texto livre → JSON |
| SPEC-021 | Subspec: Expansão de Restrições | ✅ | ⭐⭐⭐⭐ | `RestrictionExpander` — genérico → lista concreta |
| SPEC-022 | Subspec: Geração de Planos via IA | ✅ | ⭐⭐⭐⭐ | `PlanGeneratorService` — 3 planos em 1 chamada |
| SPEC-023 | Subspec: Pipeline de Validação | ✅ | ⭐⭐⭐⭐⭐ | `PlanValidator` — 6 fases determinísticas |
| SPEC-024 | Subspec: Orquestrador (UseCase) | ✅ | ⭐⭐⭐⭐ | `GerarPlanosUseCase` — fluxo completo |
| SPEC-025 | Subspec: Endpoint de Geração | ✅ | ⭐⭐⭐⭐ | `POST /generate` + rate limiting |
| SPEC-026 | Subspec: Tratamento de Erros | ✅ | ⭐⭐⭐ | Mensagens PT-BR, timeout, retry, fallback |

**Família 030 — Frontend**

| Spec | Nome | Status | Qualidade | Componente principal |
|:----:|------|:------:|:---------:|----------------------|
| SPEC-030 | **Principal:** Frontend — Página de Input | ✅ | ⭐⭐⭐ | Textarea, validação client-side, loading states |
| SPEC-031 | Subspec: Frontend — Tela de Resultados | ✅ | ⭐⭐⭐ | 3 colunas (desktop), accordion (mobile), PDF |

#### Fase 2 — Refina a Experiência (7 specs em 2 famílias — ⚪ Todas pendentes)

**Pré-requisito:** MVP (Fase 1) concluído e validado.

**Família 040 — Experiência do Usuário**

| Spec | Nome | Status | Qualidade | Depende de |
|:----:|------|:------:|:---------:|------------|
| SPEC-040 | **Principal:** Histórico de Gerações (autenticados) | ⚪ | ⬜⬜⬜⬜⬜ | MVP |
| SPEC-041 | Subspec: Sistema de Feedback (👍/👎) | ⚪ | ⬜⬜⬜⬜⬜ | MVP |
| SPEC-042 | Subspec: Regeneração Inteligente | ⚪ | ⬜⬜⬜⬜⬜ | MVP |
| SPEC-043 | Subspec: Métricas e Analytics | ⚪ | ⬜⬜⬜⬜⬜ | MVP |
| SPEC-044 | Subspec: Ajuste de Prompts por Feedback | ⚪ | ⬜⬜⬜⬜⬜ | SPEC-041 |
| SPEC-045 | Subspec: Rate Limiting Robusto | ⚪ | ⬜⬜⬜⬜⬜ | MVP |


**Família 060 — Seleção de Alimentos**

| Spec | Nome | Status | Qualidade | Depende de |
|:----:|------|:------:|:---------:|------------|
| SPEC-060 | **Principal:** Seleção de Alimentos + Geração Determinística | ⚪ | ⬜⬜⬜⬜⬜ | SPEC-020, SPEC-030 |

#### Fase 3 — Escala e Personalização (6 specs — ⚪ Todas pendentes)

**Pré-requisito:** Fase 2 concluída com > 70% de feedback positivo.

**Família 050 — Escala & Monetização**

| Spec | Nome | Status | Qualidade | Depende de |
|:----:|------|:------:|:---------:|------------|
| SPEC-050 | **Principal:** Dashboard Administrativo | ⚪ | ⬜⬜⬜⬜⬜ | Fase 2 |
| SPEC-051 | Subspec: Múltiplos Provedores de IA | ⚪ | ⬜⬜⬜⬜⬜ | Fase 2 |
| SPEC-052 | Subspec: Chat Multi-Turno | ⚪ | ⬜⬜⬜⬜⬜ | Fase 2 |
| SPEC-053 | Subspec: Exportação Avançada (PDF + CSV) | ⚪ | ⬜⬜⬜⬜⬜ | Fase 2 |
| SPEC-054 | Subspec: Perfis de Usuário Salvos | ⚪ | ⬜⬜⬜⬜⬜ | Fase 2 |
| SPEC-055 | Subspec: Assinatura e Monetização (Freemium) | ⚪ | ⬜⬜⬜⬜⬜ | Fase 2 |

> **Nota:** As SPECs usam numeração de 10 em 10 com famílias. Cada dezena (`010`, `020`...) é uma feature principal; números `01`-`09` são subspecs que estendem a principal. Novas SPECs seguem o próximo múltiplo de 10 disponível.

---

## 1. Visão do Cliente

### Dor que o cliente quer resolver

O cliente sente **sobrecarga de decisão** ao tentar montar uma dieta sozinho. Ele sabe o que gosta de comer e tem uma ideia vaga do seu objetivo, mas não sabe:

- Quantas calorias deve consumir por dia
- Como distribuir proteína, carboidrato e gordura entre as refeições
- Quais alimentos combinar para atingir os macros sem enjoar
- Como variar a dieta dentro da mesma rotina para manter adesão

Ele já tentou aplicativos de contagem de calorias, mas desistiu porque exigem **input manual de cada alimento** — um trabalho tedioso que não escala.

### O que ele espera ver ao usar o sistema

1. **Uma caixa de texto livre** onde ele descreve sua rotina com linguagem natural, sem formulários rígidos. Exemplo realista:

   > "Trabalho sentado o dia todo, mas faço musculação 4x por semana à noite. Quero ganhar massa muscular, tenho 1,75m, 72kg e 28 anos. Gosto de frango, batata doce, ovo, whey, banana e pasta de amendoim. Não como peixe. Meu café da manhã precisa ser rápido."

2. **3 planos alimentares diferentes**, todos válidos para a mesma rotina ou rotinas diferentes, apresentados lado a lado. Ele espera ver variação real — não o mesmo plano com um alimento trocado.


3. **Explicação simples** de cada plano: por que aquele plano foi sugerido, qual a lógica por trás da distribuição de macros, e como cada plano complementa os outros.

4. **PDF ou link compartilhável** para levar ao nutricionista ou salvar no celular.

### O que define sucesso para o cliente

| Critério de sucesso | Como medir |
|---------------------|------------|
| Zero fricção no input | O cliente digita 3-5 frases e recebe os planos em segundos |
| Variação perceptível | Os 3 planos são claramente diferentes em estrutura e alimentos de acordo com as rotinas informadas durante a semana |
| Refeições realistas | As quantidades e combinações fazem sentido no dia a dia brasileiro |
| Explicação compreensível | O cliente entende por que cada plano foi sugerido |
| Aderência à rotina descrita | Nenhum alimento que o cliente disse que não come aparece nos planos |

### Exemplos de inputs que o cliente pode dar

**Perfil 1 — Sedentário com desejo de emagrecer:**
> "Sou mulher, 34 anos, 1,62m, 78kg. Trabalho em home office, não faço exercício. Quero emagrecer. Gosto de salada, frango grelhado, arroz integral, ovo, iogurte e frutas. Não gosto de carne vermelha. Prefiro refeições leves à noite."

**Perfil 2 — Atleta amador:**
> "Homem, 25 anos, 1,80m, 85kg. Treino crossfit 5x por semana e corro aos sábados. Quero melhorar performance sem perder peso. Como de tudo, mas evito fritura. Preciso de bastante carbo antes do treino e proteína depois."

**Perfil 3 — Gestante:**
> "Grávida de 6 meses, 30 anos, 1,65m, 72kg. Médico pediu para ganhar peso de forma controlada. Caminho 30 min por dia. Gosto de comida caseira: arroz, feijão, carne moída, legumes cozidos, leite, frutas. Enjoo de comida muito temperada e peixe."

**Perfil 4 — Idoso com restrições:**
> "Homem, 68 anos, 1,70m, 80kg. Diabético tipo 2 controlado. Hidroginástica 3x por semana. Preciso controlar carboidrato e comer mais fibras. Gosto de peixe, frango, legumes, aveia, pão integral. Não posso comer doce nem refrigerante."

**Perfil 5 — Vegano:**
> "Mulher, 22 anos, 1,58m, 55kg. Vegana há 2 anos. Faço yoga 2x por semana. Quero manter o peso mas ganhar definição muscular. Como tofu, grão de bico, lentilha, quinoa, castanhas, frutas, vegetais. Não como nada de origem animal."

---


### Por que selecionar alimentos manualmente?

Diferente de descrever preferências em texto livre, a seleção manual de alimentos resolve 3 problemas críticos identificados no MVP:

1. **Realidade do usuário:** A IA frequentemente sugere alimentos que o usuário não conhece, não encontra no mercado ou não cabem no orçamento. Com a seleção manual, 100% dos alimentos do plano são familiares ao usuário.

2. **Zero alimentos inventados:** Elimina completamente o problema de a IA gerar alimentos fora do catálogo (LL-002). O usuário só vê o que ele mesmo selecionou.

3. **Controle de orçamento:** O usuário seleciona alimentos que cabem no bolso. Na v2, o campo  e preços permitirão meta de orçamento diário.

O fluxo de texto livre continua disponível como modo "Rápido", mas o modo "Completo" com seleção de alimentos é o recomendado para planos de longo prazo.


---

## 2. Visão de Engenharia

### Fluxo de alto nível

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. INPUT DO CLIENTE (texto livre, 3-5 frases)                    │
│    "Trabalho sentado, faço musculação 4x/semana..."              │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│ 2. EXTRAÇÃO ESTRUTURADA (IA — DeepSeek V4 Pro)                   │
│    Converte linguagem natural → JSON estruturado:                │
│    {                                                             │
│      "perfil": { "sexo": "M", "idade": 28, "peso_kg": 72, ... },│
│      "rotina": { "atividade": "moderado", "objetivo": "ganho",…},│
│      "preferencias": ["frango", "batata doce", ...],             │
│      "restricoes": ["peixe"],                                    │
│      "extra": { "cafe_rapido": true }                            │
│    }                                                             │
│    → Implementado em SPEC-020 (ExtractorService)                 │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│ 3. CÁLCULO NUTRICIONAL (algoritmo determinístico)                │
│    • TMB (Mifflin-St Jeor)                                       │
│    • GET (fator de atividade)                                    │
│    • Distribuição de macros por objetivo                         │
│    • Metas por refeição (4 refeições/dia)                        │
│    → Implementado no NutritionCalculator (sem IA)                │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│ 4. GERAÇÃO DOS 3 PLANOS (IA — DeepSeek V4 Pro)                   │
│    Gera 3 variações com eixos de diferenciação fixos             │
│    → Implementado em SPEC-022 (PlanGeneratorService)             │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│ 5. VALIDAÇÃO E PÓS-PROCESSAMENTO                                 │
│    • Verifica se alimentos existem no banco foods.json           │
│    • Corrige quantidades para ficarem entre 30g e 500g           │
│    • Garante que restrições são respeitadas (tolerância zero)    │
│    • Valida macros (±10%) e calorias (95-105% GET)               │
│    → Implementado em SPEC-023 (PlanValidator)                    │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│ 6. PDF + RESPOSTA JSON                                           │
│    Retorna DietGenerateResponse com 3 planos + link do PDF       │
│    → Implementado em SPEC-024 (Orquestrador) + SPEC-025 (Router) │
└──────────────────────────────────────────────────────────────────┘
```

### Componentes principais

| Componente | Tecnologia | Responsabilidade | Spec |
|------------|------------|------------------|:----:|
| **API Gateway** | FastAPI | Receber input, orquestrar fluxo, retornar resposta | SPEC-025 |
| **Extrator NL→JSON** | DeepSeek V4 Pro (API) | Converter texto livre do cliente em struct `PerfilExtraido` | SPEC-020 |
| **Calculadora Nutricional** | Python puro | TMB, GET, distribuição de macros — determinístico, offline | — |
| **Gerador de Planos** | DeepSeek V4 Pro (API) | Gerar 3 variações de planos alimentares em 1 chamada | SPEC-022 |
| **Validador** | Python puro | Verificar output do LLM contra `foods.json`, corrigir discrepâncias | SPEC-023 |
| **Expansor de Restrições** | Python puro | Converter restrições genéricas ("peixe") em lista concreta | SPEC-021 |
| **Banco de Alimentos** | `data/foods.json` | 68 alimentos em 8 categorias com tabela nutricional por 100g | SPEC-012 |
| **Gerador de PDF** | ReportLab | PDF profissional consolidado com os 3 planos + capa + disclaimer | — |
| **Orquestrador** | Python | Coordenar fluxo completo: extração → cálculo → geração → validação → persistência → PDF | SPEC-024 |

### Como a IA processa o input do cliente

O **Extrator NL→JSON** (SPEC-020) recebe o texto livre e retorna um JSON com esta estrutura exata:

```json
{
  "perfil": {
    "sexo": "masculino" | "feminino",
    "idade": number (1-120),
    "peso_kg": number,
    "altura_cm": number
  },
  "rotina": {
    "nivel_atividade": "sedentario" | "moderado" | "ativo",
    "objetivo": "perda_de_peso" | "manutencao" | "ganho_de_massa",
    "detalhes": "string com informações adicionais relevantes"
  },
  "preferencias": ["alimento1", "alimento2", ...],
  "restricoes": ["alimento_proibido1", ...],
  "condicoes": ["gravidez", "diabetes", "vegano", ...],
  "extra": {
    "refeicoes_rapidas": boolean,
    "orcamento_limitado": boolean,
    "observacoes": "string"
  }
}
```

**Regras de extração (RN-030 a RN-034, RN-040 a RN-043):**
- Se o cliente não especificar sexo, idade, peso ou altura → retornar erro pedindo os dados faltantes (não inferir)
- Se o nível de atividade for ambíguo → mapear para o mais próximo (ex: "treino 3x/semana" → moderado) e informar o usuário
- Se o objetivo for ambíguo → inferir por IMC (RN-032) e informar o usuário
- Alimentos mencionados como preferidos vão para `preferencias`
- Alimentos explicitamente rejeitados (ex: "não como X", "detesto Y") vão para `restricoes`
- Condições especiais detectadas vão para `condicoes` (SPEC-021 expande para lista concreta)

### Como os 3 planos são diferenciados entre si

O **Gerador de Planos** (SPEC-022) recebe os macros calculados e o perfil do cliente, e gera 3 variações usando **3 eixos de diferenciação obrigatórios** (ADR-006):

| Eixo | Plano A | Plano B | Plano C |
|------|---------|---------|---------|
| **Nome** | "Tradicional Brasileiro" | "Funcional & Nutrientes" | "Prático & Rápido" |
| **Estilo culinário** | Arroz, feijão, proteína animal clássica, salada simples | Foco em alimentos funcionais: quinoa, batata doce, oleaginosas, vegetais variados | Refeições de preparo rápido: sanduíches, bowls, shakes, ovos |
| **Distribuição das refeições** | Café 20%, Almoço 35%, Lanche 15%, Jantar 30% | Café 25%, Almoço 30%, Lanche 20%, Jantar 25% | Café 15%, Almoço 30%, Lanche 25%, Jantar 30% |
| **Prioridade de alimentos** | Preferidos do cliente + complementos da culinária brasileira | 50% preferidos + 50% alimentos de alta densidade nutricional | Preferidos que exigem pouco preparo + complementos convenientes |
| **Complexidade** | Médio (cozimento simples) | Alto (variedade de ingredientes) | Baixo (mínimo preparo) |

**Regra fundamental (RN-020):** Nenhum alimento da lista `restricoes` pode aparecer em qualquer plano. Se o cliente rejeitou peixe, peixe não aparece em A, B ou C. Tolerância: 0%.

**Regra de diversidade (RN-004):** Pelo menos 40% dos alimentos de cada plano devem ser diferentes dos outros dois. A sobreposição máxima permitida é de 60%. Validado pelo `PlanValidator` (SPEC-023).

---

## 3. Visão do Comprador (Produto/Negócio)

### Proposta de valor

> **"Descreva sua rotina em 3 frases. Receba 3 planos alimentares completos em segundos."**

O produto elimina a fricção de:
- Preencher formulários longos com dezenas de campos
- Calcular macros manualmente
- Montar cardápios do zero
- Contratar nutricionista apenas para plano inicial

### Diferenciais competitivos

| Concorrente | Limitação | Nosso diferencial |
|-------------|-----------|-------------------|
| Aplicativos de contagem (MyFitnessPal, FatSecret) | Input manual de cada alimento; não sugerem planos | Geração automática a partir de texto livre |
| Consulta com nutricionista | R$ 200-400/sessão; precisa agendar | Imediato, 24/7, custo marginal zero |
| Geradores de dieta por formulário | Rígidos, não entendem contexto ("grávida", "diabético") | IA entende contexto, restrições e nuances |
| ChatGPT genérico | Não tem banco de alimentos validado; macros podem estar errados | Cálculo determinístico + validação contra banco real |

### Métricas de sucesso do produto

| Métrica | Alvo (3 meses) | Como medir |
|---------|:-------------:|------------|
| Taxa de conversão (visitante → plano gerado) | > 40% | Eventos de analytics no frontend |
| Tempo médio até gerar 3 planos | < 30 segundos | Log de latência do endpoint `/generate` |
| Taxa de erro na extração NL→JSON | < 5% | Logs de falha com texto original |
| Planos retornados sem alimentos proibidos | 100% | Validação automática pós-geração (SPEC-023) |
| Usuários que baixam o PDF | > 60% dos que geram planos | Contagem de downloads |
| Usuários que retornam em 7 dias | > 25% | Analytics de retenção |
| Custo por plano gerado (DeepSeek) | < R$ 0,05 | Tokens consumidos × preço |

### Modelo de monetização (futuro — SPEC-055)

Na v1 (MVP), o sistema é **100% gratuito** para validação do produto. O modelo freemium está especificado na **SPEC-055** (Fase 3):

- **Plano Gratuito:** 5 gerações/mês, sem histórico, sem CSV
- **Plano Premium:** R$ 19,90/mês — ilimitado, histórico, CSV, múltiplos perfis
- **Plano Profissional:** R$ 49,90/mês — tudo + chat multi-turno, exportação avançada

---

## 4. Visão do Administrador

### O que monitorar

| Painel | Métricas | Alertas |
|--------|----------|---------|
| **Saúde da API** | Latência p50/p99, taxa de erro 5xx, uptime | Alerta se erro > 1% ou latência p99 > 10s |
| **Uso da LLM** | Tokens consumidos/dia, custo por requisição, taxa de falha da API externa | Alerta se custo diário > orçamento ou API externa fora do ar |
| **Qualidade dos planos** | % de planos que passam na validação, distribuição dos escores de qualidade | Alerta se taxa de rejeição > 10% |
| **Onboarding** | % de inputs que falham na extração (dados faltantes), motivos mais comuns de falha | Alerta se taxa de falha > 15% |
| **Negócio** | Planos gerados/dia, downloads de PDF, usuários ativos | — |

### Painéis de controle (implementados na Fase 3 — SPEC-050)

1. **Dashboard operacional** (tempo real):
   - Gráfico de requisições/minuto
   - Latência por etapa (extração → cálculo → geração → validação → PDF)
   - Status da API LLM externa (online/offline/lentidão)

2. **Dashboard de qualidade** (diário):
   - Top 10 alimentos mais sugeridos
   - Distribuição dos objetivos (perda/manutenção/ganho)
   - Exemplos de inputs que falharam na extração (para melhorar o prompt)

3. **Dashboard financeiro** (semanal):
   - Custo total com API LLM
   - Custo por plano gerado
   - Projeção de gastos

### Logs e auditorias (implementados no MVP — SPEC-013/SPEC-026)

| Evento | O que logar | Retenção |
|--------|-------------|----------|
| Requisição recebida | Timestamp, IP, texto original do cliente (sanitizado) | 30 dias |
| Extração NL→JSON | Texto original, JSON extraído, latência, tokens usados | 90 dias |
| Geração dos planos | Prompt enviado, resposta bruta do LLM, planos validados, tokens usados | 90 dias |
| Falha na validação | Plano rejeitado, motivo da rejeição, resposta original do LLM | 180 dias |
| Download de PDF | Plano ID, timestamp, IP | 30 dias |
| Erro 5xx | Stack trace completo, payload da requisição | 90 dias |

---

## 5. Roadmap e Fora do Escopo por Fase

### 5.1 Fase 1 — MVP (atual — Famílias SPEC-010, SPEC-020, SPEC-030 — 13 specs concluídas)

**O que está implementado:**
- Input em texto livre (linguagem natural)
- Extração NL→JSON via DeepSeek V4 Pro
- Cálculo nutricional determinístico (TMB, GET, macros)
- Geração de 3 planos com eixos temáticos fixos
- Validação pós-geração (6 fases: estrutural, restrições, catálogo, quantidades, nutricional, diversidade)
- Expansão de restrições genéricas para lista concreta
- PDF consolidado com os 3 planos
- Frontend responsivo (input + resultados)
- Tratamento de erros em português
- Logs estruturados em JSON com `request_id` (SPEC-013)
- Rate limiting básico (10 req/min para anônimos)
- Configuração via `.env`

### 5.2 O que NÃO está no MVP (mas está especificado para fases futuras)

| Item | Fase | Spec | Motivo |
|------|:---:|:----:|--------|
| **Histórico de planos** (autenticados) | Fase 2 | SPEC-040 | Requer auth completa + frontend de histórico |
| **Feedback 👍/👎 nos planos** | Fase 2 | SPEC-041 | Depende de MVP validado para ter volume de feedback |
| **Regeneração inteligente** (evitar alimentos da geração anterior) | Fase 2 | SPEC-042 | Requer estado entre sessões de geração |
| **Métricas e analytics** | Fase 2 | SPEC-043 | Requer volume de uso para ter significado |
| **Ajuste de prompts por feedback** | Fase 2 | SPEC-044 | Depende de SPEC-041 (feedback) |
| **Rate limiting robusto** (bloqueio, custo máximo diário) | Fase 2 | SPEC-045 | MVP usa rate limiting simples; versão robusta requer mais infra |
| **Dashboard administrativo** | Fase 3 | SPEC-050 | Requer Fase 2 concluída + volume de dados |
| **Múltiplos provedores de IA** (OpenAI, Claude) | Fase 3 | SPEC-051 | MVP usa só DeepSeek; abstração de provider é Fase 3 |
| **Chat multi-turno** (refinar plano conversando) | Fase 3 | SPEC-052 | Complexidade de manter contexto e estado entre turnos |
| **Exportação CSV + PDF melhorado** | Fase 3 | SPEC-053 | MVP tem PDF básico; versão avançada requer mais formatação |
| **Perfis de usuário salvos** (preferências, múltiplos perfis) | Fase 3 | SPEC-054 | Requer Fase 2 + autenticação completa |
| **Assinatura e monetização** (Freemium) | Fase 3 | SPEC-055 | MVP é gratuito para validação |

### 5.3 O que NÃO está em nenhuma spec (fora do roadmap atual)

| Item | Motivo |
|------|--------|
| **Integração com wearables** (Apple Watch, Garmin) | Dependência de APIs externas, OAuth. Fora do escopo atual. |
| **Registro de refeições consumidas** (diário alimentar) | Escopo separado — é um produto diferente. |
| **App mobile nativo** (iOS/Android) | O frontend web responsivo cobre o necessário. |
| **Dietas médicas específicas** (renal, cetogênica terapêutica, pós-bariátrica) | Requer validação médica, risco regulatório. |
| **Integração com delivery** (iFood, Rappi) | Dependência externa complexa. |
| **Treinos de exercício** | Escopo diferente — é um produto separado de fitness. |
| **Recomendação de suplementos** | Risco regulatório (ANVISA). |
| **Suporte multilíngue** (inglês, espanhol) | O mercado inicial é Brasil. |

---

> **Para a IA que vai gerar código:**
>
> 1. **Leia primeiro** a seção 0 (Estrutura da Documentação) para entender o mapa completo
> 2. Este documento (`visao.md`) define **O QUE** construir e **QUANDO** (roadmap)
> 3. Consulte `docs/roadmap.md` para o **status atualizado** de cada SPEC e progresso geral
> 4. Consulte `docs/arquitetura.md` para **COMO** construir (stack, camadas, modelos, prompts)
> 5. Consulte `docs/regras.md` para as **59 regras de negócio** (RN-001 a RN-142) — referencie os IDs no código
> 6. Consulte `docs/requisitos.md` para os **72 requisitos** (46 RF + 26 RNF) com priorização MoSCoW
> 7. Consulte `docs/fluxos.md` para a sequência exata de cada fluxo e tratamento de exceções
> 8. Consulte `docs/ADR.md` para as **6 decisões arquiteturais** já tomadas (não as contradiga)
> 9. Consulte `docs/licoes-aprendidas.md` para as **7 lições aprendidas** (não repita erros conhecidos)
> 10. Consulte `docs/specs/SPEC-XXX-*.md` para o detalhamento de cada feature específica
> 11. **Nunca** implemente specs de fases futuras sem que a fase anterior esteja concluída
