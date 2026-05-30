# SPEC-003: Serviço de Extração NL→JSON

**Status:** ✅ Concluído
**Fase:** 1 — MVP

---

## User Story

Como sistema, quero converter o texto livre do usuário em um JSON estruturado com perfil, preferências e restrições, para que as etapas seguintes possam operar sobre dados tipados.

---

## Critérios de Aceite

- [x] `ExtractorService` implementado em `app/services/extractor_service.py`
- [x] Método `extrair(texto: str) → PerfilExtraido`
- [x] Usa `DeepSeekClient` com system prompt de extração (inglês — LL-007)
- [x] Timeout: 15 segundos. Retry: 1 tentativa
- [x] `PerfilExtraido` como Pydantic model com campos: `perfil` (sexo, idade, peso_kg, altura_cm), `rotina` (nivel_atividade, objetivo, detalhes), `preferencias`, `restricoes`, `condicoes`, `extra`
- [x] Lança `CamposObrigatoriosAusentesException` se sexo/idade/peso/altura faltarem, listando quais campos faltam
- [x] Se `nivel_atividade` for null → assume "sedentario" (RN-031)
- [x] Se `objetivo` for null → calcula IMC e infere objetivo (RN-032)
- [x] Separa `preferencias` de `restricoes` corretamente (RN-014)
- [x] Detecta condições especiais: "gravidez", "diabetes", "hipertensao", "vegano", "vegetariano", "intolerancia_lactose" (RF-015)
- [x] Valida intervalos fisiológicos: idade 1-120, peso 20-500, altura 50-280 (RN-041)
- [x] Loga latência da extração e tokens consumidos

---

## Arquivos Previstos

- `app/services/extractor_service.py`
- `app/models/schemas.py` (atualizar com `PerfilExtraido`)

---

## Notas Técnicas

- System prompt em INGLÊS (melhor precisão do modelo — LL-007), user prompt é o texto original do usuário em português
- `response_format: { "type": "json_object" }` obrigatório (LL-001)
- Temperatura: 0.3 (extração deve ser determinística)
- O schema do JSON de resposta está documentado em `arquitetura.md` seção 6
- Campos não encontrados devem vir como `null`, não como string vazia — a validação de campos obrigatórios rejeita `null`
