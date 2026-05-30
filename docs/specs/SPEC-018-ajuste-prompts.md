# SPEC-018: Ajuste de Prompts com Base em Feedback

**Status:** ⚪ Pendente
**Fase:** 2 — Refina a Experiência
**Pré-requisito:** SPEC-015 (Sistema de Feedback) concluído

---

## User Story

Como product owner, quero usar o feedback dos usuários para melhorar os prompts do sistema e reduzir a taxa de feedback negativo.

---

## Critérios de Aceite

- [ ] Script `scripts/analisar_feedback.py` que:
  - Lê feedbacks da tabela `feedback_planos`
  - Agrupa por motivo
  - Extrai exemplos de planos que receberam feedback negativo
  - Gera relatório em Markdown com top 5 problemas e exemplos
- [ ] Processo documentado: a cada 50 feedbacks, rodar script e revisar prompts
- [ ] Versionamento de prompts: cada system prompt salvo em `prompts/extraction_v1.txt`, `prompts/generation_v1.txt`
- [ ] Novo prompt versionado como `v2` quando ajustado

---

## Arquivos Previstos

- `scripts/analisar_feedback.py`
- `prompts/extraction_v1.txt`
- `prompts/generation_v1.txt`

---

## Notas Técnicas

- Ajustes de prompt são feitos manualmente (não automatizados) com base no relatório
- Cada versão de prompt é testada com um conjunto fixo de 10 inputs de exemplo antes de ir para produção
- Prompts antigos são mantidos para rollback rápido se a nova versão performar pior
