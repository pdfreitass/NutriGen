# 📋 Architecture Decision Records (ADR) — Gerador de Planos Alimentares

> **Propósito:** Registrar decisões arquiteturais significativas com contexto, alternativas consideradas e consequências. Este documento evita que decisões sejam questionadas ou revertidas sem novos fatos.
>
> **Convenção:** ADRs são numerados sequencialmente (`ADR-001`, `ADR-002`, ...). Um ADR nunca é deletado — se uma decisão for revertida, um novo ADR é criado com status "Substituído por ADR-XXX" e o original é mantido para registro histórico.
>
> **Status possíveis:**
> - ✅ **Aceito** — Decisão vigente e implementada
> - 🔄 **Em revisão** — Sendo reavaliada; novo ADR em breve
> - ❌ **Substituído** — Substituído por ADR mais recente (ver referência)
> - ⚠️ **Temporário** — Vale apenas para a fase atual (ex: desenvolvimento). Deve ser revisto antes de produção.

---

## Template de ADR

```
### ADR-XXX: [Título da decisão]

**Data:** YYYY-MM-DD
**Status:** Aceito / Em revisão / Substituído por ADR-XXX / Temporário

**Contexto:**
[2-4 frases descrevendo o problema que exigiu a decisão. Incluir restrições relevantes
(tecnológicas, prazo, orçamento, equipe).]

**Decisão:**
[1-2 frases com a decisão tomada. Clara e sem ambiguidade.]

**Alternativas consideradas:**
[2-4 alternativas avaliadas, com o motivo de descarte de cada uma.]

**Consequências:**
- Positivas: [benefícios diretos da decisão]
- Negativas: [trade-offs aceitos, riscos assumidos]
- Requisitos: [o que precisa ser feito por causa desta decisão]
```

---

## ADRs

---

### ADR-001: Usar LLM externo (API) ao invés de modelo próprio

**Data:** 2026-05-30
**Status:** ✅ Aceito

**Contexto:**
O sistema precisa interpretar linguagem natural do usuário (extrair perfil nutricional de texto livre) e gerar 3 planos alimentares personalizados. Ambas as tarefas exigem um modelo de linguagem com capacidade de compreensão de texto em português e geração estruturada. A decisão é entre hospedar um modelo próprio (ex: Llama 3, Mistral) ou consumir uma API externa (ex: DeepSeek, OpenAI, Claude).

**Decisão:**
Usar a **API DeepSeek** (modelo `deepseek-chat` / V4 Pro) como provedor externo de LLM. Não hospedar modelo próprio na v1.

**Alternativas consideradas:**

| Alternativa | Motivo do descarte |
|-------------|-------------------|
| **Modelo local (Ollama + Llama 3)** | Exige GPU com 8GB+ VRAM para performance aceitável. Aumenta complexidade operacional (gestão de processos, atualizações de modelo). Latência imprevisível em hardware consumer. |
| **OpenAI (GPT-4o)** | Custo por token ~3-5x maior que DeepSeek para qualidade similar. Latência maior em horários de pico. Vendor lock-in mais agressivo. |
| **Claude (Anthropic)** | Custo elevado. API menos madura para `response_format: json_object`. Latência superior à DeepSeek para tarefas estruturadas. |
| **Google Gemini** | Custo intermediário. Qualidade de geração em português inferior a DeepSeek/OpenAI em benchmarks internos. |
| **Modelo próprio fine-tuned** | Exige dataset de treino com centenas de planos validados — que não existe na fase inicial. Custo de treino e hospedagem proibitivo para MVP. |

**Consequências:**

- **Positivas:**
  - Zero custo de infraestrutura de GPU. Sistema roda integralmente em CPU.
  - Atualizações do modelo são transparentes (o provedor atualiza, não nós).
  - API OpenAI-compatible facilita troca futura de provedor (basta mudar `base_url` e `api_key`).
  - Custo por requisição ~R$ 0,02-0,05 por plano gerado.
- **Negativas:**
  - Dependência de conectividade com internet. Sem conexão = sem geração.
  - Latência de rede (200-500ms por chamada, além do tempo de inferência).
  - Custo variável com o uso. Se o produto escalar para 10k+ requisições/dia, custo se torna relevante.
  - Rate limits do provedor podem limitar picos de uso.
- **Requisitos:**
  - `DEEPSEEK_API_KEY` no `.env`.
  - Cliente HTTP com timeout, retry e circuit breaker.
  - Monitoramento de custo por requisição.
  - Plano de fallback para outro provedor se a DeepSeek ficar indisponível por período prolongado.

---

### ADR-002: Gerar os 3 planos em uma única chamada de API

**Data:** 2026-05-30
**Status:** ✅ Aceito

**Contexto:**
O sistema precisa gerar 3 planos alimentares distintos. Há duas abordagens possíveis: (A) uma única chamada à API LLM que retorna os 3 planos de uma vez, ou (B) três chamadas separadas, uma por plano, possivelmente em paralelo. A escolha impacta latência total, custo, e qualidade da diferenciação entre planos.

**Decisão:**
Gerar os **3 planos em uma única chamada** à API DeepSeek. O system prompt instrui o modelo a retornar um array JSON com exatamente 3 planos, cada um em um eixo de diferenciação distinto.

**Alternativas consideradas:**

| Alternativa | Motivo do descarte |
|-------------|-------------------|
| **3 chamadas paralelas** | Custo 3x maior (cada chamada reenvia o contexto completo). Diferenciação entre planos é mais difícil de garantir — cada chamada é independente e não sabe o que as outras geraram. Risco de 3 planos muito similares. |
| **1 chamada sequencial + contexto** | A 2ª chamada receberia o 1º plano como contexto, a 3ª receberia os 2 anteriores. Latência serial (15s + 30s + 30s = 75s). Custo 3x. Complexidade adicional de manter estado entre chamadas. |
| **1 chamada base + pós-processamento** | Gerar 1 plano e derivar variações via código. Variação seria superficial (trocar 1-2 alimentos). Não atende RN-002 (diferenciação estrutural). |

**Consequências:**

- **Positivas:**
  - Custo 1x (única chamada). Latência total menor (apenas o tempo de 1 inferência).
  - O modelo tem visão completa dos 3 planos durante a geração, podendo ativamente evitar sobreposição.
  - Resposta atômica: ou todos os planos vêm, ou nenhum. Sem estado intermediário para gerenciar.
  - Simplifica o contrato de resposta (1 JSON com array de 3 planos).
- **Negativas:**
  - Prompt mais longo (inclui regras para os 3 eixos), consumindo mais tokens de input.
  - Se a resposta for inválida, perde-se a geração inteira (não apenas 1 plano).
  - Token limit do modelo (~8K-32K) pode ser um gargalo para planos muito detalhados.
  - Timeout único de 90s para tudo — se a geração for lenta, timeout afeta os 3 planos.
- **Requisitos:**
  - `response_format: { "type": "json_object" }` na chamada da API para garantir JSON válido.
  - System prompt com instruções explícitas de diferenciação entre os 3 planos.
  - Validador pós-geração que verifica RN-004 (mínimo 40% de alimentos diferentes entre planos).
  - Se a validação falhar por similaridade excessiva, rejeitar a resposta inteira e re-solicitar.

---

### ADR-003: Resposta da IA em JSON estruturado vs texto livre

**Data:** 2026-05-30
**Status:** ✅ Aceito

**Contexto:**
A API LLM pode retornar os planos em dois formatos: (A) JSON estruturado com schema definido, ou (B) texto livre em Markdown/linguagem natural, que seria então parseado pelo backend. A escolha impacta a confiabilidade do parsing, a facilidade de validação, e a flexibilidade do output.

**Decisão:**
Exigir que a API DeepSeek retorne **JSON estruturado** usando o parâmetro `response_format: { "type": "json_object" }`. O JSON deve seguir um schema predefinido com `planos[]` contendo `nome`, `descricao`, `refeicoes[]`, e cada refeição com `alimentos[]` contendo `nome`, `quantidade_g`, `proteina_g`, `carboidrato_g`, `gordura_g`, `calorias_kcal`.

**Alternativas consideradas:**

| Alternativa | Motivo do descarte |
|-------------|-------------------|
| **Texto livre (Markdown)** | Parsing de texto livre é frágil. Variações de formatação ("**Café da manhã:**" vs "### Café da manhã") quebram o parser. Impossível garantir que todos os campos numéricos estão presentes e corretos sem pós-processamento complexo. |
| **JSON + fallback para texto** | Complexidade desnecessária. Se o JSON é o formato preferido, o fallback só seria usado quando o JSON falhasse — mas se o JSON falha, o texto provavelmente também teria problemas. |
| **Function calling / Tools** | OpenAI introduziu function calling; DeepSeek suporta parcialmente. Amarraria o código a um formato específico de provedor, dificultando a troca futura. `response_format: json_object` é mais portável entre provedores. |
| **Streaming (Server-Sent Events)** | Permite mostrar progresso ao usuário. Mas exige parsing incremental de JSON, que é complexo e frágil. A latência total atual (< 60s para o fluxo completo) não justifica a complexidade adicional na v1. |

**Consequências:**

- **Positivas:**
  - Parsing determinístico (`json.loads()`). Zero ambiguidade.
  - Validação automática com Pydantic — se um campo obrigatório faltar, o erro é claro.
  - Schema documentado (seção 6 do `arquitetura.md`) serve como contrato entre backend e IA.
  - Fácil versionar: se o schema mudar, o `model_validator` do Pydantic detecta.
  - Portável entre provedores (OpenAI, DeepSeek, e Claude suportam JSON mode).
- **Negativas:**
  - Menos flexibilidade: o modelo não pode adicionar campos extras espontaneamente (ex: dicas, observações).
  - Se o modelo gerar JSON malformado (ex: string não escapada), o parsing falha e toda a resposta é descartada.
  - A descrição dos planos (`descricao`) é o único campo de texto livre — limitado a 500 caracteres.
- **Requisitos:**
  - Schema Pydantic `DietGenerateResponse` que valida a estrutura completa do JSON.
  - `DeepSeekClient` com try/except para `json.JSONDecodeError`.
  - Log da resposta bruta quando o parsing falhar, para debug e melhoria do prompt.
  - Temperatura ≤ 0.7 para reduzir variabilidade que poderia quebrar o JSON.

---

### ADR-004: Persistir histórico de planos gerados

**Data:** 2026-05-30
**Status:** ✅ Aceito

**Contexto:**
Após gerar os planos, o sistema pode (A) retornar o resultado e descartá-lo (stateless), ou (B) persistir os planos em banco de dados, permitindo histórico, re-download de PDF, e análise de qualidade. A decisão impacta o modelo de dados, requisitos de armazenamento, e conformidade com LGPD.

**Decisão:**
**Persistir** os planos gerados no SQL Server Express. Cada geração cria um registro em `SessaoGeracao` com 3 `PlanoAlimentar` associados. O PDF é salvo em disco com UUID. Ambos têm política de expiração: PDF expira em 7 dias, planos em 30 dias. Usuários autenticados têm acesso ao histórico; anônimos recebem apenas o link temporário.

**Alternativas consideradas:**

| Alternativa | Motivo do descarte |
|-------------|-------------------|
| **Stateless (não persistir)** | Impede histórico, re-download, análise de qualidade, e feedback dos usuários. O produto ficaria "cego" quanto à qualidade dos planos gerados. |
| **Persistir apenas em cache (memória)** | Dados voláteis — perdidos ao reiniciar o servidor. Não escala horizontalmente. Inviável para histórico. |
| **Persistir em banco NoSQL** | Adicionaria mais uma tecnologia à stack. SQL Server Express já cobre o caso de uso com sobra. Consultas relacionais (planos de um usuário, data de geração) são triviais em SQL. |
| **Persistir sem expiração** | Acumularia dados indefinidamente. LGPD exige que o usuário possa solicitar exclusão. Dados antigos perdem valor analítico. |

**Consequências:**

- **Positivas:**
  - Usuário pode revisitar planos anteriores (histórico).
  - PDF pode ser baixado novamente dentro do prazo de 7 dias.
  - Feedbacks (👍/👎) podem ser associados a planos específicos, gerando dados para melhorar o produto.
  - Métricas de qualidade podem ser calculadas (taxa de rejeição, alimentos mais sugeridos, etc.).
  - Dados anonimizados podem ser usados para fine-tuning futuro do modelo.
- **Negativas:**
  - Complexidade adicional: mais tabelas, migrations, políticas de expiração.
  - Armazenamento cresce com o uso (embora 10GB do SQL Server Express suportem ~500k gerações).
  - Responsabilidade LGPD: exclusão de dados deve ser implementada (RN-123).
  - Backup do banco passa a ser necessário.
- **Requisitos:**
  - Job de limpeza (scheduler ou trigger) que remove `SessaoGeracao` com `data_geracao > 30 dias` e arquivos PDF com mais de 7 dias.
  - Endpoint `DELETE /api/diet/{id}` para exclusão manual pelo usuário (LGPD).
  - `GET /api/diet/history` para usuários autenticados.
  - Política de privacidade documentando o que é armazenado e por quanto tempo.

---

### ADR-005: Permitir uso sem cadastro (modo anônimo)

**Data:** 2026-05-30
**Status:** ✅ Aceito

**Contexto:**
O sistema pode exigir que o usuário crie uma conta antes de gerar planos (como a maioria dos SaaS), ou permitir que ele use o sistema anonimamente, sem cadastro. A decisão impacta a barreira de entrada, retenção de usuários, capacidade de enviar comunicações, e complexidade do backend.

**Decisão:**
**Permitir uso sem cadastro** (modo anônimo) como fluxo principal. O cadastro é opcional e oferecido como benefício adicional (histórico de planos, re-download de PDFs antigos). O sistema funciona 100% sem login.

**Alternativas consideradas:**

| Alternativa | Motivo do descarte |
|-------------|-------------------|
| **Cadastro obrigatório** | Barreira de entrada altíssima para um MVP. O usuário quer testar o produto imediatamente. Formulário de cadastro antes de ver valor = abandono > 80%. |
| **Login social obrigatório (Google/Facebook)** | Reduz fricção vs cadastro tradicional, mas ainda é uma barreira. Além disso, introduz dependência de APIs externas (OAuth) e complexidade de integração. |
| **Freemium com limite de usos** | Ex: "3 planos grátis, depois cadastre-se". Complexidade adicional de tracking de uso anônimo (por IP? Cookie?). Pode ser considerado na v2. |

**Consequências:**

- **Positivas:**
  - Barreira zero: usuário digita texto e recebe planos em < 60s, sem formulários.
  - Taxa de conversão (visitante → plano gerado) potencialmente muito maior.
  - Demonstra valor imediato — o usuário experimenta o produto antes de decidir se cadastrar.
  - Menos código na v1 (sem fluxo de e-mail de confirmação, sem recuperação de senha no MVP).
- **Negativas:**
  - Sem e-mail, não há canal de comunicação com o usuário (newsletter, pesquisa de satisfação, re-engajamento).
  - Usuário anônimo perde acesso ao histórico se fechar o navegador (sem login, sem recuperação).
  - Abuso: sem cadastro, um único IP pode gerar dezenas de planos. Rate limiting (RNF-022) mitiga isso.
  - Métricas de retenção são mais difíceis de medir sem identidade do usuário.
- **Requisitos:**
  - `usuario_id` como NULLABLE em `SessaoGeracao`.
  - Rate limiting por IP (10 req/min) para anônimos (RNF-022).
  - Link temporário para download do PDF (UUID, válido por 7 dias) como único meio de recuperar o plano para anônimos.
  - Call-to-action sutil após a geração: "Crie uma conta gratuita para salvar seus planos e acessar o histórico."
  - Cadastro implementado como `Should Have`, não como `Must Have` (ver `requisitos.md`).

---

### ADR-006: Estratégia de diferenciação dos 3 planos — eixos temáticos fixos

**Data:** 2026-05-30
**Status:** ✅ Aceito

**Contexto:**
O sistema gera 3 planos para a mesma rotina. Esses planos precisam ser genuinamente diferentes — não basta trocar 1-2 alimentos. Há várias estratégias possíveis para garantir essa diferenciação: eixos por custo, por objetivo nutricional, por complexidade de preparo, por distribuição de macros, ou eixos temáticos fixos. A escolha impacta a qualidade percebida pelo usuário, a complexidade do prompt, e a previsibilidade do resultado.

**Decisão:**
Usar **3 eixos temáticos fixos** como estratégia de diferenciação:
1. **Tradicional Brasileiro** — Arroz, feijão, proteínas clássicas, salada. Culinária caseira.
2. **Funcional & Nutrientes** — Quinoa, batata doce, oleaginosas, vegetais variados. Alta densidade nutricional.
3. **Prático & Rápido** — Refeições de preparo < 15 min: bowls, sanduíches, ovos, shakes.

Esses eixos são fixos — não variam por usuário, não são escolhidos pelo usuário, e não são aleatórios.

**Alternativas consideradas:**

| Alternativa | Motivo do descarte |
|-------------|-------------------|
| **Eixos por custo (Econômico / Médio / Premium)** | Preço de alimentos varia por região, época do ano e supermercado. Impossível calcular com precisão. "Premium" poderia sugerir alimentos caros e gerar percepção negativa ("esse sistema quer que eu gaste muito"). |
| **Eixos por objetivo nutricional (Low Carb / High Protein / Balanceado)** | O usuário já definiu seu objetivo (ex: ganho de massa). Gerar um plano "Low Carb" para alguém que quer ganhar massa é contraditório. Os 3 planos teriam objetivos conflitantes com a meta do usuário. |
| **Eixos por distribuição de macros** | Similar ao problema acima. Se o cálculo determinístico diz que a melhor distribuição para "ganho de massa" é 30/45/25, gerar planos com 40/30/30 e 20/55/25 seria nutricionalmente pior — e o usuário não saberia qual escolher. |
| **Eixos por horário (planos para manhã/tarde/noite)** | Não faz sentido — cada plano já cobre o dia inteiro com 4-6 refeições. |
| **Eixos aleatórios (deixar o modelo decidir)** | Resultados imprevisíveis. O modelo poderia gerar 3 planos muito similares com nomes diferentes, ou criar categorias sem sentido. Sem previsibilidade, a validação de diversidade fica mais difícil. |
| **Eixos escolhidos pelo usuário** | Adiciona complexidade à interface (mais um campo). O usuário quer resultado rápido, não tomar decisões sobre metodologia de diferenciação. |

**Consequências:**

- **Positivas:**
  - Resultado previsível e consistente entre diferentes usuários. Qualquer um que use o sistema recebe os mesmos 3 "sabores" de plano.
  - Fácil de explicar na interface: cada plano tem um nome e descrição clara do seu diferencial.
  - Fácil de validar: o `PlanValidator` verifica se o `eixo` declarado no JSON confere com o conteúdo (ex: "Tradicional Brasileiro" deve ter arroz e/ou feijão; "Prático & Rápido" deve ter alimentos de preparo rápido).
  - Cobre perfis complementares: o usuário pode escolher o plano que melhor se adapta ao seu estilo de vida naquela semana.
- **Negativas:**
  - Menos flexibilidade: todos os usuários veem os mesmos 3 eixos, independentemente do perfil.
  - Se o usuário tiver restrições que tornem um eixo inviável (ex: vegano não pode ter "Tradicional Brasileiro" com frango), o modelo precisa adaptar — o que pode diluir a diferenciação.
  - Pode não agradar usuários que esperam variação por outro critério (ex: "quero um plano para dia de treino e outro para dia de descanso").
- **Requisitos:**
  - System prompt da geração deve listar explicitamente os 3 eixos com descrições e exemplos de alimentos.
  - `PlanValidator` deve verificar RN-004 (≥ 40% alimentos diferentes entre planos) como métrica quantitativa de diversidade.
  - O campo `eixo` no modelo `PlanoAlimentar` (valores: `tradicional`, `funcional`, `pratico`) permite analytics: qual eixo é mais escolhido? Qual tem melhor feedback?
  - Na v2, considerar permitir que o usuário escolha quais 3 eixos (de um catálogo de 5-6) quer ver.

---

## Índice de ADRs

| ADR | Decisão | Status | Data |
|:---:|---------|:------:|:----:|
| ADR-001 | Usar API DeepSeek (LLM externo) ao invés de modelo próprio | ✅ Aceito | 2026-05-30 |
| ADR-002 | Gerar 3 planos em única chamada à API | ✅ Aceito | 2026-05-30 |
| ADR-003 | Resposta da IA em JSON estruturado | ✅ Aceito | 2026-05-30 |
| ADR-004 | Persistir histórico de planos no banco | ✅ Aceito | 2026-05-30 |
| ADR-005 | Permitir uso anônimo (sem cadastro) | ✅ Aceito | 2026-05-30 |
| ADR-006 | Diferenciação por eixos temáticos fixos | ✅ Aceito | 2026-05-30 |

---

> **Para a IA que vai gerar código:** Estas decisões são o "chão" da arquitetura. Código que contradiga um ADR vigente deve ser tratado como bug arquitetural. Se durante a implementação surgir um cenário não previsto que questione um ADR, não reverta a decisão unilateralmente — proponha um novo ADR com status "Em revisão".
