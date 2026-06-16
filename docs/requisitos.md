# 📋 Requisitos do Sistema — Diet Plan Generator

> **Propósito:** Documento de levantamento de requisitos funcionais e não-funcionais, com priorização MoSCoW, para guiar o desenvolvimento do MVP e das versões subsequentes.
>
> **Público:** Desenvolvedores, Product Owner, QA, e IAs que vão gerar código.
>
> **Convenção:** Cada requisito tem ID único. Requisitos funcionais usam `RF-XXX`, não-funcionais usam `RNF-XXX`. A prioridade segue MoSCoW: 🔴 Must / 🟡 Should / 🟢 Could / ⚪ Won't.

---

## 1. Requisitos Funcionais (RF)

### 1.1 Módulo de Input do Usuário

| ID | Requisito | Prioridade | Regra Relacionada |
|----|-----------|:----------:|:-----------------:|
| **RF-001** | O sistema **deve** aceitar uma descrição em texto livre (linguagem natural) onde o usuário descreve sua rotina, objetivos, preferências alimentares e restrições. O input é uma única string de texto. | 🔴 Must | RN-034 |
| **RF-002** | O sistema **deve** aceitar texto entre 20 e 2000 caracteres. Inputs fora desse intervalo devem ser rejeitados com mensagem explicativa. | 🔴 Must | RN-034 |
| **RF-003** | O sistema **deve** permitir que o usuário informe opcionalmente seu e-mail para receber o PDF por e-mail. O campo de e-mail não é obrigatório para gerar os planos. | 🟡 Should | RN-120 |
| **RF-004** | O sistema **deve** exibir exemplos de inputs válidos abaixo da caixa de texto, rotacionando entre 3-5 perfis diferentes (sedentário, atleta, gestante, vegano, idoso) a cada recarga da página. | 🟢 Could | — |
| **RF-005** | O sistema **deve** oferecer um botão "Usar exemplo" que preenche automaticamente a caixa de texto com um dos exemplos, permitindo que o usuário edite antes de enviar. | 🟢 Could | — |
| **RF-006** | O sistema **deve** sanitizar o input removendo caracteres de controle, scripts (XSS) e normalizando espaços e quebras de linha antes do processamento. | 🔴 Must | — |

### 1.2 Módulo de Extração e Interpretação (NL → JSON)

| ID | Requisito | Prioridade | Regra Relacionada |
|----|-----------|:----------:|:-----------------:|
| **RF-010** | O sistema **deve** extrair do texto livre os seguintes campos estruturados: `sexo`, `idade`, `peso_kg`, `altura_cm`, `nivel_atividade`, `objetivo`, `preferencias`, `restricoes`. | 🔴 Must | RN-040 |
| **RF-011** | O sistema **deve** retornar erro claro e específico quando qualquer um dos campos obrigatórios (`sexo`, `idade`, `peso_kg`, `altura_cm`) não puder ser extraído. A mensagem deve listar exatamente quais campos estão faltando. | 🔴 Must | RN-030, RN-040 |
| **RF-012** | O sistema **deve** inferir o `nivel_atividade` a partir de descrições textuais. Ex: "malho 4x por semana" → moderado; "não faço exercício" → sedentário; "treino todo dia" → ativo. Se ambíguo, assumir sedentário. | 🔴 Must | RN-031 |
| **RF-013** | O sistema **deve** inferir o `objetivo` quando não explicitamente declarado, usando o IMC como heurística (IMC < 18.5 → ganho; 18.5-24.9 → manutenção; ≥ 25 → perda). Deve informar o usuário sobre o objetivo inferido. | 🔴 Must | RN-032 |
| **RF-014** | O sistema **deve** identificar e separar `preferencias` (alimentos que o usuário gosta/quer incluir) de `restricoes` (alimentos que o usuário rejeita/não pode consumir). | 🔴 Must | RN-020, RN-051 |
| **RF-015** | O sistema **deve** detectar menção a condições especiais no texto (gravidez, diabetes, hipertensão, veganismo, alergias) e sinalizá-las para tratamento diferenciado na geração dos planos. | 🔴 Must | RN-071, RN-072 |
| **RF-016** | O sistema **deve** validar que os valores extraídos estão dentro de intervalos fisiologicamente plausíveis: idade 1-120, peso 20-500 kg, altura 50-280 cm. Valores fora devem ser rejeitados. | 🔴 Must | RN-041 |

### 1.3 Módulo de Cálculo Nutricional

| ID | Requisito | Prioridade | Regra Relacionada |
|----|-----------|:----------:|:-----------------:|
| **RF-020** | O sistema **deve** calcular a TMB (Taxa Metabólica Basal) usando a equação de Mifflin-St Jeor, com fórmulas distintas para sexo masculino e feminino. | 🔴 Must | RN-042 |
| **RF-021** | O sistema **deve** calcular o GET (Gasto Energético Total) multiplicando a TMB pelo fator de atividade correspondente: sedentário (1.2), moderado (1.55), ativo (1.725). | 🔴 Must | — |
| **RF-022** | O sistema **deve** distribuir os macronutrientes (proteína, carboidrato, gordura) em gramas com base no GET e no objetivo, usando as distribuições padrão: perda de peso (35/35/30), manutenção (25/50/25), ganho de massa (30/45/25). | 🔴 Must | — |
| **RF-023** | O sistema **deve** rejeitar qualquer plano cujo GET esteja fora do intervalo de segurança: 1200-4000 kcal/dia (1800-4000 para gestantes; 1500-4000 para adolescentes). | 🔴 Must | RN-060, RN-061, RN-062 |
| **RF-024** | O sistema **deve** dividir as metas calóricas e de macros entre as refeições conforme a distribuição definida para cada plano. A distribuição deve ser assimétrica (ex: almoço > jantar > café > lanche). | 🔴 Must | RN-006 |

### 1.4 Módulo de Geração dos Planos (IA)

| ID | Requisito | Prioridade | Regra Relacionada |
|----|-----------|:----------:|:-----------------:|
| **RF-030** | O sistema **deve** gerar exatamente 3 planos alimentares distintos para cada requisição. | 🔴 Must | RN-001 |
| **RF-031** | Os 3 planos **devem** seguir 3 eixos de diferenciação fixos: (A) Tradicional/Brasileiro, (B) Funcional/Alta Densidade Nutricional, (C) Prático/Rápido Preparo. | 🔴 Must | RN-002, RN-003 |
| **RF-032** | Cada plano **deve** conter entre 4 e 6 refeições nomeadas, com nomes contextualizados ao Brasil: "Café da Manhã", "Almoço", "Lanche da Tarde", "Jantar", e opcionalmente "Lanche da Manhã" e/ou "Ceia". | 🔴 Must | RN-005, RN-090 |
| **RF-033** | Pelo menos 40% dos alimentos de cada plano **devem** ser diferentes dos alimentos dos outros dois planos. A sobreposição máxima permitida é de 60%. | 🔴 Must | RN-004 |
| **RF-034** | Nenhum alimento da lista de `restricoes` do usuário **pode** aparecer em qualquer um dos 3 planos. Esta é uma validação _hard_ pós-geração. | 🔴 Must | RN-020 |
| **RF-035** | O sistema **deve** usar o banco de dados `data/foods.json` como fonte autoritativa de alimentos. Se a IA sugerir um alimento que não existe no banco, o validador **deve** substituí-lo pelo match mais próximo ou removê-lo. | 🔴 Must | RN-052 |
| **RF-036** | O sistema **deve** gerar uma explicação em linguagem natural para cada plano, com 2-4 frases, descrevendo a lógica por trás daquele plano e para qual perfil ele é mais adequado. | 🟡 Should | — |
| **RF-037** | O sistema **deve** garantir que cada plano atinja as metas de macronutrientes com margem de erro de ±10% por macro individual. | 🔴 Must | RN-010 |

### 1.5 Módulo de Validação Pós-Geração

| ID | Requisito | Prioridade | Regra Relacionada |
|----|-----------|:----------:|:-----------------:|
| **RF-040** | O sistema **deve** validar que todo alimento em cada plano existe no banco `foods.json`. Alimentos não encontrados devem ser substituídos pelo match mais próximo ou removidos, com log do ocorrido. | 🔴 Must | RN-035 |
| **RF-041** | O sistema **deve** validar que nenhuma quantidade de alimento está fora do intervalo 30g-500g. Quantidades fora devem ser ajustadas para o limite mais próximo. | 🔴 Must | RN-014 |
| **RF-042** | O sistema **deve** validar que a soma calórica de cada plano está entre 95% e 105% do GET calculado. Planos fora devem ser recalculados ou, se impossível, sinalizados com aviso. | 🔴 Must | RN-015 |
| **RF-043** | O sistema **deve** validar que nenhum alimento proibido (restricoes) aparece nos planos. Se aparecer, o plano deve ser rejeitado e regenerado. | 🔴 Must | RN-020, RN-034 |
| **RF-044** | O sistema **deve** registrar em log toda falha de validação, incluindo: plano afetado, regra violada, valor esperado vs valor real, e ação tomada (correção ou rejeição). | 🟡 Should | — |

### 1.6 Módulo de Apresentação dos Planos

| ID | Requisito | Prioridade | Regra Relacionada |
|----|-----------|:----------:|:-----------------:|
| **RF-050** | O sistema **deve** exibir os 3 planos lado a lado (desktop) ou em sequência vertical (mobile) com navegação por abas ou accordion. | 🔴 Must | — |
| **RF-051** | Cada plano exibido **deve** incluir: nome do plano, explicação (2-4 frases), GET calórico, tabela de macros totais, e a lista de refeições com alimentos, quantidades e valores nutricionais. | 🔴 Must | RN-110, RN-111 |
| **RF-052** | O sistema **deve** exibir quantidades em gramas como unidade principal e, quando disponível, medida caseira entre parênteses (ex: "150g (≈ 4 colheres de sopa)"). | 🟡 Should | RN-100, RN-101 |
| **RF-053** | O sistema **deve** gerar um PDF consolidado contendo: capa (nome do paciente, data, TMB), 1 página por plano (GET, tabela de macros, tabela de refeições), e disclaimer final. | 🔴 Must | RN-113 |
| **RF-054** | O sistema **deve** disponibilizar o PDF para download via link na resposta da API e botão na interface. O PDF **deve** ser acessível via URL única (UUID) por 7 dias. | 🔴 Must | RN-131 |
| **RF-055** | O sistema **deve** oferecer um botão "Copiar plano" que copia o conteúdo textual do plano para a área de transferência em formato legível. | 🟢 Could | — |
| **RF-056** | O sistema **deve** oferecer um botão "Compartilhar" que gera um link público temporário para o plano (mesmo link do PDF, válido por 7 dias). | 🟢 Could | — |
| **RF-057** | O sistema **deve** permitir que o usuário gere novos planos a partir do mesmo input, mantendo os anteriores acessíveis via histórico (se autenticado) ou links temporários (se não autenticado). | 🟡 Should | — |

### 1.7 Módulo de Autenticação e Histórico

| ID | Requisito | Prioridade | Regra Relacionada |
|----|-----------|:----------:|:-----------------:|
| **RF-060** | O sistema **deve** permitir que o usuário gere planos **sem criar conta** (modo anônimo). Nesse modo, o acesso ao plano é apenas via link temporário. | 🔴 Must | RNF-002 |
| **RF-061** | O sistema **deve** oferecer cadastro opcional (nome, e-mail, senha) para usuários que desejam salvar histórico de planos. | 🟡 Should | RN-140 |
| **RF-062** | O sistema **deve** permitir login com e-mail e senha, retornando token JWT para autenticação nas chamadas subsequentes. | 🟡 Should | — |
| **RF-063** | O sistema **deve** oferecer recuperação de senha por e-mail com token de uso único e expiração de 1 hora. | 🟢 Could | — |
| **RF-064** | Para usuários autenticados, o sistema **deve** exibir o histórico de planos gerados, contendo: data, objetivo, GET, link para PDF (se dentro da retenção de 7 dias). | 🟡 Should | RN-140, RN-141 |
| **RF-065** | O sistema **deve** permitir que o usuário exclua planos do histórico e solicite a exclusão de todos os seus dados (LGPD). | 🟡 Should | RN-123 |

### 1.8 Módulo de Feedback

| ID | Requisito | Prioridade | Regra Relacionada |
|----|-----------|:----------:|:-----------------:|
| **RF-070** | O sistema **deve** exibir botões de feedback (👍/👎) para cada plano, permitindo que o usuário avalie a qualidade do plano gerado. | 🟢 Could | — |
| **RF-071** | O sistema **deve** permitir que o usuário, ao avaliar negativamente, selecione um motivo rápido (ex: "alimentos repetidos", "quantidades irreais", "não gostei das combinações", "outro") e opcionalmente digite um comentário. | 🟢 Could | — |
| **RF-072** | Feedbacks negativos **devem** ser registrados em log separado para análise de qualidade do modelo de geração. | 🟢 Could | — |

---

## 2. Requisitos Não-Funcionais (RNF)

### 2.1 Performance

| ID | Requisito | Prioridade | Métrica |
|----|-----------|:----------:|---------|
| **RNF-001** | O sistema **deve** retornar os 3 planos completos (extração + cálculo + geração + validação + PDF) em **menos de 60 segundos** para o percentil 95 das requisições. | 🔴 Must | p95 < 60s |
| **RNF-002** | A extração NL→JSON **deve** ser concluída em **menos de 15 segundos** para o percentil 95. | 🔴 Must | p95 < 15s |
| **RNF-003** | A geração dos 3 planos pela IA **deve** ser concluída em **menos de 30 segundos** para o percentil 95. | 🔴 Must | p95 < 30s |
| **RNF-004** | O sistema **deve** suportar pelo menos **10 requisições simultâneas** sem degradação significativa de latência (sem fila serial). | 🟡 Should | 10 req concorrentes |
| **RNF-005** | O sistema **deve** implementar timeout de **90 segundos** por requisição. Se o tempo for excedido, retornar erro 504 com mensagem amigável. | 🔴 Must | Timeout 90s |

### 2.2 Disponibilidade e Resiliência

| ID | Requisito | Prioridade | Métrica |
|----|-----------|:----------:|---------|
| **RNF-010** | O sistema **deve** ter disponibilidade de **99,5%** no horário comercial (8h-22h, horário de Brasília). | 🟡 Should | Uptime 99.5% |
| **RNF-011** | Se a API LLM externa estiver indisponível, o sistema **deve** retornar erro claro em **menos de 10 segundos** (não travar indefinidamente) com mensagem: "Nosso serviço de geração está temporariamente indisponível. Tente novamente em alguns minutos." | 🔴 Must | Fail fast < 10s |
| **RNF-012** | O sistema **deve** implementar retry com backoff exponencial (máximo 2 tentativas) para falhas transientes na API LLM. | 🟡 Should | 2 retries |
| **RNF-013** | O cálculo nutricional (TMB/GET/macros) **deve** funcionar offline, sem dependência de serviços externos. A LLM só é necessária para extração e geração. | 🔴 Must | Offline |

### 2.3 Segurança

| ID | Requisito | Prioridade | Métrica |
|----|-----------|:----------:|---------|
| **RNF-020** | Todo tráfego entre cliente e servidor **deve** usar HTTPS em produção. | 🔴 Must | TLS 1.2+ |
| **RNF-021** | Senhas de usuários **devem** ser armazenadas com hash bcrypt (nunca em texto puro ou SHA-256). | 🔴 Must | bcrypt |
| **RNF-022** | O sistema **deve** implementar rate limiting no endpoint de geração: no máximo **10 requisições por minuto por IP** para usuários não autenticados. | 🔴 Must | 10 req/min/IP |
| **RNF-023** | Dados de saúde (peso, altura, condições médicas, restrições alimentares) **não devem** ser logados em texto puro. Devem ser mascarados ou armazenados em banco segregado com acesso restrito. | 🔴 Must | LGPD |
| **RNF-024** | O sistema **deve** implementar cabeçalhos de segurança HTTP: `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`. | 🟡 Should | Headers |
| **RNF-025** | Tokens JWT **devem** expirar em 24 horas. A chave secreta **deve** ser configurada via variável de ambiente (`JWT_SECRET_KEY`) e nunca hardcoded. | 🔴 Must | JWT 24h |

### 2.4 Usabilidade e Acessibilidade

| ID | Requisito | Prioridade | Métrica |
|----|-----------|:----------:|---------|
| **RNF-030** | O sistema **deve** funcionar em navegadores modernos: Chrome, Firefox, Safari e Edge (últimas 2 versões). | 🔴 Must | 4 navegadores |
| **RNF-031** | A interface **deve** ser responsiva e funcionar em dispositivos com largura de tela a partir de 320px (smartphones) até 1920px (desktop). | 🔴 Must | 320-1920px |
| **RNF-032** | O sistema **deve** ter contraste de cores suficiente (WCAG AA, razão mínima 4.5:1 para texto normal) e todos os elementos interativos devem ser navegáveis por teclado. | 🟡 Should | WCAG AA |
| **RNF-033** | O sistema **deve** exibir indicador de carregamento (spinner ou barra de progresso) com mensagem contextual durante o processamento (ex: "Analisando sua rotina...", "Calculando necessidades nutricionais...", "Gerando os 3 planos..."). | 🔴 Must | Loading states |
| **RNF-034** | Todo erro retornado ao usuário **deve** ser em português, em linguagem clara e sem jargão técnico. Ex: "Não consegui identificar seu peso. Tente algo como: 'tenho 70kg'." — NUNCA "KeyError: 'peso_kg'". | 🔴 Must | PT-BR |
| **RNF-035** | A interface **deve** ter tempo de carregamento inicial (First Contentful Paint) inferior a **2 segundos** em conexão 4G. | 🟡 Should | FCP < 2s |

### 2.5 Manutenibilidade e Código

| ID | Requisito | Prioridade | Métrica |
|----|-----------|:----------:|---------|
| **RNF-040** | O código **deve** seguir a estrutura de camadas existente: `routers/` → `services/` → `repositories/` → `database/`, com separação clara de responsabilidades. | 🔴 Must | — |
| **RNF-041** | Todas as regras de negócio **devem** referenciar seus IDs (`RN-XXX`) em comentários no código para rastreabilidade. | 🟡 Should | RN-XXX |
| **RNF-042** | O sistema **deve** ter cobertura de testes unitários de pelo menos **80%** para os módulos de cálculo nutricional (determinísticos) e **60%** para os módulos de validação. | 🟡 Should | 80% / 60% |
| **RNF-043** | Logs **devem** ser estruturados em JSON e incluir: timestamp, nível, módulo, `request_id` (UUID), mensagem, e metadados relevantes. | 🟡 Should | JSON logs |
| **RNF-044** | A chave de API da LLM externa **deve** ser configurada via variável de ambiente e nunca versionada no repositório. | 🔴 Must | `.env` |

### 2.6 Escalabilidade

| ID | Requisito | Prioridade | Métrica |
|----|-----------|:----------:|---------|
| **RNF-050** | O sistema **deve** ser stateless, permitindo escalonamento horizontal com múltiplas instâncias atrás de um load balancer. | 🟡 Should | Stateless |
| **RNF-051** | O cache de planos em memória **pode** ser local (por instância). Não é necessário cache distribuído na v1. | 🔴 Must | Cache local |

---

## 3. Matriz de Priorização (MoSCoW)

### 🔴 Must Have (MVP — obrigatório para lançar)

| ID | Requisito | Módulo |
|----|-----------|--------|
| RF-001 | Aceitar texto livre como input | Input |
| RF-002 | Validar tamanho do input (20-2000 chars) | Input |
| RF-006 | Sanitizar input (XSS, caracteres de controle) | Input |
| RF-010 | Extrair campos estruturados do texto (NL→JSON) | Extração |
| RF-011 | Erro claro quando faltam campos obrigatórios | Extração |
| RF-012 | Inferir nível de atividade | Extração |
| RF-013 | Inferir objetivo por IMC | Extração |
| RF-014 | Separar preferências de restrições | Extração |
| RF-015 | Detectar condições especiais (gravidez, etc.) | Extração |
| RF-016 | Validar intervalos fisiológicos | Extração |
| RF-020 | Calcular TMB (Mifflin-St Jeor) | Cálculo |
| RF-021 | Calcular GET (fator de atividade) | Cálculo |
| RF-022 | Distribuir macronutrientes | Cálculo |
| RF-023 | Bloquear GET fora do intervalo seguro | Cálculo |
| RF-024 | Distribuir calorias entre refeições | Cálculo |
| RF-030 | Gerar exatamente 3 planos | Geração |
| RF-031 | Seguir 3 eixos de diferenciação | Geração |
| RF-032 | 4-6 refeições por plano | Geração |
| RF-033 | Máximo 60% de sobreposição entre planos | Geração |
| RF-034 | Zero alimentos proibidos nos planos | Geração |
| RF-035 | Usar foods.json como fonte autoritativa | Geração |
| RF-037 | Macros com margem de erro ±10% | Geração |
| RF-040 | Validar alimentos contra foods.json | Validação |
| RF-041 | Validar quantidades (30g-500g) | Validação |
| RF-042 | Validar soma calórica (95%-105% GET) | Validação |
| RF-043 | Rejeitar planos com alimentos proibidos | Validação |
| RF-050 | Exibir 3 planos lado a lado / vertical | Apresentação |
| RF-051 | Informações obrigatórias por plano | Apresentação |
| RF-053 | Gerar PDF consolidado | Apresentação |
| RF-054 | Download PDF por UUID (7 dias) | Apresentação |
| RF-060 | Gerar planos sem cadastro (anônimo) | Auth |
| RNF-001 | Latência total < 60s (p95) | Performance |
| RNF-002 | Extração NL→JSON < 15s (p95) | Performance |
| RNF-003 | Geração IA < 30s (p95) | Performance |
| RNF-005 | Timeout 90s por requisição | Performance |
| RNF-011 | Fail fast se API LLM offline (< 10s) | Resiliência |
| RNF-013 | Cálculo nutricional offline | Resiliência |
| RNF-020 | HTTPS em produção | Segurança |
| RNF-021 | bcrypt para senhas | Segurança |
| RNF-022 | Rate limiting (10 req/min/IP) | Segurança |
| RNF-023 | Não logar dados de saúde em texto puro | Segurança |
| RNF-025 | JWT expira 24h, chave via .env | Segurança |
| RNF-030 | Compatível com 4 navegadores | Usabilidade |
| RNF-031 | Responsivo (320px-1920px) | Usabilidade |
| RNF-033 | Indicador de carregamento contextual | Usabilidade |
| RNF-034 | Erros em PT-BR sem jargão | Usabilidade |
| RNF-040 | Seguir estrutura de camadas | Código |
| RNF-044 | Chave LLM via .env | Código |
| RNF-051 | Cache local por instância | Escalabilidade |

### 🟡 Should Have (importante, mas não bloqueia MVP)

| ID | Requisito | Módulo |
|----|-----------|--------|
| RF-003 | E-mail opcional para receber PDF | Input |
| RF-036 | Explicação em NL para cada plano | Geração |
| RF-044 | Log de falhas de validação | Validação |
| RF-052 | Medidas caseiras como complemento | Apresentação |
| RF-057 | Regenerar planos do mesmo input | Apresentação |
| RF-061 | Cadastro opcional (nome, e-mail, senha) | Auth |
| RF-062 | Login com JWT | Auth |
| RF-064 | Histórico de planos (autenticados) | Auth |
| RF-065 | Exclusão de dados (LGPD) | Auth |
| RNF-004 | 10 requisições simultâneas | Performance |
| RNF-010 | 99.5% uptime (horário comercial) | Disponibilidade |
| RNF-012 | Retry com backoff (2 tentativas) | Resiliência |
| RNF-024 | Headers de segurança HTTP | Segurança |
| RNF-032 | WCAG AA (contraste e teclado) | Acessibilidade |
| RNF-035 | FCP < 2s | Usabilidade |
| RNF-041 | RN-XXX nos comentários do código | Código |
| RNF-042 | 80% cobertura de testes (cálculo) | Código |
| RNF-043 | Logs estruturados (JSON) | Código |
| RNF-050 | Stateless para escalonamento horizontal | Escalabilidade |

### 🟢 Could Have (desejável, pós-MVP)

| ID | Requisito | Módulo |
|----|-----------|--------|
| RF-004 | Exemplos rotativos de input | Input |
| RF-005 | Botão "Usar exemplo" | Input |
| RF-055 | Botão "Copiar plano" | Apresentação |
| RF-056 | Botão "Compartilhar" | Apresentação |
| RF-063 | Recuperação de senha | Auth |
| RF-070 | Feedback 👍/👎 por plano | Feedback |
| RF-071 | Motivo do feedback negativo | Feedback |
| RF-072 | Log de feedbacks negativos | Feedback |

### ⚪ Won't Have (fora do escopo atual — ver `visao.md` seção 5)

| Item | Descrição |
|------|-----------|
| **Chat multi-turno** | Refinar planos via conversa com IA |
| **Integração com wearables** | Apple Watch, Garmin, etc. |
| **Diário alimentar** | Registro de refeições consumidas |
| **App mobile nativo** | iOS e Android |
| **Dietas médicas específicas** | Renal, cetogênica terapêutica, pós-bariátrica |
| **Integração com delivery** | iFood, Rappi |
| **Treinos de exercício** | Geração de fichas de treino |
| **Acompanhamento de evolução** | Peso e medidas ao longo do tempo |
| **Recomendação de suplementos** | Whey, creatina, etc. |
| **Suporte multilíngue** | Inglês, espanhol |
| **Pagamento / assinatura** | Planos pagos, checkout |

---

## 4. Resumo Quantitativo

| Prioridade | RF | RNF | Total |
|:----------:|:--:|:---:|:-----:|
| 🔴 Must Have | 29 | 16 | **45** |
| 🟡 Should Have | 9 | 10 | **19** |
| 🟢 Could Have | 8 | 0 | **8** |
| ⚪ Won't Have | — | — | 11 itens |
| **Total** | **46** | **26** | **72** |

---

> **Para a IA que vai gerar código:** Comece pelos 45 requisitos `Must Have`. Eles definem o MVP. Os `Should Have` podem ser implementados em seguida. Use os IDs `RF-XXX` e `RNF-XXX` nos commits e branches para rastreabilidade (ex: `feat/RF-030-gerar-3-planos`).
