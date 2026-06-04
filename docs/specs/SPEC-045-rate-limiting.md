# SPEC-045: Rate Limiting Robusto e Proteção contra Abuso

**Status:** ⚪ Pendente
**Fase:** 2
**Tipo:** Subspec
**Subspec de:** SPEC-040
**Depende de:** SPEC-025 (Endpoint)
**Data de criação:** 2026-05-30

---

## 1. User Story

Como operador, quero proteger a API contra abuso que geraria custos elevados com DeepSeek e degradaria o serviço para usuários legítimos.

---

## 2. Critérios de Aceite

- [ ] Rate limiting hierárquico:
  - Anônimos: 10 req/min, 50 req/hora
  - Autenticados: 30 req/min, 200 req/hora
- [ ] Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, `Retry-After`
- [ ] Bloqueio progressivo: 3x limite excedido em 1h → bloqueio 15 min
- [ ] Custo máximo diário: se `MAX_DAILY_COST_BRL` excedido → 503 com "Limite diário atingido"
- [ ] Lista de IPs banidos via `.env`: `BANNED_IPS=192.168.1.1,10.0.0.2`
- [ ] Log de toda violação de rate limit com IP, endpoint, timestamp

---

## 3. Contratos

```
.env:
  RATE_LIMIT_ANON=10
  RATE_LIMIT_AUTH=30
  RATE_LIMIT_HOUR_ANON=50
  RATE_LIMIT_HOUR_AUTH=200
  MAX_DAILY_COST_BRL=50.00
  BANNED_IPS=
```

---

## 4. Fluxo

```
Passo 1 — Atualizar RateLimitStore: adicionar janela horária + contador de violações
Passo 2 — Atualizar middleware: headers X-RateLimit-*, bloqueio progressivo, IPs banidos
Passo 3 — CostTracker: singleton que acumula custo diário estimado (tokens × preço)
Passo 4 — DeepSeekClient: após cada chamada, registrar tokens em CostTracker
Passo 5 — Middleware verifica CostTracker antes de permitir chamada à IA
```

---

## 5. Arquivos Previstos

| Arquivo | Tipo |
|---------|:----:|
| `app/middleware/limite_taxa.py` | Modificado |
| `app/infrastructure/cost_tracker.py` | Novo |
| `app/configuracao.py` | Modificado (+variáveis) |
