# Investigation: Pagamento na Entrega (014)

> Gerado pelo reversa-plan em 2026-05-31
> Feature dir: `_reversa_forward/014-pagamento-entrega`

---

## 1. Contexto técnico extraído do legado

### 1.1 Ponto de ramificação principal — `checkout()` (`core/views.py:152`)

O `checkout()` atual (pós feature 013) tem esta estrutura:

```
POST /checkout/
  ├── valida carrinho não vazio
  ├── valida name, phone, address obrigatórios
  ├── calcula effective_fee (Uber Direct ou taxa estática)
  ├── transaction.atomic():
  │   ├── Order.objects.create(status=PENDING)
  │   ├── salva user se autenticado
  │   └── cria OrderItems + limpa carrinho
  └── create_checkout_pro_preference(order)  ← único caminho possível hoje
      └── retorna init_point → JS redirect para MP
```

Esta feature divide o último passo em dois caminhos mutuamente exclusivos baseados em `payment_method` do POST.

### 1.2 Dashboard — `dashboard()` (`core/views.py:283`)

```python
total_orders_pending = Order.objects.filter(status=Order.Status.PENDING).count()
```

Hardcoded para `PENDING`. O novo status `CONFIRMED` **não aparecerá** neste KPI sem alteração. Risco: restaurante vê "0 pedidos pendentes" mesmo com pedidos na entrega aguardando preparo.

### 1.3 Manager Orders — `manager_orders()` (`core/views.py:358`)

```python
orders = Order.objects.exclude(status='OPEN').order_by('-created_at')
```

Usa `exclude` em vez de `filter`. Significa que pedidos `CONFIRMED` **já aparecerão** na listagem geral sem nenhuma alteração de código nesta view. O filtro por status via `?status=CONFIRMED` também funcionará automaticamente pois o status é validado via `Order.Status.values`.

### 1.4 API FastAPI — `check_order_status()` (`core/api.py:176`)

```python
paid_statuses = [Order.Status.PREPARING, Order.Status.DELIVERING, Order.Status.COMPLETED]
is_paid = order.status in paid_statuses
```

Esta função é usada pelo cliente para verificar se o pedido foi aprovado (polling HTMX na tela de aguardando pagamento). Para pedidos na entrega, o status é `CONFIRMED` — não está na lista. O cliente ficaria em loop infinito de polling se acessar esta rota. **Mas**: pedidos na entrega não passam pela tela de aguardando PIX, então este endpoint não é chamado neste fluxo. Sem risco imediato. 🟡

### 1.5 Status badges/colors — `api.py:63-75`

Dicionários em `core/api.py` que mapeiam status → CSS/label para o painel HTMX:

```python
status_colors = {
    Order.Status.PENDING: "bg-yellow-100 text-yellow-800",
    Order.Status.PREPARING: "bg-blue-100 text-blue-800",
    ...
}
status_badges = {
    Order.Status.PENDING: "Pendente",
    Order.Status.PREPARING: "Preparando",
    ...
}
```

`CONFIRMED` não está nesses dicionários. Pedidos com status `CONFIRMED` que aparecerem no painel via HTMX terão badge vazio e sem cor. **Precisa de entrada explícita.**

### 1.6 `process_new_order` (`core/tasks.py`)

Chamada hoje em dois pontos:
1. `api.update_paid_order()` — após webhook MP aprovar pagamento
2. Indiretamente via `process_new_order.delay()` dentro do Celery

Esta feature reutiliza `process_new_order.delay(order.id)` diretamente no `checkout()` após criação do pedido na entrega, seguindo o mesmo padrão do webhook MP. Confirmado que a task já tem retry configurado no legado. 🟢

### 1.7 `cart_drawer.html` — interatividade atual

O template usa:
- **HTMX** para posts, swaps e triggers
- **Hyperscript** para toggle/show/hide inline (ex: `_="on click toggle .hidden on #add-address-form"`)

Não há Alpine.js ou vanilla JS no template. A UI dinâmica dos novos campos de pagamento deve seguir o padrão Hyperscript já presente.

### 1.8 Máquina de estados — impacto de `CONFIRMED`

Estado atual extraído de `_reversa_sdd/state-machines.md`:

| Status | Entrada | Saída |
|--------|---------|-------|
| PENDING | checkout() online | PREPARING (webhook) ou CANCELED (manager) |
| PREPARING | balcão ou webhook | DELIVERING ou CANCELED |

Novo estado `CONFIRMED`:

| Status | Entrada | Saída |
|--------|---------|-------|
| CONFIRMED | checkout() na entrega | PREPARING (manager aceita) ou CANCELED |

`CONFIRMED` é semanticamente equivalente a "aguardando preparo sem PIX". Transição para `PREPARING` ocorre pelo mesmo mecanismo de `update_order_status()` que o manager já usa. Sem nova view necessária.

### 1.9 Template `order_modal.html` e `order_row.html`

Precisam exibir badge de método de pagamento. Padrão esperado: condicional `{% if order.payment_method == 'cash' %}`, semelhante ao padrão de badges de status já presentes.

---

## 2. Alternativas avaliadas

### 2.1 View separada para pedido na entrega (descartada)

Criar `/checkout/delivery/` separado duplicaria toda a validação de `customer_name`, `customer_phone`, `delivery_address`, `delivery_fee`, `transaction.atomic()` e criação de `OrderItems`. O custo de manutenção supera o ganho de separação de responsabilidades. A ramificação por `payment_method` dentro do `checkout()` existente é mais segura. 🟢 Decisão já documentada em `roadmap.md` (D-05).

### 2.2 Campo booleano `is_delivery` (descartado)

Não modela os sub-tipos (Dinheiro vs Cartão) nem o tipo de cartão. Exigiria mais campos auxiliares de qualquer forma. `payment_method` com choices é mais expressivo. 🟢 (D-02)

### 2.3 Novo enum `PaymentStatus` (descartado)

Separar status de pagamento do status de pedido adicionaria complexidade sem benefício imediato para o escopo desta feature. O padrão atual de usar `Order.Status` para rastrear o ciclo de vida completo é suficiente.

### 2.4 Notificação síncrona ao restaurante (descartada)

Enviar a notificação de forma síncrona dentro do `transaction.atomic()` acoplaria o fluxo de checkout ao funcionamento do sistema de notificação. `process_new_order.delay()` já é o padrão estabelecido para desacoplar. 🟢 (D-06)

---

## 3. Padrões aplicáveis

| Padrão | Aplicação nesta feature |
|--------|------------------------|
| **Ramificação por tipo** | `if payment_method == 'online': ... elif payment_method in ('cash', 'card'): ...` |
| **Default explícito no POST** | `request.POST.get('payment_method', 'online')` — sem quebrar clientes antigos |
| **Decimal para valores monetários** | `Decimal(change_amount)` com try/except, nunca `float()` |
| **Hyperscript para UI dinâmica** | `_="on change show/hide ..."` nos radio buttons do template |
| **TextChoices aninhado em Model** | `Order.PaymentMethod` e `Order.CardType` como classes internas |

---

## 4. Arquivos impactados (rascunho para legacy-impact.md)

| Arquivo | Tipo de mudança |
|---------|----------------|
| `core/models.py` | Novo enum `CONFIRMED`, novos campos `payment_method`, `change_amount`, `card_type` |
| `core/migrations/0014_order_payment_fields.py` | Migration aditiva (novo arquivo) |
| `core/views.py` — `checkout()` | Ramificação por `payment_method` |
| `core/views.py` — `dashboard()` | `total_orders_pending` inclui `CONFIRMED` |
| `core/api.py` — `status_colors` e `status_badges` | Entradas para `CONFIRMED` |
| `templates/core/partials/cart_drawer.html` | UI de seleção de pagamento |
| `templates/core/partials/order_modal.html` | Badge de método de pagamento |
| `templates/core/manager/partials/order_row.html` | Badge de método de pagamento |

**Não impactados:**
- `core/payment.py` — `create_checkout_pro_preference()` chamada apenas no fluxo online
- `core/tasks.py` — `process_new_order` reutilizado sem alteração
- `manager_orders()` — `exclude(status='OPEN')` já inclui `CONFIRMED` automaticamente

---

## 5. Riscos identificados durante investigação

| Risco | Origem | Mitigação |
|-------|--------|-----------|
| `change_amount` recebendo valor não-numérico | POST não confiável | `try: Decimal(val) except: None` |
| `CONFIRMED` sem badge no painel HTMX | Dicionários em `api.py` incompletos | Adicionar entradas explícitas |
| `total_orders_pending` subcontando | `dashboard()` hardcoded para PENDING | `filter(status__in=[PENDING, CONFIRMED])` |
| Race condition ao avançar `CONFIRMED` | `update_order_status()` sem guard de transição | Existente no legado — fora do escopo desta feature |
