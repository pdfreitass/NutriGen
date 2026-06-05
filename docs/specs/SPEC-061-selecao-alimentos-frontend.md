# SPEC-061: Frontend de Seleção de Alimentos

**Status:** ⚪ Pendente
**Fase:** 2
**Tipo:** Subspec
**Subspec de:** SPEC-060
**Depende de:** SPEC-030 (Frontend Input)
**Data de criação:** 2026-06-05

---

## 1. User Story

Como usuário, quero selecionar os alimentos que consumo no dia a dia a partir de um catálogo visual organizado por categorias, para receber planos 100% baseados na minha realidade.

---

## 2. Critérios de Aceite

- [ ] **SEL-01:** Nova tela "Selecionar Alimentos" após formulário de perfil
- [ ] **SEL-02:** 7 categorias expansíveis com ícones e contador (ex: "🍗 Proteínas (3/12)")
- [ ] **SEL-03:** Busca em tempo real (filtra com 2+ caracteres)
- [ ] **SEL-04:** Badge "🛒 Cesta" com resumo e alerta se faltar proteína
- [ ] **SEL-05:** Mínimo 5 alimentos + 1 proteína para habilitar botão

---

## 3. Arquivos Previstos

| Arquivo | Tipo |
|---------|:----:|
| `frontend/js/selecao-alimentos.js` | Novo |
| `frontend/css/selecao-alimentos.css` | Novo |
| `frontend/index.html` | Modificado |
| `frontend/js/app.js` | Modificado |
