# SPEC-042: Regeneração Inteligente de Planos

**Status:** ⚪ Pendente
**Fase:** 2 — Refina a Experiência
**Pré-requisito:** MVP (Fase 1) concluído

---

## User Story

Como usuário, quero gerar novos planos quando não gostar dos atuais, com garantia de que serão diferentes da geração anterior.

---

## Critérios de Aceite

- [ ] Botão "🔄 Gerar Novamente" envia o MESMO texto original
- [ ] Backend recebe parâmetro opcional `{ "texto": "...", "evitar_ids": ["uuid1", "uuid2"] }` com alimentos a evitar
- [ ] System prompt da regeneração inclui: "EVITE estes alimentos que já apareceram em gerações anteriores: [lista]"
- [ ] Se `evitar_ids` for enviado, temperatura sobe para 0.85 (mais variação)
- [ ] Frontend detecta se usuário gerou 3x em < 2 minutos e exibe sugestão: _"Que tal ajustar sua descrição para obter resultados mais diferentes?"_
- [ ] Planos anteriores permanecem acessíveis (não sobrescrever)

---

## Arquivos Previstos

- `app/routers/diet.py` (atualizar endpoint)
- `app/services/plan_generator_service.py` (atualizar prompt)
- `frontend/js/app.js` (contador de regenerações)

---

## Notas Técnicas

- Na v1 (MVP), a regeneração é idêntica a uma nova chamada (sem `evitar_ids`). A SPEC-042 implementa a versão inteligente
- A lista de alimentos a evitar é montada pelo frontend a partir dos planos atuais e enviada como parâmetro opcional
