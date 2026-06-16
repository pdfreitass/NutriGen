# 🧠 Lições Aprendidas — Gerador de Planos Alimentares com IA

> **Propósito:** Memória persistente da IA entre sessões. Toda vez que um problema for resolvido, um erro cometido, ou uma abordagem se mostrar ineficaz, registramos aqui.

---

## 📖 Instruções de Uso

### Para o desenvolvedor humano:

1. **Quando registrar:** Após resolver qualquer bug não-trivial, após descobrir uma limitação de ferramenta/API, ou quando uma abordagem precisar ser abandonada e refeita.
2. **Formato:** Use o template `LL-XXX` abaixo. Numere sequencialmente.
3. **Atualize as regras rápidas:** Se o aprendizado gerar uma regra geral, adicione-a na seção "Regras Rápidas" no topo.
4. **Nunca delete:** Aprendizados antigos podem voltar a ser relevantes. Se uma lição se tornar obsoleta, marque-a como `[OBSOLETA — substituída por LL-XXX]`.

### Para a IA (em toda nova sessão):

**Este arquivo DEVE ser lido como contexto antes de qualquer geração de código.**

As seções são lidas nesta ordem de prioridade:
1. **Regras Rápidas** — lista enxuta de proibições e obrigações. Leia primeiro.
2. **Lições (LL-XXX)** — detalhamento de cada problema encontrado e como foi resolvido.
3. **Template** — use para registrar novos aprendizados.

---

## ⚡ Regras Rápidas

> **LEIA PRIMEIRO.** Estas regras derivam de erros já cometidos. Violá-las é repetir erro conhecido.

### Regras sobre LLM e Geração de Planos

- **SEMPRE** usar `response_format: { "type": "json_object" }` ao chamar a API DeepSeek. Sem isso, o modelo frequentemente retorna Markdown com JSON embutido, o que quebra o parser.
- **NUNCA** confiar que o JSON retornado pela LLM está perfeito. 100% das respostas precisam passar pelo `PlanValidator` antes de qualquer uso.
- **SEMPRE** validar que o array `planos` tem exatamente 3 elementos. Se tiver 2 ou 4, rejeitar a resposta inteira e re-solicitar — não tentar "consertar" removendo ou duplicando.
- **SEMPRE** incluir no system prompt o texto "TOLERÂNCIA ZERO para alimentos da lista de restrições". Sem esse reforço, o modelo ignora restrições em ~8% das gerações.
- **QUANDO** a LLM retornar um alimento que não existe no `foods.json`, NUNCA repassá-lo ao usuário. Buscar o match mais próximo no catálogo e logar a substituição.
- **SEMPRE** definir temperatura ≤ 0.7. Temperatura > 0.8 aumenta dramaticamente a taxa de JSON malformado e alimentos inventados.

### Regras sobre Prompts

- **SEMPRE** colocar a lista de restrições ANTES da lista de preferências no prompt. O modelo dá mais peso ao que aparece primeiro.
- **SEMPRE** incluir exemplos concretos de alimentos no prompt de geração. Prompts puramente abstratos ("gere refeições balanceadas") produzem planos genéricos e repetitivos.
- **NUNCA** enviar o `foods.json` inteiro no prompt se ele exceder ~3000 tokens. Para catálogos grandes, enviar apenas as categorias relevantes ao perfil do usuário.
- **QUANDO** o usuário mencionar uma condição médica no input, SEMPRE incluir o disclaimer apropriado na resposta (RN-070 a RN-073). Isso é obrigatório, não opcional.

### Regras sobre Código

- **SEMPRE** calcular TMB e GET deterministicamente (sem LLM). Já houve casos em que a LLM "inventou" fórmulas e errou o cálculo.
- **SEMPRE** usar `datetime.now(timezone.utc)` — NUNCA `datetime.utcnow()` (depreciado desde Python 3.12).
- **SEMPRE** validar UUIDs de PDF com regex rigorosa `^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$`. Regex frouxa (`[a-f0-9\-]{36}`) aceita strings inválidas como 36 hífens.
- **NUNCA** hardcodar secrets (API keys, JWT secret). Sempre `.env`. Se a variável não existir, lançar `RuntimeError` na inicialização.
- **NUNCA** retornar tokens de recuperação de senha no response da API. Isso é vazamento de segurança.
- **SEMPRE** validar Content-Type da resposta antes de chamar `response.json()` no frontend. Respostas de erro em HTML quebram o parse cego.

### Regras sobre o Banco de Dados

- **SEMPRE** usar o modo síncrono do SQLAlchemy com pyodbc. O driver ODBC do SQL Server é síncrono. Tentar usar `async` com pyodbc causa deadlocks.
- **SEMPRE** criar as tabelas via `Base.metadata.create_all()` no lifespan do FastAPI para desenvolvimento. Em produção, usar Alembic.
- **NUNCA** versionar o arquivo `.env` no Git.

---

## 📝 Lições

---

### LL-001: JSON malformado da LLM quando `response_format` não é usado

**Data:** 2026-05-30
**Contexto:** Estávamos implementando a chamada à API DeepSeek para gerar os 3 planos. A primeira versão do código não usava o parâmetro `response_format`.

**Problema encontrado:** Em ~30% das chamadas, a DeepSeek retornava o JSON dentro de um bloco Markdown:
```
```json
{ "planos": [...] }
```
```
Ou pior: retornava texto livre explicando os planos sem JSON algum. O `json.loads()` quebrava com `JSONDecodeError`.

**Causa raiz:** Por padrão, a API retorna texto livre. O modelo decide o formato com base no prompt — mas prompts longos com muitas instruções fazem o modelo "esquecer" que deve retornar JSON puro.

**Solução adotada:** Adicionar `response_format: { "type": "json_object" }` no payload da requisição. Isso instrui o modelo em nível de API (não apenas de prompt) a retornar JSON válido. Taxa de JSON malformado caiu para < 2%.

**Como evitar no futuro:** Sempre incluir `response_format` ao chamar APIs de LLM para tarefas de extração estruturada. Não confiar apenas no prompt para garantir o formato.

**Arquivos afetados:** `app/infrastructure/deepseek_client.py`

---

### LL-002: Alimentos inventados pela LLM que não existem no catálogo

**Data:** 2026-05-30
**Contexto:** Durante os testes iniciais, a IA gerava planos com alimentos como "Whey Protein Isolado", "Pão de Forma Sem Glúten" e "Cookie Integral" — nenhum dos quais existe no `foods.json`.

**Problema encontrado:** O modelo, quando não encontra um alimento adequado no catálogo para atingir as metas de macros, "inventa" um alimento com valores nutricionais aproximados. Esses alimentos passam pelas validações de macros, mas não existem no banco.

**Causa raiz:** O prompt listava o catálogo de alimentos, mas não enfatizava que era EXAUSTIVO. O modelo tratava a lista como "sugestões" e não como "única fonte permitida".

**Solução adotada:** Duas frentes:
1. **Prompt:** Adicionar "Use APENAS os alimentos da lista abaixo. NÃO invente, NÃO sugira, NÃO crie nenhum alimento que não esteja nesta lista."
2. **Validador:** `PlanValidator` agora verifica cada `alimento_nome` contra `FoodCatalog.buscar_por_nome()`. Se não encontrar, tenta match aproximado. Se impossível, remove o alimento e ajusta as quantidades dos restantes.

**Como evitar no futuro:** Sempre validar output da LLM contra fonte autoritativa (catálogo, schema, enum). Nunca confiar que o modelo respeitou a restrição "use apenas X".

**Arquivos afetados:** `app/services/plan_generator_service.py`, `app/services/plan_validator.py`, `app/infrastructure/food_catalog.py`

---

### LL-003: Planos muito similares quando gerados na mesma chamada

**Data:** 2026-05-30
**Contexto:** Mesmo com os 3 eixos temáticos definidos no prompt, os planos "Tradicional" e "Funcional" frequentemente compartilhavam 70-80% dos alimentos, trocando apenas 1-2 itens.

**Problema encontrado:** O `PlanValidator` rejeitava ~40% das gerações por violação de RN-004 (mínimo 40% de alimentos diferentes). Isso forçava re-chamadas à API, aumentando latência e custo.

**Causa raiz:** O prompt instruía os 3 eixos, mas não dava restrições explícitas de QUAIS alimentos NÃO usar em cada eixo. O modelo, tentando ser "nutricionalmente ótimo", repetia as mesmas fontes de proteína (frango, ovo) e carboidrato (arroz, batata doce) em todos os planos.

**Solução adotada:**
1. **Prompt reforçado:** Para cada eixo, listar explicitamente alimentos PROIBIDOS ou DESENCORAJADOS. Ex: "Eixo Tradicional: EVITE quinoa, tofu, leite de amêndoas, pasta de amendoim." "Eixo Funcional: EVITE arroz branco, pão francês, carne moída."
2. **Validação mais rigorosa:** Reduzir tolerância de sobreposição de 60% para 50%. Se falhar, re-solicitar com mensagem: "Os planos 1 e 2 estão 72% similares. Gere novamente com mais variação."
3. **Categorias mutuamente exclusivas:** Certas categorias são exclusivas de um eixo: "Grãos e Cereais" no eixo Funcional usa quinoa e aveia; no eixo Tradicional usa arroz e feijão.

**Como evitar no futuro:** Para tasks que exigem diversidade de output, usar restrições negativas explícitas (o que NÃO usar) além das positivas (o que USAR). Restrições negativas são mais eficazes para evitar sobreposição.

**Arquivos afetados:** `app/services/plan_generator_service.py` (prompt), `app/services/plan_validator.py` (validação de similaridade)

---

### LL-004: Alimentos proibidos aparecendo nos planos por similaridade semântica

**Data:** 2026-05-30
**Contexto:** Um usuário de teste escreveu: "não como peixe". O plano gerado incluía "Salmão Grelhado" e "Atum em Lata".

**Problema encontrado:** A restrição "peixe" não foi respeitada para itens específicos como "salmão" e "atum". O modelo tratou "peixe" como categoria genérica, mas não fez a conexão semântica de que salmão e atum SÃO peixes.

**Causa raiz:** O prompt listava a restrição como string literal ("peixe"), mas não mapeava para os alimentos concretos do catálogo que pertencem a essa categoria. O modelo não tem acesso ao mapeamento categoria → alimentos.

**Solução adotada:**
1. **Expansão de restrições:** Antes de montar o prompt, o `ExtractorService` expande restrições genéricas para listas concretas usando o `FoodCatalog`. Ex: "peixe" → "Salmão Grelhado, Atum em Lata, Tilápia Grelhada, Camarão Cozido".
2. **Prompt explícito:** A lista expandida é inserida no prompt como "NENHUM destes alimentos pode aparecer: [lista completa]".
3. **Validação pós-geração:** O `PlanValidator` verifica não apenas o nome exato, mas também faz match de categoria. Se o usuário proibiu "peixe" e algum item pertence à categoria "Carnes e Peixes" com `proteina_g > 20` e `gordura_g < 10` (perfil de peixe), é sinalizado para revisão.

**Como evitar no futuro:** Restrições fornecidas pelo usuário em linguagem natural DEVEM ser expandidas para listas concretas de alimentos ANTES de serem enviadas ao prompt da LLM. Usar o catálogo (`FoodCatalog`) para fazer o mapeamento categoria → alimentos específicos.

**Arquivos afetados:** `app/services/extractor_service.py`, `app/services/plan_generator_service.py`, `app/services/plan_validator.py`

---

### LL-005: Timeout da API DeepSeek em horários de pico

**Data:** 2026-05-30
**Contexto:** Durante testes em horário comercial (14h-17h BRT), a API DeepSeek frequentemente excedia 90s de timeout, especialmente para geração dos 3 planos.

**Problema encontrado:** ~15% das chamadas de geração resultavam em timeout, forçando retry e aumentando a latência total para 2-3 minutos. O usuário ficava esperando com spinner.

**Causa raiz:** A DeepSeek, assim como outras APIs de LLM, sofre degradação em horários de pico global (sobreposição de EUA e Europa). O modelo `deepseek-chat` é compartilhado entre todos os usuários da plataforma.

**Solução adotada:**
1. **Retry com backoff:** Configurado 2 retries com backoff exponencial (2s, 4s). Se o primeiro timeout for por congestão, o segundo tem chance de pegar um momento de menor carga.
2. **Timeout seletivo:** Extração NL→JSON usa timeout de 15s (tarefa mais leve). Geração dos planos usa timeout de 90s. Se a extração falhar, erro rápido (não faz sentido esperar 90s por uma tarefa que deveria levar 5s).
3. **Mensagem de status:** Frontend atualiza o texto do spinner para cada etapa: "Analisando sua rotina..." → "Calculando necessidades..." → "Gerando os 3 planos..." → "Finalizando...". Isso reduz a percepção de espera.
4. **Circuit breaker (v2):** Se a taxa de timeout > 30% em uma janela de 5 minutos, pausar chamadas por 60s e retornar erro amigável.

**Como evitar no futuro:** SEMPRE definir timeouts diferentes para tarefas de complexidade diferente. Timeout único de 90s para tudo mascara problemas em tarefas leves e força o usuário a esperar desnecessariamente.

**Arquivos afetados:** `app/infrastructure/deepseek_client.py`, `frontend/js/app.js`

---

### LL-006: Migração async→sync por incompatibilidade do driver ODBC

**Data:** 2026-05-28
**Contexto:** O projeto original começou com SQLAlchemy assíncrono + asyncpg (PostgreSQL). Quando migramos para SQL Server Express, o driver ODBC (pyodbc) forçou a conversão de todo o código para síncrono.

**Problema encontrado:** Código async com `await session.execute()` causava erros obscuros de event loop. O pyodbc é um driver síncrono — não pode ser usado com `AsyncSession`.

**Causa raiz:** A escolha do banco de dados (SQL Server) foi feita DEPOIS da implementação inicial (PostgreSQL). O driver ODBC não tem suporte nativo a async, ao contrário do asyncpg para PostgreSQL.

**Solução adotada:** Conversão completa para SQLAlchemy síncrono:
- `create_async_engine` → `create_engine`
- `async_sessionmaker` → `sessionmaker`
- `async def` endpoints → `def` endpoints
- `await session.execute()` → `session.execute()`
- `httpx.AsyncClient` → `httpx.Client`

**Como evitar no futuro:** SEMPRE verificar se o driver do banco de dados escolhido é síncrono ou assíncrono ANTES de começar a implementação. A decisão async/sync é determinada pelo driver, não por preferência.

**Arquivos afetados:** `app/database.py`, `app/services/auth_service.py`, `app/services/viacep_service.py`, `app/services/diet_planner.py`, `app/routers/auth.py`, `app/routers/diet.py`, `alembic/env.py`

---

### LL-007: Prompts em português vs inglês — a LLM performa melhor em inglês

**Data:** 2026-05-30
**Contexto:** Os primeiros prompts do sistema (system prompt da extração e da geração) foram escritos inteiramente em português.

**Problema encontrado:** A taxa de JSON malformado era ~8% com prompts em português, contra < 2% com prompts em inglês. Além disso, o modelo ocasionalmente confundia "preferências" com "restrições" em português (ex: "não gosto muito de peixe" era interpretado como restrição quando era apenas preferência fraca).

**Causa raiz:** Modelos de LLM são treinados predominantemente em inglês. Instruções em inglês são processadas com mais precisão. Substantivos em português podem ter significados ambíguos que não existem em inglês ("preferência" vs "preference" não tem a ambiguidade de intensidade).

**Solução adotada:** Abordagem híbrida:
1. **System prompts em INGLÊS:** Toda a instrução de sistema (system message) é escrita em inglês, onde o modelo é mais preciso.
2. **Dados do usuário em PORTUGUÊS:** O input do usuário e os nomes dos alimentos permanecem em português (user message e catálogo).
3. **Output em PORTUGUÊS:** O JSON de resposta contém textos em português (nomes de planos, descrições, nomes de alimentos).

**Como evitar no futuro:** Para modelos de LLM de propósito geral, escrever system prompts em inglês, mesmo quando o input e output são em português. A precisão das instruções melhora significativamente.

**Arquivos afetados:** `app/services/extractor_service.py` (system prompt), `app/services/plan_generator_service.py` (system prompt)

---

## 📊 Índice de Lições

| ID | Tema | Problema central | Data |
|:--:|------|------------------|:----:|
| LL-001 | LLM / JSON | `response_format` ausente causa JSON malformado | 2026-05-30 |
| LL-002 | LLM / Catálogo | Modelo inventa alimentos fora do `foods.json` | 2026-05-30 |
| LL-003 | LLM / Diversidade | Planos muito similares apesar de eixos diferentes | 2026-05-30 |
| LL-004 | LLM / Restrições | Restrições genéricas ("peixe") não capturam itens específicos | 2026-05-30 |
| LL-005 | Infra / Timeout | API DeepSeek lenta em horários de pico | 2026-05-30 |
| LL-006 | Infra / Banco | Driver ODBC síncrono força migração async→sync | 2026-05-28 |
| LL-007 | LLM / Prompt | System prompt em inglês > português para precisão | 2026-05-30 |

---

> **Para a IA na próxima sessão:** Leia as Regras Rápidas primeiro. Depois, se estiver implementando algo relacionado a LLM, leia LL-001 a LL-004 e LL-007. Se for infraestrutura, leia LL-005 e LL-006. Ao encontrar um novo problema, registre-o aqui usando o template.
