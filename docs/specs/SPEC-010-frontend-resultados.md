# SPEC-010: Frontend — Tela de Resultados com 3 Planos

**Status:** 🔴 Pendente
**Fase:** 1 — MVP

---

## User Story

Como usuário, quero visualizar os 3 planos gerados de forma clara e comparável, com ações para baixar PDF e gerar novamente.

---

## Critérios de Aceite

- [ ] Transição suave (fadeIn) da tela de input para tela de resultados
- [ ] Seção de sumário no topo: cards com TMB, GET, objetivo, peso, altura
- [ ] **Desktop (≥ 768px):** 3 colunas lado a lado, cada plano é um card completo
- [ ] **Mobile (< 768px):** Accordion vertical com abas "Tradicional | Funcional | Prático"
- [ ] Cada card de plano contém:
  - Nome do plano + badge do eixo
  - Descrição (2-4 frases)
  - Resumo de macros (3 cards: Proteína, Carboidrato, Gordura)
  - Refeições em tabela: Alimento | Qtde (g) | Prot | Carb | Gord | kcal
  - Totais do plano
- [ ] Ações por plano: "📄 Baixar PDF", "📋 Copiar" (clipboard)
- [ ] Ações globais: "🔄 Gerar Novamente", "➕ Novo Paciente"
- [ ] Disclaimer obrigatório no rodapé da tela (RN-070)
- [ ] Botão de feedback 👍/👎 abaixo de cada plano (visual na Fase 1, funcional na Fase 2)

---

## Arquivos Previstos

- `frontend/index.html` (atualizar seção de resultados)
- `frontend/css/style.css` (atualizar com estilos dos planos e responsividade)
- `frontend/js/app.js` (atualizar `renderResults`)

---

## Notas Técnicas

- O frontend existente já tem uma tela de resultados (`page-results`) com `renderResults()`. Adaptar para o novo schema
- A função `renderResults` atual espera `DietGenerateResponse` do schema antigo
- O PDF é único (consolidado com os 3 planos), não um por plano
