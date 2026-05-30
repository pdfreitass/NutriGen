# SPEC-022: Chat Multi-Turno para Refinar Planos

**Status:** ⚪ Pendente
**Fase:** 3 — Escala e Personalização
**Pré-requisito:** Fase 2 concluída com > 70% de aprovação

---

## User Story

Como usuário, quero poder conversar com a IA para refinar os planos gerados, fazendo ajustes pontuais sem precisar regenerar tudo do zero.

---

## Critérios de Aceite

- [ ] Após a geração inicial, campo de texto aparece abaixo dos planos: _"Quer ajustar algo? Ex: 'Troca o frango do almoço por peixe', 'Aumenta a proteína do café da manhã', 'Não gostei do plano 2, refaz só ele'"_
- [ ] `POST /api/diet/{sessao_id}/refine` com body `{ "mensagem": "..." }`
- [ ] Mantém contexto da geração original (planos atuais + perfil + metas)
- [ ] Retorna planos atualizados (substitui os anteriores na tela)
- [ ] Histórico de refinamentos salvo como subtópicos da `SessaoGeracao`
- [ ] Limite de 5 turnos de refinamento por sessão

---

## Arquivos Previstos

- `app/routers/diet.py` (novo endpoint)
- `app/services/plan_refiner_service.py` (novo)
- `app/models/database/mensagem_refinamento.py` (novo modelo)
- `frontend/js/app.js` (chat UI)

---

## Notas Técnicas

- O contexto da conversa é mantido no backend (armazenado na sessão)
- Cada turno custa ~1/3 de uma geração completa (prompt menor, resposta menor)
- O limite de 5 turnos evita loops infinitos e custos excessivos
