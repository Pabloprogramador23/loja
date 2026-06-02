# Legacy Impact: 014-pagamento-entrega

> Data: 2026-05-31
> Feature: Pagamento na Entrega

## Arquivos modificados

| Arquivo afetado | Componente (`_reversa_sdd/`) | Tipo | Severidade | Justificativa |
|-----------------|------------------------------|------|------------|---------------|
| `core/models.py` | `architecture.md#Order` | regra-nova + delta-de-dados | HIGH | Novo status `CONFIRMED`, 3 novos campos (`payment_method`, `change_amount`, `card_type`), 2 novas classes de choices internas |
| `core/migrations/0014_order_payment_fields.py` | `architecture.md#Order` | delta-de-dados | HIGH | Migration aditiva com AddField para os 3 novos campos; nenhum dado existente afetado (defaults seguros) |
| `core/views.py` — `checkout()` | `code-analysis.md#2.3` | regra-alterada | HIGH | Ramificação por `payment_method`; fluxo na entrega cria Order com `CONFIRMED` e dispara `process_new_order.delay()`; fluxo online inalterado |
| `core/views.py` — `dashboard()` | `code-analysis.md#3.1` | regra-alterada | MEDIUM | `total_orders_pending` agora inclui `CONFIRMED` além de `PENDING` |
| `core/api.py` | `architecture.md#FastAPI` | regra-nova | LOW | Entradas de `CONFIRMED` adicionadas em `status_colors` e `status_badges`; sem alteração de lógica |
| `templates/core/partials/cart_drawer.html` | `architecture.md#Frontend` | regra-alterada | HIGH | UI de seleção de pagamento substituiu botão único; campos dinâmicos via Hyperscript |
| `templates/core/partials/order_modal.html` | `architecture.md#Frontend` | regra-nova | MEDIUM | Badge de método de pagamento adicionado; botão "Confirmar Pedido" estendido para `CONFIRMED` |
| `templates/core/manager/partials/order_row.html` | `architecture.md#Frontend` | regra-nova | MEDIUM | Badge compacto de método de pagamento; botão "Aceitar" estendido para `CONFIRMED` |

## Arquivos criados

| Arquivo | Tipo |
|---------|------|
| `core/migrations/0014_order_payment_fields.py` | componente-novo |
| `core/tests_checkout_delivery.py` | componente-novo |
| `core/tests_dashboard_confirmed.py` | componente-novo |

## Diff conceitual por componente

### Order (core/models.py)

O model recebeu um novo estado terminal de entrada (`CONFIRMED`) — pedidos na entrega nascem neste estado e aguardam o manager avançar para `PREPARING`. Os campos `payment_method` (default `online`), `change_amount` (nullable) e `card_type` (blank) são aditivos e retrocompatíveis: pedidos históricos recebem `payment_method='online'` via default da migration.

### checkout() (core/views.py)

A função mantém a estrutura de `transaction.atomic()` com criação de `OrderItem`. A ramificação ocorre **após** a criação do Order: se `payment_method` for `cash` ou `card`, o status é `CONFIRMED` e `process_new_order.delay()` é chamado diretamente (sem webhook MP). Se `online` (default), o fluxo existente com `create_checkout_pro_preference()` permanece inalterado.

### dashboard() (core/views.py)

Um único filtro alterado: `filter(status=PENDING)` → `filter(status__in=[PENDING, CONFIRMED])`. O KPI "Pedidos Pendentes" passa a refletir todos os pedidos aguardando preparo, independente do método de pagamento.

### Frontend

O `cart_drawer.html` substituiu o botão único "Finalizar Pedido" por dois botões de seleção de método ("Pagar Online" / "Pagar na Entrega") com sub-seleção de Dinheiro/Cartão e campos condicionais via Hyperscript. O input `payment_method` (hidden) é atualizado dinamicamente. `order_modal.html` e `order_row.html` receberam badges de método de pagamento.

## Regras preservadas (de `_reversa_sdd/domain.md`)

| Regra | Status |
|-------|--------|
| RN-04: Checkout valida customer_name, customer_phone, delivery_address | ✅ Preservada |
| RN-08: Pedido de balcão nasce em PREPARING sem PIX | ✅ Preservada (manager_create_order não tocado) |
| RN-13: KPIs do dashboard | ✅ Preservada com extensão (CONFIRMED incluído) |
| RN-14: process_new_order notifica restaurante | ✅ Preservada e reutilizada |

## Regras modificadas

| Regra | Alteração |
|-------|-----------|
| RN-XX (nova): `checkout()` cria Order com `status=PENDING` | Alterada: agora depende de `payment_method` — `CONFIRMED` para entrega, `PENDING` para online |
| RN-XX (nova): KPI `total_orders_pending` conta apenas `PENDING` | Alterada: agora conta `PENDING` + `CONFIRMED` |
