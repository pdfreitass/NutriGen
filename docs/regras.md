# 📏 Regras de Negócio — Diet Plan Generator

> **Propósito:** Documento normativo com todas as regras de negócio do sistema. Cada regra tem um identificador único (`RN-XXX`) para ser referenciada no código, testes e documentação.
>
> **Público:** Desenvolvedores, QA, Product Owner, e IAs que vão gerar código a partir deste documento.
>
> **Convenção:** Toda regra usa **DEVE** (obrigatório) ou **DEVERIA** (recomendado). Regras com **DEVE** quebram o sistema se não forem cumpridas.

---

**Regras minhas que quero que a IA ao ler os documentos se atente:**
Idioma
Todo o projeto deve ser desenvolvido em Português (PT-BR).
Documentações, comentários, mensagens de erro, validações e textos exibidos ao usuário devem estar em Português.
Nomes técnicos de classes, métodos, bibliotecas e tecnologias podem permanecer em inglês quando fizer sentido.
Leitura Obrigatória

Antes de iniciar qualquer tarefa:

Ler todos os arquivos da pasta /docs.
Ler os arquivos relacionados à funcionalidade que será alterada.
Entender a arquitetura atual do projeto.
Verificar se já existe implementação semelhante.

Nenhuma alteração deve ser realizada sem essa análise prévia.

Planejamento Obrigatório

Antes de escrever qualquer código:

Explicar o que foi entendido da tarefa.
Apresentar um plano de implementação.
Informar quais arquivos serão modificados.
Informar quais arquivos serão criados (caso necessário).
Aguardar aprovação do desenvolvedor.
Criação de Arquivos e Diretórios

É proibido:

Criar arquivos sem necessidade.
Criar diretórios sem necessidade.
Duplicar funcionalidades já existentes.

Caso seja necessário criar arquivos ou diretórios:

Explicar o motivo.
Informar o benefício.
Solicitar aprovação antes da criação.
Alteração de Arquivos

Antes de alterar qualquer arquivo:

Explicar o motivo da alteração.
Informar o impacto da mudança.
Identificar possíveis riscos.
Git e Versionamento

É proibido:

Criar commits automaticamente.
Executar push automaticamente.
Executar merge automaticamente.
Criar branches automaticamente.

Toda ação Git deve ser aprovada previamente.

Commits
Nenhum commit deve ser realizado sem autorização explícita.
Sempre sugerir uma mensagem de commit antes de executá-lo.
Utilizar Conventional Commits.

Exemplos:

feat(auth): implementar autenticação JWT
fix(cliente): corrigir validação de CPF
refactor(agendamento): simplificar regra de conflito
Branches

Quando houver necessidade de envio ao repositório:

Utilizar a branch do desenvolvedor: devpedro
Nunca enviar código diretamente para main
Nunca criar branches sem autorização
Qualidade de Código

Todo código deve:

Seguir SOLID quando aplicável.
Seguir Clean Code.
Evitar duplicação.
Ser legível.
Ser de fácil manutenção.
Utilizar nomes claros e consistentes.
Segurança
Nunca armazenar senhas em texto puro.
Utilizar BCrypt para hash de senhas.
Validar todas as entradas.
Tratar exceções adequadamente.
Não expor informações sensíveis.
Banco de Dados
Não alterar estruturas existentes sem justificativa.
Não remover tabelas, colunas ou constraints sem aprovação.
Explicar impactos de qualquer alteração estrutural.
Revisão Obrigatória

Após concluir qualquer implementação:

Revisar o código gerado.
Identificar possíveis bugs.
Identificar riscos de segurança.
Identificar melhorias.
Apresentar um resumo técnico da implementação.
Regra Principal

A IA deve atuar como assistente de desenvolvimento.

A IA nunca deve assumir que pode:

Criar arquivos.
Excluir arquivos.
Renomear arquivos.
Executar comandos Git.
Alterar arquitetura.
Refatorar grandes partes do sistema.

Sem aprovação explícita do desenvolvedor.

## 1. Regras de Geração dos Planos

### 1.1 Diferenciação obrigatória entre planos

| ID | Regra |
|----|-------|
| **RN-001** | O sistema **DEVE** gerar exatamente 3 planos alimentares por requisição. Nem 2, nem 4. |
| **RN-002** | Os 3 planos **DEVEM** ser estruturalmente distintos. Não é aceitável gerar o mesmo plano com 1-2 alimentos trocados. A diferenciação **DEVE** seguir uma matriz de 3 eixos (ex: Tradicional, Funcional/Nutrientes, Prático/Rápido). |
| **RN-003** | Cada plano **DEVE** ter um nome descritivo que comunique seu diferencial (ex: "Tradicional Brasileiro", "Funcional & Nutrientes", "Prático & Rápido"). O nome não pode ser genérico como "Plano A", "Plano B", "Plano C". |
| **RN-004** | Pelo menos 40% dos alimentos de cada plano **DEVEM** ser diferentes dos alimentos dos outros dois planos. Alimentos-base como arroz e feijão podem se repetir. |
| **RN-005** | Cada plano **DEVE** conter entre 4 e 6 refeições. O número de refeições pode variar entre planos da mesma requisição. |
| **RN-006** | A distribuição calórica entre as refeições **DEVE** ser assimétrica e variar entre planos, seguindo um destes perfis ou similar: Café 20-25%, Almoço 30-35%, Lanche 15-20%, Jantar 25-30%. Nenhum plano pode ter a mesma distribuição que outro. |

### 1.2 Critérios nutricionais mínimos

| ID | Regra |
|----|-------|
| **RN-010** | Todo plano **DEVE** atender às metas de macronutrientes calculadas com margem de erro de ±10% para cada macro individual (proteína, carboidrato, gordura). |
| **RN-011** | Todo plano **DEVE** conter ao menos 1 alimento-fonte de proteína por refeição principal (almoço e jantar). Café da manhã e lanches **DEVERIAM** conter proteína, mas não é obrigatório. |
| **RN-012** | Todo plano **DEVE** conter ao menos 1 porção de vegetais ou frutas por dia. O ideal é 2-3 porções, distribuídas entre as refeições. |
| **RN-013** | Nenhum alimento individual **DEVE** representar mais de 50% das calorias totais de uma refeição. Refeições **DEVEM** ser compostas por múltiplos alimentos. |
| **RN-014** | A quantidade de qualquer alimento **DEVE** estar entre 30g e 500g. Valores fora desse intervalo são considerados irreais para consumo em uma refeição. |
| **RN-015** | A soma das calorias de todas as refeições de um plano **DEVE** estar entre 95% e 105% do GET (Gasto Energético Total) calculado para aquela rotina. |

### 1.3 Restrições alimentares

| ID | Regra |
|----|-------|
| **RN-020** | Se o usuário declarar explicitamente que **não come** um alimento, categoria ou ingrediente (ex: "não como peixe", "detesto brócolis", "nada de origem animal"), esse item **DEVE** ser excluído de **todos** os planos gerados. Taxa de violação aceitável: 0%. |
| **RN-021** | Se o usuário mencionar alergia ou intolerância (ex: "tenho intolerância à lactose", "sou alérgico a amendoim"), o sistema **DEVE** excluir o alérgeno de todos os planos **E** exibir um aviso explícito: "⚠️ Alerta: este plano exclui [alérgeno] conforme sua restrição. Sempre confirme com seu médico ou nutricionista." |
| **RN-022** | Se o usuário declarar dieta restritiva por convicção (vegano, vegetariano, ovolactovegetariano), o sistema **DEVE** respeitar a restrição em 100% dos alimentos sugeridos e **DEVE** garantir que as fontes proteicas alternativas (leguminosas, tofu, grão-de-bico) apareçam em quantidade suficiente para atingir a meta proteica. |
| **RN-023** | Se a restrição do usuário for incompatível com as metas nutricionais calculadas (ex: vegano + ganho de massa com altíssima proteína), o sistema **DEVE** gerar os planos mesmo assim, mas **DEVE** incluir um aviso: "⚠️ Atingir sua meta proteica com as restrições atuais pode exigir suplementação. Consulte um nutricionista." |

### 1.4 Input insuficiente ou ambíguo

| ID | Regra |
|----|-------|
| **RN-030** | Se o input não contiver **sexo, idade, peso e altura**, o sistema **DEVE** retornar um erro claro listando exatamente quais campos estão faltando. Exemplo: "Não consegui identificar seu peso e altura. Por favor, inclua essas informações na sua descrição." |
| **RN-031** | Se o nível de atividade for ambíguo (ex: "faço exercício de vez em quando"), o sistema **DEVE** assumir "sedentário" como padrão seguro e informar o usuário: "Assumi nível de atividade sedentário. Se não for o caso, especifique quantas vezes por semana você se exercita." |
| **RN-032** | Se o objetivo for ambíguo (ex: "quero ficar em forma"), o sistema **DEVE** inferir com base no IMC: IMC < 18.5 → ganho_de_massa, IMC 18.5-24.9 → manutencao, IMC 25-29.9 → perda_de_peso, IMC ≥ 30 → perda_de_peso. O sistema **DEVE** informar qual objetivo foi assumido e por quê. |
| **RN-033** | Se o usuário não informar nenhum alimento preferido, o sistema **DEVE** gerar planos usando apenas o banco de dados interno (foods.json), priorizando alimentos comuns da culinária brasileira. |
| **RN-034** | O input do usuário **DEVE** ter entre 20 e 2000 caracteres. Inputs menores que 20 caracteres são rejeitados com mensagem "Descreva sua rotina com mais detalhes". Inputs maiores que 2000 caracteres são truncados com aviso. |

---

## 2. Regras de Validação do Input

### 2.1 Campos obrigatórios e formato

| ID | Regra |
|----|-------|
| **RN-040** | São considerados **obrigatórios** para prosseguir com a geração: sexo biológico (masculino/feminino), idade (1-120 anos), peso (20-500 kg), altura (50-280 cm). A ausência de qualquer um desses **DEVE** bloquear a geração. |
| **RN-041** | O sistema **DEVE** validar que `idade`, `peso_kg` e `altura_cm` estão dentro dos intervalos fisiologicamente plausíveis. Valores fora do intervalo **DEVEM** ser rejeitados com mensagem específica. |
| **RN-042** | O sexo biológico **DEVE** ser "masculino" ou "feminino". Qualquer outro valor **DEVE** ser rejeitado. O cálculo da TMB (Mifflin-St Jeor) exige sexo binário. |
| **RN-043** | Se o campo `sexo` for extraído como `None` pelo LLM, o sistema **DEVE** retornar erro pedindo que o usuário especifique. |

### 2.2 Tratamento de contradições

| ID | Regra |
|----|-------|
| **RN-050** | Se o input contiver afirmações contraditórias (ex: "quero emagrecer" + "como pizza todo dia"), o sistema **DEVE** ignorar a contradição e processar com base no **objetivo declarado** (emagrecer), gerando os planos adequados. O sistema não julga nem comenta o estilo de vida do usuário. |
| **RN-051** | Se houver contradição entre restrições (ex: "não como nada de origem animal, mas gosto de frango"), o sistema **DEVE** priorizar a **restrição** (vegano) e ignorar o alimento conflitante. O frango não aparece em nenhum plano. |
| **RN-052** | Se o input mencionar um alimento que não existe no banco `foods.json`, o sistema **DEVE** tentar encontrar o match mais próximo (ex: "carne de panela" → "Carne Moída Magra" ou "Filé Mignon"). Se nenhum match razoável existir, o alimento é ignorado silenciosamente. |

---

## 3. Regras de Saúde e Segurança

### 3.1 Limites calóricos

| ID | Regra |
|----|-------|
| **RN-060** | Nenhum plano gerado **DEVE** ter GET (calorias diárias totais) inferior a **1200 kcal/dia** ou superior a **4000 kcal/dia**. Planos fora desse intervalo são bloqueados e o usuário recebe a mensagem: "Os valores calculados estão fora da faixa segura para geração automática. Consulte um nutricionista para um plano personalizado." |
| **RN-061** | Para **gestantes**, o limite mínimo sobe para **1800 kcal/dia**. O sistema **DEVE** detectar menção a gravidez no input e aplicar esse limite. |
| **RN-062** | Para **adolescentes** (idade < 18 anos), o limite mínimo é **1500 kcal/dia**. O sistema **DEVE** exibir o aviso: "⚠️ Planos alimentares para adolescentes devem ser supervisionados por um nutricionista." |

### 3.2 Alertas obrigatórios

| ID | Regra |
|----|-------|
| **RN-070** | **TODA** resposta do sistema **DEVE** conter o disclaimer em local visível: "⚠️ **Aviso importante:** Este plano alimentar é gerado automaticamente e não substitui a consulta com um nutricionista ou médico. Antes de iniciar qualquer dieta, consulte um profissional de saúde." |
| **RN-071** | Se o input mencionar **gravidez**, o sistema **DEVE** gerar os planos normalmente, mas **DEVE** incluir um alerta adicional: "⚠️ Durante a gestação, as necessidades nutricionais variam por trimestre. Os planos abaixo usam valores de referência para o 2º trimestre. **É indispensável o acompanhamento com seu obstetra e nutricionista.**" |
| **RN-072** | Se o input mencionar **condição médica** (diabetes, hipertensão, colesterol alto, hipotireoidismo, doença renal, doença celíaca, etc.), o sistema **DEVE** incluir o alerta: "⚠️ Seu perfil menciona [condição]. Este plano usa diretrizes nutricionais gerais e **não considera** particularidades do seu tratamento. **Consulte seu médico** antes de adotar qualquer plano alimentar." |
| **RN-073** | Se o input mencionar **transtorno alimentar** (anorexia, bulimia, compulsão) ou linguagem que sugira relação não-saudável com comida, o sistema **DEVE** se recusar a gerar planos e retornar: "Percebemos que você mencionou desafios com alimentação. Recomendamos buscar apoio profissional especializado. Não podemos gerar planos alimentares neste contexto." |

### 3.3 Responsabilidade

| ID | Regra |
|----|-------|
| **RN-080** | O sistema **NÃO** é um dispositivo médico. Isso **DEVE** estar declarado nos Termos de Uso e no disclaimer de toda resposta. |
| **RN-081** | O sistema **NÃO DEVE** recomendar suplementos alimentares, medicamentos para emagrecimento, ou substâncias ergogênicas. Se o usuário mencionar suplementos no input (ex: "tomo whey e creatina"), o sistema pode incluí-los no plano apenas como item informativo (sem dosagem), com o aviso: "⚠️ Suplementos devem ser recomendados por nutricionista. As dosagens não são sugeridas por este sistema." |
| **RN-082** | O sistema **NÃO DEVE** sugerir dietas com restrição calórica severa (< 1200 kcal/dia), jejum prolongado, ou qualquer prática alimentar que possa ser considerada de risco. |

---

## 4. Regras de Apresentação dos Planos

### 4.1 Estrutura mínima

| ID | Regra |
|----|-------|
| **RN-090** | Cada plano **DEVE** conter no mínimo 4 refeições nomeadas. Os nomes padrão são: "Café da Manhã", "Almoço", "Lanche da Tarde", "Jantar". Planos podem adicionar "Lanche da Manhã" e/ou "Ceia" se a distribuição calórica exigir. |
| **RN-091** | Cada refeição **DEVE** conter pelo menos 1 alimento e no máximo 5 alimentos. Refeições com 6+ alimentos são consideradas irreais para o dia a dia. |
| **RN-092** | Cada alimento em uma refeição **DEVE** ser apresentado com: nome, quantidade em gramas, proteína (g), carboidrato (g), gordura (g), calorias (kcal). |

### 4.2 Formato das quantidades

| ID | Regra |
|----|-------|
| **RN-100** | Quantidades **DEVEM** ser exibidas em **gramas** (unidade principal). Medidas caseiras **DEVERIAM** ser exibidas como complemento entre parênteses, quando aplicável (ex: "Arroz Branco Cozido: 150g (≈ 4 colheres de sopa)"). |
| **RN-101** | A tabela de conversão para medidas caseiras **DEVE** ser baseada em uma tabela fixa interna (ex: arroz cozido = 25g por colher de sopa, feijão = 30g por concha pequena, etc.). Se não houver conversão cadastrada para o alimento, exibir apenas gramas. |
| **RN-102** | Quantidades **DEVEM** ser arredondadas: gramas para o inteiro mais próximo (ex: 147.3g → 147g), macros para 1 casa decimal (ex: 31.47g → 31.5g), calorias para o inteiro mais próximo. |

### 4.3 Informações nutricionais

| ID | Regra |
|----|-------|
| **RN-110** | Cada plano **DEVE** exibir um **resumo de macros** contendo: proteína total (g), carboidrato total (g), gordura total (g), calorias totais (kcal). |
| **RN-111** | O resumo do plano **DEVE** incluir o GET calculado e o objetivo (perda de peso, manutenção ou ganho de massa). |
| **RN-112** | Cada refeição **DEVE** exibir a soma de calorias daquela refeição. |
| **RN-113** | O PDF gerado **DEVE** conter: capa (nome do paciente, data, TMB), 1 página por plano (GET, tabela de macros, refeições em tabela), e disclaimer final. |

---

## 5. Regras de Dados do Usuário

### 5.1 Coleta e armazenamento

| ID | Regra |
|----|-------|
| **RN-120** | O sistema **DEVE** coletar apenas os dados estritamente necessários para gerar os planos: sexo, idade, peso, altura, preferências alimentares, restrições, e e-mail (se o usuário quiser receber o PDF por e-mail). |
| **RN-121** | Dados de saúde (peso, altura, condições médicas mencionadas) **NÃO DEVEM** ser compartilhados com terceiros em hipótese alguma. |
| **RN-122** | O texto original em linguagem natural enviado pelo usuário **PODE** ser armazenado para fins de melhoria do modelo de extração, **DESDE QUE** anonimizado (sem nome, e-mail ou identificadores). O usuário **DEVE** consentir com isso. |
| **RN-123** | O sistema **DEVE** permitir que o usuário solicite a exclusão de todos os seus dados (LGPD). O prazo para exclusão é de até 15 dias úteis. |

### 5.2 Retenção

| ID | Regra |
|----|-------|
| **RN-130** | Planos gerados e seus metadados (JSON de entrada e saída) **DEVEM** ser armazenados por no máximo **30 dias** no servidor. Após esse período, **DEVEM** ser excluídos automaticamente. |
| **RN-131** | Arquivos PDF gerados **DEVEM** ser armazenados por no máximo **7 dias** no servidor. Após esse período, **DEVEM** ser excluídos automaticamente. |
| **RN-132** | Logs de requisição (sem o texto original do usuário) **DEVEM** ser mantidos por **90 dias** para fins de monitoramento e debugging. |
| **RN-133** | O cache de planos em memória (dicionário Python) é volátil e **PODE** ser perdido a qualquer momento (reinicialização do servidor). O sistema **NÃO DEVE** depender dele como única fonte de persistência. |

### 5.3 Histórico do usuário

| ID | Regra |
|----|-------|
| **RN-140** | O sistema **PODE** oferecer um histórico de planos gerados para usuários autenticados, listando data de geração, objetivo e link para download do PDF (enquanto dentro do prazo de retenção). |
| **RN-141** | O histórico **NÃO DEVE** expor o texto original do usuário para outros usuários. Cada usuário vê apenas seu próprio histórico. |
| **RN-142** | Se o usuário não estiver autenticado, o plano gerado **DEVE** ser acessível apenas pelo link de download retornado na resposta. Após expiração do PDF (7 dias), o link retorna 404. |

---

## 📋 Índice de Regras

| Faixa | Categoria | Quantidade |
|:-----:|-----------|:----------:|
| RN-001 a RN-006 | Geração — Diferenciação | 6 |
| RN-010 a RN-015 | Geração — Nutricional | 6 |
| RN-020 a RN-023 | Geração — Restrições | 4 |
| RN-030 a RN-034 | Geração — Input ambíguo | 5 |
| RN-040 a RN-043 | Validação — Campos | 4 |
| RN-050 a RN-052 | Validação — Contradições | 3 |
| RN-060 a RN-062 | Saúde — Limites calóricos | 3 |
| RN-070 a RN-073 | Saúde — Alertas | 4 |
| RN-080 a RN-082 | Saúde — Responsabilidade | 3 |
| RN-090 a RN-092 | Apresentação — Estrutura | 3 |
| RN-100 a RN-102 | Apresentação — Quantidades | 3 |
| RN-110 a RN-113 | Apresentação — Nutricional | 4 |
| RN-120 a RN-123 | Dados — Coleta | 4 |
| RN-130 a RN-133 | Dados — Retenção | 4 |
| RN-140 a RN-142 | Dados — Histórico | 3 |
| **Total** | | **59 regras** |

---

> **Para a IA que vai gerar código:** Regras com **DEVE** são inegociáveis e devem ser implementadas como validações _hard_ (lançam erro ou bloqueiam o fluxo). Regras com **DEVERIA** são recomendações e podem ser implementadas como _soft warnings_. Use os IDs `RN-XXX` nos comentários do código para rastreabilidade (ex: `# RN-020: verificar restrições alimentares`).
