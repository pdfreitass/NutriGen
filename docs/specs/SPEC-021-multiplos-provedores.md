# SPEC-021: Múltiplos Provedores de IA

**Status:** ⚪ Pendente
**Fase:** 3 — Escala e Personalização
**Pré-requisito:** Fase 2 concluída com > 70% de aprovação

---

## User Story

Como operador do sistema, quero poder alternar entre diferentes provedores de IA (DeepSeek, OpenAI, Claude) para comparar qualidade e custo, e ter fallback se o provedor principal falhar.

---

## Critérios de Aceite

- [ ] Interface `LLMProvider` (Protocol/ABC) com método `chat_completion(messages, **kwargs)`
- [ ] Implementações concretas: `DeepSeekProvider`, `OpenAIProvider`, `ClaudeProvider`
- [ ] Configuração por `.env`:
  - `LLM_PROVIDER=deepseek` (padrão)
  - `LLM_FALLBACK_PROVIDER=openai` (opcional)
- [ ] Fallback automático: se provider principal falhar 3x consecutivas, alterna para fallback
- [ ] Métricas por provider: latência média, custo por requisição, taxa de erro
- [ ] Provider pode ser trocado sem reiniciar o servidor (recarregar config)

---

## Arquivos Previstos

- `app/infrastructure/llm_provider.py` (interface)
- `app/infrastructure/deepseek_provider.py` (refatorar DeepSeekClient)
- `app/infrastructure/openai_provider.py` (novo)
- `app/infrastructure/claude_provider.py` (novo)

---

## Notas Técnicas

- A interface `LLMProvider` abstrai completamente o provedor
- OpenAI e DeepSeek têm APIs compatíveis. Claude requer adaptação (Anthropic SDK ou API Messages)
- Os serviços (ExtractorService, PlanGeneratorService) não sabem qual provedor está sendo usado
