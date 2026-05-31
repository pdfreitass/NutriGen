# 🗺️ Roadmap — NutriGen

> **Propósito:** Fonte oficial de acompanhamento do projeto. Toda feature nova, correção significativa ou melhoria estrutural passa por este documento antes de ser implementada.
>
> **Atualizado em:** 2026-05-30
>
> **Regra de ouro:** Uma SPEC só é marcada como `[x] Concluído` após validação explícita do desenvolvedor. A IA pode sugerir a marcação, mas nunca a executa unilateralmente.

---

## 📊 Resumo do Projeto

| Métrica | Valor |
|---------|:----:|
| Total de SPECs | **25** |
| Concluídas | **12** |
| Parciais | **0** |
| Em andamento | **0** |
| Pendentes | **13** |
| Progresso Geral | **92%** |

```
Progresso: [██████████████████████████████████████████████░░] 92%
```

---

## 🎯 Fase 1 — MVP: Funciona e Entrega Valor

**Objetivo:** Versão mínima que um usuário real pode usar para descrever sua rotina, receber 3 planos e baixar o PDF.

| ID | SPEC | Status |
|----|------|--------|
| [SPEC-001](SPEC-001-configuracao-deepseek.md) | Configuração do Cliente DeepSeek | ✅ Concluído |
| [SPEC-002](SPEC-002-catalogo-alimentos.md) | Catálogo de Alimentos (FoodCatalog) | ✅ Concluído |
| [SPEC-003](SPEC-003-extracao-nl-json.md) | Serviço de Extração NL→JSON | ✅ Concluído |
| [SPEC-004](SPEC-004-geracao-planos-ia.md) | Serviço de Geração de Planos via IA | ✅ Concluído |
| [SPEC-005](SPEC-005-pipeline-validacao.md) | Pipeline de Validação Pós-Geração | ✅ Concluído |
| [SPEC-006](SPEC-006-orquestrador.md) | Atualização do Orquestrador (DietPlannerUseCase) | ✅ Concluído |
| [SPEC-007](SPEC-007-endpoint-geracao.md) | Atualização do Endpoint de Geração | ✅ Concluído |
| [SPEC-008](SPEC-008-expansao-restricoes.md) | Expansão de Restrições e Condições Especiais | ✅ Concluído |
| [SPEC-009](SPEC-009-frontend-input.md) | Frontend — Página de Input com Linguagem Natural | ✅ Concluído |
| [SPEC-010](SPEC-010-frontend-resultados.md) | Frontend — Tela de Resultados com 3 Planos | ✅ Concluído |
| [SPEC-011](SPEC-011-tratamento-erros.md) | Tratamento de Erros e Resiliência da LLM | ✅ Concluído |
| [SPEC-012](SPEC-012-configuracao-ambiente.md) | Configuração de Ambiente e Segurança | ✅ Concluído |
| [SPEC-013](SPEC-013-logs-observabilidade.md) | Logs e Observabilidade Básica | 🟡 Parcial |

---

## 🔧 Fase 2 — Refina a Experiência

**Pré-requisito:** MVP (Fase 1) concluído e em uso por pelo menos 10 usuários beta.

| ID | SPEC | Status |
|----|------|--------|
| [SPEC-014](SPEC-014-historico-geracoes.md) | Histórico de Gerações para Usuários Autenticados | ⚪ Pendente |
| [SPEC-015](SPEC-015-feedback-planos.md) | Sistema de Feedback de Planos | ⚪ Pendente |
| [SPEC-016](SPEC-016-regeneracao-inteligente.md) | Regeneração Inteligente de Planos | ⚪ Pendente |
| [SPEC-017](SPEC-017-metricas-analytics.md) | Métricas e Analytics Básicos | ⚪ Pendente |
| [SPEC-018](SPEC-018-ajuste-prompts.md) | Ajuste de Prompts com Base em Feedback | ⚪ Pendente |
| [SPEC-019](SPEC-019-rate-limiting.md) | Rate Limiting Robusto e Proteção contra Abuso | ⚪ Pendente |

---

## 🚀 Fase 3 — Escala e Personalização

**Pré-requisito:** Fase 2 concluída com feedback positivo (> 70% de aprovação).

| ID | SPEC | Status |
|----|------|--------|
| [SPEC-020](SPEC-020-dashboard-admin.md) | Dashboard Administrativo | ⚪ Pendente |
| [SPEC-021](SPEC-021-multiplos-provedores.md) | Múltiplos Provedores de IA | ⚪ Pendente |
| [SPEC-022](SPEC-022-chat-multi-turno.md) | Chat Multi-Turno para Refinar Planos | ⚪ Pendente |
| [SPEC-023](SPEC-023-exportacao-avancada.md) | Exportação Avançada (PDF Melhorado + CSV) | ⚪ Pendente |
| [SPEC-024](SPEC-024-perfis-usuario.md) | Perfis de Usuário e Preferências Salvas | ⚪ Pendente |
| [SPEC-025](SPEC-025-assinatura-monetizacao.md) | Sistema de Assinatura e Monetização | ⚪ Pendente |

---

## 💡 Backlog de Ideias

| # | Ideia | Complexidade | Impacto |
|:-:|-------|:-----------:|:-------:|
| 1 | Aplicativo mobile nativo (iOS/Android) com notificações push | Alta | Alto |
| 2 | Integração com smartwatch (Apple Health / Google Fit) | Alta | Médio |
| 3 | Lista de compras automática da semana | Baixa | Alto |
| 4 | Comparação entre planos lado a lado com destaques visuais | Média | Médio |
| 5 | Recomendações semanais por e-mail | Média | Alto |
| 6 | Modo nutricionista — múltiplos pacientes | Alta | Alto |
| 7 | Fine-tuning do modelo com dados anonimizados | Alta | Médio |
| 8 | Integração com iFood/Mercado — "Comprar ingredientes" | Alta | Baixo |
| 9 | Suporte a dietas médicas (renal, cetogênica, pós-bariátrica) | Alta | Médio |
| 10 | Comunidade — compartilhar e votar em planos | Alta | Médio |

---

## 📋 Regra de Atualização

1. **SPEC iniciada:** marcar `[~] Em andamento`, atualizar data de início.
2. **SPEC concluída:** marcar `[x] Concluído`, registrar data, listar arquivos alterados.
3. **SPEC bloqueada:** adicionar `⚠️ Bloqueada por:` com referência.
4. **Ideia vira SPEC:** mover para fase apropriada com ID sequencial.

**A IA NUNCA marca uma SPEC como concluída sem confirmação explícita do desenvolvedor.**

---

> **Para a IA na próxima sessão:** Este roadmap é o plano de voo. Antes de implementar qualquer coisa, verifique se já existe uma SPEC para aquela funcionalidade. Se não existir, proponha a criação da SPEC primeiro. Não implemente fora do roadmap sem discutir.
