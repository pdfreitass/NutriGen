# 💡 Banco de Ideias Sugeridas — NutriGen

> **Propósito:** Registro de ideias sugeridas pela IA durante o desenvolvimento. Funciona como uma "caixa de entrada" antes de virarem SPECs formais no roadmap.
>
> **Fluxo:** IA sugere → Desenvolvedor aprova/rejeita → Se aprovado, ideia é movida para o [roadmap.md](roadmap.md) e/ou vira uma SPEC.
>
> **Atualizado em:** 2026-06-05

---

## 📋 Status das Ideias

| # | Ideia | Status | Data | Decisão |
|:-:|-------|:------:|------|---------|
| 1 | Lista de compras automática da semana | ⏳ Aguardando | 05/06/2026 | — |
| 2 | Comparação lado a lado dos 3 planos com destaques visuais | ⏳ Aguardando | 05/06/2026 | — |
| 3 | Modo nutricionista — múltiplos pacientes | ⏳ Aguardando | 05/06/2026 | — |
| 4 | Recomendações semanais por e-mail | ⏳ Aguardando | 05/06/2026 | — |
| 5 | Notificações push para horários de refeição | ⏳ Aguardando | 05/06/2026 | — |
| 6 | Dark mode no frontend | ⏳ Aguardando | 05/06/2026 | — |
| 7 | Suporte a múltiplos idiomas (i18n) | ⏳ Aguardando | 05/06/2026 | — |
| 8 | Editor de alimentos — usuário pode sugerir novos alimentos para o catálogo | ⏳ Aguardando | 05/06/2026 | — |
| 9 | Gráfico de evolução — acompanhar calorias/macros ao longo da semana | ⏳ Aguardando | 05/06/2026 | — |
| 10 | Testes automatizados (pytest) para o pipeline de geração | ⏳ Aguardando | 05/06/2026 | — |

---

## 🔍 Detalhamento das Ideias

### 1. Lista de compras automática da semana

**Complexidade:** Baixa | **Impacto:** Alto

Agrupar todos os ingredientes dos 3 planos, somar quantidades totais da semana, agrupar por categoria (hortifruti, proteínas, grãos, etc.) e gerar um PDF/checklist de compras.

- **Arquivos previstos:** `app/utils/gerador_lista_compras.py` (novo), `app/routers/dieta.py` (novo endpoint `GET /api/diet/{id}/shopping-list`)
- **Relacionado a:** SPEC-053 (exportação avançada)

---

### 2. Comparação lado a lado dos 3 planos

**Complexidade:** Média | **Impacto:** Médio

Tabela visual comparando os 3 planos coluna a coluna: calorias por refeição, distribuição de macros, variedade de alimentos. Destacar com cores o que cada plano tem de melhor.

- **Arquivos previstos:** `frontend/js/comparacao.js` (novo), `frontend/css/comparacao.css` (novo), `frontend/index.html` (modificado)
- **Relacionado a:** SPEC-031 (frontend resultados)

---

### 3. Modo nutricionista — múltiplos pacientes

**Complexidade:** Alta | **Impacto:** Alto

Permitir que um nutricionista cadastrado gerencie múltiplos pacientes, cada um com seu perfil, histórico de planos e evolução. Dashboard separado.

- **Arquivos previstos:** `app/models/database/paciente.py` (novo), `app/routers/nutricionista.py` (novo), `app/services/servico_paciente.py` (novo)
- **Relacionado a:** SPEC-050 (dashboard admin)

---

### 4. Recomendações semanais por e-mail

**Complexidade:** Média | **Impacto:** Alto

Usuário cadastrado recebe toda segunda-feira um e-mail com sugestão de cardápio semanal baseado no perfil e preferências salvas.

- **Arquivos previstos:** `app/services/servico_email.py` (novo), `app/services/scheduler.py` (novo)
- **Relacionado a:** SPEC-054 (perfis de usuário)
- **Dependências novas:** `smtplib` (stdlib) ou SendGrid/Resend API

---

### 5. Notificações push para horários de refeição

**Complexidade:** Média | **Impacto:** Médio

Notificações no navegador (Service Worker) ou futuramente no app mobile lembrando o usuário dos horários das refeições do plano ativo.

- **Arquivos previstos:** `frontend/js/notificacoes.js` (novo), `frontend/service-worker.js` (novo)
- **Relacionado a:** Ideia #1 do backlog (app mobile)

---

### 6. Dark mode no frontend

**Complexidade:** Baixa | **Impacto:** Médio

Alternância entre tema claro/escuro no frontend com toggle, persistindo preferência no `localStorage`.

- **Arquivos previstos:** `frontend/css/dark-mode.css` (novo), `frontend/css/style.css` (modificado), `frontend/js/app.js` (modificado)

---

### 7. Suporte a múltiplos idiomas (i18n)

**Complexidade:** Alta | **Impacto:** Médio

Internacionalização: extrair todas as strings do frontend e mensagens de erro do backend para arquivos de tradução (PT-BR, EN, ES).

- **Arquivos previstos:** `frontend/js/i18n.js` (novo), `frontend/locales/` (novo diretório)
- **Relacionado a:** Regra do projeto "todo em PT-BR"

---

### 8. Editor de alimentos — sugerir novos alimentos

**Complexidade:** Média | **Impacto:** Médio

Usuário pode sugerir novos alimentos para o catálogo via frontend. Nutricionista/admin aprova. Os aprovados entram no `foods.json`.

- **Arquivos previstos:** `app/routers/alimentos.py` (novo endpoint), `app/models/database/sugestao_alimento.py` (novo)
- **Relacionado a:** SPEC-060 (seleção de alimentos), SPEC-012 (catálogo de alimentos)

---

### 9. Gráfico de evolução de calorias/macros

**Complexidade:** Média | **Impacto:** Médio

Se o usuário registrar o que realmente comeu, mostrar gráfico comparando planejado vs. realizado por dia/semana (Chart.js ou similar).

- **Arquivos previstos:** `frontend/js/graficos.js` (novo), `app/routers/registro.py` (novo endpoint `POST /api/tracking/log`)
- **Dependências novas:** Chart.js (CDN, sem instalação)

---

### 10. Testes automatizados (pytest)

**Complexidade:** Alta | **Impacto:** Alto

Cobertura de testes unitários e de integração para o pipeline completo: extração, cálculo de TMB, geração de planos, validação, PDF. Essencial antes de crescer mais.

- **Arquivos previstos:** `tests/` (novo diretório), `tests/test_extractor.py`, `tests/test_nutrition_calculator.py`, `tests/test_plan_generator.py`, `tests/test_plan_validator.py`, `tests/test_use_case.py`
- **Dependências novas:** `pytest`, `pytest-cov`, `pytest-mock` (dev, não produção)

---

## 📝 Regras do Banco de Ideias

1. **Sugestão:** IA sugere ideias verbalmente durante a conversa.
2. **Aprovação:** Desenvolvedor aprova ou rejeita.
3. **Registro:** Se aprovado, IA adiciona neste arquivo com status "✅ Aprovado".
4. **SPEC:** Se a ideia for complexa, IA propõe criar uma SPEC ou atualiza o roadmap.
5. **Implementação:** Só implementa após aprovação explícita do desenvolvedor.

---

> **Legenda de Status:**
> - ⏳ Aguardando — Sugerido, aguardando decisão
> - ✅ Aprovado — Aprovado, pronto para SPEC/implementação
> - ❌ Rejeitado — Não será implementado
> - 🔄 Em SPEC — Já virou SPEC formal no roadmap
