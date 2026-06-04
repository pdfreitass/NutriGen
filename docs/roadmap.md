# 🗺️ Roadmap — NutriGen

> **Propósito:** Fonte oficial de acompanhamento do projeto. Toda feature nova, correção significativa ou melhoria estrutural passa por este documento antes de ser implementada.
>
> **Atualizado em:** 2026-06-04
>
> **Regra de ouro:** Uma SPEC só é marcada como `[x] Concluído` após validação explícita do desenvolvedor. A IA pode sugerir a marcação, mas nunca a executa unilateralmente.

---

## 📊 Resumo do Projeto

| Métrica | Valor |
|---------|:----:|
| Total de SPECs | **26** |
| Concluídas | **13** |
| Parciais | **0** |
| Em andamento | **0** |
| Pendentes | **13** |
| Progresso Geral | **50%** |
| Qualidade Média (concluídas) | **⭐⭐⭐⭐** (3.8/5) |

```
Progresso:  [█████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░] 50%
Qualidade:  [████████████████████████████████████████████████████] 3.8/5
```

---

## ⭐ Legenda de Qualidade

| Estrelas | Nome | Significado |
|:--------:|------|-------------|
| ⭐⭐⭐⭐⭐ | **Excelente** | Produção. Cobre todos os edge cases, testado, documentado, sem débito técnico. |
| ⭐⭐⭐⭐ | **Bom** | Funcional e robusto. Cobre os cenários principais. Pequenas melhorias possíveis. |
| ⭐⭐⭐ | **Mediano** | Funciona no happy path. Falta cobertura de erros, edge cases ou polimento. |
| ⭐⭐ | **Fraco** | Funcionalidade básica presente mas com bugs conhecidos ou incompleta. |
| ⭐ | **Crítico** | Mal implementado. Precisa ser refeito. Não usar em produção. |
| ⬜ | **Pendente** | Ainda não implementado. |

---

## 🎯 Fase 1 — ✅ MVP CONCLUÍDO! (13/13 = 100%)

**Objetivo:** Versão mínima que um usuário real pode usar para descrever sua rotina, receber 3 planos e baixar o PDF.

### Família 010 — Infraestrutura & Configuração

| ID | SPEC | Status | Qualidade |
|----|------|--------|:---------:|
| [SPEC-010](SPEC-010-configuracao-deepseek.md) | **Principal:** Configuração do Cliente DeepSeek | ✅ | ⭐⭐⭐⭐ |
|   ↳ [SPEC-011](SPEC-011-configuracao-ambiente.md) | Subspec: Configuração de Ambiente e Segurança | ✅ | ⭐⭐⭐⭐ |
|   ↳ [SPEC-012](SPEC-012-catalogo-alimentos.md) | Subspec: Catálogo de Alimentos (FoodCatalog) | ✅ | ⭐⭐⭐⭐⭐ |
|   ↳ [SPEC-013](SPEC-013-logs-observabilidade.md) | Subspec: Logs e Observabilidade Básica | ✅ | ⭐⭐⭐ |

### Família 020 — Pipeline de Processamento

| ID | SPEC | Status | Qualidade |
|----|------|--------|:---------:|
| [SPEC-020](SPEC-020-extracao-nl-json.md) | **Principal:** Serviço de Extração NL→JSON | ✅ | ⭐⭐⭐⭐ |
|   ↳ [SPEC-021](SPEC-021-expansao-restricoes.md) | Subspec: Expansão de Restrições e Condições Especiais | ✅ | ⭐⭐⭐⭐ |
|   ↳ [SPEC-022](SPEC-022-geracao-planos-ia.md) | Subspec: Serviço de Geração de Planos via IA | ✅ | ⭐⭐⭐⭐ |
|   ↳ [SPEC-023](SPEC-023-pipeline-validacao.md) | Subspec: Pipeline de Validação Pós-Geração | ✅ | ⭐⭐⭐⭐⭐ |
|   ↳ [SPEC-024](SPEC-024-orquestrador.md) | Subspec: Orquestrador (UseCase) | ✅ | ⭐⭐⭐⭐ |
|   ↳ [SPEC-025](SPEC-025-endpoint-geracao.md) | Subspec: Endpoint de Geração | ✅ | ⭐⭐⭐⭐ |
|   ↳ [SPEC-026](SPEC-026-tratamento-erros.md) | Subspec: Tratamento de Erros e Resiliência | ✅ | ⭐⭐⭐ |

### Família 030 — Frontend

| ID | SPEC | Status | Qualidade |
|----|------|--------|:---------:|
| [SPEC-030](SPEC-030-frontend-input.md) | **Principal:** Frontend — Página de Input | ✅ | ⭐⭐⭐ |
|   ↳ [SPEC-031](SPEC-031-frontend-resultados.md) | Subspec: Frontend — Tela de Resultados | ✅ | ⭐⭐⭐ |

---

## 🔧 Fase 2 — Refina a Experiência

**Pré-requisito:** MVP (Fase 1) concluído e em uso por pelo menos 10 usuários beta.

### Família 040 — Experiência do Usuário

| ID | SPEC | Status | Qualidade |
|----|------|--------|:---------:|
| [SPEC-040](SPEC-040-historico-geracoes.md) | **Principal:** Histórico de Gerações (autenticados) | ⚪ Pendente | ⬜⬜⬜⬜⬜ |
|   ↳ [SPEC-041](SPEC-041-feedback-planos.md) | Subspec: Sistema de Feedback de Planos (👍/👎) | ⚪ Pendente | ⬜⬜⬜⬜⬜ |
|   ↳ [SPEC-042](SPEC-042-regeneracao-inteligente.md) | Subspec: Regeneração Inteligente de Planos | ⚪ Pendente | ⬜⬜⬜⬜⬜ |
|   ↳ [SPEC-043](SPEC-043-metricas-analytics.md) | Subspec: Métricas e Analytics Básicos | ⚪ Pendente | ⬜⬜⬜⬜⬜ |
|   ↳ [SPEC-044](SPEC-044-ajuste-prompts.md) | Subspec: Ajuste de Prompts com Base em Feedback | ⚪ Pendente | ⬜⬜⬜⬜⬜ |
|   ↳ [SPEC-045](SPEC-045-rate-limiting.md) | Subspec: Rate Limiting Robusto e Proteção contra Abuso | ⚪ Pendente | ⬜⬜⬜⬜⬜ |

---

### Família 060 — Seleção de Alimentos

| ID | SPEC | Status | Qualidade |
|----|------|--------|:---------:|
| [SPEC-060](SPEC-060-selecao-alimentos.md) | **Principal:** Seleção de Alimentos + Geração Determinística | ⚪ Pendente | ⬜⬜⬜⬜⬜ |

---

## 🚀 Fase 3 — Escala e Personalização

**Pré-requisito:** Fase 2 concluída com feedback positivo (> 70% de aprovação).

### Família 050 — Escala & Monetização

| ID | SPEC | Status | Qualidade |
|----|------|--------|:---------:|
| [SPEC-050](SPEC-050-dashboard-admin.md) | **Principal:** Dashboard Administrativo | ⚪ Pendente | ⬜⬜⬜⬜⬜ |
|   ↳ [SPEC-051](SPEC-051-multiplos-provedores.md) | Subspec: Múltiplos Provedores de IA | ⚪ Pendente | ⬜⬜⬜⬜⬜ |
|   ↳ [SPEC-052](SPEC-052-chat-multi-turno.md) | Subspec: Chat Multi-Turno para Refinar Planos | ⚪ Pendente | ⬜⬜⬜⬜⬜ |
|   ↳ [SPEC-053](SPEC-053-exportacao-avancada.md) | Subspec: Exportação Avançada (PDF + CSV) | ⚪ Pendente | ⬜⬜⬜⬜⬜ |
|   ↳ [SPEC-054](SPEC-054-perfis-usuario.md) | Subspec: Perfis de Usuário e Preferências Salvas | ⚪ Pendente | ⬜⬜⬜⬜⬜ |
|   ↳ [SPEC-055](SPEC-055-assinatura-monetizacao.md) | Subspec: Sistema de Assinatura e Monetização | ⚪ Pendente | ⬜⬜⬜⬜⬜ |

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
2. **SPEC concluída:** marcar `[x] Concluído`, atribuir nota de qualidade (⭐1-5), listar arquivos alterados.
3. **Qualidade reavaliada:** se uma SPEC for melhorada, atualizar as estrelas e registrar a data da reavaliação.
4. **SPEC bloqueada:** adicionar `⚠️ Bloqueada por:` com referência.
5. **Nova SPEC Principal:** ID múltiplo de 10 (ex: `060`). Adicionar como nova família na fase correta.
6. **Nova Subspec:** ID sequencial dentro da dezena (ex: `032` para família `030`). Adicionar com `↳` abaixo da Principal.

**A IA NUNCA marca uma SPEC como concluída ou altera a qualidade sem confirmação explícita do desenvolvedor.**

---

> **Para a IA na próxima sessão:** Este roadmap é o plano de voo. Antes de implementar qualquer coisa, verifique se já existe uma SPEC para aquela funcionalidade. Se não existir, proponha a criação da SPEC primeiro. Não implemente fora do roadmap sem discutir.
