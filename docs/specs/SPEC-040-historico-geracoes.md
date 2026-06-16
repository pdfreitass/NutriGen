# SPEC-040: Histórico de Gerações para Usuários Autenticados

**Status:** ⚪ Pendente
**Fase:** 2
**Tipo:** Principal
**Depende de:** SPEC-025 (Endpoint), SPEC-031 (Frontend Resultados)
**Data de criação:** 2026-05-30

---

## 1. User Story

Como usuário autenticado, quero acessar o histórico de todos os planos que já gerei, para revisitar planos anteriores sem precisar salvar os PDFs.

---

## 2. Critérios de Aceite

### 2.1 Backend

- [ ] **HIST-01:** `GET /api/diet/history?page=1&limit=10` retorna lista paginada de gerações do usuário.
  - **Input:** Query params `page` (default 1), `limit` (default 10, max 50). Header `Authorization: Bearer <JWT>`.
  - **Output esperado:** `{ "items": [...], "total": 15, "page": 1, "pages": 2 }`
  - **Regras relacionadas:** RN-140, RN-141

- [ ] **HIST-02:** Cada item do histórico contém:
  - `sessao_id`: UUID da sessão
  - `data_geracao`: datetime ISO 8601
  - `objetivo`: perda_de_peso / manutencao / ganho_de_massa
  - `get_calorico`: kcal
  - `tmb`: kcal
  - `pdf_disponivel`: bool (true se PDF ainda não expirou)
  - `pdf_url`: string | null (link apenas se dentro de 7 dias)
  - `resumo`: `{ "planos": [{ "nome": "...", "eixo": "...", "calorias": 0 }] }`

- [ ] **HIST-03:** `DELETE /api/diet/{sessao_id}` remove a sessão e planos associados (LGPD).
  - **Input:** `sessao_id` (int), JWT do dono.
  - **Output:** 200 `{ "mensagem": "Sessão excluída com sucesso" }`
  - **Erro:** 403 se não for dono, 404 se não existir.

- [ ] **HIST-04:** Itens com `data_geracao > 30 dias` não aparecem (expiração automática, RN-130).

### 2.2 Frontend

- [ ] **HIST-05:** Nova página "Meus Planos" acessível pelo header (ícone 📋, visível apenas logado).
- [ ] **HIST-06:** Lista de cards com: data formatada (dd/mm/aaaa), objetivo (ícone), GET, botão PDF (se disponível), botão Excluir.
- [ ] **HIST-07:** Paginação: "Mostrando 1-10 de 15" com botões Anterior/Próximo.

---

## 3. Contratos de Dados

### 3.1 GET /api/diet/history

**Response 200:**
```json
{
  "items": [{
    "sessao_id": 42,
    "data_geracao": "2026-06-04T15:30:00Z",
    "objetivo": "perda_de_peso",
    "get_calorico": 1856.0,
    "tmb": 1546.0,
    "pdf_disponivel": true,
    "pdf_url": "/api/diet/abc123/pdf",
    "resumo": {
      "planos": [
        {"nome": "Tradicional Brasileiro", "eixo": "tradicional", "calorias_estimadas": 1800},
        {"nome": "Funcional & Nutrientes", "eixo": "funcional", "calorias_estimadas": 1820},
        {"nome": "Prático & Rápido", "eixo": "pratico", "calorias_estimadas": 1780}
      ]
    }
  }],
  "total": 15,
  "page": 1,
  "pages": 2
}
```

### 3.2 DELETE /api/diet/{sessao_id}

**Response 200:** `{ "mensagem": "Sessão excluída com sucesso" }`
**Response 403:** `{ "detail": "Você não tem permissão para excluir esta sessão" }`
**Response 404:** `{ "detail": "Sessão não encontrada" }`

---

## 4. Fluxo de Implementação

```
Passo 1 — SessaoGeracaoRepository.listar_por_usuario(usuario_id, page, limit)
  Recebe: usuario_id: int
  Faz: Query SQLAlchemy filtrando usuario_id, data_geracao < 30 dias, ordenado DESC
  Retorna: tuple[list[SessaoGeracao], int] (items, total)

Passo 2 — GET /api/diet/history
  Recebe: JWT → usuario_id + page, limit
  Faz: Chama repository, monta response com pdf_disponivel (data + 7 dias > now)
  Retorna: JSON paginado

Passo 3 — DELETE /api/diet/{sessao_id}
  Recebe: sessao_id + JWT
  Faz: Verifica dono, executa delete em cascata (planos, refeições, itens)
  Retorna: 200 ou erro
```

---

## 5. Regras de Negócio

| ID | Regra |
|----|-------|
| RN-140 | Histórico disponível apenas para usuários autenticados |
| RN-141 | Cada usuário vê apenas seu próprio histórico |
| RN-130 | Planos com > 30 dias são excluídos automaticamente |
| RN-131 | PDFs com > 7 dias são excluídos (link retorna 404) |
| RN-123 | Usuário pode solicitar exclusão de dados (LGPD) — endpoint DELETE |

---

## 6. Arquivos Previstos

| Arquivo | Camada | Tipo |
|---------|:------:|:----:|
| `app/routers/dieta.py` | API | Modificado (+GET /history, +DELETE) |
| `app/infrastructure/repositorio_sessao.py` | Infrastructure | Novo |
| `frontend/index.html` | Frontend | Modificado (nova página) |
| `frontend/js/app.js` | Frontend | Modificado (lógica histórico) |

---

## 7. Notas Técnicas

- **Performance:** Query com índice em `(usuario_id, data_geracao DESC)`. Paginação via `LIMIT/OFFSET`.
- **Segurança:** Verificar `usuario_id` do JWT contra o dono da sessão no DELETE.
- **Compatibilidade:** Endpoint atual `POST /generate` não é afetado.
