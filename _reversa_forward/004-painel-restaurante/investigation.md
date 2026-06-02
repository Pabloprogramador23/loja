# Investigation: 004-painel-restaurante

> Data: `2026-05-27`

## 1. Alternativas avaliadas para o modelo de comanda

### Opção A (escolhida): Estender `Order` com status `OPEN` + campo `table_label`
- ✅ Zero modelos novos
- ✅ Reutiliza `OrderItem`, `TenantManager`, `create_pix_payment`, dashboard de pedidos
- ✅ Webhook de aprovação funciona sem modificação para comandas PIX
- ✅ Delta mínimo: 1 campo, 1 valor de status, 1 migration
- ⚠️ `table_label` fica em branco em pedidos não-comanda (aceitável — campo opcional)
- ⚠️ `update_order_status` pode tecnicamente mover qualquer pedido para `OPEN` se não for protegido

### Opção B descartada: Modelo `Comanda` separado
- ❌ Duplicaria lógica de `OrderItem` (snapshot de preço, total, tenant)
- ❌ Precisaria de lógica de "conversão" de Comanda → Order ao fechar
- ❌ Dois modelos para representar o mesmo conceito de "pedido"
- ❌ Dashboard de pedidos não mostraria comandas fechadas sem JOIN extra

### Opção C descartada: Flag `is_comanda = BooleanField`
- ❌ Sem representação de estado "aberto" — precisaria de outro campo para saber se está fechada
- ❌ Mais ambíguo que um status explícito

## 2. Alternativas para interatividade (add/remove item)

### HTMX com partial template (escolhido)
- ✅ Padrão já usado no projeto (`update_order_status`, `order_details_modal`, `cart_detail`)
- ✅ Sem JS adicional além do que já está carregado
- ✅ Funciona sem Alpine.js, React ou similar
- Referência no projeto: `templates/core/manager/` + `hx-target` / `hx-swap`

### Alpine.js com estado local (descartado)
- ❌ Não está no projeto atualmente — introduziria dependência nova
- ❌ Estado local pode dessincronizar do banco se múltiplos garçons acessarem a mesma comanda

### Polling HTMX (descartado para este caso)
- Desnecessário — o sistema de comandas não exige atualização em tempo real entre múltiplos dispositivos no escopo atual

## 3. Mobile sidebar

### Hyperscript `_="on click toggle .hidden on #mobile-sidebar"` (escolhido)
- ✅ `hyperscript.org` já carregado via CDN em `base.html` (linha 101)
- ✅ Zero dependências novas
- ✅ Compatível com Tailwind classes

### Alpine.js `x-show` (descartado)
- Não está no projeto

### Tailwind headlessui (descartado)
- Requer instalação de pacote NPM — projeto não usa bundler Node

## 4. Padrão HTMX para add/remove item

O partial `_comanda_items.html` é retornado por `comanda_add_item` e `comanda_remove_item` e faz swap no container `#comanda-items`. Segue o mesmo padrão de `order_details_modal` que retorna fragment HTML via `render(request, 'template.html', ctx)`.

```
POST /dashboard/comandas/<id>/add-item/
  hx-post + hx-target="#comanda-items" + hx-swap="outerHTML"
  → retorna _comanda_items.html renderizado com itens atualizados

POST /dashboard/comandas/<id>/remove-item/<item_id>/
  hx-post + hx-target="#comanda-items" + hx-swap="outerHTML"
  → retorna _comanda_items.html renderizado com itens atualizados
```

## 5. Fechar comanda via PIX — fluxo completo

```
Manager clica "Fechar via PIX"
  → POST /dashboard/comandas/<id>/close/ com payment_method=pix
  → view chama create_pix_payment(order)
  → create_pix_payment: usa token do tenant (RN-09), fallback mock se TEST-0000
  → order.status = PENDING; order.save()
  → view retorna comanda_detail.html com qr_code + qr_code_base64 visíveis
  → (usuário paga)
  → Webhook POST /api/webhooks/mercadopago → update_paid_order(order_id)
  → order.status = PREPARING
  → Comanda some da lista de abertas (/dashboard/comandas/)
  → Aparece em /dashboard/orders/ como PREPARING
```

Nenhuma mudança necessária em `core/payment.py`, `core/api.py` ou `core/tasks.py`.

## 6. Proteção de `update_order_status` contra retorno a OPEN

A view `update_order_status` (`core/views.py`) aceita qualquer valor de `Order.Status`. Para evitar que um Manager coloque um pedido em `OPEN` acidentalmente via o dashboard de pedidos, a view `manager_orders` e o template de atualização de status devem excluir `OPEN` das opções do dropdown. Isso é uma edição de template, não de view.
