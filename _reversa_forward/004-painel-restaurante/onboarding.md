# Onboarding: 004-painel-restaurante

> Data: `2026-05-27`
> Pré-requisito: servidor rodando em `http://127.0.0.1:8000/` com usuário Manager (is_staff=True) logado

---

## Pré-condições

1. Servidor rodando: `uvicorn store_saas.asgi:application --reload --port 8000`
2. Migration aplicada: `python manage.py migrate`
3. Usuário Manager logado (ex.: usuário Pablo que tem `owned_store = Pizzaria do Pablo`)

---

## Parte 1 — Correções de Navegação

### Teste N-01: Header "Meus Pedidos" redireciona manager corretamente

1. Logue como Manager
2. Clique em "Meus Pedidos" no header
3. **Esperado:** redireciona para `/dashboard/orders/` (lista de pedidos da loja)
4. **Regressão:** logue como cliente (sem `is_staff`) e clique "Meus Pedidos" → deve ir para `/account/orders/`

### Teste N-02: Link "Painel de Gerência" na sidebar de conta

1. Como Manager, acesse `/account/`
2. Olhe a sidebar esquerda
3. **Esperado:** item "Painel de Gerência" visível, clicável, leva para `/dashboard/`
4. **Regressão:** logue como cliente → sidebar NÃO deve exibir "Painel de Gerência"

### Teste N-03: Mobile sidebar no painel manager

1. Como Manager, acesse `/dashboard/`
2. Reduza o viewport para < 768px (ou use DevTools → responsive)
3. **Esperado:** botão hamburger visível no topo
4. Clique no botão → sidebar off-canvas abre com Visão Geral, Pedidos, Comandas, Catálogo, Configurações
5. Clique em qualquer item → navega corretamente

---

## Parte 2 — Sistema de Comandas

### Teste C-01: Criar nova comanda

1. Acesse `/dashboard/comandas/`
2. Clique em "Nova Comanda"
3. Digite "Mesa 3" no campo de identificador
4. Clique em "Criar"
5. **Esperado:** comanda criada, redirecionado para tela da comanda "Mesa 3" com zero itens e total R$ 0,00

### Teste C-02: Adicionar itens incrementalmente

1. Na tela da comanda "Mesa 3":
2. Selecione um produto no dropdown (ex.: "X-Bacon Crocante") e quantidade 2
3. Clique "Adicionar"
4. **Esperado:** item aparece na lista sem recarregar a página; total atualiza para R$ 57,80 (2 × R$ 28,90)
5. Adicione outro produto (ex.: "Coca-Cola Lata 350ml" × 3)
6. **Esperado:** lista mostra 2 itens, total atualiza para R$ 75,80

### Teste C-03: Remover item da comanda

1. Na comanda "Mesa 3" com itens:
2. Clique no botão "Remover" ao lado da Coca-Cola
3. **Esperado:** item removido da lista sem recarregar; total retorna para R$ 57,80

### Teste C-04: Listar comandas abertas

1. Crie mais uma comanda "Mesa 7" com qualquer item
2. Acesse `/dashboard/comandas/`
3. **Esperado:** lista exibe "Mesa 3" e "Mesa 7" com número de itens e total de cada

### Teste C-05: Fechar comanda — pagamento presencial

1. Na comanda "Mesa 3":
2. Clique "Fechar Comanda"
3. Escolha "Pagamento Presencial"
4. **Esperado:**
   - Comanda some de `/dashboard/comandas/` (não aparece mais na lista de abertas)
   - Em `/dashboard/orders/` aparece o pedido "Mesa 3" com status "Preparando"

### Teste C-06: Fechar comanda — via PIX

1. Na comanda "Mesa 7":
2. Clique "Fechar Comanda"
3. Escolha "Fechar via PIX"
4. **Esperado:**
   - QR Code exibido na tela (ou mock QR Code em dev com token TEST-0000)
   - Código copia-e-cola visível
   - Comanda com status "Pendente" em `/dashboard/orders/`

### Teste C-07: Comanda com zero itens não pode ser fechada via PIX

1. Crie comanda "Mesa Teste" sem adicionar nenhum item
2. Clique "Fechar via PIX"
3. **Esperado:** mensagem de erro "Adicione ao menos um item antes de fechar via PIX" (sem gerar QR Code)

---

## Parte 3 — Verificação de Isolamento Multi-tenant

1. Se tiver dois usuários Manager de lojas diferentes:
2. Crie comanda na Loja A
3. Logue na Loja B
4. Acesse `/dashboard/comandas/`
5. **Esperado:** comanda da Loja A não aparece na Loja B

---

## Verificação de Regressão Geral

- [ ] Checkout do cliente (fluxo normal) ainda funciona
- [ ] Dashboard de pedidos (`/dashboard/orders/`) não mostra comandas `OPEN`
- [ ] KPIs do dashboard (pendentes, vendas, hoje) não contam comandas `OPEN`
- [ ] Rastreamento público `/order/<id>/track/` não expõe dados de comanda aberta
