# SPEC-013: Logs e Observabilidade Básica

**Status:** 🔴 Pendente
**Fase:** 1 — MVP

---

## User Story

Como desenvolvedor, quero logs estruturados de cada etapa do fluxo de geração, para conseguir debugar problemas em produção sem acessar o servidor diretamente.

---

## Critérios de Aceite

- [ ] Logs em JSON estruturado (RNF-043) com campos: `timestamp`, `level`, `module`, `request_id`, `message`, `metadata`
- [ ] `request_id` (UUID) gerado no middleware e propagado para todas as camadas
- [ ] Logs em cada etapa crítica:
  - Requisição recebida (input sanitizado, NÃO logar texto original se contiver dados de saúde — RN-023)
  - Extração NL→JSON (latência, tokens consumidos, sucesso/falha)
  - Cálculo nutricional (TMB, GET, objetivo)
  - Geração IA (latência, tokens consumidos, sucesso/falha)
  - Validação (correções aplicadas, sucesso/falha)
  - Persistência (sucesso/falha)
  - PDF (sucesso/falha)
  - Resposta enviada (latência total)
- [ ] Logs de erro com stack trace completo (mas sem dados sensíveis)
- [ ] Nível INFO para fluxo normal, WARNING para correções automáticas, ERROR para falhas
- [ ] Logs no console (stdout) na v1 — sem necessidade de sistema externo

---

## Arquivos Previstos

- `app/logging_config.py` (novo)
- `app/middleware/logging.py` (novo)
- `app/main.py` (atualizar para incluir middleware de logging)

---

## Notas Técnicas

- Usar `logging` padrão do Python com `JSONFormatter`
- O `request_id` pode ser propagado via `contextvars` (thread-safe, não precisa passar como parâmetro)
- Mascarar dados sensíveis nos logs: `DEEPSEEK_API_KEY`, `JWT_SECRET_KEY`, senhas, dados de saúde
