# SPEC-011: Tratamento de Erros e Resiliência da LLM

**Status:** ✅ Concluído
**Fase:** 1 — MVP

---

## User Story

Como usuário, quero receber mensagens de erro claras e em português quando algo der errado, para saber o que fazer sem frustração.

---

## Critérios de Aceite

- [ ] Toda resposta de erro do backend é em português, sem jargão técnico (RNF-034)
- [ ] Frontend trata cada HTTP status com mensagem e ação sugerida:

| HTTP | Comportamento |
|:----:|---------------|
| 400 | Exibe mensagem abaixo da caixa de texto. Texto preservado para edição |
| 422 | Exibe mensagem de validação. Campos problemáticos destacados |
| 429 | Exibe "Muitas requisições. Aguarde X segundos." com contagem regressiva |
| 500 | Exibe "Erro interno. Nossa equipe foi notificada. Tente novamente." |
| 502 | Exibe "Não foi possível gerar planos válidos. Tente descrever sua rotina com outras palavras." |
| 503 | Exibe "Nossa IA está temporariamente indisponível. Tente novamente em alguns minutos." |
| 504 | Exibe "Tempo limite excedido. Tente um texto mais curto ou tente novamente." |
| Rede offline | Exibe "Sem conexão com a internet. Verifique sua rede." |

- [ ] Timeout no frontend: 95 segundos (5s a mais que o timeout do backend)
- [ ] Botão "Tentar Novamente" em toda mensagem de erro 5xx
- [ ] Se 3 erros consecutivos → sugestão proativa: "Estamos enfrentando instabilidade. Tente novamente mais tarde."

---

## Arquivos Previstos

- `app/routers/diet.py` (atualizar tratamento de exceções)
- `frontend/js/app.js` (atualizar `apiRequest` error handling)

---

## Notas Técnicas

- O `apiRequest` já foi atualizado com verificação de Content-Type (LL-005). Manter
- Exceções do backend devem ser logadas com stack trace completo, mas a resposta ao usuário NUNCA inclui stack trace
- Usar `request_id` (UUID gerado no middleware) em todos os logs para correlação
