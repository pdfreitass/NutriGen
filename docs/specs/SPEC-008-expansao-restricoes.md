# SPEC-008: Expansão de Restrições e Condições Especiais

**Status:** 🔴 Pendente
**Fase:** 1 — MVP

---

## User Story

Como usuário com restrições alimentares, quero que o sistema entenda restrições genéricas ("não como peixe", "sou vegano") e as aplique corretamente em todos os planos, para que eu confie que os planos são seguros para mim.

---

## Critérios de Aceite

- [ ] `RestrictionExpander` implementado em `app/services/restriction_expander.py`
- [ ] Método `expandir(restricoes: list[str], condicoes: list[str], catalogo: FoodCatalog) → ExpandedRestrictions`
- [ ] `ExpandedRestrictions` contém: `alimentos_proibidos` (lista concreta), `severidade` (alergia | conviccao | preferencia), `avisos` (lista de strings)
- [ ] Mapeamentos implementados:
  - "peixe" → ["Salmão Grelhado", "Atum em Lata", "Tilápia Grelhada", "Camarão Cozido"]
  - "carne vermelha" → ["Carne Moída Magra", "Filé Mignon", "Costela Bovina", "Lombo Suíno"]
  - "frutos do mar" → mesmo que peixe
  - "laticínios" → todos da categoria "Laticínios"
  - "glúten" → ["Pão Francês", "Pão Integral", "Macarrão Cozido"]
  - "vegano" → categorias "Carnes e Peixes" + "Laticínios" + "Ovo Cozido", "Ovo Mexido"
  - "vegetariano" → categoria "Carnes e Peixes"
  - "ovolactovegetariano" → categoria "Carnes e Peixes"
- [ ] Classificação de severidade:
  - "alergia"/"intolerancia" → Tipo A (tolerância zero, aviso obrigatório)
  - "vegano"/"vegetariano" → Tipo B (tolerância zero, ajuste de macros se necessário)
  - "não gosto"/"evito" → Tipo C (evitar, mas pode incluir se necessário)
- [ ] Avisos gerados automaticamente por tipo de condição (RN-021, RN-022, RN-023, RN-070, RN-071, RN-072)
- [ ] Detecção de transtorno alimentar no texto → **bloqueio total** (RN-073)

---

## Arquivos Previstos

- `app/services/restriction_expander.py`

---

## Notas Técnicas

- A expansão DEVE rodar ANTES da montagem do prompt de geração (SPEC-004) e ANTES da validação (SPEC-005)
- O mapeamento de categorias usa `FoodCatalog` — se um alimento for adicionado ao `foods.json`, a expansão automaticamente o inclui
- Para condições médicas (diabetes, hipertensão), o sistema não ajusta os planos — apenas adiciona o aviso obrigatório
- Strings para detecção de transtorno alimentar: "anorexia", "bulimia", "compulsão alimentar", "transtorno alimentar", "não como há", "vômito"
