# SPEC-009: Frontend — Página de Input com Linguagem Natural

**Status:** ✅ Concluído
**Fase:** 1 — MVP

---

## User Story

Como usuário, quero uma caixa de texto simples onde eu possa descrever minha rotina livremente, para gerar planos alimentares sem preencher formulários longos.

---

## Critérios de Aceite

- [ ] Página principal com uma `textarea` grande (mínimo 4 linhas visíveis)
- [ ] Placeholder: _"Descreva sua rotina, objetivos e preferências alimentares... Ex: 'Trabalho sentado, faço musculação 4x por semana. Quero ganhar massa. Tenho 1,75m, 72kg, 28 anos. Gosto de frango, batata doce, ovos. Não como peixe.'"_
- [ ] Contador de caracteres em tempo real: "X/2000" (verde se > 20, vermelho se < 20)
- [ ] Botão "Gerar Planos" — desabilitado se < 20 caracteres
- [ ] Abaixo da caixa, 3 exemplos rotativos (a cada 5 segundos) de inputs reais (sedentário, atleta, vegano, gestante, idoso)
- [ ] Botão "Usar este exemplo" que preenche a caixa com o exemplo atual
- [ ] Validação client-side: remoção de tags HTML, normalização de espaços
- [ ] Overlay de loading com texto contextual que muda durante o processamento (4 estágios)
- [ ] Mensagens de erro estilizadas (alerta amarelo) abaixo da caixa de texto, sem perder o conteúdo digitado

---

## Arquivos Previstos

- `frontend/index.html` (atualizar seção da página de dieta)
- `frontend/css/style.css` (atualizar estilos da textarea, loading overlay)
- `frontend/js/app.js` (atualizar lógica de envio)

---

## Notas Técnicas

- O HTML/CSS/JS existente tem uma estrutura de formulário com campos individuais. Essa estrutura **deve ser substituída** por uma única caixa de texto
- O overlay de loading já existe (`loading-overlay`). Atualizar `loading-text` dinamicamente conforme o estágio
- A chamada API usa `apiRequest('POST', '/api/diet/generate', { texto: inputValue })`
- O texto do usuário deve ser preservado se houver erro — não limpar a caixa
