# SPEC-003: Serviço de Extração NL→JSON

**Status:** 🔴 Pendente
**Fase:** 1 — MVP

---

## User Story

Como sistema, quero converter o texto livre do usuário em um JSON estruturado com perfil, preferências e restrições, para que as etapas seguintes possam operar sobre dados tipados.

---

## Critérios de Aceite

- [ ] `ExtractorService` implementado em `app/services/extractor_service.py`
- [ ] Método `extrair(texto: str) → PerfilExtraido`
- [ ] Usa `DeepSeekClient` com system prompt de extração (inglês — LL-007)
- [ ] Timeout: 15 segundos. Retry: 1 tentativa
- [ ] `PerfilExtraido` como Pydantic model com campos: `perfil` (sexo, idade, peso_kg, altura_cm), `rotina` (nivel_atividade, objetivo, detalhes), `preferencias`, `restricoes`, `condicoes`, `extra`
- [ ] Lança `CamposObrigatoriosAusentesException` se sexo/idade/peso/altura faltarem, listando quais campos faltam
- [ ] Se `nivel_atividade` for null → assume "sedentario" (RN-031)
- [ ] Se `objetivo` for null → calcula IMC e infere objetivo (RN-032)
- [ ] Separa `preferencias` de `restricoes` corretamente (RN-014)
- [ ] Detecta condições especiais: "gravidez", "diabetes", "hipertensao", "vegano", "vegetariano", "intolerancia_lactose" (RF-015)
- [ ] Valida intervalos fisiológicos: idade 1-120, peso 20-500, altura 50-280 (RN-041)
- [ ] Loga latência da extração e tokens consumidos

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
