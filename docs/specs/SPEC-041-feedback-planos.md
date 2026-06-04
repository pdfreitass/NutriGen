# SPEC-041: Sistema de Feedback de Planos

**Status:** ⚪ Pendente
**Fase:** 2 — Refina a Experiência
**Pré-requisito:** MVP (Fase 1) concluído

---

## User Story

Como product owner, quero coletar feedback dos usuários sobre a qualidade dos planos gerados, para melhorar o sistema com dados reais.

---

## Critérios de Aceite

- [ ] Botões 👍/👎 abaixo de cada plano na tela de resultados
- [ ] Clique em 👎 abre mini-formulário com opções:
  - "Alimentos repetidos entre planos"
  - "Quantidades irreais (muito ou pouco)"
  - "Não gostei das combinações"
  - "Alimentos que não como apareceram"
  - "Outro" (campo de texto livre opcional)
- [ ] `POST /api/diet/{sessao_id}/feedback` com body `{ "plano_id": X, "positivo": false, "motivo": "...", "comentario": "..." }`
- [ ] Feedback salvo em tabela `feedback_planos` com FK para `PlanoAlimentar`
- [ ] Métricas agregadas no admin: % de feedback positivo por eixo, motivos mais comuns de feedback negativo
- [ ] Log separado para feedbacks negativos (RF-072)

---

## Arquivos Previstos

- `app/routers/diet.py` (novo endpoint)
- `app/models/database/feedback.py` (novo modelo ORM)
- `alembic/versions/` (nova migração para tabela feedback_planos)
- `frontend/js/app.js` (lógica de feedback)

---

## Notas Técnicas

- Feedback é anônimo — não requer autenticação
- Um mesmo usuário pode dar feedback múltiplas vezes (cada clique é um registro novo)
- Os dados de feedback serão usados na Fase 2 para ajustar prompts e na Fase 3 para fine-tuning
