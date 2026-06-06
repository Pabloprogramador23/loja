# Legacy Impact: 022-remover-botao-tema

> Feature: `022-remover-botao-tema`
> Data: `2026-06-05`
> Gerado por: `/reversa-coding`

## Arquivos afetados

| Arquivo afetado | Componente (`_reversa_sdd/`) | Tipo | Severidade | Justificativa |
|-----------------|------------------------------|------|------------|---------------|
| `templates/dashboard_base.html` | `core/dashboard-manager` | regra-alterada | LOW | Elemento `<button onclick="toggleTheme()">` removido do sidebar; JS `toggleTheme()` permanece no `<head>` |

## Diff conceitual por componente

### `core/dashboard-manager` — Sidebar do painel

**Antes:** O sidebar do painel do gestor exibia, logo acima da info do usuário, um botão de alternância de tema (ícone lua/sol + texto "Tema") que invocava `toggleTheme()` ao clique.

**Depois:** O botão foi removido. O sidebar exibe apenas a navegação, a info do usuário e o botão de logout. A função JS `toggleTheme()` permanece declarada no `<head>` mas sem invocador na UI. O script anti-FOUC continua aplicando o tema baseado em `localStorage` / preferência do servidor (`theme_pref` via `UserSettings`).

## Regras preservadas

| Regra | Fonte | Status |
|-------|-------|--------|
| RN-19 Preferência de tema global por usuário | `_reversa_sdd/domain.md#RN-19` | 🟢 intacta — `UserSettings`, `set_theme`, `theme_pref` e anti-FOUC não alterados |
| RN-12 Acesso ao dashboard — controle binário | `_reversa_sdd/domain.md#RN-12` | 🟢 intacta — lógica de staff não alterada |

## Regras modificadas

| Regra | Fonte | Mudança |
|-------|-------|---------|
| (implícita) Gestor pode alternar tema pela UI do painel | `templates/dashboard_base.html` sidebar | **Removida da UI** — a preferência persiste em banco, mas não há mais controle visual para alterá-la pelo painel |
