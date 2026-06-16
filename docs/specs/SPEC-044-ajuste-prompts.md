# SPEC-044: Ajuste de Prompts com Base em Feedback

**Status:** ⚪ Pendente
**Fase:** 2
**Tipo:** Subspec
**Subspec de:** SPEC-040
**Depende de:** SPEC-041 (Feedback)
**Data de criação:** 2026-05-30

---

## 1. User Story

Como product owner, quero usar o feedback dos usuários para melhorar iterativamente os prompts do sistema, reduzindo a taxa de insatisfação.

---

## 2. Critérios de Aceite

- [ ] Script `scripts/analisar_feedback.py` lê feedbacks, agrupa por motivo, extrai exemplos de planos negativos, gera relatório Markdown
- [ ] Extrair prompts atuais para arquivos versionados: `prompts/extraction_v1.txt`, `prompts/generation_v1.txt`
- [ ] Novo prompt versionado como `v2`, `v3` etc quando ajustado
- [ ] A cada 50 feedbacks, rodar script e revisar prompts manualmente
- [ ] Prompts antigos mantidos para rollback (carregar por versão via env `PROMPT_VERSION=v1`)

---

## 3. Fluxo

```
Passo 1 — Extrair system prompts do código para prompts/*.txt
Passo 2 — Carregar prompts de arquivos (não hardcoded) usando PROMPT_VERSION do .env
Passo 3 — Script scripts/analisar_feedback.py: query SQL → agrupar → gerar relatório
Passo 4 — Processo manual: revisar relatório → ajustar prompt → criar vN+1 → testar → deploy
```

---

## 4. Arquivos Previstos

| Arquivo | Tipo |
|---------|:----:|
| `scripts/analisar_feedback.py` | Novo |
| `prompts/extraction_v1.txt` | Novo |
| `prompts/generation_v1.txt` | Novo |
| `app/services/servico_extracao.py` | Modificado (carregar de arquivo) |
| `app/services/servico_geracao_planos.py` | Modificado (carregar de arquivo) |
