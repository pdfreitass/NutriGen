# SPEC-004: Serviço de Geração de Planos via IA

**Status:** ✅ Concluído
**Fase:** 1 — MVP

---

## User Story

Como sistema, quero enviar os dados estruturados do usuário + metas nutricionais para a IA e receber 3 planos alimentares completos em JSON, para que o usuário visualize opções variadas.

---

## Critérios de Aceite

- [ ] `PlanGeneratorService` implementado em `app/services/plan_generator_service.py`
- [ ] Método `gerar(perfil: PerfilExtraido, metas: MetasNutricionais) → PlanosGerados`
- [ ] Usa `DeepSeekClient` com system prompt de geração (inglês) + dados do usuário (português)
- [ ] System prompt inclui: 3 eixos fixos, restrições expandidas (ANTES das preferências), catálogo de alimentos relevantes, metas de macros ±10%
- [ ] `MetasNutricionais` como dataclass: tmb, get_calorico, proteina_g, carboidrato_g, gordura_g
- [ ] `PlanosGerados` como Pydantic model contendo `list[PlanoGerado]` com exatamente 3 elementos
- [ ] `PlanoGerado` contém: nome, eixo, descricao, refeicoes (lista de `RefeicaoGerada`), cada uma com alimentos (`ItemGerado`)
- [ ] Timeout: 90 segundos. Retry: 2 tentativas com backoff (2s, 4s)
- [ ] Temperatura: 0.7
- [ ] `response_format: { "type": "json_object" }` (LL-001)
- [ ] Loga latência e tokens consumidos

---

## Arquivos Previstos

- `app/services/plan_generator_service.py`
- `app/models/schemas.py` (atualizar com `PlanosGerados`, `PlanoGerado`, `RefeicaoGerada`, `ItemGerado`)

---

## Notas Técnicas

- O system prompt DEVE incluir a frase "TOLERÂNCIA ZERO para alimentos da lista de restrições" (LL-002)
- A lista de restrições deve vir ANTES das preferências no prompt (LL-003 — ordem importa)
- O catálogo enviado no prompt deve ser limitado a ~3000 tokens. Se o catálogo completo exceder, selecionar apenas categorias relevantes (ex: vegano → pular "Carnes e Peixes" e "Laticínios")
- O contrato completo do JSON de resposta está na seção 6 do `arquitetura.md`
