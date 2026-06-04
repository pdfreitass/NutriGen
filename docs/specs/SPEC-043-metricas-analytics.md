# SPEC-043: Métricas e Analytics Básicos

**Status:** ⚪ Pendente
**Fase:** 2
**Tipo:** Subspec
**Subspec de:** SPEC-040
**Depende de:** SPEC-041 (Feedback)
**Data de criação:** 2026-05-30

---

## 1. User Story

Como product owner, quero métricas básicas de uso do sistema, para tomar decisões baseadas em dados.

---

## 2. Critérios de Aceite

- [ ] `GET /api/admin/metrics` (protegido por JWT admin) retorna:
  - Planos gerados hoje / semana / mês
  - Distribuição de objetivos (% perda/manutenção/ganho)
  - Distribuição de eixos (tradicional/funcional/pratico)
  - Taxa de erro (extração, geração, validação)
  - Latência média (extração, geração, total)
  - Custo estimado DeepSeek (tokens × preço)
  - Top 10 alimentos mais sugeridos
- [ ] Middleware de analytics registra evento `plan_gerado` após resposta (background, não bloqueante)
- [ ] Tabela `eventos_analytics` (leve, anonimizada, sem IP/texto original)

---

## 3. Contratos de Dados

```json
// GET /api/admin/metrics
{
  "periodo": {"hoje": "2026-06-04", "dias": 7},
  "geracoes": {"hoje": 12, "semana": 87, "mes": 340},
  "objetivos_pct": {"perda_de_peso": 45, "manutencao": 30, "ganho_de_massa": 25},
  "eixos_pct": {"tradicional": 40, "funcional": 35, "pratico": 25},
  "taxa_erro_pct": 4.2,
  "latencia_media_s": {"extracao": 2.5, "geracao": 10.2, "total": 14.8},
  "custo_estimado_brl": 2.45,
  "top_alimentos": ["Peito de Frango Grelhado", "Arroz Branco Cozido", "Banana"]
}
```

---

## 4. Fluxo de Implementação

```
Passo 1 — Criar EventoAnalytics ORM (tipo, metadados_json, criado_em)
Passo 2 — Middleware analytics: após response, thread separada salva evento
Passo 3 — GET /api/admin/metrics: agrega eventos por período
Passo 4 — DeepSeekClient registra tokens consumidos para cálculo de custo
```

---

## 5. Arquivos Previstos

| Arquivo | Camada | Tipo |
|---------|:------:|:----:|
| `app/models/database/evento_analytics.py` | Domain | Novo |
| `app/routers/admin.py` | API | Novo |
| `app/middleware/analytics.py` | API | Novo |
| `alembic/versions/xxx_analytics.py` | Infra | Nova migração |
