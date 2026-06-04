# SPEC-053: Exportação Avançada (PDF Melhorado + CSV)

**Status:** ⚪ Pendente
**Fase:** 3 — Escala e Personalização
**Pré-requisito:** Fase 2 concluída com > 70% de aprovação

---

## User Story

Como usuário, quero exportar meus planos em formatos diferentes para diferentes usos: PDF profissional para o nutricionista, CSV para controle pessoal.

---

## Critérios de Aceite

- [ ] PDF melhorado:
  - Capa com logo do sistema
  - Tabela de medidas caseiras (coluna adicional)
  - Gráfico de distribuição de macros (pizza chart via ReportLab)
  - Opção de incluir/excluir explicações dos planos
- [ ] `GET /api/diet/{sessao_id}/csv` — download de CSV com todos os alimentos de todos os planos
  - Colunas: Plano, Refeição, Alimento, Quantidade (g), Proteína, Carbo, Gordura, kcal
- [ ] `GET /api/diet/{sessao_id}/pdf?formato=simplificado` — PDF de 1 página vs PDF completo (3 páginas)

---

## Arquivos Previstos

- `app/utils/pdf_generator.py` (atualizar)
- `app/utils/csv_generator.py` (novo)
- `app/routers/diet.py` (novo endpoint CSV)

---

## Notas Técnicas

- O ReportLab suporta gráficos de pizza nativos (`Drawing` + `Pie`)
- O CSV usa `csv.writer` da stdlib (sem dependências)
- Medidas caseiras exigem tabela de conversão (RN-101)
