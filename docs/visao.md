# 🔭 Visão do Produto — Diet Plan Generator (v2 com IA)

> **Propósito:** Documento de visão em 5 perspectivas. Deve ser usado como contexto por uma IA para gerar código. Seja preciso e sem ambiguidades.

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

## 2. Visão de Engenharia

### Fluxo de alto nível

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. INPUT DO CLIENTE (texto livre, 3-5 frases)                    │
│    "Trabalho sentado, faço musculação 4x/semana..."              │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│ 2. EXTRAÇÃO ESTRUTURADA (IA — LLM)                               │
│    Converte linguagem natural → JSON estruturado:                │
│    {                                                             │
│      "perfil": { "sexo": "M", "idade": 28, "peso_kg": 72, ... },│
│      "rotina": { "atividade": "moderado", "objetivo": "ganho",…},│
│      "preferencias": ["frango", "batata doce", ...],             │
│      "restricoes": ["peixe"],                                    │
│      "extra": { "cafe_rapido": true }                            │
│    }                                                             │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│ 3. CÁLCULO NUTRICIONAL (algoritmo determinístico)                │
│    • TMB (Mifflin-St Jeor)                                       │
│    • GET (fator de atividade)                                    │
│    • Distribuição de macros por objetivo                         │
│    • Metas por refeição (4 refeições/dia)                        │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│ 4. GERAÇÃO DOS 3 PLANOS (IA — LLM)                               │
│    Gera 3 variações com eixos de diferenciação (ver abaixo)      │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│ 5. VALIDAÇÃO E PÓS-PROCESSAMENTO                                 │
│    • Verifica se alimentos existem no banco JSON                 │
│    • Corrige quantidades para ficarem entre 50g e 400g           │
│    • Garante que restrições são respeitadas                      │
│    • Gera explicação para cada plano                             │
└──────────────────────────┬───────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────┐
│ 6. PDF + RESPOSTA JSON                                           │
│    Retorna DietGenerateResponse com 3 planos + PDF               │
└──────────────────────────────────────────────────────────────────┘
```

### Componentes principais

| Componente | Tecnologia | Responsabilidade |
|------------|------------|------------------|
| **API Gateway** | FastAPI (existente) | Receber input, orquestrar fluxo, retornar resposta |
| **Extrator NL→JSON** | LLM (via API OpenAI / Anthropic / local) | Converter texto livre do cliente em struct `DietGenerateRequest` |
| **Calculadora Nutricional** | Python puro (existente) | TMB, GET, distribuição de macros — determinístico |
| **Gerador de Planos** | LLM (via API) | Gerar 3 variações de planos alimentares |
| **Validador** | Python puro | Verificar output do LLM contra `foods.json`, corrigir discrepâncias |
| **Banco de Alimentos** | `data/foods.json` (existente) | 68+ alimentos com tabela nutricional por 100g |
| **Gerador de PDF** | ReportLab (existente) | PDF profissional com os 3 planos |

### Como a IA processa o input do cliente

O **Extrator NL→JSON** recebe o texto livre e retorna um JSON com esta estrutura exata:

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
  "extra": {
    "refeicoes_rapidas": boolean,
    "orcamento_limitado": boolean,
    "observacoes": "string"
  }
}
```

**Regras de extração:**
- Se o cliente não especificar sexo, idade, peso ou altura → retornar erro pedindo os dados faltantes (não inferir)
- Se o nível de atividade for ambíguo → mapear para o mais próximo (ex: "treino 3x/semana" → moderado)
- Se o objetivo for ambíguo → perguntar (não inferir) ou inferir por contexto de peso
- Alimentos mencionados como preferidos vão para `preferencias`
- Alimentos explicitamente rejeitados (ex: "não como X", "detesto Y") vão para `restricoes`

### Como os 3 planos são diferenciados entre si

O **Gerador de Planos** recebe os macros calculados e o perfil do cliente, e gera 3 variações usando **3 eixos de diferenciação obrigatórios**:

| Eixo | Plano A | Plano B | Plano C |
|------|---------|---------|---------|
| **Nome** | "Tradicional Brasileiro" | "Funcional & Nutrientes" | "Prático & Rápido" |
| **Estilo culinário** | Arroz, feijão, proteína animal clássica, salada simples | Foco em alimentos funcionais: quinoa, batata doce, oleaginosas, vegetais variados | Refeições de preparo rápido: sanduíches, bowls, shakes, ovos |
| **Distribuição das refeições** | Café 20%, Almoço 35%, Lanche 15%, Jantar 30% | Café 25%, Almoço 30%, Lanche 20%, Jantar 25% | Café 15%, Almoço 30%, Lanche 25%, Jantar 30% |
| **Prioridade de alimentos** | Preferidos do cliente + complementos da culinária brasileira | 50% preferidos + 50% alimentos de alta densidade nutricional | Preferidos que exigem pouco preparo + complementos convenientes |
| **Complexidade** | Médio (cozimento simples) | Alto (variedade de ingredientes) | Baixo (mínimo preparo) |

**Regra fundamental:** Nenhum alimento da lista `restricoes` pode aparecer em qualquer plano. Se o cliente rejeitou peixe, peixe não aparece em A, B ou C.

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
| Planos retornados sem alimentos proibidos | 100% | Validação automática pós-geração |
| Usuários que baixam o PDF | > 60% dos que geram planos | Contagem de downloads |
| Usuários que retornam em 7 dias | > 25% | Analytics de retenção |

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

### Painéis de controle necessários

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

### Logs e auditorias importantes

| Evento | O que logar | Retenção |
|--------|-------------|----------|
| Requisição recebida | Timestamp, IP, texto original do cliente (sanitizado) | 30 dias |
| Extração NL→JSON | Texto original, JSON extraído, latência, tokens usados | 90 dias |
| Geração dos planos | Prompt enviado, resposta bruta do LLM, planos validados, tokens usados | 90 dias |
| Falha na validação | Plano rejeitado, motivo da rejeição, resposta original do LLM | 180 dias |
| Download de PDF | Plano ID, timestamp, IP | 30 dias |
| Erro 5xx | Stack trace completo, payload da requisição | 90 dias |

---

## 5. Fora do Escopo (v1)

### O que NÃO será implementado na versão inicial

| Item | Motivo | Quando considerar |
|------|--------|-------------------|
| **Chat multi-turno** (refinar plano conversando) | Complexidade de manter contexto e estado | v2 |
| **Integração com wearables** (Apple Watch, Garmin) | Dependência de APIs externas, OAuth | v3 |
| **Registro de refeições consumidas** (diário alimentar) | Escopo separado — é um produto diferente | Produto separado |
| **Compartilhamento social** dos planos | Não é core | v2 |
| **App mobile nativo** (iOS/Android) | O frontend web responsivo cobre o necessário | v3 |
| **Suporte a dietas médicas específicas** (renal, cetogênica terapêutica, pós-bariátrica) | Requer validação médica, risco regulatório | Avaliar com consultoria especializada |
| **Integração com delivery** (iFood, Rappi) | Dependência externa complexa | v3 |
| **Treinos de exercício** | Escopo diferente — é um produto separado de fitness | Produto separado |
| **Acompanhamento de peso e medidas ao longo do tempo** | Requer persistência de histórico, visualizações | v2 |
| **Recomendação de suplementos** | Risco regulatório (ANVISA) | Avaliar com jurídico |
| **Suporte multilíngue** (inglês, espanhol) | O mercado inicial é Brasil | v2 |
| **Pagamento / assinatura** | v1 será gratuito para validação do produto | v2 |

---

> **Para a IA que vai gerar código:** Este documento define O QUE construir. Consulte `docs/architecture.md` para COMO construir (stack, estrutura de pastas, padrões). Consulte `docs/Registros de decisão de arquitetura.md` para entender as escolhas já feitas.
