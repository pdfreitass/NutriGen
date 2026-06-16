# SPEC-041: Sistema de Feedback de Planos

**Status:** ⚪ Pendente
**Fase:** 2
**Tipo:** Subspec
**Subspec de:** SPEC-040
**Depende de:** SPEC-040 (Histórico)
**Data de criação:** 2026-05-30

---

## 1. User Story

Como product owner, quero coletar feedback dos usuários sobre a qualidade dos planos gerados, para identificar padrões de insatisfação e melhorar o sistema com dados reais.

---

## 2. Critérios de Aceite

### 2.1 Backend

- [ ] **FB-01:** `POST /api/diet/feedback` com body `{ "sessao_id": int, "plano_idx": 0..2, "positivo": bool, "motivo": str|null, "comentario": str|null }`.
  - **Input:** JSON com campos obrigatórios: `sessao_id`, `plano_idx`, `positivo`.
  - **Output:** 201 `{ "mensagem": "Feedback registrado. Obrigado!" }`
  - **Tabela:** `feedback_planos(id, sessao_id, plano_idx, positivo, motivo, comentario, criado_em)`

- [ ] **FB-02:** `GET /api/diet/feedback/stats` retorna métricas agregadas (apenas admin).
  - **Output:** `{ "total_feedbacks": N, "positivos_pct": X, "por_eixo": {...}, "motivos_negativos": {...} }`

- [ ] **FB-03:** Feedback anônimo — não requer autenticação. Anti-spam: 1 feedback por sessão+plano por IP (24h).

### 2.2 Frontend

- [ ] **FB-04:** Botões 👍/👎 abaixo de cada plano na tela de resultados.
- [ ] **FB-05:** Clique em 👎 abre mini-formulário com radio buttons: "Alimentos repetidos", "Quantidades irreais", "Combinações ruins", "Alimentos indesejados", "Outro" + campo texto opcional.
- [ ] **FB-06:** Toast de confirmação: "Obrigado pelo feedback!" após envio.

---

## 3. Contratos de Dados

### POST /api/diet/feedback
```json
// Request
{ "sessao_id": 42, "plano_idx": 0, "positivo": false, "motivo": "quantidades_irreais", "comentario": "500g de frango no café é muito" }

// Response 201
{ "mensagem": "Feedback registrado. Obrigado!" }

// Response 429 (spam)
{ "detail": "Você já avaliou este plano. Tente novamente em 24h." }
```

---

## 4. Fluxo de Implementação

```
Passo 1 — Criar modelo ORM Feedback(id, sessao_id, plano_idx, positivo, motivo, comentario, ip_hash, criado_em)
Passo 2 — POST /api/diet/feedback → validar anti-spam → salvar → 201
Passo 3 — Frontend: adicionar botões 👍/👎 em _buildPlanCard(), handler de clique
Passo 4 — Migração Alembic para tabela feedback_planos
```

---

## 5. Regras de Negócio

| ID | Regra |
|----|-------|
| RN-146 | Feedback é anônimo — não requer login |
| RN-147 | Máximo 1 feedback por sessão+plano por IP a cada 24h (anti-spam) |
| RN-148 | Feedbacks negativos são logados separadamente para análise (RF-072) |

---

## 6. Arquivos Previstos

| Arquivo | Camada | Tipo |
|---------|:------:|:----:|
| `app/models/database/feedback.py` | Domain | Novo |
| `app/routers/dieta.py` | API | Modificado (+POST /feedback) |
| `alembic/versions/xxx_feedback.py` | Infra | Nova migração |
| `frontend/js/app.js` | Frontend | Modificado |
