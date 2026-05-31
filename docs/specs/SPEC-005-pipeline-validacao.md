# SPEC-005: Pipeline de Validação Pós-Geração (PlanValidator)

**Status:** ✅ Concluído
**Fase:** 1 — MVP

---

## User Story

Como sistema, quero validar e corrigir automaticamente os planos gerados pela IA antes de mostrá-los ao usuário, para garantir que estejam nutricionalmente corretos, não contenham alimentos proibidos, e sejam realmente diferentes entre si.

---

## Critérios de Aceite

- [ ] `PlanValidator` implementado em `app/services/plan_validator.py`
- [ ] Método `validar(planos: PlanosGerados, metas: MetasNutricionais, restricoes: list[str], catalogo: FoodCatalog) → ValidationResult`
- [ ] `ValidationResult` contém: `planos_corrigidos`, `correcoes_aplicadas` (lista de strings), `aprovado` (bool)

### Validações (ordem fixa):

**Fase 1 — Estrutural:**
- [ ] RN-001: `planos` tem exatamente 3 elementos (rejeitar se ≠ 3)
- [ ] RN-005: Cada plano tem 4-6 refeições (remover excedentes, adicionar refeição vazia com warning se < 4)

**Fase 2 — Restrições (TOLERÂNCIA ZERO):**
- [ ] RN-020: Nenhum alimento da lista de `restricoes` aparece. Se aparecer → remover e substituir por similar da mesma categoria
- [ ] RN-021: Se alergia detectada → adicionar flag de aviso na resposta

**Fase 3 — Catálogo:**
- [ ] LL-002: Todo alimento existe no `FoodCatalog`. Se não → buscar match mais próximo. Se impossível → remover

**Fase 4 — Quantidades:**
- [ ] RN-014: Toda quantidade entre 30g e 500g. Fora → clampar

**Fase 5 — Nutricional:**
- [ ] RN-010: Cada macro individual dentro de ±10% do calculado. Fora → ajustar quantidades proporcionalmente
- [ ] RN-015: Soma calórica entre 95% e 105% do GET. Fora → ajustar quantidades

**Fase 6 — Diversidade:**
- [ ] RN-004: Máximo 60% de sobreposição de alimentos entre qualquer par de planos. Se exceder → rejeitar planos e sinalizar para re-solicitação

- [ ] Se `aprovado == False` → `PlanGeneratorService` é chamado novamente (máximo 1 re-tentativa) com mensagem de erro específica no prompt
- [ ] Loga toda correção aplicada com detalhes

---

## Arquivos Previstos

- `app/services/plan_validator.py`

---

## Notas Técnicas

- A validação é 100% determinística (sem IA). Roda em < 50ms para 3 planos
- Correções automáticas são preferíveis a rejeições — só rejeitar se impossível corrigir
- Se a re-tentativa também falhar → lançar `PlanValidationException` que o endpoint trata como 502
- As correções aplicadas são incluídas no log mas NÃO são mostradas ao usuário
- A ordem das validações é importante: restrições primeiro (segurança), estrutura depois (consistência), nutricional por último (ajuste fino)
