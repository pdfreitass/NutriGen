# SPEC-043: Métricas e Analytics Básicos

**Status:** ⚪ Pendente
**Fase:** 2 — Refina a Experiência
**Pré-requisito:** MVP (Fase 1) concluído

---

## User Story

Como product owner, quero métricas básicas de uso do sistema, para tomar decisões baseadas em dados.

---

## Critérios de Aceite

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

---

## Arquivos Previstos

- `app/routers/admin.py` (novo)
- `app/models/database/evento_analytics.py` (novo)
- `app/middleware/analytics.py` (novo)
- `alembic/versions/` (nova migração)

---

## Notas Técnicas

- O middleware de analytics NÃO deve impactar a latência da resposta — registra o evento após enviar a resposta ao cliente (background)
- Dados de analytics são anonimizados: sem IP, sem texto original, sem e-mail
