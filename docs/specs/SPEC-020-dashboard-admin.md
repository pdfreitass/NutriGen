# SPEC-020: Dashboard Administrativo

**Status:** ⚪ Pendente
**Fase:** 3 — Escala e Personalização
**Pré-requisito:** Fase 2 concluída com > 70% de aprovação

---

## User Story

Como administrador, quero um painel web para monitorar o sistema em tempo real, visualizar métricas e gerenciar usuários.

---

## Critérios de Aceite

- [ ] Página `GET /admin` protegida por autenticação admin (JWT com role `admin`)
- [ ] Abas do dashboard:
  - **Visão Geral:** planos gerados hoje, usuários ativos, taxa de erro, custo DeepSeek
  - **Métricas:** gráficos de uso (diário/semanal), distribuição de objetivos, latência
  - **Qualidade:** taxa de feedback positivo/negativo, top motivos de rejeição
  - **Usuários:** lista de usuários cadastrados, data de cadastro, total de gerações
  - **Logs:** visualização dos últimos 100 logs de erro
- [ ] Gráficos simples (Chart.js ou similar) — sem dependência pesada
- [ ] Filtro por período: hoje, 7 dias, 30 dias, personalizado

---

## Arquivos Previstos

- `frontend/admin.html` (novo)
- `frontend/css/admin.css` (novo)
- `frontend/js/admin.js` (novo)
- `app/routers/admin.py` (atualizar com endpoints de dados)

---

## Notas Técnicas

- O dashboard é uma página separada do frontend principal, acessível apenas por admins
- Gráficos usam dados agregados (não fazem consultas pesadas ao banco em tempo real)
- Métricas são pré-calculadas a cada hora por um job simples
