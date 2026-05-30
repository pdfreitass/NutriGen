# SPEC-025: Sistema de Assinatura e Monetização

**Status:** ⚪ Pendente
**Fase:** 3 — Escala e Personalização
**Pré-requisito:** Fase 2 concluída com > 70% de aprovação

---

## User Story

Como product owner, quero monetizar o sistema com um modelo freemium, para cobrir custos de infraestrutura e API DeepSeek.

---

## Critérios de Aceite

- [ ] Plano Gratuito: 5 gerações por mês, sem histórico, sem exportação CSV
- [ ] Plano Premium (R$ 19,90/mês): gerações ilimitadas, histórico completo, exportação CSV, múltiplos perfis
- [ ] Plano Profissional (R$ 49,90/mês): tudo do Premium + chat multi-turno, exportação avançada
- [ ] Integração com Stripe ou Mercado Pago para pagamentos
- [ ] Contador de gerações por usuário (reset mensal)
- [ ] Bloqueio automático ao atingir limite do plano gratuito
- [ ] Página de upgrade com comparação de planos

---

## Arquivos Previstos

- `app/models/database/assinatura.py` (novo)
- `app/services/payment_service.py` (novo)
- `app/routers/payment.py` (novo)
- `app/middleware/quota.py` (novo)
- `alembic/versions/` (várias migrações)
- `frontend/planos.html` (página de planos e preços)

---

## Notas Técnicas

- A monetização é a última SPEC da Fase 3 — o sistema já deve ter uma base de usuários validada
- Começar com um gateway de pagamento brasileiro (Mercado Pago) para simplicidade fiscal
- Webhook do gateway notifica o sistema sobre pagamentos confirmados/cancelados
