# Onboarding: Testando a remoção do botão de tema

> Identificador: `022-remover-botao-tema`
> Data: `2026-06-05`

## Pré-requisitos

- Servidor rodando (`uvicorn store_saas.asgi:application --reload --port 8000`)
- Usuário gestor disponível para login

## Passo a passo de validação

### 1. Confirmar que o botão sumiu do sidebar

```
GET http://127.0.0.1:8000/dashboard/
```
Fazer login como gestor → inspecionar o sidebar esquerdo.

**Resultado esperado:** Sidebar contém navegação, info do usuário e botão "Sair". Nenhum botão com ícone de lua/sol ou texto "Tema".

### 2. Confirmar que a função toggleTheme() ainda existe

No DevTools do browser, console:
```javascript
typeof toggleTheme
```
**Resultado esperado:** `"function"` — a função ainda está declarada no `<head>`.

### 3. Confirmar que o dark mode continua aplicado

Se o usuário tinha preferência `dark` salva, o painel deve carregar já em modo escuro (classe `dark` no `<html>`).

**Resultado esperado:** Sem botão, mas o tema continua sendo aplicado pelo anti-FOUC com base em `localStorage` / preferência do servidor.

### 4. Confirmar que a vitrine não foi afetada

```
GET http://127.0.0.1:8000/
```
**Resultado esperado:** Header e layout da vitrine idênticos ao estado anterior — sem alteração.

### 5. Confirmar que nenhum .py foi alterado

```bash
git diff --name-only | grep "\.py$"
```
**Resultado esperado:** Nenhuma linha de output.

### 6. Grep de validação

```bash
grep -rn "onclick=\"toggleTheme()" templates/
```
**Resultado esperado:** Nenhuma ocorrência (o botão foi removido; a declaração da função não usa `onclick`).
