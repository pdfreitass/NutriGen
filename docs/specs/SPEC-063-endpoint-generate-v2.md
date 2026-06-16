# SPEC-063: Endpoint Generate-v2 + Fallback Determinístico

**Status:** ⚪ Pendente
**Fase:** 2
**Tipo:** Subspec
**Subspec de:** SPEC-060
**Depende de:** SPEC-025 (Endpoint), SPEC-062 (Distribuição)
**Data de criação:** 2026-06-05

---

## 1. User Story

Como sistema, quero oferecer um endpoint que aceite a lista de alimentos selecionados pelo usuário e gere planos deterministicamente, usando IA apenas para nomes/descrições, com fallback se a IA estiver offline.

---

## 2. Critérios de Aceite

- [ ] **GENV2-01:** `POST /api/diet/generate-v2` aceita `FoodSelectionRequest` (perfil + alimentos + texto_rotina)
- [ ] **GENV2-02:** Valida mínimo 5 alimentos + proteína obrigatória (400 se inválido)
- [ ] **GENV2-03:** Pipeline: calcular metas → distribuir alimentos → (opcional) IA para nomes/descrições → PDF
- [ ] **GENV2-04:** Fallback determinístico se DeepSeek offline: nomes padrão, sem chamada IA
- [ ] **GENV2-05:** Mantém endpoint legado `POST /api/diet/generate` funcionando

---

## 3. Arquivos Previstos

| Arquivo | Tipo |
|---------|:----:|
| `app/models/esquemas.py` | Modificado (+FoodSelectionRequest) |
| `app/routers/dieta.py` | Modificado (+POST /generate-v2) |
| `app/routers/alimentos.py` | Novo (GET /api/foods/catalog) |
| `app/use_cases/gerar_planos.py` | Modificado (+executar_v2) |
