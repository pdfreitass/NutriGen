# SPEC-012: Configuração de Ambiente e Segurança

**Status:** ✅ Concluído
**Fase:** 1 — MVP

---

## User Story

Como desenvolvedor, quero que todas as configurações sensíveis estejam em variáveis de ambiente e que o sistema falhe rápido se algo essencial estiver ausente.

---

## Critérios de Aceite

- [ ] `.env.example` criado com todas as variáveis necessárias (sem valores reais)
- [ ] `python-dotenv` carrega `.env` na inicialização
- [ ] Validação de variáveis obrigatórias na inicialização:
  - `DEEPSEEK_API_KEY` → RuntimeError se ausente
  - `JWT_SECRET_KEY` → RuntimeError se ausente
  - `DATABASE_URL` → usa default para SQL Server local se ausente
- [ ] `.env` adicionado ao `.gitignore`
- [ ] Headers de segurança no FastAPI: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`
- [ ] CORS restrito a `localhost:8000` e `127.0.0.1:8000` (não `*`)
- [ ] Rate limiting configurável via `.env`: `RATE_LIMIT_ANON=10`, `RATE_LIMIT_AUTH=30`

---

## Arquivos Previstos

- `.env.example`
- `.gitignore` (atualizar)
- `app/main.py` (atualizar CORS, headers, rate limit middleware)
- `app/config.py` (novo — centraliza leitura de config)

---

## Notas Técnicas

- O `.env.example` DEVE listar TODAS as variáveis usadas pelo sistema com comentários explicando cada uma
- NUNCA versionar `.env` real no Git
- O arquivo `app/config.py` centraliza `os.getenv()` para evitar chamadas espalhadas e facilitar testes
