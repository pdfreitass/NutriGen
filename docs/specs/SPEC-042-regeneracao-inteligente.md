# SPEC-042: Regeneração Inteligente de Planos

**Status:** ⚪ Pendente
**Fase:** 2
**Tipo:** Subspec
**Subspec de:** SPEC-040
**Depende de:** SPEC-040 (Histórico)
**Data de criação:** 2026-05-30

---

## 1. User Story

Como usuário, quero gerar novos planos quando não gostar dos atuais, com garantia de que serão diferentes da geração anterior — sem repetir os mesmos alimentos.

---

## 2. Critérios de Aceite

### 2.1 Backend

- [ ] **REGEN-01:** `POST /api/diet/generate` aceita campo opcional `evitar_alimentos: list[str]` com nomes de alimentos a excluir.
  - **Input:** Mesmo schema atual + `evitar_alimentos` (opcional).
  - **Output:** Idêntico ao atual.

- [ ] **REGEN-02:** Se `evitar_alimentos` for enviado, temperatura do DeepSeek sobe para 0.85.

- [ ] **REGEN-03:** Prompt de geração inclui: "EVITE estes alimentos que já apareceram em planos anteriores: [lista]".

### 2.2 Frontend

- [ ] **REGEN-04:** Botão "🔄 Gerar Novamente" coleta nomes de alimentos dos 3 planos atuais e envia em `evitar_alimentos`.
- [ ] **REGEN-05:** Contador de regenerações: se ≥ 3 em < 2 minutos, exibe sugestão: "Que tal ajustar sua rotina para mais variação?".
- [ ] **REGEN-06:** Toast informando: "Gerando novos planos com alimentos diferentes dos anteriores..."

---

## 3. Contratos de Dados

```json
// Request (campo novo)
{
  "sexo": "masculino", "idade": 21, "peso_kg": 88, "altura_cm": 184,
  "nivel_atividade": "ativo", "texto": "...",
  "evitar_alimentos": ["Arroz Branco Cozido", "Peito de Frango Grelhado", "Banana"]
}
```

---

## 4. Fluxo de Implementação

```
Passo 1 — Atualizar DietGenerateRequestV2: adicionar campo evitar_alimentos: list[str] = []
Passo 2 — GerarPlanosUseCase: se evitar_alimentos, adicionar à lista de restrições expandidas
Passo 3 — PlanGeneratorService: se evitar_alimentos, temp=0.85 e reforçar no prompt
Passo 4 — Frontend: botão "Gerar Novamente" coleta alimentos e reenvia
```

---

## 5. Arquivos Previstos

| Arquivo | Camada | Tipo |
|---------|:------:|:----:|
| `app/models/esquemas.py` | Domain | Modificado (+evitar_alimentos) |
| `app/use_cases/gerar_planos.py` | Application | Modificado |
| `app/services/servico_geracao_planos.py` | Application | Modificado |
| `frontend/js/app.js` | Frontend | Modificado |
