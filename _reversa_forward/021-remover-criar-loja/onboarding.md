# Onboarding: Testando a remoção de "Criar Loja"

> Identificador: `021-remover-criar-loja`
> Data: `2026-06-05`

## Pré-requisitos

- Servidor rodando (`uvicorn store_saas.asgi:application --reload --port 8000`)
- Nenhuma sessão autenticada aberta (use aba anônima)

## Passo a passo de validação

### 1. Confirmar que a rota não existe mais

```
GET http://127.0.0.1:8000/criar-loja/
```

**Resultado esperado:** HTTP 404 — página de erro padrão do Django.

### 2. Confirmar que o link sumiu da tela de login

```
GET http://127.0.0.1:8000/login/
```

**Resultado esperado:** Tela de login sem nenhum link ou texto "Crie sua loja" ou "🏪".  
Apenas o link "Criar uma conta nova" (que vai para `/signup/`) deve permanecer.

### 3. Confirmar que o cadastro de cliente ainda funciona

```
GET http://127.0.0.1:8000/signup/
```

**Resultado esperado:** Formulário de cadastro de cliente exibido normalmente.  
Preencher e submeter → usuário criado e redirecionado para index.

### 4. Confirmar que o login ainda funciona

```
GET http://127.0.0.1:8000/login/
```

Entrar com um usuário existente → redirecionado para dashboard (se owner) ou index (se cliente).

### 5. Confirmar grep limpo

Execute no terminal, na raiz do projeto:

```bash
grep -r "criar_loja" --include="*.py" --include="*.html" .
```

**Resultado esperado:** Nenhuma linha de output.

## O que NÃO deve ser afetado

- `/signup/` continua funcional
- `/login/` e `/logout/` continuam funcionais
- Modal de checkout (auth modal) continua funcional
- Django Admin em `/admin/` permite criar Store normalmente
