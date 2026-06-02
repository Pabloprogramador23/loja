# Onboarding: 002-cadastro-loja-saas

> Passo a passo para testar a feature manualmente após o coding.

---

## Pré-requisitos

```powershell
# 1. Aplicar a migration nova
python manage.py migrate

# 2. Subir o servidor (se não estiver rodando)
uvicorn store_saas.asgi:application --reload --port 8000
```

---

## Cenário 1: Criar loja nova com sucesso

1. Acesse `http://127.0.0.1:8000/criar-loja/` sem estar autenticado
2. Preencha o formulário:
   - Nome de usuário: `joao`
   - Senha + confirmação: qualquer senha válida
   - Nome da loja: `Pizza do João`
   - Subdomínio: `pizzadojoao`
3. Envie o formulário
4. **Resultado esperado:** redirect para `http://127.0.0.1:8000/dashboard/` com sessão autenticada como `joao`
5. **Verificação extra:** `http://127.0.0.1:8000/admin/core/store/` — loja `pizzadojoao` exibe `joao` no campo `owner`

---

## Cenário 2: Subdomínio duplicado

1. Sem sair da sessão de `joao`, abra aba anônima e acesse `http://127.0.0.1:8000/criar-loja/`
2. Preencha com subdomínio `pizzadojoao` (já existente)
3. **Resultado esperado:** formulário exibe "Este subdomínio já está em uso"; nenhum usuário criado

---

## Cenário 3: Subdomínio reservado

1. No formulário, tente subdomínio `admin`
2. **Resultado esperado:** formulário exibe "Subdomínio reservado"

---

## Cenário 4: Login de dono → redirect para dashboard

1. Encerre a sessão clicando em "Sair"
2. Acesse `http://127.0.0.1:8000/login/`
3. Faça login com `joao` / senha
4. **Resultado esperado:** redirect automático para `/dashboard/`

---

## Cenário 5: Login de cliente → redirect para home

1. Crie um usuário comum em `http://127.0.0.1:8000/signup/` (sem criar loja)
2. Faça login com esse usuário em `/login/`
3. **Resultado esperado:** redirect para `/` (home da loja), **não** para `/dashboard/`

---

## Cenário 6: Cliente sem ownership não acessa dashboard diretamente

1. Ainda autenticado como o cliente do cenário 5, acesse `http://127.0.0.1:8000/dashboard/`
2. **Resultado esperado:** redirect para `/`

---

## Cenário 7: Superuser acessa dashboard normalmente

1. Acesse `http://127.0.0.1:8000/login/` e entre com o superuser criado via `createsuperuser`
2. Acesse `http://127.0.0.1:8000/dashboard/`
3. **Resultado esperado:** HTTP 200 — dashboard carregado normalmente

---

## Cenário 8: Usuário autenticado acessa /criar-loja/

1. Autenticado como qualquer usuário, acesse `http://127.0.0.1:8000/criar-loja/`
2. **Resultado esperado:** redirect para `/` (não exibe o formulário)

---

## Cenário 9: Link na tela de login

1. Sem autenticação, acesse `http://127.0.0.1:8000/login/`
2. **Resultado esperado:** link "Crie sua loja" visível na página, apontando para `/criar-loja/`

---

## Checklist final

| Cenário | Status |
|---------|--------|
| Criação de loja — happy path | ⬜ |
| Subdomínio duplicado | ⬜ |
| Subdomínio reservado | ⬜ |
| Login de dono → dashboard | ⬜ |
| Login de cliente → home | ⬜ |
| Cliente sem ownership → bloqueado no dashboard | ⬜ |
| Superuser acessa dashboard | ⬜ |
| Usuário autenticado em /criar-loja/ → redirect | ⬜ |
| Link "Crie sua loja" na tela de login | ⬜ |
