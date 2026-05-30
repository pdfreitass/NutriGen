# 🥗 NutriGen — Gerador de Planos Alimentares com IA

Descreva sua rotina em linguagem natural e receba **3 planos alimentares distintos** gerados por inteligência artificial.

> **“Descreva sua rotina em 3 frases. Receba 3 planos em segundos.”**

---

## 🚀 Funcionalidades

- ✅ Input em linguagem natural — sem formulários rígidos
- ✅ Extração automática de perfil, preferências e restrições via IA
- ✅ Cálculo de TMB (Mifflin-St Jeor) e GET
- ✅ 3 planos distintos: **Tradicional Brasileiro**, **Funcional & Nutrientes**, **Prático & Rápido**
- ✅ Banco de dados com 68 alimentos categorizados
- ✅ PDF profissional com todos os planos
- ✅ Uso anônimo — sem cadastro obrigatório
- ✅ Documentação Swagger automática

---

## 📦 Instalação

```bash
# Clonar o repositório
git clone https://github.com/pdfreitass/NutriGen.git
cd NutriGen

# Criar ambiente virtual
python -m venv .venv
source .venv/Scripts/activate  # Windows
# ou: source .venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas chaves (DeepSeek API Key obrigatória)

# Criar banco de dados no SQL Server Express
# Execute no SQL Server Management Studio:
# CREATE DATABASE nutrigen;
```

---

## ▶️ Como Rodar

```bash
uvicorn app.main:app --reload
```

Acesse:
- **Swagger UI**: http://localhost:8000/docs
- **Frontend**: http://localhost:8000
- **Health Check**: http://localhost:8000/health

---

## 📖 Endpoints

### `POST /api/diet/generate`

Gera 3 planos alimentares a partir de texto livre.

**Exemplo de requisição:**
```json
{
  "texto": "Trabalho sentado o dia todo, faço musculação 4x por semana. Quero ganhar massa. Tenho 1,75m, 72kg e 28 anos. Gosto de frango, batata doce, ovo e banana. Não como peixe."
}
```

### `GET /api/diet/{id}/pdf`

Download do PDF consolidado com os 3 planos.

### `POST /api/auth/register` `POST /api/auth/login`

Cadastro e autenticação de usuários (opcional).

---

## 🏗️ Tecnologias

| Tecnologia | Finalidade |
|------------|------------|
| **Python 3.12** | Linguagem base |
| **FastAPI** | Framework web REST |
| **Pydantic v2** | Validação de dados |
| **SQLAlchemy 2.0** | ORM |
| **SQL Server Express** | Banco de dados |
| **Alembic** | Migrações de banco |
| **DeepSeek V4 Pro** | Geração de planos via IA |
| **ReportLab** | Geração de PDF |
| **bcrypt + PyJWT** | Autenticação segura |

---

## 📁 Estrutura do Projeto

```
NutriGen/
├── app/
│   ├── main.py                  # Entry point FastAPI
│   ├── database.py              # Configuração SQLAlchemy + SQL Server
│   ├── models/
│   │   ├── schemas.py           # Schemas Pydantic (validação)
│   │   └── database/            # Modelos ORM (SQLAlchemy)
│   ├── repositories/            # Padrão Repository (acesso a dados)
│   ├── services/                # Lógica de negócio + IA
│   ├── routers/                 # Endpoints da API
│   └── utils/                   # Utilitários (PDF generator)
├── frontend/                    # SPA (HTML/CSS/JS)
├── data/
│   └── foods.json               # Catálogo de 68 alimentos
├── alembic/                     # Migrações de banco
├── docs/                        # Documentação completa
│   ├── visao.md                 # Visão do produto (5 perspectivas)
│   ├── arquitetura.md           # Arquitetura técnica
│   ├── regras.md                # 59 regras de negócio
│   ├── requisitos.md            # 72 requisitos (RF + RNF)
│   ├── ADR.md                   # 6 decisões arquiteturais
│   ├── fluxos.md                # 5 fluxos detalhados
│   ├── licoes-aprendidas.md     # Memória persistente da IA
│   └── specs/roadmap.md         # 25 SPECs em 3 fases
├── requirements.txt
└── README.md
```

---

## 📚 Documentação

| Documento | Conteúdo |
|-----------|----------|
| [`docs/visao.md`](docs/visao.md) | Visão do cliente, engenharia, comprador e admin |
| [`docs/arquitetura.md`](docs/arquitetura.md) | Arquitetura em camadas, stack, fluxos, prompt engineering |
| [`docs/regras.md`](docs/regras.md) | 59 regras de negócio (RN-001 a RN-142) |
| [`docs/requisitos.md`](docs/requisitos.md) | 46 requisitos funcionais + 26 não-funcionais |
| [`docs/ADR.md`](docs/ADR.md) | 6 decisões arquiteturais registradas |
| [`docs/fluxos.md`](docs/fluxos.md) | 5 fluxos de interação detalhados |
| [`docs/licoes-aprendidas.md`](docs/licoes-aprendidas.md) | Memória persistente entre sessões de IA |
| [`docs/specs/roadmap.md`](docs/specs/roadmap.md) | 25 SPECs em 3 fases + backlog |

---

## 📄 Licença

Projeto pessoal — Pedro Freitas
