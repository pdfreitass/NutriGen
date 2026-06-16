# 🏗️ Documento de Arquitetura — Gerador de Planos Alimentares com IA

> **Propósito:** Este documento é a referência arquitetural canônica do sistema. Toda decisão técnica, modelo de dados, fluxo de processamento e contrato de integração está descrito aqui. Deve ser usado por agentes de IA e desenvolvedores como fonte única de verdade para gerar código.
>
> **Público:** Desenvolvedores, Arquitetos, Tech Lead, e IAs geradoras de código.
>
> **Versão:** 1.0 — Maio 2026

---

## 1. Visão Geral da Arquitetura

### 1.1 Objetivo da Arquitetura

A arquitetura foi projetada para suportar um sistema que recebe input em linguagem natural do usuário, processa esse input via IA (DeepSeek V4 Pro), gera 3 planos alimentares distintos, e entrega o resultado de volta ao usuário com persistência em banco de dados relacional — tudo isso com o menor acoplamento possível entre as partes e máxima testabilidade.

O sistema é um **monólito modular**: uma única aplicação Python (FastAPI) com camadas internas bem definidas que podem, no futuro, ser extraídas para serviços independentes se necessário.

### 1.2 Benefícios da Arquitetura Escolhida

| Benefício | Detalhe |
|-----------|---------|
| **Simplicidade operacional** | Um único processo, sem orquestração de containers ou filas. Roda localmente com `uvicorn`. |
| **Baixa latência** | Comunicação entre camadas é feita por chamada de função, não por rede. |
| **Testabilidade** | Cada camada pode ser testada isoladamente com mocks na camada inferior. |
| **Evolução incremental** | A separação em camadas permite extrair módulos para serviços externos no futuro sem reescrever lógica de negócio. |
| **Custo zero de infraestrutura** | Roda localmente em Windows com SQL Server Express. Nenhum serviço pago obrigatório no desenvolvimento. |
| **Adequado ao MVP** | Complexidade proporcional ao estágio atual do produto. Sem overengineering. |

### 1.3 Justificativa para Monólito Modular

A alternativa seria uma arquitetura de microsserviços, mas isso traria:

- **Overhead de rede:** Cada chamada entre serviços adiciona latência de milissegundos, que se acumulam em um fluxo de 12 etapas com IA envolvida.
- **Complexidade operacional:** Orquestração de múltiplos processos, service discovery, health checks, distributed tracing — desnecessário para um sistema com < 100 requisições por dia na fase inicial.
- **Custo:** Múltiplos serviços exigem múltiplos deployments, cada um consumindo recursos. SQL Server Express já é o bastante.

O **monólito modular** oferece o melhor dos dois mundos: código organizado como se fossem serviços separados (baixo acoplamento), mas executando em um único processo (alta coesão, baixa latência). Se no futuro o módulo de geração IA precisar escalar independentemente, a camada `Infrastructure` pode ser extraída para um worker separado sem reescrever `Domain` ou `Application`.

### 1.4 Diagrama Textual da Arquitetura

```
┌──────────────────────────────────────────────────────────────────┐
│                         USUÁRIO                                  │
│              (Navegador — Frontend HTML/CSS/JS)                  │
└──────────────────────────┬───────────────────────────────────────┘
                           │  HTTP (REST JSON)
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                     API LAYER (FastAPI)                          │
│                                                                  │
│  ┌─────────────────────┐    ┌──────────────────────────────┐    │
│  │  Router: /api/diet  │    │  Router: /api/auth           │    │
│  │  POST /generate     │    │  POST /register              │    │
│  │  GET /{id}/pdf      │    │  POST /login                 │    │
│  └─────────┬───────────┘    └──────────────┬───────────────┘    │
│            │                               │                     │
│  ┌─────────▼───────────────────────────────▼────────────────┐   │
│  │              Pydantic Schemas (DTOs / Validação)         │   │
│  └──────────────────────────┬───────────────────────────────┘   │
└─────────────────────────────┼────────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────────┐
│                   APPLICATION LAYER                              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Casos de Uso (Use Cases)                                │   │
│  │                                                          │   │
│  │  GerarPlanosUseCase                                      │   │
│  │    1. Recebe input NL do usuário                         │   │
│  │    2. Chama ExtractorService (NL → JSON estruturado)     │   │
│  │    3. Chama NutritionCalculator (TMB, GET, macros)       │   │
│  │    4. Chama PlanGeneratorService (3 planos via IA)       │   │
│  │    5. Chama PlanValidator (pós-processamento)            │   │
│  │    6. Persiste resultado                                 │   │
│  │    7. Dispara geração de PDF                             │   │
│  │    8. Retorna resposta ao cliente                        │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬────────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────────┐
│                     DOMAIN LAYER                                 │
│                                                                  │
│  ┌────────────────────┐  ┌─────────────────────────────────┐    │
│  │  Entidades         │  │  Regras de Negócio (RN-xxx)     │    │
│  │  - Usuario         │  │  - Validação de macros ±10%     │    │
│  │  - SessaoGeracao   │  │  - Bloqueio GET < 1200 kcal    │    │
│  │  - PlanoAlimentar  │  │  - Restrições alimentares 0%    │    │
│  │  - Refeicao        │  │  - Diferenciação 40% planos     │    │
│  │  - ItemRefeicao    │  │  - Intervalos fisiológicos      │    │
│  └────────────────────┘  └─────────────────────────────────┘    │
└─────────────────────────────┬────────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────────┐
│                  INFRASTRUCTURE LAYER                            │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │  SQL Server      │  │  DeepSeek API    │  │  Alembic     │  │
│  │  Express         │  │  (HTTP)          │  │  Migrations  │  │
│  │                  │  │                  │  │              │  │
│  │  SQLAlchemy ORM  │  │  Modelo:         │  │  Versiona-   │  │
│  │  Repositórios    │  │  DeepSeek V4 Pro │  │  mento de    │  │
│  │                  │  │                  │  │  schema      │  │
│  └──────┬───────────┘  └────────┬─────────┘  └──────────────┘  │
│         │                       │                                │
└─────────┼───────────────────────┼────────────────────────────────┘
          │                       │
          ▼                       ▼
┌──────────────────┐    ┌──────────────────────┐
│  SQL Server      │    │  api.deepseek.com    │
│  (localhost)     │    │  (Internet)          │
└──────────────────┘    └──────────────────────┘
```

### 1.5 Responsabilidade de Cada Componente

| Componente | Camada | Responsabilidade |
|------------|:------:|------------------|
| **Frontend HTML/CSS/JS** | Externa | Interface do usuário. Coleta input NL, exibe planos, gerencia navegação entre páginas, download de PDF. |
| **Routers (FastAPI)** | API | Recebem requisições HTTP, delegam para Application Layer, retornam respostas JSON. Não contêm lógica de negócio. |
| **Pydantic Schemas** | API | Validam formato e tipos dos dados de entrada e saída. Definem contratos da API (OpenAPI/Swagger). |
| **Use Cases** | Application | Orquestram o fluxo completo de cada operação. Conhecem a sequência de passos mas não implementam a lógica fina. |
| **Services** | Application | Implementam a lógica de aplicação: extração NL→JSON, geração de planos via IA, cálculo nutricional. |
| **Entities** | Domain | Modelos de domínio puros. Representam conceitos do negócio sem dependência de frameworks. |
| **Business Rules** | Domain | Validações e restrições de negócio (RN-001 a RN-142). Independem de infraestrutura. |
| **SQLAlchemy ORM** | Infrastructure | Mapeamento objeto-relacional. Traduz entidades de domínio para tabelas do SQL Server. |
| **Repositories** | Infrastructure | Abstraem acesso a dados. A Application Layer não conhece SQL. |
| **DeepSeek Client** | Infrastructure | Cliente HTTP para a API DeepSeek. Gerencia autenticação, timeout, retry. |
| **Alembic** | Infrastructure | Versionamento e aplicação de migrações de schema do banco de dados. |
| **SQL Server Express** | Externa | Banco de dados relacional. Armazena usuários, sessões de geração, planos, refeições e itens. |

---

## 2. Arquitetura em Camadas

### 2.1 API Layer (Camada de Apresentação)

**Responsabilidades:**

- Definir endpoints REST via FastAPI Routers
- Receber e validar payloads JSON usando Pydantic Schemas
- Converter DTOs de entrada em objetos de domínio (ou parâmetros para Use Cases)
- Retornar respostas HTTP padronizadas (200, 201, 400, 401, 404, 422, 500, 504)
- Servir documentação Swagger automática em `/docs`
- Gerenciar CORS, rate limiting e headers de segurança
- Servir o frontend estático (SPA) via `StaticFiles`

**O que NÃO faz:** Não contém lógica de negócio. Um router nunca chama diretamente um repository ou faz cálculo nutricional. Ele apenas recebe, valida, delega e responde.

**Fluxo dentro da camada:**

```
Requisição HTTP
    → Router recebe
    → Pydantic valida o body/query/path params
    → Se inválido → 422 Unprocessable Entity (automático, Pydantic)
    → Se válido → chama Use Case da Application Layer
    → Recebe resultado
    → Serializa com Pydantic Response Schema
    → Retorna HTTP Response
```

**Dependências:** A API Layer depende apenas da **Application Layer**. Ela NUNCA importa nada de `Domain` ou `Infrastructure` diretamente.

### 2.2 Application Layer (Camada de Aplicação)

**Responsabilidades:**

- Implementar casos de uso (Use Cases)
- Orquestrar o fluxo entre Domain e Infrastructure
- Coordenar serviços de aplicação (extratores, geradores, validadores)
- Gerenciar transações de banco de dados (iniciar, commit, rollback)
- Emitir eventos de log e auditoria
- Montar prompts para a IA e interpretar respostas

**Casos de uso principais:**

| Caso de Uso | Descrição |
|-------------|-----------|
| `GerarPlanosUseCase` | Fluxo completo: extrair input → calcular nutrição → gerar 3 planos via IA → validar → persistir → gerar PDF → retornar |
| `RegistrarUsuarioUseCase` | Validar dados de cadastro, verificar unicidade, hash de senha, persistir |
| `AutenticarUsuarioUseCase` | Verificar credenciais, gerar JWT |
| `RecuperarSenhaUseCase` | Gerar token, enviar e-mail (ou retornar em desenvolvimento) |
| `RedefinirSenhaUseCase` | Validar token, atualizar senha |

**Serviços de aplicação:**

| Serviço | Responsabilidade |
|---------|------------------|
| `ExtractorService` | Envia o texto NL do usuário para a API DeepSeek e recebe um JSON estruturado de volta. |
| `NutritionCalculator` | Calcula TMB, GET, distribuição de macros. **Determinístico — não usa IA.** |
| `PlanGeneratorService` | Envia os macros calculados + preferências + restrições para a API DeepSeek e recebe 3 planos completos. |
| `PlanValidator` | Valida os planos contra as regras de negócio (RN-010 a RN-015, RN-020 a RN-023). Corrige ou rejeita. |
| `PdfGeneratorService` | Orquestra a geração de PDF (usa ReportLab internamente). |

**Dependências:** A Application Layer depende da **Domain Layer** (entidades e regras de negócio) e da **Infrastructure Layer** (repositórios, clientes HTTP). Ela NUNCA importa nada da API Layer.

### 2.3 Domain Layer (Camada de Domínio)

**Responsabilidades:**

- Definir as entidades de negócio puras (sem acoplamento com ORM ou banco)
- Implementar Value Objects (ex: `Macros`, `Calorias`, `FaixaEtaria`)
- Implementar regras de negócio como funções puras ou métodos de entidade
- Definir interfaces (Protocols/ABCs) para repositórios e serviços externos (Dependency Inversion)
- **Não depender de nenhuma outra camada.** Domain é o núcleo independente.

**Entidades de domínio:**

| Entidade | Descrição |
|----------|-----------|
| `Usuario` | Dados cadastrais do usuário. |
| `PerfilNutricional` | Value Object com sexo, idade, peso, altura, IMC, TMB. Imutável após cálculo. |
| `SessaoGeracao` | Agregação raiz. Representa uma sessão de geração: input original, perfil extraído, data. Contém 3 Planos. |
| `PlanoAlimentar` | Entidade. Um dos 3 planos gerados. Contém nome, eixo de diferenciação, GET, macros totais, lista de Refeições. |
| `Refeicao` | Entidade. Uma refeição do plano (ex: "Café da Manhã"). Contém lista de Itens. |
| `ItemRefeicao` | Value Object (ou entidade fraca). Um alimento com sua quantidade em gramas e valores nutricionais calculados. |
| `Alimento` | Value Object do catálogo. Representa um alimento do banco `foods.json` com sua tabela nutricional. |

**Regras de negócio na camada de domínio:**

- `Macros.dentro_da_margem(get_calorico) → bool` — Verifica RN-010 (±10%)
- `PlanoAlimentar.calorias_totais() → float` — Soma calorias de todas as refeições
- `PlanoAlimentar.validar_calorias(get_calorico) → bool` — Verifica RN-015 (95%-105%)
- `PlanoAlimentar.tem_alimento_proibido(restricoes) → bool` — Verifica RN-020
- `PlanoAlimentar.sobreposicao_com(outro_plano) → float` — Calcula % de alimentos em comum
- `PerfilNutricional.calcular_imc() → float`

**Dependências:** A Domain Layer **não depende de nenhuma outra camada**. Ela define interfaces (ex: `PlanoRepository`) que a Infrastructure implementa.

### 2.4 Infrastructure Layer (Camada de Infraestrutura)

**Responsabilidades:**

- Implementar as interfaces definidas pela Domain Layer (repositórios, clientes)
- Gerenciar conexão com SQL Server Express via SQLAlchemy
- Implementar cliente HTTP para API DeepSeek
- Configurar e executar migrações Alembic
- Carregar e servir o arquivo `data/foods.json`
- Gerar arquivos PDF via ReportLab
- Gerenciar cache em memória para objetos de uso frequente (ex: catálogo de alimentos)

**Componentes de infraestrutura:**

| Componente | Responsabilidade |
|------------|------------------|
| `UsuarioRepository` | Implementa interface `UsuarioRepositoryInterface`. CRUD de usuários, busca por e-mail/CPF, tokens de recuperação. |
| `SessaoGeracaoRepository` | Persiste e recupera sessões de geração e planos associados. |
| `DeepSeekClient` | Cliente HTTP tipado para a API DeepSeek. Gerencia API key, headers, timeout (90s), retry (2 tentativas com backoff). |
| `FoodCatalog` | Carrega `foods.json` em memória na inicialização. Fornece métodos de busca: `buscar_por_nome()`, `buscar_por_categoria()`, `listar_todos()`. |
| `PdfReportLabWriter` | Implementa geração de PDF usando ReportLab. |
| `DatabaseSession` | Factory de sessões SQLAlchemy. Gerencia engine, pool (5-10 conexões), e ciclo de vida da sessão. |
| `AlembicMigrationRunner` | Scripts de migração versionados. |

**Integração com API DeepSeek:**

```
┌──────────────────────────────────────────────────────────────────┐
│                      DeepSeekClient                              │
│                                                                  │
│  Configuração (via .env):                                       │
│    DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx                         │
│    DEEPSEEK_BASE_URL=https://api.deepseek.com/v1                 │
│    DEEPSEEK_MODEL=deepseek-chat                                  │
│    DEEPSEEK_TIMEOUT=90                                           │
│    DEEPSEEK_MAX_RETRIES=2                                        │
│                                                                  │
│  Fluxo de chamada:                                               │
│    1. Monta payload JSON com model, messages, temperature,       │
│       response_format={type: "json_object"}                      │
│    2. Envia POST para {base_url}/chat/completions               │
│    3. Timeout de 90s por chamada                                │
│    4. Se timeout ou erro 5xx → retry com backoff exponencial    │
│       (1ª tentativa: espera 2s, 2ª tentativa: espera 4s)        │
│    5. Se todas as tentativas falharem → lança                     │
│       DeepSeekUnavailableException                              │
│    6. Se sucesso → extrai content da resposta, faz parse JSON    │
│    7. Se JSON inválido → lança DeepSeekInvalidResponseException │
└──────────────────────────────────────────────────────────────────┘
```

### 2.5 Fluxo de Dependência Entre Camadas

```
┌──────────────────────────────────────────────────────────────────┐
│                     REGRA DE OURO                                │
│                                                                  │
│  As dependências SEMPRE apontam PARA DENTRO:                    │
│                                                                  │
│  API → Application → Domain ← Infrastructure                    │
│                                                                  │
│  - API depende de Application                                   │
│  - Application depende de Domain e Infrastructure               │
│  - Domain NÃO depende de ninguém (núcleo independente)           │
│  - Infrastructure implementa interfaces do Domain               │
│    (Dependency Inversion Principle)                              │
│                                                                  │
│  NUNCA:                                                          │
│  - Domain importar Infrastructure ❌                             │
│  - Domain importar Application ❌                                │
│  - Domain importar API ❌                                        │
│  - Application importar API ❌                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Stack Tecnológica

| Tecnologia | Versão | Finalidade | Motivo da Escolha |
|------------|:------:|------------|-------------------|
| **Python** | 3.12+ | Linguagem de programação | Ecossistema maduro para IA/ML, tipagem forte, ampla adoção no mercado. Versão 3.12 traz melhorias de performance e sintaxe moderna (`X \| Y` para Union types). |
| **FastAPI** | 0.115+ | Framework web REST | Performance comparável a Node.js/Go, validação automática via Pydantic, documentação Swagger nativa, suporte nativo a async. Ideal para APIs que orquestram chamadas externas (DeepSeek). |
| **Pydantic** | 2.9+ | Validação e serialização de dados | Validação em tempo de execução com mensagens de erro claras. Integração nativa com FastAPI. Suporte a `EmailStr`, `model_validator`, tipos literais e ranges. |
| **Uvicorn** | 0.30+ | Servidor ASGI | Servidor de produção para FastAPI. Leve, com suporte a múltiplos workers e hot-reload em desenvolvimento. |
| **SQLAlchemy** | 2.0+ | ORM (Object-Relational Mapping) | Abstração madura sobre SQL Server. Suporte a `DeclarativeBase`, `Mapped[]`, `mapped_column()`. Evita SQL injection por design. Modo síncrono para compatibilidade com pyodbc. |
| **pyodbc** | 5.3+ | Driver ODBC para SQL Server | Driver oficial Microsoft para SQL Server em Windows. Compatível com Windows Authentication (Trusted_Connection), eliminando necessidade de gerenciar senhas de banco. |
| **SQL Server Express** | 2019+ | Banco de dados relacional | Gratuito, instalado localmente, sem custo operacional. Integração nativa com Windows Authentication. Capacidade de 10GB — mais que suficiente para anos de uso do sistema. |
| **Alembic** | 1.18+ | Migrações de banco de dados | Versionamento de schema como código. Integração nativa com SQLAlchemy. Permite evoluir o banco sem perder dados entre versões. |
| **DeepSeek API** | V4 Pro | Geração de planos via IA | Modelo de linguagem de alta性能. Custo acessível. Suporte a `response_format: json_object` para respostas estruturadas. API REST padrão OpenAI-compatible, facilitando integração e futura troca de provedor. |
| **bcrypt** | 4.2+ | Hash de senhas | Algoritmo lento e resistente a GPU para hashing de senhas. Sal automático embutido. Padrão da indústria. |
| **PyJWT** | 2.9+ | Tokens JWT | Autenticação stateless. Token auto-contido com expiração. |
| **ReportLab** | 4.2+ | Geração de PDF | Biblioteca Python pura, sem dependências externas. Controle total sobre layout de tabelas e estilização. |
| **httpx** | 0.28+ | Cliente HTTP | Usado para chamadas à API DeepSeek e ViaCEP. Suporte a timeout, retry e conexões persistentes. |
| **python-dotenv** | 1.2+ | Variáveis de ambiente | Carrega configurações de `.env` sem código boilerplate. Essencial para gerenciar chaves de API e secrets. |
| **Git** | — | Controle de versão | Padrão da indústria. Histórico completo, branches, code review via Pull Requests. |
| **GitHub** | — | Hospedagem do repositório | Colaboração, CI/CD (GitHub Actions), backups automáticos. |

---

## 4. Fluxo Principal de Dados

### 4.1 Diagrama de Sequência Textual

```
USUÁRIO          FRONTEND         FASTAPI          APPLICATION       DEEPSEEK API       SQL SERVER
  │                 │                │                  │                 │                 │
  │  Digita texto   │                │                  │                 │                 │
  │────────────────▶│                │                  │                 │                 │
  │                 │  POST /generate│                  │                 │                 │
  │                 │───────────────▶│                  │                 │                 │
  │                 │                │  Pydantic valid. │                 │                 │
  │                 │                │──▶ input ok?     │                 │                 │
  │                 │                │                  │                 │                 │
  │                 │                │  executa caso de uso              │                 │
  │                 │                │─────────────────▶│                 │                 │
  │                 │                │                  │                 │                 │
  │                 │                │                  │  ETAPA 1: Extração NL→JSON          │
  │                 │                │                  │  monta prompt   │                 │
  │                 │                │                  │────────────────▶│                 │
  │                 │                │                  │  (até 15s)      │                 │
  │                 │                │                  │◀────────────────│                 │
  │                 │                │                  │  JSON perfil    │                 │
  │                 │                │                  │                 │                 │
  │                 │                │                  │  ETAPA 2: Cálculo (local, < 1ms)    │
  │                 │                │                  │  TMB, GET, Macros                   │
  │                 │                │                  │                 │                 │
  │                 │                │                  │  ETAPA 3: Geração 3 Planos          │
  │                 │                │                  │  monta prompt   │                 │
  │                 │                │                  │────────────────▶│                 │
  │                 │                │                  │  (até 30s)      │                 │
  │                 │                │                  │◀────────────────│                 │
  │                 │                │                  │  JSON 3 planos  │                 │
  │                 │                │                  │                 │                 │
  │                 │                │                  │  ETAPA 4: Validação (local)         │
  │                 │                │                  │  + Correções    │                 │
  │                 │                │                  │                 │                 │
  │                 │                │                  │  ETAPA 5: Persistência              │
  │                 │                │                  │─────────────────────────────────────▶│
  │                 │                │                  │◀─────────────────────────────────────│
  │                 │                │                  │                 │                 │
  │                 │                │                  │  ETAPA 6: PDF (local)               │
  │                 │                │                  │  ReportLab gera arquivo              │
  │                 │                │                  │                 │                 │
  │                 │                │  JSON + pdf_url  │                 │                 │
  │                 │                │◀─────────────────│                 │                 │
  │                 │  JSON + pdf_url│                  │                 │                 │
  │                 │◀───────────────│                  │                 │                 │
  │                 │                │                  │                 │                 │
  │  Exibe 3 planos │                │                  │                 │                 │
  │◀────────────────│                │                  │                 │                 │
```

### 4.2 Detalhamento de Cada Etapa

#### Etapa 1 — Extração NL→JSON

**O que acontece:** O texto livre do usuário (ex: "Trabalho sentado, faço musculação 4x/semana...") é enviado para a API DeepSeek com um prompt de sistema que instrui o modelo a extrair campos estruturados. O modelo retorna um JSON com `perfil` (sexo, idade, peso, altura), `rotina` (nível de atividade, objetivo), `preferencias`, `restricoes`, e `extra` (observações).

**Validação pós-extração:**
- Campos obrigatórios (`sexo`, `idade`, `peso_kg`, `altura_cm`) presentes?
- Valores dentro de intervalos fisiológicos?
- Se faltar algo → erro 400 com mensagem específica listando o que está faltando

**Timeout:** 15 segundos. Se exceder, retry (1 tentativa adicional).

#### Etapa 2 — Cálculo Nutricional

**O que acontece:** Com o perfil extraído (sexo, idade, peso, altura, nível de atividade, objetivo), o sistema calcula deterministicamente (sem IA):

1. **TMB** via Mifflin-St Jeor
2. **GET** via fator de atividade
3. **Macros** em gramas conforme objetivo (ou personalizado)
4. **Validação** do GET contra limites de segurança (1200-4000 kcal)

**Tempo:** < 1ms (cálculo aritmético puro).

#### Etapa 3 — Geração dos 3 Planos

**O que acontece:** Os macros calculados, preferências, restrições e o texto original do usuário são enviados para a API DeepSeek com um prompt de sistema detalhado (ver seção 5). O modelo retorna um JSON com exatamente 3 planos, cada um em um eixo de diferenciação distinto.

**Timeout:** 30 segundos. Se exceder, retry (1 tentativa adicional).

#### Etapa 4 — Validação Pós-Geração

**O que acontece:** Os 3 planos retornados pela IA passam por um pipeline de validação determinística:

1. **Validação de alimentos:** Todo alimento citado existe no `foods.json`? Se não, substituir pelo match mais próximo. Logar o ocorrido.
2. **Validação de restrições:** Nenhum alimento proibido aparece? (RN-020 — tolerância 0%)
3. **Validação de quantidades:** Toda quantidade está entre 30g e 500g? (RN-014)
4. **Validação de macros:** Proteína, carbo e gordura dentro de ±10% do calculado? (RN-010)
5. **Validação calórica:** Soma das calorias entre 95% e 105% do GET? (RN-015)
6. **Validação de diferenciação:** Pelo menos 40% de alimentos diferentes entre planos? (RN-004)
7. **Validação estrutural:** Cada plano tem entre 4 e 6 refeições? (RN-005)

**Ações:** Se qualquer validação falhar, o sistema tenta corrigir automaticamente (ajustar quantidades, substituir alimentos, redistribuir refeições). Se a correção for impossível (ex: plano inteiro com alimentos proibidos), o plano é rejeitado e um novo é solicitado à IA.

#### Etapa 5 — Persistência

**O que acontece:** Os 3 planos validados são persistidos no SQL Server Express via SQLAlchemy:

- `SessaoGeracao` — 1 registro com input original, perfil extraído, data
- `PlanoAlimentar` — 3 registros (1 por plano)
- `Refeicao` — 12-18 registros (4-6 por plano)
- `ItemRefeicao` — 24-90 registros (1-5 alimentos por refeição)

Tudo em uma única transação. Se falhar, rollback e erro 500.

#### Etapa 6 — Geração de PDF

**O que acontece:** O ReportLab gera um PDF consolidado com:
- Capa (nome, data, TMB, GET)
- 1 página por plano (macros, tabela de refeições)
- Disclaimer final obrigatório

O PDF é salvo em `outputs/{uuid}.pdf` e o UUID é retornado na resposta.

#### Etapas 7-8 — Resposta ao Cliente

**O que acontece:** A API Layer recebe o resultado da Application Layer, serializa via Pydantic `DietGenerateResponse`, e retorna HTTP 200 com:
- Dados do paciente
- TMB calculada
- 3 planos completos
- URL para download do PDF

O frontend renderiza os 3 planos lado a lado (desktop) ou em accordion vertical (mobile).

---

## 5. Estratégia de Prompt Engineering

### 5.1 Construção do Prompt de Extração (NL → JSON)

O prompt de extração tem um objetivo único: converter texto livre em JSON estruturado. Ele **não** gera planos.

**System Prompt (extração):**

```
Você é um extrator de informações nutricionais. Converta a descrição do usuário
em um JSON estruturado com os campos abaixo.

Regras:
1. Extraia APENAS o que está explícito no texto. Não invente valores.
2. Se um campo obrigatório (sexo, idade, peso_kg, altura_cm) não estiver no texto,
   marque como null.
3. Para 'nivel_atividade', classifique como:
   - "sedentario" (não faz exercício ou menos de 2x/semana)
   - "moderado" (exercício 2-4x/semana)
   - "ativo" (exercício 5-7x/semana)
4. Para 'objetivo', classifique como:
   - "perda_de_peso" (quer emagrecer, perder peso, secar, definir)
   - "manutencao" (quer manter, saúde, bem-estar)
   - "ganho_de_massa" (quer ganhar peso, hipertrofia, crescer, volume)
   Se não estiver claro, marque como null.
5. Alimentos que o usuário diz GOSTAR vão em 'preferencias'.
6. Alimentos que o usuário diz NÃO COMER / DETESTAR / TER ALERGIA vão em 'restricoes'.
7. Detecte condições especiais e marque em 'condicoes': "gravidez", "diabetes",
   "hipertensao", "vegano", "vegetariano", "intolerancia_lactose", etc.
```

**User Prompt (extração):** O texto bruto do usuário.

**Response esperado:**

```json
{
  "perfil": {
    "sexo": "masculino",
    "idade": 28,
    "peso_kg": 72.0,
    "altura_cm": 175.0
  },
  "rotina": {
    "nivel_atividade": "moderado",
    "objetivo": "ganho_de_massa",
    "detalhes": "Musculação 4x por semana à noite. Café da manhã rápido."
  },
  "preferencias": ["frango", "batata doce", "ovo", "whey", "banana", "pasta de amendoim"],
  "restricoes": ["peixe"],
  "condicoes": [],
  "extra": {
    "refeicoes_rapidas": true,
    "observacoes": ""
  }
}
```

### 5.2 Construção do Prompt de Geração (3 Planos)

O prompt de geração recebe o JSON extraído + os macros calculados e gera os 3 planos completos.

**System Prompt (geração):**

```
Você é um nutricionista especializado em montar planos alimentares personalizados.
Gere EXATAMENTE 3 planos alimentares distintos para o perfil abaixo.

REGRAS INEGOCIÁVEIS:
1. Gere EXATAMENTE 3 planos. Nem 2, nem 4.
2. Os 3 planos DEVEM ser estruturalmente diferentes entre si (pelo menos 40% de
   alimentos diferentes).
3. OS 3 EIXOS DE DIFERENCIAÇÃO SÃO FIXOS:
   - Plano 1: "Tradicional Brasileiro" — arroz, feijão, proteínas clássicas,
     salada simples. Preparo caseiro. Custo acessível.
   - Plano 2: "Funcional & Nutrientes" — quinoa, batata doce, oleaginosas,
     vegetais variados. Foco em densidade nutricional e antioxidantes.
   - Plano 3: "Prático & Rápido" — refeições de preparo rápido (< 15 min):
     sanduíches, bowls, ovos, shakes. Ideal para rotina corrida.

RESTRIÇÕES ALIMENTARES (TOLERÂNCIA ZERO):
- NENHUM plano pode conter: [lista de restrições do usuário]
- Condições especiais detectadas: [gravidez, diabetes, alergias, etc.]

MACROS CALCULADOS (use como meta ±10%):
- GET: XXXX kcal/dia
- Proteína: XXg | Carboidrato: XXg | Gordura: XXg

ESTRUTURA DE CADA PLANO:
- 4 a 6 refeições: Café da Manhã, Almoço, Lanche da Tarde, Jantar
  (+ Lanche da Manhã e/ou Ceia se necessário)
- 1 a 5 alimentos por refeição
- Quantidades entre 30g e 500g por alimento
- Use APENAS alimentos do banco de dados fornecido abaixo
- Inclua nome do alimento, quantidade em gramas, e valores nutricionais

BANCO DE ALIMENTOS DISPONÍVEL:
[lista de alimentos do foods.json com valores nutricionais por 100g]
```

**User Prompt (geração):**

```
Perfil do usuário:
- Sexo: [sexo]
- Idade: [idade] anos
- Peso: [peso] kg
- Altura: [altura] cm
- Nível de atividade: [nivel_atividade]
- Objetivo: [objetivo]
- Preferências: [preferencias]
- Restrições: [restricoes]
- GET calculado: [GET] kcal/dia
- Macros: [proteina]g proteína, [carbo]g carbo, [gordura]g gordura

Texto original do usuário: "[texto original]"
```

### 5.3 Garantia de Restrições Alimentares

A estratégia para garantir que restrições (intolerâncias, alergias, proibições) sejam respeitadas opera em **3 níveis**:

| Nível | Mecanismo | Quando atua |
|:-----:|-----------|-------------|
| **1. Prompt** | As restrições são listadas em destaque no system prompt com a instrução: "NENHUM plano pode conter: [restrições]. TOLERÂNCIA ZERO." | Antes da geração |
| **2. Validação pós-geração** | O `PlanValidator` varre cada alimento de cada plano contra a lista de `restricoes`. Se encontrar, remove o alimento e substitui por alternativa similar da mesma categoria. | Após a geração, antes de persistir |
| **3. Bloqueio final** | Se após a correção o plano ainda contiver um alimento proibido (ex: falha na substituição), o plano inteiro é descartado e a IA é chamada novamente com mensagem de erro específica. | Última barreira |

**Exemplo de detecção de alergias:**

Se o texto do usuário contiver "sou alérgico a amendoim" ou "tenho intolerância à lactose", o extrator classifica essas condições. O gerador então:

- Remove `Amendoim Torrado` e `Pasta de Amendoim` de todos os planos
- Substitui `Leite Integral` por `Leite de Amêndoas` (se lactose)
- Substitui `Queijo Mussarela` por `Tofu` (se lactose + vegano)

### 5.4 Garantia de Diversidade Entre Planos

A diversidade é garantida pelos **3 eixos fixos de diferenciação** (Tradicional, Funcional, Prático) definidos no system prompt. Adicionalmente:

**Abordagem escolhida:** Eixos temáticos fixos (não aleatórios, não baseados em custo).

**Justificativa:** Eixos temáticos fixos produzem variação perceptível e significativa para o usuário. Abordagens alternativas foram descartadas:

| Abordagem | Problema |
|-----------|----------|
| Eixos por custo (Econômico / Médio / Premium) | Preço de alimentos varia por região e época; difícil de calcular com precisão |
| Eixos por objetivo (Emagrecer / Manter / Ganhar) | O usuário já tem 1 objetivo. 3 planos para o mesmo objetivo com a mesma estratégia seriam redundantes |
| Eixos aleatórios | Resultados imprevisíveis; pode gerar planos sem sentido |
| Eixos por horário (Manhã / Tarde / Noite) | Não faz sentido para planos diários |

**Validação de diversidade:** Após a geração, o `PlanValidator` calcula a porcentagem de alimentos compartilhados entre cada par de planos. Se qualquer par tiver mais de 60% de sobreposição, o plano mais similar é rejeitado e um novo é solicitado com instrução explícita de "mais diferente".

---

## 6. Contrato de Resposta da IA

### 6.1 Formato da Resposta

A API DeepSeek é configurada com `response_format: { "type": "json_object" }`, o que garante que a resposta seja um JSON válido. O parâmetro `temperature` é configurado como `0.7` para balancear criatividade com consistência.

### 6.2 Schema JSON Esperado (Geração de Planos)

```json
{
  "planos": [
    {
      "nome": "Tradicional Brasileiro",
      "descricao": "Plano baseado na culinária brasileira clássica, com arroz, feijão, proteínas magras e saladas. Ideal para quem valoriza comida caseira e ingredientes acessíveis. Custo médio: R$ 25-35/dia.",
      "eixo": "tradicional",
      "objetivo": "ganho_de_massa",
      "calorias_estimadas": 2850,
      "refeicoes": [
        {
          "nome": "Café da Manhã",
          "horario": "07:00",
          "alimentos": [
            {
              "nome": "Ovo Mexido",
              "quantidade_g": 150,
              "proteina_g": 19.5,
              "carboidrato_g": 1.5,
              "gordura_g": 16.5,
              "calorias_kcal": 233
            },
            {
              "nome": "Pão Integral",
              "quantidade_g": 100,
              "proteina_g": 9.0,
              "carboidrato_g": 49.0,
              "gordura_g": 3.0,
              "calorias_kcal": 265
            },
            {
              "nome": "Banana",
              "quantidade_g": 120,
              "proteina_g": 1.6,
              "carboidrato_g": 26.4,
              "gordura_g": 0.4,
              "calorias_kcal": 118
            }
          ]
        },
        {
          "nome": "Almoço",
          "horario": "12:00",
          "alimentos": [
            {
              "nome": "Arroz Branco Cozido",
              "quantidade_g": 200,
              "proteina_g": 5.0,
              "carboidrato_g": 56.0,
              "gordura_g": 0.6,
              "calorias_kcal": 260
            },
            {
              "nome": "Feijão Carioca Cozido",
              "quantidade_g": 150,
              "proteina_g": 7.2,
              "carboidrato_g": 20.4,
              "gordura_g": 0.8,
              "calorias_kcal": 114
            },
            {
              "nome": "Peito de Frango Grelhado",
              "quantidade_g": 180,
              "proteina_g": 55.8,
              "carboidrato_g": 0.0,
              "gordura_g": 6.5,
              "calorias_kcal": 297
            },
            {
              "nome": "Brócolis Cozido",
              "quantidade_g": 100,
              "proteina_g": 2.8,
              "carboidrato_g": 7.0,
              "gordura_g": 0.4,
              "calorias_kcal": 35
            }
          ]
        },
        {
          "nome": "Lanche da Tarde",
          "horario": "16:00",
          "alimentos": [
            {
              "nome": "Iogurte Grego",
              "quantidade_g": 200,
              "proteina_g": 18.0,
              "carboidrato_g": 8.0,
              "gordura_g": 10.0,
              "calorias_kcal": 194
            },
            {
              "nome": "Aveia em Flocos",
              "quantidade_g": 50,
              "proteina_g": 6.8,
              "carboidrato_g": 33.2,
              "gordura_g": 3.3,
              "calorias_kcal": 190
            }
          ]
        },
        {
          "nome": "Jantar",
          "horario": "20:00",
          "alimentos": [
            {
              "nome": "Batata Doce Cozida",
              "quantidade_g": 250,
              "proteina_g": 4.0,
              "carboidrato_g": 50.0,
              "gordura_g": 0.3,
              "calorias_kcal": 215
            },
            {
              "nome": "Salmão Grelhado",
              "quantidade_g": 150,
              "proteina_g": 37.5,
              "carboidrato_g": 0.0,
              "gordura_g": 19.5,
              "calorias_kcal": 330
            },
            {
              "nome": "Couve Refogada",
              "quantidade_g": 100,
              "proteina_g": 2.0,
              "carboidrato_g": 6.0,
              "gordura_g": 2.5,
              "calorias_kcal": 50
            }
          ]
        }
      ]
    }
  ]
}
```

### 6.3 Validação da Resposta pelo Backend

O `PlanValidator` executa as seguintes verificações sobre o JSON retornado:

| Verificação | Ação se falhar |
|-------------|----------------|
| `planos` é uma lista com exatamente 3 elementos | Rejeitar. Re-solicitar à IA. |
| Cada plano tem `nome`, `descricao`, `refeicoes` | Preencher campos faltantes com defaults ou rejeitar. |
| Cada `refeicao` é uma lista com 4 a 6 elementos | Ajustar (remover extras ou adicionar refeição vazia com warning). |
| Cada `alimentos` em uma refeição tem 1 a 5 itens | Remover excedentes. |
| Todo `nome` de alimento existe no `foods.json` | Substituir pelo match mais próximo. Logar. |
| Toda `quantidade_g` está entre 30 e 500 | Clampar para o limite mais próximo. |
| Nenhum alimento está na lista de `restricoes` | Remover e substituir. Se impossível, rejeitar plano. |
| A soma de macros do plano está dentro de ±10% do calculado | Ajustar quantidades proporcionalmente. |

---

## 7. Modelo de Dados

### 7.1 Entidade: Usuario

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | `INTEGER` (PK, autoincrement) | Identificador único |
| `nome_completo` | `VARCHAR(150)` | Nome completo do usuário |
| `email` | `VARCHAR(255)` (UNIQUE) | E-mail para login e recuperação |
| `cpf` | `VARCHAR(11)` (UNIQUE) | CPF apenas números |
| `telefone` | `VARCHAR(15)` | Telefone com DDD |
| `senha_hash` | `VARCHAR(255)` | Hash bcrypt da senha |
| `cep` | `VARCHAR(8)` | CEP para endereço |
| `logradouro` | `VARCHAR(255)` | Endereço (via ViaCEP) |
| `bairro` | `VARCHAR(100)` | Bairro |
| `cidade` | `VARCHAR(100)` | Cidade |
| `estado` | `VARCHAR(2)` | UF |
| `criado_em` | `DATETIME` | Data de cadastro (server default: NOW) |

**Relacionamentos:**
- `Usuario` 1 ──── N `SessaoGeracao` (um usuário pode ter múltiplas sessões de geração)
- `Usuario` 1 ──── N `RecuperacaoSenha` (um usuário pode ter múltiplos tokens de recuperação)

### 7.2 Entidade: RecuperacaoSenha

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | `INTEGER` (PK, autoincrement) | Identificador único |
| `usuario_id` | `INTEGER` (FK → Usuario.id) | Usuário dono do token |
| `token` | `VARCHAR(255)` (UNIQUE) | Token criptográfico |
| `criado_em` | `DATETIME` | Data de criação |
| `expira_em` | `DATETIME` | Data de expiração (1h após criação) |
| `utilizado` | `BOOLEAN` | Se o token já foi usado |

### 7.3 Entidade: SessaoGeracao

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | `INTEGER` (PK, autoincrement) | Identificador único |
| `usuario_id` | `INTEGER` (FK → Usuario.id, NULLABLE) | Usuário (NULL se anônimo) |
| `texto_original` | `VARCHAR(2000)` | Input original do usuário |
| `perfil_json` | `VARCHAR(4000)` | JSON com perfil extraído (sexo, idade, etc.) |
| `tmb` | `FLOAT` | TMB calculada |
| `get_calorico` | `FLOAT` | GET calculado |
| `objetivo` | `VARCHAR(30)` | Objetivo detectado |
| `macros_json` | `VARCHAR(500)` | JSON com macros calculados |
| `pdf_uuid` | `VARCHAR(36)` | UUID do PDF gerado |
| `data_geracao` | `DATETIME` | Data/hora da geração (server default: NOW) |
| `data_expiracao_pdf` | `DATETIME` | PDF expira 7 dias após geração |

**Relacionamentos:**
- `SessaoGeracao` N ──── 1 `Usuario` (opcional — pode ser anônimo)
- `SessaoGeracao` 1 ──── 3 `PlanoAlimentar` (exatamente 3 planos por sessão)

### 7.4 Entidade: PlanoAlimentar

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | `INTEGER` (PK, autoincrement) | Identificador único |
| `sessao_id` | `INTEGER` (FK → SessaoGeracao.id) | Sessão de geração |
| `nome` | `VARCHAR(100)` | Nome do plano (ex: "Tradicional Brasileiro") |
| `eixo` | `VARCHAR(30)` | Eixo de diferenciação (tradicional / funcional / pratico) |
| `descricao` | `VARCHAR(500)` | Explicação do plano (2-4 frases) |
| `ordem` | `INTEGER` | Ordem de exibição (1, 2 ou 3) |
| `get_calorico` | `FLOAT` | GET usado neste plano |
| `macros_json` | `VARCHAR(500)` | JSON com {proteina_g, carboidrato_g, gordura_g} |

**Relacionamentos:**
- `PlanoAlimentar` N ──── 1 `SessaoGeracao`
- `PlanoAlimentar` 1 ──── N `Refeicao` (4-6 refeições por plano)

### 7.5 Entidade: Refeicao

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | `INTEGER` (PK, autoincrement) | Identificador único |
| `plano_id` | `INTEGER` (FK → PlanoAlimentar.id) | Plano ao qual pertence |
| `nome` | `VARCHAR(50)` | Nome da refeição (ex: "Café da Manhã") |
| `horario` | `VARCHAR(10)` | Horário sugerido (ex: "07:00") |
| `ordem` | `INTEGER` | Ordem dentro do plano (1 = primeira refeição) |

**Relacionamentos:**
- `Refeicao` N ──── 1 `PlanoAlimentar`
- `Refeicao` 1 ──── N `ItemRefeicao` (1-5 itens por refeição)

### 7.6 Entidade: ItemRefeicao

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id` | `INTEGER` (PK, autoincrement) | Identificador único |
| `refeicao_id` | `INTEGER` (FK → Refeicao.id) | Refeição à qual pertence |
| `alimento_nome` | `VARCHAR(150)` | Nome do alimento (referência ao foods.json) |
| `quantidade_g` | `FLOAT` | Quantidade em gramas |
| `proteina_g` | `FLOAT` | Proteína calculada para esta porção |
| `carboidrato_g` | `FLOAT` | Carboidrato calculado |
| `gordura_g` | `FLOAT` | Gordura calculada |
| `calorias_kcal` | `FLOAT` | Calorias calculadas |

**Relacionamentos:**
- `ItemRefeicao` N ──── 1 `Refeicao`

### 7.7 Diagrama de Relacionamentos (Textual)

```
Usuario (1) ──────────< (N) SessaoGeracao
    │                            │
    │                            │ (exatamente 3)
    │                            │
    │                    PlanoAlimentar (3 por sessão)
    │                            │
    │                            │ (4 a 6)
    │                            │
    │                        Refeicao
    │                            │
    │                            │ (1 a 5)
    │                            │
    │                       ItemRefeicao
    │
    └──────────< (N) RecuperacaoSenha
```

**Nota:** A entidade `Alimento` **não** é persistida no banco. Ela vive no arquivo `data/foods.json` e é carregada em memória pelo `FoodCatalog`. Os `ItemRefeicao` referenciam alimentos por nome (string), não por FK. Isso simplifica a persistência e permite evoluir o catálogo de alimentos sem migrações de banco.

---

## 8. Banco de Dados

### 8.1 SQL Server Express

**Justificativa da escolha:**

| Critério | Avaliação |
|----------|-----------|
| **Instalação local** | Instalador oficial Microsoft, gratuito. Configuração via Windows Authentication sem senhas. |
| **Integração Windows** | `Trusted_Connection=yes` elimina gestão de credenciais de banco. Usa a conta Windows do desenvolvedor. |
| **Adequação ao MVP** | Capacidade de 10GB — suficiente para ~5 milhões de planos. Muito além do necessário na fase inicial. |
| **Portfólio** | SQL Server é amplamente usado no mercado corporativo brasileiro. Ter experiência com ele agrega valor ao portfólio. |
| **Baixa complexidade operacional** | Sem containers, sem orquestração. Um serviço Windows que roda em background. |

**Connection String:**

```
DRIVER={ODBC Driver 17 for SQL Server};
SERVER=localhost\SQLEXPRESS;
DATABASE=diet_plan_generator;
Trusted_Connection=yes
```

Traduzida para SQLAlchemy:

```
mssql+pyodbc:///?odbc_connect=DRIVER%3D{ODBC+Driver+17+for+SQL+Server}%3BSERVER%3Dlocalhost%5CSQLEXPRESS%3BDATABASE%3Ddiet_plan_generator%3BTrusted_Connection%3Dyes
```

### 8.2 Estratégia de Migrations com Alembic

**Fluxo de trabalho:**

```
1. Desenvolvedor altera modelos SQLAlchemy (ex: adiciona campo em PlanoAlimentar)
2. Executa: alembic revision --autogenerate -m "adiciona campo xyz em PlanoAlimentar"
3. Alembic compara modelos Python com schema atual do banco
4. Gera script de migração em alembic/versions/
5. Desenvolvedor revisa o script gerado (autogenerate não é perfeito)
6. Executa: alembic upgrade head
7. Migração aplicada no banco local
8. Script versionado no Git — outros devs executam alembic upgrade head
```

**Configuração (`alembic/env.py`):**

- `target_metadata = Base.metadata` — Alembic detecta automaticamente mudanças nos modelos
- `DATABASE_URL` lida do `.env` (não do `alembic.ini`)
- Engine síncrono (compatível com pyodbc)
- Pool `NullPool` para migrações (evita conexões órfãs)

---

## 9. Integrações Externas

### 9.1 API DeepSeek

| Aspecto | Detalhe |
|---------|---------|
| **Finalidade** | Duas chamadas distintas: (1) Extração de perfil NL→JSON, (2) Geração dos 3 planos alimentares |
| **Modelo** | DeepSeek V4 Pro (`deepseek-chat`) |
| **Endpoint** | `POST https://api.deepseek.com/v1/chat/completions` |
| **Autenticação** | Header `Authorization: Bearer {DEEPSEEK_API_KEY}` |
| **Content-Type** | `application/json` |
| **Configuração** | Todas as configurações via variáveis de ambiente no `.env` |
| **Timeout** | 90 segundos por chamada |
| **Retry** | 2 tentativas com backoff exponencial (2s, 4s) |
| **Rate Limit** | Controlado pelo lado do cliente: máximo 3 chamadas simultâneas (semáforo) |

**Variáveis de ambiente:**

```env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT=90
DEEPSEEK_MAX_RETRIES=2
```

**Tratamento de falhas:**

| Falha | Ação |
|-------|------|
| Timeout (> 90s) | Retry (1x). Se falhar novamente → `DeepSeekUnavailableException` |
| Erro 5xx (servidor) | Retry com backoff. Se esgotar tentativas → `DeepSeekUnavailableException` |
| Erro 4xx (cliente) | Não faz retry. Lança `DeepSeekClientException` com detalhes. |
| Erro 401 (API key inválida) | Erro fatal na inicialização. Sistema não sobe. |
| Erro 429 (rate limit) | Espera `Retry-After` segundos e tenta novamente. |
| JSON de resposta inválido | `DeepSeekInvalidResponseException`. Loga resposta bruta para debug. |
| Resposta sem `planos` | `DeepSeekInvalidResponseException`. Re-solicita com prompt reforçado. |

**Fallback:** Não há fallback para outro provedor de IA na v1. Se a DeepSeek estiver indisponível, o sistema retorna erro 503 com mensagem amigável. A adição de múltiplos provedores está prevista como evolução futura.

### 9.2 ViaCEP (existente, mantido)

| Aspecto | Detalhe |
|---------|---------|
| **Finalidade** | Buscar endereço pelo CEP durante cadastro do usuário |
| **Endpoint** | `GET https://viacep.com.br/ws/{cep}/json/` |
| **Timeout** | 10 segundos |
| **Fallback** | Se offline, campos de endereço ficam vazios (preenchimento manual) |

---

## 10. Segurança

### 10.1 Validação de Entrada

| Mecanismo | Onde | Descrição |
|-----------|------|-----------|
| **Pydantic** | API Layer | Valida tipos, ranges (ge/le), formatos (EmailStr), literais. Rejeita payloads malformados com 422. |
| **Sanitização HTML** | API Layer | Remove tags HTML, scripts e caracteres de controle do texto livre do usuário antes de qualquer processamento (XSS prevention). |
| **Validação fisiológica** | Application Layer | RF-016: rejeita idade < 1 ou > 120, peso < 20 ou > 500, altura < 50 ou > 280. |
| **Rate Limiting** | API Layer | RNF-022: máximo 10 requisições/minuto por IP para não autenticados. Implementado via middleware. |
| **Size limit** | API Layer | Corpo da requisição limitado a 1MB. Texto do usuário limitado a 2000 caracteres. |

### 10.2 Sanitização de Dados

- Todo input de texto livre do usuário é stripado de caracteres de controle (ASCII 0-31, exceto \n, \r, \t)
- Tags HTML são removidas via regex antes do armazenamento
- O texto original é armazenado sanitizado, nunca raw
- Dados de saúde (peso, altura, condições médicas) são mascarados nos logs: `[DADO_SAUDE_REMOVIDO]`

### 10.3 Armazenamento Seguro de Chaves

| Chave/Secret | Onde fica | Proteção |
|--------------|-----------|----------|
| `DEEPSEEK_API_KEY` | `.env` (nunca versionado) | Adicionado ao `.gitignore`. Documentado no `README.md` como obrigatório. |
| `JWT_SECRET_KEY` | `.env` (nunca versionado) | Se não configurada, sistema não sobe (RuntimeError na inicialização). |
| `DATABASE_URL` | `.env` | Contém connection string. Não versionado. |
| Senhas de usuário | Banco (hash bcrypt) | Nunca em texto puro. bcrypt com custo 12. |
| PDF UUIDs | Gerados com `uuid.uuid4()` | Não previsíveis. Validados com regex rigorosa contra path traversal. |

### 10.4 Variáveis de Ambiente

Todas as configurações sensíveis ou específicas de ambiente são gerenciadas via `.env` e carregadas com `python-dotenv`:

```env
# Banco de Dados
DATABASE_URL=mssql+pyodbc:///?odbc_connect=...

# DeepSeek
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT=90
DEEPSEEK_MAX_RETRIES=2

# JWT
JWT_SECRET_KEY=chave-secreta-gerada-aleatoriamente
JWT_EXPIRATION_HOURS=24

# Aplicação
APP_ENV=development
APP_DEBUG=true
APP_PORT=8000
```

### 10.5 Tratamento de Exceções

| Exceção | HTTP Status | Mensagem para o usuário |
|----------|:-----------:|-------------------------|
| `PydanticValidationError` | 422 | Detalhes do campo inválido (automático) |
| `CampoObrigatorioAusenteException` | 400 | "Não consegui identificar [campo]. Por favor, inclua no texto." |
| `ValorFisiologicoInvalidoException` | 400 | "O valor informado para [campo] está fora do intervalo esperado." |
| `DeepSeekUnavailableException` | 503 | "Nosso serviço de IA está temporariamente indisponível. Tente novamente em alguns minutos." |
| `DeepSeekInvalidResponseException` | 502 | "Não foi possível gerar os planos. Nossa equipe foi notificada." |
| `PlanoValidacaoException` | 500 | "Erro interno ao validar os planos gerados. Tente novamente." |
| `DatabaseException` | 500 | "Erro interno ao salvar os dados. Tente novamente." |
| `TimeoutException` | 504 | "A geração dos planos excedeu o tempo limite. Tente um texto mais curto ou tente novamente." |
| `RateLimitException` | 429 | "Muitas requisições. Aguarde alguns segundos e tente novamente." |
| Genérico não tratado | 500 | "Erro interno. Nossa equipe foi notificada." (Detalhes NUNCA expostos) |

### 10.6 Logs de Erro

- Logs estruturados em JSON (RNF-043)
- Incluem `request_id` (UUID) para correlação entre logs
- Stack traces completos são logados, mas NUNCA retornados para o cliente
- Dados sensíveis (API keys, senhas, dados de saúde) são mascarados nos logs
- Nível ERROR para falhas internas; nível WARNING para falhas de validação do usuário

---

## 11. Escalabilidade Futura

A arquitetura foi projetada para evoluir sem reescrita. Abaixo, as direções de crescimento previstas e como a arquitetura atual as suporta.

### 11.1 Curto Prazo (v1.1 — pós-MVP)

| Evolução | Impacto na arquitetura | Camada afetada |
|----------|------------------------|:--------------:|
| **Autenticação JWT** | Já suportada. Basta adicionar middleware `Depends(verificar_token)` nos endpoints. | API, Application |
| **Histórico de gerações** | Já suportado. `SessaoGeracao` persiste tudo. Basta criar endpoint `GET /api/diet/history`. | API, Application |
| **Exportação para PDF** | Já implementada. ReportLab incluso. | Infrastructure |
| **Cache de alimentos** | `FoodCatalog` já carrega em memória. Pode evoluir para Redis se necessário. | Infrastructure |
| **Feedback de planos** | Adicionar entidade `Feedback` com FK para `PlanoAlimentar`. | Domain, Infrastructure |

### 11.2 Médio Prazo (v2)

| Evolução | Impacto na arquitetura | Camada afetada |
|----------|------------------------|:--------------:|
| **Múltiplos provedores de IA** | A interface `PlanoGeneratorInterface` já permite trocar implementação. Criar `OpenAIPlanGenerator`, `ClaudePlanGenerator`, etc. | Infrastructure |
| **Área administrativa** | Adicionar routers admin com autenticação role-based. Métricas de uso, qualidade dos planos, custos. | API, Application |
| **Chat multi-turno** | Adicionar entidade `Conversa` e estado de sessão. Refatorar `GerarPlanosUseCase` para modo interativo. | Domain, Application |
| **Cache distribuído (Redis)** | Substituir cache em memória por Redis para suportar múltiplas instâncias. | Infrastructure |

### 11.3 Longo Prazo (v3)

| Evolução | Impacto na arquitetura | Camada afetada |
|----------|------------------------|:--------------:|
| **Worker de IA separado** | Extrair `PlanGeneratorService` para um worker independente (Celery ou similar). Filas para processamento assíncrono. WebSocket para notificar progresso. | Application, Infrastructure |
| **App mobile nativo** | A API REST já é compatível. Basta desenvolver cliente mobile (React Native / Flutter). | Externa |
| **Integração com nutricionistas** | Adicionar entidade `Nutricionista`, permissões de acesso a planos de pacientes, dashboard profissional. | Todas |
| **Treinos de exercício** | Novo módulo independente. Pode ser um monolito modular separado ou integrado. | Novo módulo |
| **Pagamentos / Assinatura** | Integrar gateway de pagamento (Stripe/Mercado Pago). Adicionar entidades `Assinatura`, `PlanoPremium`. | API, Domain, Infrastructure |

### 11.4 Preparação para o Futuro

A arquitetura atual já está preparada para essas evoluções porque:

1. **Domain Layer independente:** Adicionar novas regras de negócio não afeta API ou Infrastructure
2. **Interfaces bem definidas:** Trocar implementação de IA (DeepSeek → OpenAI) é uma mudança na Infrastructure apenas
3. **Monólito modular:** Se um módulo crescer demais, extraí-lo para um serviço separado é uma mudança de deployment, não de código
4. **Stateless por design:** Adicionar mais instâncias atrás de load balancer não requer mudanças de código (exceto cache distribuído)
5. **Versionamento de schema (Alembic):** Adicionar colunas/tabelas é seguro e rastreável
6. **API REST padrão:** Clientes mobile ou third-party consomem a mesma API que o frontend web

---

> **Para a IA que vai gerar código:** Este documento define a arquitetura canônica. Use-o como referência para:
> - Decidir onde cada classe/módulo/arquivo deve ficar (qual camada)
> - Seguir o fluxo de dependências (API → Application → Domain ← Infrastructure)
> - Implementar o contrato de resposta da IA (seção 6)
> - Configurar integrações externas (seção 9)
> - Aplicar regras de segurança (seção 10)
> 
> Consulte também:
> - `docs/visao.md` — Visão do produto (O QUE construir)
> - `docs/regras.md` — Regras de negócio (RN-001 a RN-142)
> - `docs/requisitos.md` — Requisitos funcionais e não-funcionais com priorização
