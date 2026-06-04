# SPEC-045: Rate Limiting Robusto e Proteção contra Abuso

**Status:** ⚪ Pendente
**Fase:** 2 — Refina a Experiência
**Pré-requisito:** MVP (Fase 1) concluído

---

## User Story

Como operador do sistema, quero proteger a API contra abuso e uso excessivo que poderia gerar custos elevados com a API DeepSeek.

---

## Critérios de Aceite

- [ ] Rate limiting com `slowapi` (ou middleware customizado):
  - Anônimos: 10 req/min, 50 req/hora
  - Autenticados: 30 req/min, 200 req/hora
- [ ] Headers HTTP informativos: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, `Retry-After`
- [ ] Bloqueio temporário: se exceder o limite 3x em 1 hora → bloqueio de 15 minutos
- [ ] Lista de IPs banidos manualmente (via `.env` ou banco)
- [ ] Log de rate limit excedido com IP e timestamp
- [ ] Custo máximo diário configurável: se o gasto estimado com DeepSeek exceder `MAX_DAILY_COST` → retornar 503 mesmo com API disponível

---

## Arquivos Previstos

- `app/middleware/rate_limit.py` (atualizar)
- `app/config.py` (atualizar com novas variáveis)

---

## Notas Técnicas

- O rate limiting usa dicionário em memória (como o cache de PDFs). Isso é suficiente para single-instance
- Se migrar para múltiplas instâncias no futuro, migrar para Redis
- O bloqueio de 15 minutos também é em memória — reset ao reiniciar o servidor
