# Regression Watch: 022-remover-botao-tema

> Feature: `022-remover-botao-tema`
> Gerado por: `/reversa-coding`
> Data: `2026-06-05`

## Watch Items

| ID | Origem | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------|-----------------------------|---------------------|-------------------|
| W001 | `templates/dashboard_base.html` sidebar | Nenhum `<button onclick="toggleTheme()">` presente no sidebar do painel | ausência | grep por `onclick="toggleTheme()"` em `templates/` retorna match |
| W002 | `templates/dashboard_base.html` `<head>` | Função `toggleTheme()` declarada no `<head>` — infraestrutura dark mode intacta | presença | grep por `function toggleTheme` em `dashboard_base.html` retorna zero matches |
| W003 | `templates/dashboard_base.html` sidebar | Botão de logout (`{% url 'logout' %}`) ainda presente no sidebar | presença | grep por `logout` no sidebar retorna zero matches |
| W004 | Todos os arquivos `.py` | Nenhum arquivo Python foi alterado por esta feature | ausência | `git diff --name-only` mostra arquivos `.py` com mudanças |

## Observações (sem peso de regressão)

- 🟡 A preferência de tema salva em `UserSettings` para cada gestor continua sendo aplicada pelo script anti-FOUC — sem botão, o tema não pode ser alterado pela UI do painel, mas a preferência existente é respeitada.

## Histórico de re-extrações

*(será preenchido pelo agente reverso quando `/reversa` for executado novamente)*

## Arquivadas

*(vazio)*
