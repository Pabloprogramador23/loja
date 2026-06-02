# Actions: Bugfix — Inputs invisíveis no modo escuro (Configurações)

> Identificador: `008-bugfix-dark-mode-inputs`
> Data: `2026-05-30`
> Tipo: `bugfix`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 1 |
| Paralelizáveis (`[//]`) | 0 |
| Arquivos modificados | 1 |

---

## Sintoma

Na página de Configurações (`/manager/settings/`), em modo escuro, o texto digitado nos campos de formulário ficava invisível. O fundo dos inputs permanecia branco (padrão do browser) enquanto o browser forçava cor de texto clara por inferência do `color-scheme`, resultando em texto branco sobre fundo branco.

O campo "Taxa de entrega (R$)" foi o primeiro a ser identificado pelo usuário em 2026-05-30, após o deploy da feature 007. Os campos "Nome da Loja" e "Token de Acesso (Mercado Pago)" tinham o mesmo problema latente.

---

## Causa Raiz

Os widgets do `StoreSettingsForm` em `core/forms.py` não tinham classes Tailwind `dark:` — apenas classes para light mode. Em dark mode, o Tailwind não sobrescrevia o background nem a cor do texto, deixando o browser aplicar suas próprias regras de acessibilidade (texto claro sobre fundo claro).

---

## Fase única — Correção

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Em `core/forms.py`, adicionar `dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400` nos widgets `name`, `mercadopago_access_token`, `delivery_fee` e `free_delivery_threshold` do `StoreSettingsForm`. | - | - | `core/forms.py` | 🟢 | `[X]` |

---

## Verificação

Após correção, testado manualmente em modo escuro: todos os campos de texto em Configurações exibem fundo cinza escuro (`gray-700`) e texto branco, consistente com o restante da interface.

---

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-30 | Bug identificado durante testes manuais pós-feature 007; correção aplicada (T001) | pablo + Claude Code |
