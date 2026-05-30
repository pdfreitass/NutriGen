# 🗺️ Roadmap — Gerador de Planos Alimentares com IA

> **Propósito:** Fonte oficial de acompanhamento do projeto. Toda feature nova, correção significativa ou melhoria estrutural passa por este documento antes de ser implementada.
>
> **Atualizado em:** 2026-05-30
>
> **Regra de ouro:** Uma SPEC só é marcada como `[x] Concluído` após validação explícita do desenvolvedor. A IA pode sugerir a marcação, mas nunca a executa unilateralmente.

---

## 📊 Resumo do Projeto

| Métrica | Valor |
|---------|:----:|
| Total de SPECs | **25** |
| Concluídas | **0** |
| Em andamento | **0** |
| Pendentes | **25** |
| Progresso Geral | **0%** |

```
Progresso: [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0%
```

### Distribuição por Fase

| Fase | SPECs | Status |
|------|:-----:|--------|
| **Fase 1 — MVP** (Funciona e entrega valor) | SPEC-001 a SPEC-013 (13) | 🔴 Pendente |
| **Fase 2 — Refina a Experiência** | SPEC-014 a SPEC-019 (6) | ⚪ Pendente |
| **Fase 3 — Escala e Personalização** | SPEC-020 a SPEC-025 (6) | ⚪ Pendente |
| **Backlog de Ideias** | 10 itens (sem SPEC) | 💡 Ideias |

---

## 🎯 MVP — Fase 1: Funciona e Entrega Valor

### Escopo

Versão mínima que um usuário real pode usar para: descrever sua rotina em linguagem natural, receber 3 planos alimentares distintos gerados por IA, visualizar os planos na tela, e baixar um PDF.

### Funcionalidades incluídas

- Input em linguagem natural (caixa de texto única)
- Extração automática de perfil, preferências e restrições via IA
- Cálculo determinístico de TMB, GET e macros
- Geração de 3 planos distintos via DeepSeek
- Validação pós-geração contra catálogo de alimentos
- Visualização lado a lado dos 3 planos (desktop) / accordion (mobile)
- PDF consolidado com todos os planos
- Uso anônimo (sem cadastro obrigatório)
- Tratamento de erros com mensagens em português

### Funcionalidades EXCLUÍDAS do MVP

- Cadastro e login de usuário (existente no código legado, mas não obrigatório para o fluxo principal)
- Histórico de gerações
- Feedback de planos
- Chat multi-turno
- Compartilhamento
- Dashboard administrativo
- Múltiplos provedores de IA
- Medidas caseiras nas quantidades

### Critério de conclusão do MVP

Um usuário consegue:
1. Acessar a URL do sistema
2. Digitar 3-5 frases descrevendo sua rotina
3. Clicar em "Gerar Planos"
4. Ver 3 planos diferentes em menos de 60 segundos
5. Baixar um PDF com os planos

### Estimativa

~3-4 semanas para um desenvolvedor full-time, considerando que a base do projeto (FastAPI, SQLAlchemy, estrutura de pastas) já existe.

---

## SPECs do MVP

---

### SPEC-001: Configuração do Cliente DeepSeek

**Status:** [ ] Não iniciado

**User Story:** Como desenvolvedor, quero um cliente HTTP tipado para a API DeepSeek, para que os serviços de extração e geração possam chamar a IA sem repetir código de conexão.

**Critérios de Aceite:**
- [ ] `DeepSeekClient` implementado em `app/infrastructure/deepseek_client.py`
- [ ] Suporta `chat_completion(messages, temperature, response_format, timeout)` como método principal
- [ ] Lê `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL` do `.env`
- [ ] Timeout configurável por chamada (default extração: 15s, default geração: 90s)
- [ ] Retry com backoff exponencial: 2 tentativas, intervalo 2s e 4s
- [ ] Lança `DeepSeekUnavailableException` se API offline após retries
- [ ] Lança `DeepSeekInvalidResponseException` se JSON de resposta inválido
- [ ] Loga latência de cada chamada (método `log_latency`)
- [ ] Erro na inicialização se `DEEPSEEK_API_KEY` não configurada (RuntimeError)

**Arquivos previstos:**
- `app/infrastructure/__init__.py`
- `app/infrastructure/deepseek_client.py`
- `app/exceptions.py` (ou `app/infrastructure/exceptions.py`)
- `.env` (atualizar com variáveis DeepSeek)

**Notas Técnicas:**
- Usar `httpx.Client` (síncrono, compatível com o resto do stack)
- A API DeepSeek é OpenAI-compatible: endpoint `{base_url}/chat/completions`
- Header: `Authorization: Bearer {DEEPSEEK_API_KEY}`
- Payload: `{ "model": "...", "messages": [...], "temperature": 0.7, "response_format": {"type": "json_object"} }`
- O campo `response_format` é obrigatório para geração; opcional para extração (LL-001)
- A classe deve ser stateless — pode ser instanciada uma vez e reusada

---

### SPEC-002: Catálogo de Alimentos (FoodCatalog)

**Status:** [ ] Não iniciado

**User Story:** Como serviço de geração de planos, quero um catálogo de alimentos carregado em memória com busca por nome, categoria e valores nutricionais, para que os planos gerados usem apenas alimentos reais e validados.

**Critérios de Aceite:**
- [ ] `FoodCatalog` implementado em `app/infrastructure/food_catalog.py`
- [ ] Carrega `data/foods.json` em memória na inicialização do módulo
- [ ] Método `buscar_por_nome(nome: str) → Alimento | None` com match por tokens (LL-002)
- [ ] Método `buscar_por_categoria(categoria: str) → list[Alimento]`
- [ ] Método `listar_todos() → list[Alimento]`
- [ ] Método `expandir_restricao(restricao: str) → list[str]` — mapeia categoria genérica para lista de alimentos (LL-004)
- [ ] Método `categorias_disponiveis() → list[str]`
- [ ] `Alimento` como dataclass com: nome, categoria, proteina_g, carboidrato_g, gordura_g, calorias_kcal
- [ ] Catálogo atual com 68 alimentos em 8 categorias

**Arquivos previstos:**
- `app/infrastructure/food_catalog.py`
- `app/domain/entities.py` (ou `app/models/food.py` para `Alimento` dataclass)

**Notas Técnicas:**
- O `FoodCatalog` é um singleton carregado uma vez no módulo
- A busca por nome usa o algoritmo de 3 fases documentado em `food_suggester.py` (match exato → match por tokens → preferência pelo mais curto)
- A expansão de restrições usa mapeamento fixo: "peixe" → ["Salmão Grelhado", "Atum em Lata", "Tilápia Grelhada", "Camarão Cozido"], "laticínios" → ["Leite Integral", "Queijo Mussarela", "Iogurte Natural", ...], "carne vermelha" → ["Carne Moída Magra", "Filé Mignon", "Costela Bovina", "Lombo Suíno"], "glúten" → ["Pão Francês", "Pão Integral", "Macarrão Cozido"]
- O arquivo `foods.json` existente em `data/foods.json` continua como fonte autoritativa

---

### SPEC-003: Serviço de Extração NL→JSON

**Status:** [ ] Não iniciado

**User Story:** Como sistema, quero converter o texto livre do usuário em um JSON estruturado com perfil, preferências e restrições, para que as etapas seguintes possam operar sobre dados tipados.

**Critérios de Aceite:**
- [ ] `ExtractorService` implementado em `app/services/extractor_service.py`
- [ ] Método `extrair(texto: str) → PerfilExtraido`
- [ ] Usa `DeepSeekClient` com system prompt de extração (inglês — LL-007)
- [ ] Timeout: 15 segundos. Retry: 1 tentativa
- [ ] `PerfilExtraido` como Pydantic model com campos: `perfil` (sexo, idade, peso_kg, altura_cm), `rotina` (nivel_atividade, objetivo, detalhes), `preferencias`, `restricoes`, `condicoes`, `extra`
- [ ] Lança `CamposObrigatoriosAusentesException` se sexo/idade/peso/altura faltarem, listando quais campos faltam
- [ ] Se `nivel_atividade` for null → assume "sedentario" (RN-031)
- [ ] Se `objetivo` for null → calcula IMC e infere objetivo (RN-032)
- [ ] Separa `preferencias` de `restricoes` corretamente (RN-014)
- [ ] Detecta condições especiais: "gravidez", "diabetes", "hipertensao", "vegano", "vegetariano", "intolerancia_lactose" (RF-015)
- [ ] Valida intervalos fisiológicos: idade 1-120, peso 20-500, altura 50-280 (RN-041)
- [ ] Loga latência da extração e tokens consumidos

**Arquivos previstos:**
- `app/services/extractor_service.py`
- `app/models/schemas.py` (atualizar com `PerfilExtraido`)

**Notas Técnicas:**
- System prompt em INGLÊS (melhor precisão do modelo — LL-007), user prompt é o texto original do usuário em português
- `response_format: { "type": "json_object" }` obrigatório (LL-001)
- Temperatura: 0.3 (extração deve ser determinística)
- O schema do JSON de resposta está documentado em `arquitetura.md` seção 6
- Campos não encontrados devem vir como `null`, não como string vazia — a validação de campos obrigatórios rejeita `null`

---

### SPEC-004: Serviço de Geração de Planos via IA

**Status:** [ ] Não iniciado

**User Story:** Como sistema, quero enviar os dados estruturados do usuário + metas nutricionais para a IA e receber 3 planos alimentares completos em JSON, para que o usuário visualize opções variadas.

**Critérios de Aceite:**
- [ ] `PlanGeneratorService` implementado em `app/services/plan_generator_service.py`
- [ ] Método `gerar(perfil: PerfilExtraido, metas: MetasNutricionais) → PlanosGerados`
- [ ] Usa `DeepSeekClient` com system prompt de geração (inglês) + dados do usuário (português)
- [ ] System prompt inclui: 3 eixos fixos, restrições expandidas (ANTES das preferências), catálogo de alimentos relevantes, metas de macros ±10%
- [ ] `MetasNutricionais` como dataclass: tmb, get_calorico, proteina_g, carboidrato_g, gordura_g
- [ ] `PlanosGerados` como Pydantic model contendo `list[PlanoGerado]` com exatamente 3 elementos
- [ ] `PlanoGerado` contém: nome, eixo, descricao, refeicoes (lista de `RefeicaoGerada`), cada uma com alimentos (`ItemGerado`)
- [ ] Timeout: 90 segundos. Retry: 2 tentativas com backoff (2s, 4s)
- [ ] Temperatura: 0.7
- [ ] `response_format: { "type": "json_object" }` (LL-001)
- [ ] Loga latência e tokens consumidos

**Arquivos previstos:**
- `app/services/plan_generator_service.py`
- `app/models/schemas.py` (atualizar com `PlanosGerados`, `PlanoGerado`, `RefeicaoGerada`, `ItemGerado`)

**Notas Técnicas:**
- O system prompt DEVE incluir a frase "TOLERÂNCIA ZERO para alimentos da lista de restrições" (LL-002)
- A lista de restrições deve vir ANTES das preferências no prompt (LL-003 — ordem importa)
- O catálogo enviado no prompt deve ser limitado a ~3000 tokens. Se o catálogo completo exceder, selecionar apenas categorias relevantes (ex: vegano → pular "Carnes e Peixes" e "Laticínios")
- O contrato completo do JSON de resposta está na seção 6 do `arquitetura.md`

---

### SPEC-005: Pipeline de Validação Pós-Geração (PlanValidator)

**Status:** [ ] Não iniciado

**User Story:** Como sistema, quero validar e corrigir automaticamente os planos gerados pela IA antes de mostrá-los ao usuário, para garantir que estejam nutricionalmente corretos, não contenham alimentos proibidos, e sejam realmente diferentes entre si.

**Critérios de Aceite:**
- [ ] `PlanValidator` implementado em `app/services/plan_validator.py`
- [ ] Método `validar(planos: PlanosGerados, metas: MetasNutricionais, restricoes: list[str], catalogo: FoodCatalog) → ValidationResult`
- [ ] `ValidationResult` contém: `planos_corrigidos`, `correcoes_aplicadas` (lista de strings), `aprovado` (bool)
- [ ] Validações executadas em sequência (ordem fixa):

  **Fase 1 — Estrutural:**
  - [ ] RN-001: `planos` tem exatamente 3 elementos (rejeitar se ≠ 3)
  - [ ] RN-005: Cada plano tem 4-6 refeições (remover excedentes, adicionar refeição vazia com warning se < 4)

  **Fase 2 — Restrições (TOLERÂNCIA ZERO):**
  - [ ] RN-020: Nenhum alimento da lista de `restricoes` aparece. Se aparecer → remover e substituir por similar da mesma categoria
  - [ ] RN-021: Se alergia detectada → adicionar flag de aviso na resposta

  **Fase 3 — Catálogo:**
  - [ ] LL-002: Todo alimento existe no `FoodCatalog`. Se não → buscar match mais próximo. Se impossível → remover

  **Fase 4 — Quantidades:**
  - [ ] RN-014: Toda quantidade entre 30g e 500g. Fora → clampar

  **Fase 5 — Nutricional:**
  - [ ] RN-010: Cada macro individual dentro de ±10% do calculado. Fora → ajustar quantidades proporcionalmente
  - [ ] RN-015: Soma calórica entre 95% e 105% do GET. Fora → ajustar quantidades

  **Fase 6 — Diversidade:**
  - [ ] RN-004: Máximo 60% de sobreposição de alimentos entre qualquer par de planos. Se exceder → rejeitar planos e sinalizar para re-solicitação

- [ ] Se `aprovado == False` → `PlanGeneratorService` é chamado novamente (máximo 1 re-tentativa) com mensagem de erro específica no prompt
- [ ] Loga toda correção aplicada com detalhes (alimento X substituído por Y, quantidade ajustada de A para B)

**Arquivos previstos:**
- `app/services/plan_validator.py`

**Notas Técnicas:**
- A validação é 100% determinística (sem IA). Roda em < 50ms para 3 planos.
- Correções automáticas são preferíveis a rejeições — só rejeitar se impossível corrigir
- Se a re-tentativa também falhar → lançar `PlanValidationException` que o endpoint trata como 502
- As correções aplicadas são incluídas no log mas NÃO são mostradas ao usuário (ele vê apenas o resultado final corrigido)
- A ordem das validações é importante: restrições primeiro (segurança), estrutura depois (consistência), nutricional por último (ajuste fino)

---

### SPEC-006: Atualização do Orquestrador (DietPlannerUseCase)

**Status:** [ ] Não iniciado

**User Story:** Como sistema, quero um orquestrador que coordene o fluxo completo (extração → cálculo → geração → validação → persistência → PDF) de forma coesa e com tratamento de erros em cada etapa.

**Critérios de Aceite:**
- [ ] `DietPlannerUseCase` (ou `GerarPlanosUseCase`) implementado em `app/use_cases/gerar_planos.py`
- [ ] Método `executar(texto: str) → DietGenerateResponse`
- [ ] Fluxo orquestrado na ordem exata (Fluxo 1 do `fluxos.md`):
  1. `ExtractorService.extrair(texto)` → `PerfilExtraido`
  2. `NutritionCalculator.calcular(perfil)` → `MetasNutricionais` (usa TMB/GET/macros existentes)
  3. `PlanGeneratorService.gerar(perfil, metas)` → `PlanosGerados`
  4. `PlanValidator.validar(planos, metas, restricoes, catalogo)` → `ValidationResult`
  5. Se `aprovado == False` → voltar ao passo 3 (máximo 1x)
  6. `SessaoGeracaoRepository.salvar(sessao, planos)` → persistência
  7. `PdfGeneratorService.gerar(response)` → UUID do PDF
  8. Montar e retornar `DietGenerateResponse`
- [ ] Cada etapa tem try/except individual com exceção específica
- [ ] Logs em cada etapa com `request_id` para correlação
- [ ] Se DeepSeek falhar na extração → 503 (não tenta geração)
- [ ] Se DeepSeek falhar na geração → 503 após retries
- [ ] Se validação falhar 2x → 502
- [ ] Se banco falhar → 500 com rollback
- [ ] Se PDF falhar → continua sem PDF (pdf_url = null)

**Arquivos previstos:**
- `app/use_cases/__init__.py`
- `app/use_cases/gerar_planos.py`
- `app/models/schemas.py` (atualizar `DietGenerateResponse` para novo schema)

**Notas Técnicas:**
- O `NutritionCalculator` reusa `tmb_calculator.py` e `macro_distributor.py` existentes (já implementados e testados)
- O fluxo está documentado em detalhes no `fluxos.md` — Fluxo 1 (16 passos com 10 exceções)
- A persistência usa os modelos ORM existentes (`SessaoGeracao`, `PlanoAlimentar`, `Refeicao`, `ItemRefeicao`)
- O PDF usa `pdf_generator.py` existente, adaptado para o novo schema de resposta

---

### SPEC-007: Atualização do Endpoint de Geração

**Status:** [ ] Não iniciado

**User Story:** Como frontend, quero um endpoint `POST /api/diet/generate` que aceite texto livre (não um JSON estruturado), para que o usuário possa descrever sua rotina em linguagem natural.

**Critérios de Aceite:**
- [ ] `POST /api/diet/generate` aceita `{ "texto": "string" }` como body
- [ ] Validações de entrada:
  - `texto` obrigatório (422 se ausente)
  - `texto` entre 20 e 2000 caracteres (400 se fora)
  - Sanitização: remove tags HTML, caracteres de controle (exceto \n, \r, \t)
- [ ] Rate limiting: 10 req/min para IPs anônimos, 30 req/min para autenticados
- [ ] Chama `DietPlannerUseCase.executar(texto)`
- [ ] Retorna `DietGenerateResponse` com paciente, TMB, 3 planos, pdf_url
- [ ] Tratamento de erros mapeado para HTTP (ver tabela abaixo)
- [ ] Content-Type: `application/json`

**Mapeamento de erros para HTTP:**

| Exceção | HTTP Status | Mensagem para o usuário |
|---------|:-----------:|-------------------------|
| `CamposObrigatoriosAusentesException` | 400 | "Não consegui identificar [campos]. Tente: 'tenho Xkg, Ycm, Z anos, [sexo]'." |
| `ValorFisiologicoInvalidoException` | 400 | "O valor para [campo] está fora do esperado. Verifique e tente novamente." |
| `GETForaDoIntervaloSeguroException` | 400 | "GET calculado: X kcal. O mínimo seguro é 1200 kcal. Consulte um nutricionista." |
| `DeepSeekUnavailableException` | 503 | "Nossa IA está temporariamente indisponível. Tente novamente em alguns minutos." |
| `DeepSeekInvalidResponseException` | 502 | "Não foi possível gerar os planos. Nossa equipe foi notificada." |
| `PlanValidationException` | 502 | "Não foi possível gerar planos válidos. Tente descrever sua rotina com outras palavras." |
| `TimeoutException` | 504 | "Tempo limite excedido. Tente um texto mais curto." |
| `RateLimitException` | 429 | "Muitas requisições. Aguarde 60 segundos." |
| Qualquer outra | 500 | "Erro interno. Nossa equipe foi notificada." |

**Arquivos previstos:**
- `app/routers/diet.py` (atualizar)
- `app/middleware/rate_limit.py` (novo)

**Notas Técnicas:**
- O router existente em `app/routers/diet.py` aceitava `DietGenerateRequest` (JSON estruturado com paciente + rotinas). Esse schema antigo **não é mais usado** — o endpoint agora recebe `{ "texto": "..." }`
- O endpoint de download de PDF (`GET /api/diet/{pdf_id}/pdf`) permanece igual
- O rate limiting pode ser implementado com `slowapi` ou middleware manual simples (dicionário em memória com limpeza periódica)

---

### SPEC-008: Expansão de Restrições e Condições Especiais

**Status:** [ ] Não iniciado

**User Story:** Como usuário com restrições alimentares, quero que o sistema entenda restrições genéricas ("não como peixe", "sou vegano") e as aplique corretamente em todos os planos, para que eu confie que os planos são seguros para mim.

**Critérios de Aceite:**
- [ ] `RestrictionExpander` implementado em `app/services/restriction_expander.py`
- [ ] Método `expandir(restricoes: list[str], condicoes: list[str], catalogo: FoodCatalog) → ExpandedRestrictions`
- [ ] `ExpandedRestrictions` contém: `alimentos_proibidos` (lista concreta), `severidade` (alergia | conviccao | preferencia), `avisos` (lista de strings)
- [ ] Mapeamentos implementados:
  - "peixe" → ["Salmão Grelhado", "Atum em Lata", "Tilápia Grelhada", "Camarão Cozido"]
  - "carne vermelha" → ["Carne Moída Magra", "Filé Mignon", "Costela Bovina", "Lombo Suíno"]
  - "frutos do mar" → ["Salmão Grelhado", "Atum em Lata", "Tilápia Grelhada", "Camarão Cozido"]
  - "laticínios" → todos da categoria "Laticínios"
  - "glúten" → ["Pão Francês", "Pão Integral", "Macarrão Cozido"]
  - "vegano" → categorias "Carnes e Peixes" + "Laticínios" + alimentos "Ovo Cozido", "Ovo Mexido"
  - "vegetariano" → categoria "Carnes e Peixes" (ovos e laticínios OK)
  - "ovolactovegetariano" → categoria "Carnes e Peixes"
- [ ] Classificação de severidade (Fluxo 3, passo 3):
  - "alergia"/"intolerancia" → Tipo A (tolerância zero, aviso obrigatório)
  - "vegano"/"vegetariano" → Tipo B (tolerância zero, ajuste de macros se necessário)
  - "não gosto"/"evito" → Tipo C (evitar, mas pode incluir se necessário)
- [ ] Avisos gerados automaticamente por tipo de condição (RN-021, RN-022, RN-023, RN-070, RN-071, RN-072)
- [ ] Detecção de transtorno alimentar no texto → **bloqueio total** (RN-073)

**Arquivos previstos:**
- `app/services/restriction_expander.py`

**Notas Técnicas:**
- A expansão DEVE rodar ANTES da montagem do prompt de geração (SPEC-004) e ANTES da validação (SPEC-005)
- O mapeamento de categorias usa os dados do `FoodCatalog` — se um alimento for adicionado ao `foods.json`, a expansão automaticamente o inclui
- Para condições médicas (diabetes, hipertensão), o sistema não ajusta os planos — apenas adiciona o aviso obrigatório
- A lista de strings para detecção de transtorno alimentar inclui: "anorexia", "bulimia", "compulsão alimentar", "transtorno alimentar", "não como há", "vômito"

---

### SPEC-009: Frontend — Página de Input com Linguagem Natural

**Status:** [ ] Não iniciado

**User Story:** Como usuário, quero uma caixa de texto simples onde eu possa descrever minha rotina livremente, para gerar planos alimentares sem preencher formulários longos.

**Critérios de Aceite:**
- [ ] Página principal com uma `textarea` grande (mínimo 4 linhas visíveis)
- [ ] Placeholder: _"Descreva sua rotina, objetivos e preferências alimentares... Ex: 'Trabalho sentado, faço musculação 4x por semana. Quero ganhar massa. Tenho 1,75m, 72kg, 28 anos. Gosto de frango, batata doce, ovos. Não como peixe.'"_
- [ ] Contador de caracteres em tempo real: "X/2000" (verde se > 20, vermelho se < 20)
- [ ] Botão "Gerar Planos" — desabilitado se < 20 caracteres
- [ ] Abaixo da caixa, 3 exemplos rotativos (a cada 5 segundos) de inputs reais (sedentário, atleta, vegano, gestante, idoso)
- [ ] Botão "Usar este exemplo" que preenche a caixa com o exemplo atual
- [ ] Validação client-side: remoção de tags HTML, normalização de espaços
- [ ] Overlay de loading com texto contextual que muda durante o processamento (4 estágios — Fluxo 1)
- [ ] Mensagens de erro estilizadas (alerta amarelo) abaixo da caixa de texto, sem perder o conteúdo digitado

**Arquivos previstos:**
- `frontend/index.html` (atualizar seção da página de dieta)
- `frontend/css/style.css` (atualizar estilos da textarea, loading overlay)
- `frontend/js/app.js` (atualizar lógica de envio)

**Notas Técnicas:**
- O HTML/CSS/JS existente tem uma estrutura de formulário com campos individuais (nome, sexo, idade, etc.) + 3 rotinas. Essa estrutura **deve ser substituída** por uma única caixa de texto
- O overlay de loading já existe (`loading-overlay`). Atualizar `loading-text` dinamicamente conforme o estágio
- A chamada API usa `apiRequest('POST', '/api/diet/generate', { texto: inputValue })` — body diferente do antigo `DietGenerateRequest`
- O texto do usuário deve ser preservado se houver erro — não limpar a caixa

---

### SPEC-010: Frontend — Tela de Resultados com 3 Planos

**Status:** [ ] Não iniciado

**User Story:** Como usuário, quero visualizar os 3 planos gerados de forma clara e comparável, com ações para baixar PDF e gerar novamente.

**Critérios de Aceite:**
- [ ] Transição suave (fadeIn) da tela de input para tela de resultados
- [ ] Seção de sumário no topo: cards com TMB, GET, objetivo, peso, altura
- [ ] **Desktop (≥ 768px):** 3 colunas lado a lado, cada plano é um card completo
- [ ] **Mobile (< 768px):** Accordion vertical com abas "Tradicional | Funcional | Prático"
- [ ] Cada card de plano contém:
  - Nome do plano + badge do eixo
  - Descrição (2-4 frases)
  - Resumo de macros (3 cards: Proteína, Carboidrato, Gordura)
  - Refeições em tabela: Alimento | Qtde (g) | Prot | Carb | Gord | kcal
  - Totais do plano
- [ ] Ações por plano: "📄 Baixar PDF" (link para PDF consolidado), "📋 Copiar" (clipboard)
- [ ] Ações globais: "🔄 Gerar Novamente", "➕ Novo Paciente"
- [ ] Disclaimer obrigatório no rodapé da tela (RN-070)
- [ ] Botão de feedback 👍/👎 abaixo de cada plano (funcionalidade completa na Fase 2; na Fase 1 pode ser só visual)

**Arquivos previstos:**
- `frontend/index.html` (atualizar seção de resultados)
- `frontend/css/style.css` (atualizar com estilos dos planos e responsividade)
- `frontend/js/app.js` (atualizar `renderResults`)

**Notas Técnicas:**
- O frontend existente já tem uma tela de resultados (`page-results`) com `renderResults()`. Adaptar para o novo schema de resposta
- A função `renderResults` atual espera `DietGenerateResponse` do schema antigo. O novo schema tem estrutura similar mas nomes de campos diferentes
- O PDF é único (consolidado com os 3 planos), não um por plano — o botão "Baixar PDF" pode ficar na área global

---

### SPEC-011: Tratamento de Erros e Resiliência da LLM

**Status:** [ ] Não iniciado

**User Story:** Como usuário, quero receber mensagens de erro claras e em português quando algo der errado, para saber o que fazer sem frustração.

**Critérios de Aceite:**
- [ ] Toda resposta de erro do backend é em português, sem jargão técnico (RNF-034)
- [ ] Frontend trata cada HTTP status com mensagem e ação sugerida:

  | HTTP | Comportamento |
  |:----:|---------------|
  | 400 | Exibe mensagem abaixo da caixa de texto. Texto preservado para edição |
  | 422 | Exibe mensagem de validação. Campos problemáticos destacados |
  | 429 | Exibe "Muitas requisições. Aguarde X segundos." com contagem regressiva |
  | 500 | Exibe "Erro interno. Nossa equipe foi notificada. Tente novamente." |
  | 502 | Exibe "Não foi possível gerar planos válidos. Tente descrever sua rotina com outras palavras." |
  | 503 | Exibe "Nossa IA está temporariamente indisponível. Tente novamente em alguns minutos." |
  | 504 | Exibe "Tempo limite excedido. Tente um texto mais curto ou tente novamente." |
  | Rede offline | Exibe "Sem conexão com a internet. Verifique sua rede." |

- [ ] Timeout no frontend: 95 segundos (5s a mais que o timeout do backend)
- [ ] Botão "Tentar Novamente" em toda mensagem de erro 5xx
- [ ] Se 3 erros consecutivos → sugestão proativa: "Estamos enfrentando instabilidade. Tente novamente mais tarde."

**Arquivos previstos:**
- `app/routers/diet.py` (atualizar tratamento de exceções)
- `frontend/js/app.js` (atualizar `apiRequest` error handling)

**Notas Técnicas:**
- O `apiRequest` já foi atualizado com verificação de Content-Type (LL-005). Manter.
- Exceções do backend devem ser logadas com stack trace completo, mas a resposta ao usuário NUNCA inclui stack trace
- Usar `request_id` (UUID gerado no middleware) em todos os logs para correlação

---

### SPEC-012: Configuração de Ambiente e Segurança

**Status:** [ ] Não iniciado

**User Story:** Como desenvolvedor, quero que todas as configurações sensíveis estejam em variáveis de ambiente e que o sistema falhe rápido se algo essencial estiver ausente.

**Critérios de Aceite:**
- [ ] `.env.example` criado com todas as variáveis necessárias (sem valores reais)
- [ ] `python-dotenv` carrega `.env` na inicialização
- [ ] Validação de variáveis obrigatórias na inicialização:
  - `DEEPSEEK_API_KEY` → RuntimeError se ausente
  - `JWT_SECRET_KEY` → RuntimeError se ausente
  - `DATABASE_URL` → usa default para SQL Server local se ausente
- [ ] `.env` adicionado ao `.gitignore`
- [ ] Headers de segurança no FastAPI: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`
- [ ] CORS restrito a `localhost:8000` e `127.0.0.1:8000` (não `*`)
- [ ] Rate limiting configurável via `.env`: `RATE_LIMIT_ANON=10`, `RATE_LIMIT_AUTH=30`

**Arquivos previstos:**
- `.env.example`
- `.gitignore` (atualizar)
- `app/main.py` (atualizar CORS, headers, rate limit middleware)
- `app/config.py` (novo — centraliza leitura de config)

**Notas Técnicas:**
- O `.env.example` DEVE listar TODAS as variáveis usadas pelo sistema com comentários explicando cada uma
- NUNCA versionar `.env` real no Git
- O arquivo `app/config.py` centraliza `os.getenv()` para evitar chamadas espalhadas e facilitar testes

---

### SPEC-013: Logs e Observabilidade Básica

**Status:** [ ] Não iniciado

**User Story:** Como desenvolvedor, quero logs estruturados de cada etapa do fluxo de geração, para conseguir debugar problemas em produção sem acessar o servidor diretamente.

**Critérios de Aceite:**
- [ ] Logs em JSON estruturado (RNF-043) com campos: `timestamp`, `level`, `module`, `request_id`, `message`, `metadata`
- [ ] `request_id` (UUID) gerado no middleware e propagado para todas as camadas
- [ ] Logs em cada etapa crítica:
  - Requisição recebida (input sanitizado, NÃO logar texto original se contiver dados de saúde — RN-023)
  - Extração NL→JSON (latência, tokens consumidos, sucesso/falha)
  - Cálculo nutricional (TMB, GET, objetivo)
  - Geração IA (latência, tokens consumidos, sucesso/falha)
  - Validação (correções aplicadas, sucesso/falha)
  - Persistência (sucesso/falha)
  - PDF (sucesso/falha)
  - Resposta enviada (latência total)
- [ ] Logs de erro com stack trace completo (mas sem dados sensíveis)
- [ ] Nível INFO para fluxo normal, WARNING para correções automáticas, ERROR para falhas
- [ ] Logs no console (stdout) na v1 — sem necessidade de sistema externo

**Arquivos previstos:**
- `app/logging_config.py` (novo)
- `app/middleware/logging.py` (novo)
- `app/main.py` (atualizar para incluir middleware de logging)

**Notas Técnicas:**
- Usar `logging` padrão do Python com `JSONFormatter`
- O `request_id` pode ser propagado via `contextvars` (thread-safe, não precisa passar como parâmetro)
- Mascarar dados sensíveis nos logs: `DEEPSEEK_API_KEY`, `JWT_SECRET_KEY`, senhas, dados de saúde

---

## 🔧 Fase 2 — Refina a Experiência

**Objetivo:** Melhorar a qualidade dos planos, a experiência do usuário e a observabilidade do sistema com base no uso real do MVP.

**Pré-requisito:** MVP (Fase 1) concluído e em uso por pelo menos 10 usuários beta.

---

### SPEC-014: Histórico de Gerações para Usuários Autenticados

**Status:** [ ] Não iniciado

**User Story:** Como usuário autenticado, quero acessar o histórico de todos os planos que já gerei, para revisitar planos anteriores sem precisar salvar os PDFs.

**Critérios de Aceite:**
- [ ] `GET /api/diet/history` retorna lista de `SessaoGeracao` do usuário autenticado
- [ ] Cada item contém: data, objetivo, GET, link para PDF (se dentro de 7 dias)
- [ ] Paginação: 10 resultados por página
- [ ] Ordenação: mais recente primeiro
- [ ] Frontend: página "Meus Planos" acessível pelo header (apenas logado)
- [ ] Cada item do histórico é clicável → expande para mostrar resumo dos 3 planos
- [ ] Botão "Excluir" em cada item (soft delete ou hard delete com confirmação)
- [ ] `DELETE /api/diet/{sessao_id}` remove a sessão e os planos associados

**Arquivos previstos:**
- `app/routers/diet.py` (atualizar com novo endpoint)
- `app/repositories/sessao_geracao_repository.py` (novo)
- `frontend/index.html` (nova página "Meus Planos")
- `frontend/js/app.js` (lógica de histórico)

**Notas Técnicas:**
- Usuários anônimos NÃO têm acesso ao histórico (dados não são vinculados a identidade)
- Planos com `usuario_id = NULL` não aparecem em nenhum histórico
- A expiração de PDF (7 dias) e planos (30 dias) continua valendo — itens expirados não aparecem no histórico

---

### SPEC-015: Sistema de Feedback de Planos

**Status:** [ ] Não iniciado

**User Story:** Como product owner, quero coletar feedback dos usuários sobre a qualidade dos planos gerados, para melhorar o sistema com dados reais.

**Critérios de Aceite:**
- [ ] Botões 👍/👎 abaixo de cada plano na tela de resultados
- [ ] Clique em 👎 abre mini-formulário com opções:
  - "Alimentos repetidos entre planos"
  - "Quantidades irreais (muito ou pouco)"
  - "Não gostei das combinações"
  - "Alimentos que não como apareceram"
  - "Outro" (campo de texto livre opcional)
- [ ] `POST /api/diet/{sessao_id}/feedback` com body `{ "plano_id": X, "positivo": false, "motivo": "...", "comentario": "..." }`
- [ ] Feedback salvo em tabela `feedback_planos` com FK para `PlanoAlimentar`
- [ ] Métricas agregadas no admin: % de feedback positivo por eixo, motivos mais comuns de feedback negativo
- [ ] Log separado para feedbacks negativos (RF-072)

**Arquivos previstos:**
- `app/routers/diet.py` (novo endpoint)
- `app/models/database/feedback.py` (novo modelo ORM)
- `alembic/versions/` (nova migração para tabela feedback_planos)
- `frontend/js/app.js` (lógica de feedback)

**Notas Técnicas:**
- Feedback é anônimo — não requer autenticação
- Um mesmo usuário pode dar feedback múltiplas vezes (cada clique é um registro novo)
- Os dados de feedback serão usados na Fase 2 para ajustar prompts e na Fase 3 para fine-tuning

---

### SPEC-016: Regeneração Inteligente de Planos

**Status:** [ ] Não iniciado

**User Story:** Como usuário, quero gerar novos planos quando não gostar dos atuais, com garantia de que serão diferentes da geração anterior.

**Critérios de Aceite:**
- [ ] Botão "🔄 Gerar Novamente" envia o MESMO texto original
- [ ] Backend recebe parâmetro opcional `{ "texto": "...", "evitar_ids": ["uuid1", "uuid2"] }` com alimentos a evitar (extraídos dos planos anteriores)
- [ ] System prompt da regeneração inclui: "EVITE estes alimentos que já apareceram em gerações anteriores: [lista]"
- [ ] Se `evitar_ids` for enviado, temperatura sobe para 0.85 (mais variação)
- [ ] Frontend detecta se usuário gerou 3x em < 2 minutos e exibe sugestão: _"Que tal ajustar sua descrição para obter resultados mais diferentes?"_ (Fluxo 5, passo 6)
- [ ] Planos anteriores permanecem acessíveis (não sobrescrever)

**Arquivos previstos:**
- `app/routers/diet.py` (atualizar endpoint)
- `app/services/plan_generator_service.py` (atualizar prompt)
- `frontend/js/app.js` (contador de regenerações)

**Notas Técnicas:**
- Na v1 (MVP), a regeneração é idêntica a uma nova chamada (sem `evitar_ids`). A SPEC-016 implementa a versão inteligente
- A lista de alimentos a evitar é montada pelo frontend a partir dos planos atuais e enviada como parâmetro opcional

---

### SPEC-017: Métricas e Analytics Básicos

**Status:** [ ] Não iniciado

**User Story:** Como product owner, quero métricas básicas de uso do sistema, para tomar decisões baseadas em dados.

**Critérios de Aceite:**
- [ ] Endpoint `GET /api/admin/metrics` (protegido por token admin) retornando:
  - Planos gerados hoje / esta semana / este mês
  - Distribuição de objetivos (perda/manutenção/ganho) em %
  - Distribuição de eixos mais visualizados (tradicional/funcional/pratico)
  - Taxa de erro (extração, geração, validação)
  - Latência média (extração, geração, total)
  - Custo estimado com API DeepSeek (tokens consumidos × preço por token)
  - Top 10 alimentos mais sugeridos
- [ ] Middleware de analytics: cada requisição bem-sucedida registra evento `plan_gerado` com metadados
- [ ] Eventos armazenados em tabela `eventos_analytics` (leve, só metadados, sem dados do usuário)

**Arquivos previstos:**
- `app/routers/admin.py` (novo)
- `app/models/database/evento_analytics.py` (novo)
- `app/middleware/analytics.py` (novo)
- `alembic/versions/` (nova migração)

**Notas Técnicas:**
- O middleware de analytics NÃO deve impactar a latência da resposta — registra o evento após enviar a resposta ao cliente (background)
- Dados de analytics são anonimizados: sem IP, sem texto original, sem e-mail

---

### SPEC-018: Ajuste de Prompts com Base em Feedback

**Status:** [ ] Não iniciado

**User Story:** Como product owner, quero usar o feedback dos usuários para melhorar os prompts do sistema e reduzir a taxa de feedback negativo.

**Critérios de Aceite:**
- [ ] Script `scripts/analisar_feedback.py` que:
  - Lê feedbacks da tabela `feedback_planos`
  - Agrupa por motivo
  - Extrai exemplos de planos que receberam feedback negativo
  - Gera relatório em Markdown com top 5 problemas e exemplos
- [ ] Processo documentado: a cada 50 feedbacks, rodar script e revisar prompts
- [ ] Versionamento de prompts: cada system prompt salvo em `prompts/extraction_v1.txt`, `prompts/generation_v1.txt`
- [ ] Novo prompt versionado como `v2` quando ajustado

**Arquivos previstos:**
- `scripts/analisar_feedback.py`
- `prompts/extraction_v1.txt`
- `prompts/generation_v1.txt`

**Notas Técnicas:**
- Ajustes de prompt são feitos manualmente (não automatizados) com base no relatório
- Cada versão de prompt é testada com um conjunto fixo de 10 inputs de exemplo antes de ir para produção
- Prompts antigos são mantidos para rollback rápido se a nova versão performar pior

---

### SPEC-019: Rate Limiting Robusto e Proteção contra Abuso

**Status:** [ ] Não iniciado

**User Story:** Como operador do sistema, quero proteger a API contra abuso e uso excessivo que poderia gerar custos elevados com a API DeepSeek.

**Critérios de Aceite:**
- [ ] Rate limiting com `slowapi` (ou middleware customizado):
  - Anônimos: 10 req/min, 50 req/hora
  - Autenticados: 30 req/min, 200 req/hora
- [ ] Headers HTTP informativos: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, `Retry-After`
- [ ] Bloqueio temporário: se exceder o limite 3x em 1 hora → bloqueio de 15 minutos
- [ ] Lista de IPs banidos manualmente (via `.env` ou banco)
- [ ] Log de rate limit excedido com IP e timestamp
- [ ] Custo máximo diário configurável: se o gasto estimado com DeepSeek exceder `MAX_DAILY_COST` → retornar 503 mesmo com API disponível

**Arquivos previstos:**
- `app/middleware/rate_limit.py` (atualizar)
- `app/config.py` (atualizar com novas variáveis)

**Notas Técnicas:**
- O rate limiting usa dicionário em memória (como o cache de PDFs). Isso é suficiente para single-instance
- Se migrar para múltiplas instâncias no futuro, migrar para Redis
- O bloqueio de 15 minutos também é em memória — reset ao reiniciar o servidor

---

## 🚀 Fase 3 — Escala e Personalização

**Objetivo:** Expandir o sistema para suportar mais usuários, mais opções de personalização, e iniciar monetização.

**Pré-requisito:** Fase 2 concluída com feedback positivo dos usuários beta (> 70% de aprovação).

---

### SPEC-020: Dashboard Administrativo

**Status:** [ ] Não iniciado

**User Story:** Como administrador, quero um painel web para monitorar o sistema em tempo real, visualizar métricas e gerenciar usuários.

**Critérios de Aceite:**
- [ ] Página `GET /admin` protegida por autenticação admin (JWT com role `admin`)
- [ ] Abas do dashboard:
  - **Visão Geral:** planos gerados hoje, usuários ativos, taxa de erro, custo DeepSeek
  - **Métricas:** gráficos de uso (diário/semanal), distribuição de objetivos, latência
  - **Qualidade:** taxa de feedback positivo/negativo, top motivos de rejeição
  - **Usuários:** lista de usuários cadastrados, data de cadastro, total de gerações
  - **Logs:** visualização dos últimos 100 logs de erro
- [ ] Gráficos simples (Chart.js ou similar) — sem dependência pesada
- [ ] Filtro por período: hoje, 7 dias, 30 dias, personalizado

**Arquivos previstos:**
- `frontend/admin.html` (novo)
- `frontend/css/admin.css` (novo)
- `frontend/js/admin.js` (novo)
- `app/routers/admin.py` (atualizar com endpoints de dados)

**Notas Técnicas:**
- O dashboard é uma página separada do frontend principal, acessível apenas por admins
- Gráficos usam dados agregados (não fazem consultas pesadas ao banco em tempo real)
- Métricas são pré-calculadas a cada hora por um job simples (ou calculadas on-demand para volumes baixos)

---

### SPEC-021: Múltiplos Provedores de IA

**Status:** [ ] Não iniciado

**User Story:** Como operador do sistema, quero poder alternar entre diferentes provedores de IA (DeepSeek, OpenAI, Claude) para comparar qualidade e custo, e ter fallback se o provedor principal falhar.

**Critérios de Aceite:**
- [ ] Interface `LLMProvider` (Protocol/ABC) com método `chat_completion(messages, **kwargs)`
- [ ] Implementações concretas: `DeepSeekProvider`, `OpenAIProvider`, `ClaudeProvider`
- [ ] Configuração por `.env`:
  - `LLM_PROVIDER=deepseek` (padrão)
  - `LLM_FALLBACK_PROVIDER=openai` (opcional)
- [ ] Fallback automático: se provider principal falhar 3x consecutivas, alterna para fallback
- [ ] Métricas por provider: latência média, custo por requisição, taxa de erro
- [ ] Provider pode ser trocado sem reiniciar o servidor (recarregar config)

**Arquivos previstos:**
- `app/infrastructure/llm_provider.py` (interface)
- `app/infrastructure/deepseek_provider.py` (refatorar DeepSeekClient)
- `app/infrastructure/openai_provider.py` (novo)
- `app/infrastructure/claude_provider.py` (novo)

**Notas Técnicas:**
- A interface `LLMProvider` abstrai completamente o provedor — os serviços (ExtractorService, PlanGeneratorService) não sabem qual provedor está sendo usado
- A diferença entre provedores está apenas na autenticação e no formato da requisição — o schema de resposta é o mesmo (JSON mode)
- OpenAI e DeepSeek têm APIs compatíveis. Claude requer adaptação (Anthropic SDK ou API Messages)

---

### SPEC-022: Chat Multi-Turno para Refinar Planos

**Status:** [ ] Não iniciado

**User Story:** Como usuário, quero poder conversar com a IA para refinar os planos gerados, fazendo ajustes pontuais sem precisar regenerar tudo do zero.

**Critérios de Aceite:**
- [ ] Após a geração inicial, campo de texto aparece abaixo dos planos: _"Quer ajustar algo? Ex: 'Troca o frango do almoço por peixe', 'Aumenta a proteína do café da manhã', 'Não gostei do plano 2, refaz só ele'"_
- [ ] `POST /api/diet/{sessao_id}/refine` com body `{ "mensagem": "..." }`
- [ ] Mantém contexto da geração original (planos atuais + perfil + metas)
- [ ] Retorna planos atualizados (substitui os anteriores na tela)
- [ ] Histórico de refinamentos salvo como subtópicos da `SessaoGeracao`
- [ ] Limite de 5 turnos de refinamento por sessão

**Arquivos previstos:**
- `app/routers/diet.py` (novo endpoint)
- `app/services/plan_refiner_service.py` (novo)
- `app/models/database/mensagem_refinamento.py` (novo modelo)
- `frontend/js/app.js` (chat UI)

**Notas Técnicas:**
- O contexto da conversa é mantido no backend (armazenado na sessão)
- Cada turno custa ~1/3 de uma geração completa (prompt menor, resposta menor)
- O limite de 5 turnos evita loops infinitos e custos excessivos

---

### SPEC-023: Exportação Avançada (PDF Melhorado + CSV)

**Status:** [ ] Não iniciado

**User Story:** Como usuário, quero exportar meus planos em formatos diferentes para diferentes usos: PDF profissional para o nutricionista, CSV para controle pessoal.

**Critérios de Aceite:**
- [ ] PDF melhorado:
  - Capa com logo do sistema
  - Tabela de medidas caseiras (coluna adicional)
  - Gráfico de distribuição de macros (pizza chart via ReportLab)
  - Opção de incluir/excluir explicações dos planos
- [ ] `GET /api/diet/{sessao_id}/csv` — download de CSV com todos os alimentos de todos os planos
  - Colunas: Plano, Refeição, Alimento, Quantidade (g), Proteína, Carbo, Gordura, kcal
- [ ] `GET /api/diet/{sessao_id}/pdf?formato=simplificado` — PDF de 1 página (resumo) vs PDF completo (3 páginas)

**Arquivos previstos:**
- `app/utils/pdf_generator.py` (atualizar)
- `app/utils/csv_generator.py` (novo)
- `app/routers/diet.py` (novo endpoint CSV)

**Notas Técnicas:**
- O ReportLab suporta gráficos de pizza nativos (`Drawing` + `Pie`)
- O CSV usa `csv.writer` da stdlib (sem dependências)
- Medidas caseiras exigem tabela de conversão (RN-101)

---

### SPEC-024: Perfis de Usuário e Preferências Salvas

**Status:** [ ] Não iniciado

**User Story:** Como usuário autenticado, quero salvar meu perfil (peso, altura, preferências, restrições) para não precisar digitar tudo novamente a cada geração.

**Critérios de Aceite:**
- [ ] Usuário pode salvar perfil padrão durante ou após o cadastro
- [ ] Perfil padrão preenche automaticamente a caixa de texto com um resumo: _"Tenho X anos, Y kg, Z cm, sexo [M/F]. Objetivo: [X]. Gosto de: [alimentos]. Não como: [restrições]."_
- [ ] Usuário pode editar o texto preenchido antes de enviar
- [ ] `PUT /api/auth/perfil` para atualizar perfil padrão
- [ ] `GET /api/auth/perfil` para recuperar perfil padrão
- [ ] Suporte a múltiplos perfis (ex: "Eu", "Meu filho", "Minha esposa") — até 3 perfis por conta gratuita

**Arquivos previstos:**
- `app/models/database/perfil_usuario.py` (novo)
- `app/routers/auth.py` (novos endpoints)
- `alembic/versions/` (nova migração)
- `frontend/js/app.js` (preenchimento automático)

**Notas Técnicas:**
- Cada perfil salvo é apenas um template de texto — não substitui o input em linguagem natural
- O sistema continua aceitando texto livre mesmo para usuários com perfil salvo

---

### SPEC-025: Sistema de Assinatura e Monetização

**Status:** [ ] Não iniciado

**User Story:** Como product owner, quero monetizar o sistema com um modelo freemium, para cobrir custos de infraestrutura e API DeepSeek.

**Critérios de Aceite:**
- [ ] Plano Gratuito: 5 gerações por mês, sem histórico, sem exportação CSV
- [ ] Plano Premium (R$ 19,90/mês): gerações ilimitadas, histórico completo, exportação CSV, múltiplos perfis
- [ ] Plano Profissional (R$ 49,90/mês): tudo do Premium + chat multi-turno, exportação avançada
- [ ] Integração com Stripe ou Mercado Pago para pagamentos
- [ ] Contador de gerações por usuário (reset mensal)
- [ ] Bloqueio automático ao atingir limite do plano gratuito
- [ ] Página de upgrade com comparação de planos

**Arquivos previstos:**
- `app/models/database/assinatura.py` (novo)
- `app/services/payment_service.py` (novo)
- `app/routers/payment.py` (novo)
- `app/middleware/quota.py` (novo)
- `alembic/versions/` (várias migrações)
- `frontend/planos.html` (página de planos e preços)

**Notas Técnicas:**
- A monetização é a última SPEC da Fase 3 — o sistema já deve ter uma base de usuários validada
- Começar com um gateway de pagamento brasileiro (Mercado Pago) para simplicidade fiscal
- Webhook do gateway notifica o sistema sobre pagamentos confirmados/cancelados

---

## 💡 Backlog de Ideias

Ideias sem prioridade definida, para discussão futura. Podem se tornar SPECs em fases posteriores.

| # | Ideia | Complexidade | Impacto |
|:-:|-------|:-----------:|:-------:|
| 1 | **Aplicativo mobile nativo** (iOS/Android) com notificações push lembrando de seguir o plano | Alta | Alto |
| 2 | **Integração com smartwatch** (Apple Health / Google Fit) para ajustar GET automaticamente com base em calorias gastas | Alta | Médio |
| 3 | **Lista de compras automática** — ao gerar um plano, gerar lista de compras da semana com quantidades | Baixa | Alto |
| 4 | **Comparação entre planos** — tela mostrando diferenças lado a lado com destaques visuais (verde = melhor, vermelho = pior) | Média | Médio |
| 5 | **Recomendações semanais** — sistema envia e-mail com 3 novos planos automaticamente | Média | Alto |
| 6 | **Modo nutricionista** — profissional cadastrado pode criar planos para múltiplos pacientes e gerenciá-los | Alta | Alto |
| 7 | **Fine-tuning do modelo** — treinar modelo com dados anonimizados dos melhores planos (mais bem avaliados) | Alta | Médio |
| 8 | **Integração com iFood/Mercado** — botão "Comprar ingredientes" que gera carrinho no app de delivery | Alta | Baixo |
| 9 | **Suporte a dietas médicas** — renal, cetogênica terapêutica, pós-bariátrica (com validação de nutricionista parceiro) | Alta | Médio |
| 10 | **Comunidade** — usuários compartilham planos publicamente, votam nos melhores, comentam | Alta | Médio |

---

## 📋 Regra de Atualização

1. **Quando uma SPEC for iniciada:** marcar `[~] Em andamento`, atualizar data de início, atualizar resumo geral.
2. **Quando uma SPEC for concluída:** marcar `[x] Concluído`, registrar data de conclusão, listar arquivos alterados, atualizar percentual.
3. **Quando uma SPEC for bloqueada:** adicionar `⚠️ Bloqueada por:` com referência à SPEC bloqueante.
4. **Quando uma ideia do backlog virar SPEC:** movê-la para a fase apropriada com ID sequencial.

**A IA NUNCA deve marcar uma SPEC como concluída sem confirmação explícita do desenvolvedor.** A IA pode sugerir a marcação, listando evidências de completude, mas a decisão final é humana.

---

> **Para a IA na próxima sessão:** Este roadmap é o plano de voo. Antes de implementar qualquer coisa, verifique se já existe uma SPEC para aquela funcionalidade. Se não existir, proponha a criação da SPEC primeiro. Não implemente fora do roadmap sem discutir.
