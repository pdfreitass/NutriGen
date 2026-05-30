# 🔄 Fluxos do Sistema — Gerador de Planos Alimentares com IA

> **Propósito:** Documentar todos os fluxos de interação do sistema, da abertura da página até a exportação do PDF. Cada fluxo descreve o caminho exato que os dados percorrem, os estados possíveis, e como cada erro é tratado.
>
> **Público:** Desenvolvedores, QA, Product Owner, e IAs implementando as features correspondentes.
>
> **Como usar:** Para implementar uma feature, leia o fluxo correspondente. Os passos numerados são a sequência exata que o código deve seguir. As exceções são os `if/else` e `try/except` necessários.

---

## Fluxo 1: Geração de Planos (Fluxo Principal — Happy Path)

**Ator:** Usuário (autenticado ou anônimo)

**Pré-condição:**
- O sistema está online (FastAPI + SQL Server Express)
- A API DeepSeek está acessível
- O frontend foi carregado no navegador

**Passos:**

1. **Usuário acessa o sistema.**
   - Frontend carrega `index.html`, `style.css`, `app.js`.
   - Se há token JWT no `localStorage` e o token é válido → usuário é autenticado automaticamente. Header mostra nome.
   - Se não há token → modo anônimo. Header mostra "Entrar | Criar conta".

2. **Usuário vê a caixa de texto principal.**
   - Placeholder: _"Descreva sua rotina, objetivos e preferências alimentares..."_
   - Abaixo da caixa, 3 exemplos rotativos de inputs válidos (RF-004).
   - Botão "Usar exemplo" preenche a caixa com um exemplo editável (RF-005).
   - Contador de caracteres (mínimo 20, máximo visível: 2000).

3. **Usuário digita ou cola sua descrição e clica em "Gerar Planos".**

4. **Validação pré-envio (frontend):**
   - Texto sanitizado: tags HTML e caracteres de controle removidos (RF-006).
   - Se < 20 caracteres → mensagem "Descreva sua rotina com mais detalhes (mínimo 20 caracteres)". Botão desabilitado.
   - Se > 2000 caracteres → truncado com aviso "Seu texto foi resumido para 2000 caracteres".
   - Se OK → botão muda para estado `loading`. Overlay de carregamento aparece.

5. **Requisição enviada:** `POST /api/diet/generate` com body `{ "texto": "<input do usuário>" }`.

6. **Rate limiting (backend):**
   - Middleware verifica IP. Se > 10 req/min (anônimo) → retorna 429 _"Muitas requisições. Aguarde alguns instantes."_
   - Se OK → prossegue.

7. **Extração NL→JSON (Etapa 1 — DeepSeek):**
   - System prompt de extração + texto do usuário são enviados para `DeepSeekClient.extract()`.
   - Timeout: 15 segundos. Retry: 1 tentativa.
   - Se OK → recebe JSON com perfil, preferências, restrições, condições.
   - **Spinner frontend:** _"Analisando sua rotina..."_

8. **Validação da extração (backend):**
   - Campos obrigatórios (`sexo`, `idade`, `peso_kg`, `altura_cm`) estão presentes?
   - Valores dentro de intervalos fisiológicos? (RN-041)
   - Se faltar campos → **Fluxo 2 (Input Incompleto)**.
   - Se OK → prossegue.

9. **Cálculo nutricional (Etapa 2 — local, determinístico):**
   - TMB via Mifflin-St Jeor.
   - GET via fator de atividade.
   - Distribuição de macros conforme objetivo.
   - Validação de GET contra limites de segurança (RN-060).
   - Se GET < 1200 ou > 4000 → bloqueia. Mensagem: _"Valores fora da faixa segura. Consulte um nutricionista."_
   - **Spinner frontend:** _"Calculando suas necessidades nutricionais..."_

10. **Montagem do prompt de geração (backend):**
    - Restrições são expandidas de categorias genéricas para lista concreta (LL-004).
    - Catálogo de alimentos relevantes é selecionado (categorias que fazem sentido para o perfil).
    - System prompt de geração + macros + preferências + restrições expandidas são combinados.

11. **Geração dos 3 planos (Etapa 3 — DeepSeek):**
    - Prompt enviado para `DeepSeekClient.generate_plans()`.
    - `response_format: { "type": "json_object" }` (LL-001).
    - Temperatura: 0.7. Timeout: 90 segundos. Retry: 2 tentativas com backoff (2s, 4s).
    - **Spinner frontend:** _"Gerando os 3 planos alimentares..."_

12. **Validação pós-geração (Etapa 4 — PlanValidator):**
    - Array `planos` tem exatamente 3 elementos? (RN-001)
    - Cada plano tem 4-6 refeições? (RN-005)
    - Nenhum alimento proibido? (RN-020 — tolerância 0%)
    - Todo alimento existe no `foods.json`? (LL-002)
    - Quantidades entre 30g e 500g? (RN-014)
    - Macros dentro de ±10% do calculado? (RN-010)
    - Soma calórica entre 95% e 105% do GET? (RN-015)
    - Pelo menos 40% de alimentos diferentes entre planos? (RN-004)
    - Se qualquer validação falhar → corrigir automaticamente ou rejeitar e re-solicitar à IA (máximo 1 re-tentativa).
    - **Spinner frontend:** _"Validando e ajustando os planos..."_

13. **Persistência (Etapa 5 — SQL Server):**
    - 1 transação: `SessaoGeracao` + 3 `PlanoAlimentar` + 12-18 `Refeicao` + 24-90 `ItemRefeicao`.
    - Se usuário autenticado → `usuario_id` preenchido.
    - Se anônimo → `usuario_id = NULL`.
    - Se erro de banco → rollback. Retorna 500.

14. **Geração de PDF (Etapa 6 — ReportLab):**
    - PDF consolidado com capa + 3 páginas de planos + disclaimer.
    - Salvo em `outputs/{uuid}.pdf`.
    - `pdf_uuid` armazenado em `SessaoGeracao`.
    - **Spinner frontend:** _"Gerando PDF..."_

15. **Resposta ao frontend:**
    - HTTP 200 com `DietGenerateResponse` (JSON completo + `pdf_url`).
    - Overlay de loading desaparece.

16. **Renderização dos resultados (frontend — Fluxo 4):**
    - Três planos exibidos lado a lado (desktop) ou em accordion (mobile).
    - Seção de sumário: TMB, GET, objetivo detectado.
    - Botões: Baixar PDF, Copiar plano, Gerar novamente, Compartilhar.

**Pós-condição:**
- `SessaoGeracao` persistida no banco com 3 planos.
- PDF salvo em disco (expira em 7 dias).
- Usuário visualiza os 3 planos na tela de resultados.
- Se usuário anônimo e fechar o navegador, só poderá reacessar pelo link do PDF (7 dias).

**Exceções:**

| Etapa | O que pode dar errado | Tratamento |
|:-----:|----------------------|------------|
| 5 | Rede offline (cliente) | Frontend detecta `fetch` erro de rede → mensagem: _"Sem conexão. Verifique sua internet."_ |
| 6 | Rate limit excedido | HTTP 429 → mensagem com tempo de espera estimado (60 segundos). |
| 7 | API DeepSeek offline | `DeepSeekUnavailableException` → HTTP 503. Mensagem: _"IA temporariamente indisponível. Tente novamente em alguns minutos."_ |
| 7 | Timeout extração (> 15s) | Retry 1x. Se falhar → mesmo tratamento de API offline. |
| 8 | Campos obrigatórios faltando | **Fluxo 2.** |
| 9 | GET fora do intervalo seguro | HTTP 400. Mensagem específica (ex: _"GET calculado: 980 kcal. O mínimo seguro é 1200 kcal."_). |
| 11 | Timeout geração (> 90s) | Retry 2x. Se todas falharem → HTTP 504. Mensagem: _"Tempo limite excedido. Tente um texto mais curto."_ |
| 11 | JSON malformado da LLM | `DeepSeekInvalidResponseException`. Retry 1x com temperatura reduzida (0.3). |
| 12 | Validação falha (após correção) | Retry 1x com prompt reforçado. Se falhar de novo → HTTP 502. Mensagem: _"Não foi possível gerar planos válidos. Tente descrever sua rotina com outras palavras."_ |
| 13 | Erro de banco de dados | Rollback. HTTP 500. Log completo com stack trace. |
| 14 | Erro ao gerar PDF (disco cheio, permissão) | PDF não gerado. `pdf_url = null` na resposta. Plano ainda é retornado (sem PDF). Aviso no frontend: _"PDF não pôde ser gerado, mas seus planos estão abaixo."_ |

---

## Fluxo 2: Tratamento de Input Incompleto

**Ator:** Sistema (backend — `ExtractorService` + `PlanValidator`)

**Pré-condição:**
- O usuário enviou um texto para `POST /api/diet/generate`.
- A extração NL→JSON foi concluída (Fluxo 1, Etapa 7).

**Passos:**

1. **Verificação de campos obrigatórios.**
   - O JSON extraído é validado contra o schema `PerfilExtraido`.
   - Campos verificados: `sexo`, `idade`, `peso_kg`, `altura_cm`.
   - Se TODOS presentes → prossegue para cálculo nutricional (Fluxo 1, Etapa 9).
   - Se ALGUM ausente → este fluxo é acionado.

2. **Construção da mensagem de erro.**
   - O sistema monta uma lista dos campos faltantes em português claro.
   - Exemplo: _"Não consegui identificar seu peso e altura. Inclua algo como: 'tenho 70kg e 1,75m de altura'."_
   - A mensagem é contextual: se o usuário mencionou "sou magro" mas não deu peso, sugerir: _"Você mencionou que é magro, mas não informou seu peso."_
   - **NUNCA** exibir termos técnicos como "KeyError: peso_kg" ou "ValidationError" (RNF-034).

3. **Resposta ao frontend.**
   - HTTP 400 Bad Request.
   - Body:
     ```json
     {
       "erro": "input_incompleto",
       "campos_faltantes": ["peso_kg", "altura_cm"],
       "mensagem": "Não consegui identificar seu peso e altura. Tente: 'tenho 70kg, 1,75m, 28 anos, homem'.",
       "texto_original": "<input original do usuário>"
     }
     ```

4. **Frontend exibe o erro.**
   - Overlay de loading desaparece.
   - Abaixo da caixa de texto, aparece um alerta amarelo (warning) com a mensagem.
   - A caixa de texto **mantém o conteúdo original** — o usuário não perde o que já digitou.
   - O cursor é posicionado no final da caixa de texto para o usuário complementar.
   - Se o campo faltante for específico, placeholder da caixa muda temporariamente: _"Complete: tenho __kg, __cm de altura..."_

5. **Usuário edita e reenvia.**
   - Fluxo 1 reinicia da Etapa 3 (clique em "Gerar Planos").

**Casos especiais de input incompleto:**

| Situação | Tratamento |
|----------|------------|
| Só faltam `preferencias` (sem alimentos preferidos) | Não é erro. Planos são gerados apenas com catálogo (RN-033). |
| `nivel_atividade` não mencionado | Inferir como "sedentário". Informar o usuário: _"Assumi atividade sedentária. Se pratica exercícios, especifique."_ (RN-031) |
| `objetivo` não mencionado | Inferir por IMC (RN-032). Informar: _"Pelo seu peso e altura, assumi que seu objetivo é [X]."_ |
| `sexo` não mencionado mas o nome sugere gênero | NÃO inferir por nome. Solicitar explicitamente. Nome não é indicador confiável de sexo biológico. |
| Input menciona conflitos (ex: "quero emagrecer mas como fast food todo dia") | Ignorar contradição. Processar com base no objetivo declarado (RN-050). Não julgar. |

**Pós-condição:**
- Nenhum dado é persistido no banco (a sessão não foi criada).
- O texto original do usuário é preservado no frontend para edição.
- O sistema está pronto para nova tentativa.

**Exceções:**

| O que pode dar errado | Tratamento |
|----------------------|------------|
| Input com < 20 caracteres | Barrado na validação pré-envio (frontend). Não chega ao backend. |
| Input só com números (ex: "70 175 28 M") | O modelo pode extrair corretamente se os números estiverem em ordem convencional. Se falhar, pedir formato mais natural. |
| Input em outro idioma (inglês, espanhol) | O modelo DeepSeek suporta múltiplos idiomas. Processar normalmente. |
| Usuário reenvia o mesmo texto 3x sem complementar | Na 3ª tentativa, frontend sugere proativamente: _"Ainda não consegui identificar [campos]. Que tal usar um dos exemplos abaixo como ponto de partida?"_ |

---

## Fluxo 3: Input com Restrições Alimentares

**Ator:** Sistema (backend — `ExtractorService` + `PlanGeneratorService` + `PlanValidator`)

**Pré-condição:**
- O usuário enviou um texto que contém restrições alimentares explícitas.
- A extração NL→JSON identificou entradas no campo `restricoes` e/ou `condicoes` (RF-014, RF-015).

**Passos:**

1. **Identificação de restrições na extração.**
   - O `ExtractorService` analisa o texto e classifica menções em 3 níveis:
     - **Restrição explícita:** "não como X", "detesto Y", "sou alérgico a Z" → campo `restricoes`.
     - **Restrição por convicção:** "sou vegano", "sou vegetariano" → campo `condicoes`.
     - **Condição médica:** "tenho diabetes", "sou hipertenso", "grávida de 6 meses" → campo `condicoes`.

2. **Expansão de restrições genéricas para lista concreta (LL-004).**
   - Restrições genéricas são expandidas usando `FoodCatalog`:
     - "peixe" → "Salmão Grelhado", "Atum em Lata", "Tilápia Grelhada", "Camarão Cozido"
     - "carne vermelha" → "Carne Moída Magra", "Filé Mignon", "Costela Bovina", "Lombo Suíno"
     - "laticínios" → "Leite Integral", "Queijo Mussarela", "Iogurte Natural", "Requeijão Cremoso", etc.
     - "glúten" → "Pão Francês", "Pão Integral", "Macarrão Cozido", "Aveia em Flocos" (se não for sem glúten)
   - Restrições por convicção:
     - "vegano" → TODOS os alimentos de "Carnes e Peixes", "Laticínios", e "Ovo" são adicionados a `restricoes`.
     - "vegetariano" → TODOS os alimentos de "Carnes e Peixes" são adicionados (ovos e laticínios OK).

3. **Classificação de severidade.**
   - **Tipo A — Alergia/Intolerância:** Tolerância ZERO. Se o alimento aparecer, plano é rejeitado integralmente. Aviso obrigatório na resposta (RN-021).
   - **Tipo B — Convicção (vegano/vegetariano):** Tolerância ZERO. Aviso na resposta. Metas proteicas são ajustadas para fontes vegetais (RN-022).
   - **Tipo C — Preferência ("não gosto muito"):** Processado como `preferencias` negativas. O sistema evita, mas se for necessário para atingir macros, pode incluir com quantidade reduzida.

4. **Impacto no prompt de geração.**
   - As restrições expandidas são inseridas no system prompt ANTES das preferências (LL-003 — restrições primeiro têm mais peso).
   - Texto exato no prompt: _"RESTRIÇÕES (TOLERÂNCIA ZERO — se algum destes alimentos aparecer, a resposta será rejeitada): [lista expandida]"_

5. **Impacto nos 3 planos.**
   - **TODOS os 3 planos** devem respeitar as restrições. Não existe "plano A sem restrições e plano B com". A restrição se aplica uniformemente.
   - **Ajuste de macros para restrições severas:**
     - Se vegano + ganho de massa → fontes proteicas: tofu, soja, grão de bico, lentilha, quinoa. Meta proteica pode ser reduzida em até 15% se impossível atingir (com aviso — RN-023).
   - **Ajuste dos eixos:**
     - Se vegano → "Tradicional Brasileiro" mantém arroz e feijão, mas proteína animal é substituída por proteína vegetal.
     - Se sem glúten → "Prático & Rápido" evita pães e massas; foca em bowls e saladas.
     - Se intolerante a lactose → "Funcional & Nutrientes" usa leites vegetais e queijos sem lactose.

6. **Validação pós-geração específica para restrições.**
   - O `PlanValidator` varre CADA alimento de CADA plano contra a lista de restrições expandida.
   - Se encontrar violação → o alimento é removido e substituído pelo similar mais próximo da mesma categoria que NÃO está na lista de restrições.
   - Se não houver substituto viável → o plano é rejeitado. Nova chamada à IA com mensagem: _"O plano continha [alimento proibido]. Refaça sem ele."_

7. **Adição de avisos na resposta.**
   - Para alergias (Tipo A): _"⚠️ Este plano exclui [alérgeno] devido à sua restrição. Sempre confirme com seu médico."_ (RN-021)
   - Para condições médicas (gravidez, diabetes): avisos específicos (RN-071, RN-072).
   - Para veganismo com meta proteica reduzida: _"⚠️ Atingir sua meta proteica com restrições veganas pode exigir suplementação."_ (RN-023)
   - Os avisos aparecem tanto no JSON de resposta quanto no PDF.

**Pós-condição:**
- Os 3 planos gerados NÃO contêm nenhum alimento da lista de restrições expandida.
- Os avisos apropriados foram incluídos na resposta.
- A sessão de geração registra `condicoes` detectadas para análise de qualidade.

**Exceções:**

| O que pode dar errado | Tratamento |
|----------------------|------------|
| Restrição elimina 80%+ do catálogo (ex: "só como frango, arroz e banana") | Plano gerado com variação limitada. Aviso: _"Com poucos alimentos disponíveis, a variação entre planos é reduzida."_ |
| Restrição conflita com objetivo (ex: vegano + ganho de massa com meta proteica muito alta) | Meta proteica reduzida em até 15%. Aviso claro sobre possível necessidade de suplementação. |
| Detecção incorreta de condição médica (ex: "minha dieta é diabética de tão doce" — ironia) | O `ExtractorService` pode classificar errado. Como é melhor pecar pelo excesso de zelo, mostrar o aviso de diabetes mesmo assim. |
| Usuário menciona transtorno alimentar (anorexia, bulimia) | **BLOQUEAR imediatamente.** Não gerar planos. Retornar mensagem de apoio com recomendação profissional (RN-073). |

---

## Fluxo 4: Visualização e Exportação dos Planos

**Ator:** Usuário

**Pré-condição:**
- Os 3 planos foram gerados com sucesso (Fluxo 1 concluído).
- O frontend recebeu o JSON completo (`DietGenerateResponse`).

**Passos:**

1. **Transição para tela de resultados.**
   - Overlay de loading desaparece.
   - Tela de input é escondida (`hidden`).
   - Tela de resultados é exibida com animação de entrada (`fadeIn`).

2. **Seção de sumário do paciente.**
   - Cards no topo da tela:
     - TMB calculada (kcal/dia)
     - GET (kcal/dia)
     - Objetivo detectado (com ícone: 📉 Perda / ⚖️ Manutenção / 💪 Ganho)
     - Peso e altura informados
   - Abaixo: _"Paciente: [nome]_ | _Sexo: [masculino/feminino]_ | _Idade: [X] anos"_
   - Link: _"Não é você? Editar dados"_ → volta para tela de input com texto original preservado.

3. **Navegação entre planos.**
   - **Desktop (≥ 768px):** 3 colunas lado a lado. Cada plano é um card completo visível simultaneamente.
   - **Mobile (< 768px):** Accordion vertical. Apenas 1 plano expandido por vez. Abas no topo: "Tradicional | Funcional | Prático".
   - Scroll suave até o plano correspondente ao clicar na aba.

4. **Conteúdo de cada card de plano:**

   **Cabeçalho:**
   - Nome do plano (ex: "Tradicional Brasileiro") com badge do eixo.
   - Descrição do plano (2-4 frases explicando a lógica).

   **Resumo de macros:**
   - 3 cards horizontais: Proteína (g), Carboidrato (g), Gordura (g).
   - Barra de progresso visual: % de cada macro em relação ao total calórico.

   **Refeições (tabela):**
   - Cada refeição é uma seção com título (ex: "Café da Manhã — 07:00 — 520 kcal").
   - Tabela com colunas: Alimento | Qtde (g) | Prot | Carb | Gord | kcal.
   - Medida caseira entre parênteses quando disponível (ex: "Arroz Branco: 150g (≈ 4 colheres de sopa)").
   - Linha de totais da refeição ao final.

   **Totais do plano:**
   - Linha destacada: kcal totais | proteína total | carbo total | gordura total.
   - Comparação com a meta: "95% da meta calórica ✓" ou "⚠️ 88% — um pouco abaixo" (se fora da margem).

5. **Ações disponíveis para cada plano:**

   | Ação | Ícone | Comportamento |
   |------|:-----:|---------------|
   | **Baixar PDF** | 📄 | Abre `GET /api/diet/{pdf_uuid}/pdf` em nova aba. Download inicia automaticamente. |
   | **Copiar plano** | 📋 | Copia o conteúdo textual do plano (formato lista) para clipboard. Toast: "Plano copiado!" |
   | **Compartilhar** | 🔗 | Copia o link do PDF para clipboard. Toast: "Link copiado! Válido por 7 dias." |

   **Observação:** "Baixar PDF" baixa o PDF consolidado com TODOS os 3 planos + capa. "Copiar plano" copia apenas o plano atual (1 dos 3).

6. **Ações globais (abaixo dos 3 planos):**

   | Ação | Ícone | Comportamento |
   |------|:-----:|---------------|
   | **Gerar Novamente** | 🔄 | **Fluxo 5 (Regeneração).** |
   | **Novo Paciente** | ➕ | Volta para tela de input com campos limpos. |

7. **Seção de feedback (Could Have — RF-070 a RF-072):**
   - Abaixo de cada plano: "Este plano foi útil?" 👍 👎
   - Se 👎 → abre mini-formulário com opções: "Alimentos repetidos", "Quantidades irreais", "Não gostei das combinações", "Outro".
   - Feedback salvo via `POST /api/diet/{sessao_id}/feedback`.

8. **Disclaimer obrigatório (visível em TODA a tela de resultados):**
   - Texto fixo no rodapé da página:
   > ⚠️ **Aviso importante:** Este plano alimentar é gerado automaticamente e não substitui a consulta com um nutricionista ou médico. Antes de iniciar qualquer dieta, consulte um profissional de saúde. (RN-070)

**Pós-condição:**
- Usuário visualiza os 3 planos com todas as ações disponíveis.
- PDF pode ser baixado a qualquer momento (dentro de 7 dias).
- Usuário pode interagir com cada plano individualmente (copiar, feedback).

**Exceções:**

| O que pode dar errado | Tratamento |
|----------------------|------------|
| PDF expirou (> 7 dias) | Link de download retorna 404. Mensagem: _"PDF expirado. Gere novos planos para obter um novo PDF."_ |
| Clipboard API não suportada (navegador antigo) | Fallback: selecionar texto e mostrar "Pressione Ctrl+C para copiar". |
| PDF não foi gerado (erro na Etapa 14 do Fluxo 1) | Botão "Baixar PDF" desabilitado com tooltip: _"PDF não disponível para esta geração."_ |
| Usuário recarrega a página (anônimo, sem token JWT) | Resultados são perdidos. Apenas o link do PDF (se salvo) permite reacessar. Call-to-action após geração: _"Crie uma conta gratuita para não perder seus planos."_ |

---

## Fluxo 5: Regeneração de Planos

**Ator:** Usuário

**Pré-condição:**
- Uma geração anterior foi concluída e o usuário está na tela de resultados (Fluxo 4).
- O input original está preservado no estado da sessão (frontend ou backend).

**Passos:**

1. **Usuário clica em "Gerar Novamente" (🔄).**
   - Botão está disponível na tela de resultados (Fluxo 4, Etapa 6).

2. **Confirmação (opcional, Could Have):**
   - Modal de confirmação: _"Novos planos substituirão os atuais. Deseja continuar?"_
   - Botões: "Sim, gerar novos" / "Cancelar".
   - Se cancelar → permanece na tela de resultados.

3. **Reenvio da requisição.**
   - O MESMO texto original é reenviado para `POST /api/diet/generate`.
   - O backend NÃO sabe que é uma regeneração — processa como se fosse uma requisição nova.
   - Nova `SessaoGeracao` é criada (não sobrescreve a anterior).

4. **O que muda na nova geração:**

   | Aspecto | Comportamento |
   |---------|---------------|
   | **Texto original** | IDÊNTICO ao da geração anterior. |
   | **Perfil extraído** | IDÊNTICO (mesmo texto → mesmos campos extraídos). |
   | **Cálculo nutricional** | IDÊNTICO (determinístico). |
   | **Planos gerados** | **DIFERENTES.** Temperatura 0.7 + seed aleatória geram variação. |
   | **Nomes dos planos** | **DIFERENTES.** Novos UUIDs, nova URL de PDF. |
   | **Sessão anterior** | **PRESERVADA.** Continua acessível no histórico (se autenticado) ou pelo link antigo. |

   **Garantia de variação entre gerações:**
   - A temperatura de 0.7 garante variação natural entre chamadas.
   - Se o usuário clicar "Gerar Novamente" 3x seguidas e receber planos muito similares entre as gerações, o sistema NÃO tem como evitar (não há estado entre sessões de geração).
   - Na v2: adicionar parâmetro `seed` ou `variation_id` para forçar diversidade entre gerações consecutivas.

5. **Transição para nova tela de resultados.**
   - A tela de resultados é re-renderizada com os novos planos.
   - A geração anterior NÃO é exibida lado a lado (usuário vê apenas a nova).
   - Se usuário autenticado → pode acessar a geração anterior pelo histórico (`/api/diet/history`).

6. **Usuário insatisfeito após múltiplas regenerações.**
   - Se o usuário clicar "Gerar Novamente" 3x em menos de 2 minutos, o frontend exibe sugestão proativa:
     > _"Percebemos que você já gerou 3 variações. Que tal ajustar sua descrição para obter resultados mais diferentes? Tente adicionar mais alimentos preferidos ou mudar o foco da sua rotina."_

**Pós-condição:**
- Nova `SessaoGeracao` criada com nova trinca de planos.
- PDF novo gerado com novo UUID.
- Usuário visualiza os novos planos.
- Gerações anteriores permanecem acessíveis (histórico ou links temporários).

**Exceções:**

| O que pode dar errado | Tratamento |
|----------------------|------------|
| API DeepSeek retorna planos quase idênticos aos anteriores | Não detectável na v1 (sem comparação entre sessões). Na v2: armazenar hash dos planos e comparar. |
| Usuário regenera 5x em 5 minutos (abuso) | Rate limiting por IP (10 req/min) cobre isso naturalmente. |
| Input original foi perdido (usuário recarregou a página como anônimo) | Botão "Gerar Novamente" escondido. Apenas "Novo Paciente" disponível (input limpo). |
| Usuário quer "voltar" para a geração anterior | Se autenticado: histórico. Se anônimo: impossível (a menos que tenha salvo o link do PDF anterior). |

---

## 📊 Mapa de Navegação entre Fluxos

```
                    ┌──────────────────────┐
                    │   Usuário acessa o   │
                    │       sistema        │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Tela de input       │
                    │  (caixa de texto)    │
                    └──────────┬───────────┘
                               │ usuário digita e envia
                               ▼
                    ┌──────────────────────┐
                    │  Fluxo 1: Geração    │
                    │  (happy path)        │
                    └─────┬──────┬────┬────┘
                          │      │    │
                 ┌────────┘      │    └────────┐
                 ▼               ▼             ▼
          ┌────────────┐  ┌────────────┐  ┌────────────┐
          │ Campos OK  │  │ Input      │  │ Restrições │
          │ → Fluxo 1  │  │ incompleto │  │ detectadas │
          │ continua   │  │ → Fluxo 2  │  │ → Fluxo 3  │
          └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
                │               │                │
                └───────────────┴────────────────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │  Tela de Resultados  │
                    │  → Fluxo 4           │
                    └─────┬──────┬────┬────┘
                          │      │    │
                 ┌────────┘      │    └────────┐
                 ▼               ▼             ▼
          ┌────────────┐  ┌────────────┐  ┌────────────┐
          │ Baixar PDF │  │ Copiar/    │  │ Gerar      │
          │             │  │ Compartil. │  │ Novamente  │
          │             │  │            │  │ → Fluxo 5  │
          └────────────┘  └────────────┘  └────────────┘
```

---

> **Para a IA que vai gerar código:** Cada passo numerado nestes fluxos corresponde a uma função, validação ou branch no código. Use os fluxos como checklist de implementação. Ao terminar uma feature, percorra o fluxo correspondente e verifique se todos os passos e exceções estão cobertos.
