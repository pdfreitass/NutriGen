# SPEC-006: Atualização do Orquestrador (DietPlannerUseCase)

**Status:** ✅ Concluído
**Fase:** 1 — MVP

---

## User Story

Como sistema, quero um orquestrador que coordene o fluxo completo (extração → cálculo → geração → validação → persistência → PDF) de forma coesa e com tratamento de erros em cada etapa.

---

## Critérios de Aceite

- [ ] `DietPlannerUseCase` (ou `GerarPlanosUseCase`) implementado em `app/use_cases/gerar_planos.py`
- [ ] Método `executar(texto: str) → DietGenerateResponse`
- [ ] Fluxo orquestrado na ordem exata (Fluxo 1 do `fluxos.md`):
  1. `ExtractorService.extrair(texto)` → `PerfilExtraido`
  2. `NutritionCalculator.calcular(perfil)` → `MetasNutricionais`
  3. `PlanGeneratorService.gerar(perfil, metas)` → `PlanosGerados`
  4. `PlanValidator.validar(planos, metas, restricoes, catalogo)` → `ValidationResult`
  5. Se `aprovado == False` → voltar ao passo 3 (máximo 1x)
  6. `SessaoGeracaoRepository.salvar(sessao, planos)` → persistência
  7. `PdfGeneratorService.gerar(response)` → UUID do PDF
  8. Montar e retornar `DietGenerateResponse`
- [ ] Cada etapa tem try/except individual com exceção específica
- [ ] Logs em cada etapa com `request_id` para correlação
- [ ] Se DeepSeek falhar na extração → 503
- [ ] Se DeepSeek falhar na geração → 503 após retries
- [ ] Se validação falhar 2x → 502
- [ ] Se banco falhar → 500 com rollback
- [ ] Se PDF falhar → continua sem PDF (pdf_url = null)

---

## Arquivos Previstos

- `app/use_cases/__init__.py`
- `app/use_cases/gerar_planos.py`
- `app/models/schemas.py` (atualizar `DietGenerateResponse` para novo schema)

---

## Notas Técnicas

- O `NutritionCalculator` reusa `tmb_calculator.py` e `macro_distributor.py` existentes (já implementados e testados)
- O fluxo está documentado em detalhes no `fluxos.md` — Fluxo 1 (16 passos com 10 exceções)
- A persistência usa os modelos ORM existentes (`SessaoGeracao`, `PlanoAlimentar`, `Refeicao`, `ItemRefeicao`)
- O PDF usa `pdf_generator.py` existente, adaptado para o novo schema de resposta
