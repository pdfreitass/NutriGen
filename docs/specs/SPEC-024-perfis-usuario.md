# SPEC-024: Perfis de Usuário e Preferências Salvas

**Status:** ⚪ Pendente
**Fase:** 3 — Escala e Personalização
**Pré-requisito:** Fase 2 concluída com > 70% de aprovação

---

## User Story

Como usuário autenticado, quero salvar meu perfil (peso, altura, preferências, restrições) para não precisar digitar tudo novamente a cada geração.

---

## Critérios de Aceite

- [ ] Usuário pode salvar perfil padrão durante ou após o cadastro
- [ ] Perfil padrão preenche automaticamente a caixa de texto com um resumo: _"Tenho X anos, Y kg, Z cm, sexo [M/F]. Objetivo: [X]. Gosto de: [alimentos]. Não como: [restrições]."_
- [ ] Usuário pode editar o texto preenchido antes de enviar
- [ ] `PUT /api/auth/perfil` para atualizar perfil padrão
- [ ] `GET /api/auth/perfil` para recuperar perfil padrão
- [ ] Suporte a múltiplos perfis (ex: "Eu", "Meu filho", "Minha esposa") — até 3 perfis por conta gratuita

---

## Arquivos Previstos

- `app/models/database/perfil_usuario.py` (novo)
- `app/routers/auth.py` (novos endpoints)
- `alembic/versions/` (nova migração)
- `frontend/js/app.js` (preenchimento automático)

---

## Notas Técnicas

- Cada perfil salvo é apenas um template de texto — não substitui o input em linguagem natural
- O sistema continua aceitando texto livre mesmo para usuários com perfil salvo
