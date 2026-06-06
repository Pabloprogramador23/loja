# Onboarding: Painel SaaS Admin

> Identificador: `023-painel-saas-admin`
> Data: `2026-06-05`
> Para: quem vai testar a feature pela primeira vez

## Pré-requisitos

- Servidor rodando (`uvicorn` na porta 8000 ou Docker)
- Usuário superuser criado (`python manage.py createsuperuser` ou via seed)
- Pelo menos uma loja cadastrada no banco

## Passo a passo

### 1. Acessar o painel

1. Abra `http://127.0.0.1:8000/saas/`
2. Se não estiver logado, você será redirecionado para `/login/`
3. Faça login com as credenciais do superuser (ex: `admin` / `admin`)
4. Você será redirecionado de volta para `/saas/` automaticamente

**O que você deve ver:**
- Cabeçalho indicando "Painel SaaS" (diferente do dashboard do lojista)
- Contadores no topo: total de lojas ativas e inativas
- Tabela com todas as lojas: nome, subdomínio, status badge, pedidos hoje, pedidos totais, data de criação, botões de ação

### 2. Testar o toggle de ativar/desativar

1. Na listagem, clique no badge de status de uma loja (ex: "Ativa")
2. O badge deve mudar imediatamente para "Inativa" (sem recarregar a página)
3. Em outra aba, tente acessar a loja pelo subdomínio — deve retornar 404
4. Volte ao painel e reative a loja clicando novamente
5. Confirme que a loja volta a ser acessível

### 3. Testar o botão "Ver loja"

1. Na linha de qualquer loja, clique em "Ver loja"
2. Uma nova aba deve abrir com a página pública da loja
3. Em dev (sem subdomínio real), a URL será `http://127.0.0.1:8000/` com header de tenant

### 4. Criar uma nova loja

1. Clique no botão "Nova loja" (topo da listagem ou link `/saas/lojas/nova/`)
2. Preencha:
   - Nome da loja: `Teste Burguer`
   - Subdomínio: `testeburger` (sem espaços, sem acentos)
   - Email do gerente: `gerente@teste.com`
   - Senha: qualquer senha segura
3. Clique em "Criar loja"
4. Você deve ser redirecionado para `/saas/` e ver `testeburger` na listagem como "Ativa"
5. Faça logout e tente logar com `gerente@teste.com` — deve funcionar e redirecionar para `/dashboard/`

### 5. Testar o detalhe de uma loja

1. Na listagem, clique no nome de qualquer loja
2. Você deve ver: dados cadastrais, owner, token MP mascarado (ex: `****-XXXXXX`), taxa de entrega, últimos 10 pedidos

### 6. Testar proteção de rota

1. Crie (ou use) um usuário com `is_staff=True` mas `is_superuser=False` (um Manager de loja)
2. Faça login com esse usuário
3. Tente acessar `http://127.0.0.1:8000/saas/`
4. Deve ser redirecionado silenciosamente para `/dashboard/` — sem mensagem de erro

## Casos de erro esperados

| Situação | Comportamento esperado |
|----------|----------------------|
| Subdomínio já existe no formulário de criação | Erro de validação no campo "Subdomínio" |
| Tentar desativar a própria loja do superusuário | Mensagem de bloqueio / botão desabilitado |
| Acessar `/saas/lojas/999/` com ID inexistente | 404 |
