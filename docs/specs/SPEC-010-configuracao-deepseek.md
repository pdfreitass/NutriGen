# SPEC-010: Configuração do Cliente DeepSeek

**Status:** ✅ Concluído
**Fase:** 1 — MVP
**Data de conclusão:** 2026-05-30

---

## User Story

Como desenvolvedor, quero um cliente HTTP tipado para a API DeepSeek, para que os serviços de extração e geração possam chamar a IA sem repetir código de conexão.

---

## Critérios de Aceite

- [x] `DeepSeekClient` implementado em `app/infrastructure/deepseek_client.py`
- [x] Suporta `chat_completion(messages, temperature, response_format, timeout)` como método principal
- [x] Lê `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL` do `.env`
- [x] Timeout configurável por chamada (default extração: 15s, default geração: 90s)
- [x] Retry com backoff exponencial: 2 tentativas, intervalo 2s e 4s
- [x] Lança `DeepSeekUnavailableError` se API offline após retries
- [x] Lança `DeepSeekInvalidResponseError` se JSON de resposta inválido
- [x] Loga latência de cada chamada (método `_log_success`)
- [x] Erro na inicialização se `DEEPSEEK_API_KEY` não configurada (RuntimeError)

---

## Arquivos Implementados

| Arquivo | Descrição |
|---------|-----------|
| `app/infrastructure/deepseek_client.py` | Classe `DeepSeekClient` stateless com retry, backoff, logs |
| `app/infrastructure/__init__.py` | Exporta `DeepSeekClient` |
| `app/config.py` | Leitura centralizada de `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`, timeouts |
| `app/exceptions.py` | `DeepSeekError`, `DeepSeekUnavailableError`, `DeepSeekInvalidResponseError`, `DeepSeekTimeoutError` |
| `.env.example` | Template com todas as variáveis DeepSeek |

---

## Notas Técnicas

- Usa `httpx.Client` (síncrono, compatível com o resto do stack)
- A API DeepSeek é OpenAI-compatible: endpoint `{base_url}/chat/completions`
- Header: `Authorization: Bearer {DEEPSEEK_API_KEY}`
- Payload: `{ "model": "...", "messages": [...], "temperature": 0.7, "response_format": {"type": "json_object"} }`
- `response_format` é opcional — obrigatório para geração, opcional para extração
- A classe é stateless — pode ser instanciada uma vez e reusada
- Métodos de conveniência: `extract_content(response)` e `extract_json(response)`
