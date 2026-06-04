# SPEC-025: Atualização do Endpoint de Geração

**Status:** ✅ Concluído
**Fase:** 1 — MVP

---

## User Story

Como frontend, quero um endpoint `POST /api/diet/generate` que aceite texto livre (não um JSON estruturado), para que o usuário possa descrever sua rotina em linguagem natural.

---

## Critérios de Aceite

- [ ] `POST /api/diet/generate` aceita `{ "texto": "string" }` como body
- [ ] Validações de entrada:
  - `texto` obrigatório (422 se ausente)
  - `texto` entre 20 e 2000 caracteres (400 se fora)
  - Sanitização: remove tags HTML, caracteres de controle (exceto \n, \r, \t)
- [ ] Rate limiting: 10 req/min para IPs anônimos, 30 req/min para autenticados
- [ ] Chama `DietPlannerUseCase.executar(texto)`
- [ ] Retorna `DietGenerateResponse` com paciente, TMB, 3 planos, pdf_url
- [ ] Tratamento de erros mapeado para HTTP:

| Exceção | HTTP | Mensagem |
|---------|:----:|----------|
| `CamposObrigatoriosAusentesException` | 400 | "Não consegui identificar [campos]. Tente: 'tenho Xkg, Ycm, Z anos, [sexo]'." |
| `ValorFisiologicoInvalidoException` | 400 | "O valor para [campo] está fora do esperado." |
| `GETForaDoIntervaloSeguroException` | 400 | "GET calculado: X kcal. O mínimo seguro é 1200 kcal." |
| `DeepSeekUnavailableException` | 503 | "Nossa IA está temporariamente indisponível." |
| `DeepSeekInvalidResponseException` | 502 | "Não foi possível gerar os planos. Nossa equipe foi notificada." |
| `PlanValidationException` | 502 | "Não foi possível gerar planos válidos." |
| `TimeoutException` | 504 | "Tempo limite excedido. Tente um texto mais curto." |
| `RateLimitException` | 429 | "Muitas requisições. Aguarde 60 segundos." |
| Qualquer outra | 500 | "Erro interno. Nossa equipe foi notificada." |

- [ ] Content-Type: `application/json`

---

## Arquivos Previstos

- `app/routers/diet.py` (atualizar)
- `app/middleware/rate_limit.py` (novo)

---

## Notas Técnicas

- O router existente aceitava `DietGenerateRequest` (JSON estruturado). Esse schema antigo **não é mais usado** — o endpoint agora recebe `{ "texto": "..." }`
- O endpoint de download de PDF (`GET /api/diet/{pdf_id}/pdf`) permanece igual
- O rate limiting pode ser implementado com `slowapi` ou middleware manual simples
