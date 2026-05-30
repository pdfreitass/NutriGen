# SPEC-014: Histórico de Gerações para Usuários Autenticados

**Status:** ⚪ Pendente
**Fase:** 2 — Refina a Experiência
**Pré-requisito:** MVP (Fase 1) concluído

---

## User Story

Como usuário autenticado, quero acessar o histórico de todos os planos que já gerei, para revisitar planos anteriores sem precisar salvar os PDFs.

---

## Critérios de Aceite

- [ ] `GET /api/diet/history` retorna lista de `SessaoGeracao` do usuário autenticado
- [ ] Cada item contém: data, objetivo, GET, link para PDF (se dentro de 7 dias)
- [ ] Paginação: 10 resultados por página
- [ ] Ordenação: mais recente primeiro
- [ ] Frontend: página "Meus Planos" acessível pelo header (apenas logado)
- [ ] Cada item do histórico é clicável → expande para mostrar resumo dos 3 planos
- [ ] Botão "Excluir" em cada item (soft delete ou hard delete com confirmação)
- [ ] `DELETE /api/diet/{sessao_id}` remove a sessão e os planos associados

---

## Arquivos Previstos

- `app/routers/diet.py` (atualizar com novo endpoint)
- `app/repositories/sessao_geracao_repository.py` (novo)
- `frontend/index.html` (nova página "Meus Planos")
- `frontend/js/app.js` (lógica de histórico)

---

## Notas Técnicas

- Usuários anônimos NÃO têm acesso ao histórico
- Planos com `usuario_id = NULL` não aparecem em nenhum histórico
- A expiração de PDF (7 dias) e planos (30 dias) continua valendo — itens expirados não aparecem no histórico
