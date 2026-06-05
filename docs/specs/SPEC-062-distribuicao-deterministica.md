# SPEC-062: Algoritmo de Distribuição Determinística

**Status:** ⚪ Pendente
**Fase:** 2
**Tipo:** Subspec
**Subspec de:** SPEC-060
**Depende de:** SPEC-012 (Catálogo de Alimentos)
**Data de criação:** 2026-06-05

---

## 1. User Story

Como sistema, quero distribuir alimentos selecionados em 3 planos com 4-6 refeições cada, de forma determinística, atingindo as metas de macros sem depender de IA.

---

## 2. Critérios de Aceite

- [ ] **DIST-01:** `MealDistributor` recebe alimentos + metas → 3 planos com refeições
- [ ] **DIST-02:** Distribuição calórica por eixo: Tradicional (20/35/15/30), Funcional (25/30/20/25), Prático (15/30/25/30)
- [ ] **DIST-03:** Alimentos preferidos aparecem em 2+ planos
- [ ] **DIST-04:** Quantidades ajustadas automaticamente (±10% macros, 95-105% GET)
- [ ] **DIST-05:** Máximo 50% sobreposição entre planos

---

## 3. Arquivos Previstos

| Arquivo | Tipo |
|---------|:----:|
| `app/services/distribuidor_refeicoes.py` | Novo |
