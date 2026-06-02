# Regression Watch: 014-pagamento-entrega

> Feature: Pagamento na Entrega
> Gerado em: 2026-05-31

## Watch Items

| ID | Origem | Regra esperada após mudança | Tipo | Sinal de violação |
|----|--------|-----------------------------|------|-------------------|
| W001 | `core/views.py — checkout()` | Pedido criado com `payment_method=cash` ou `card` tem `status=CONFIRMED` e `process_new_order.delay()` é chamado; sem chamada a `create_checkout_pro_preference()` | presença | Se extração futura mostrar que `checkout()` chama MP para pedidos na entrega, ou que `status=PENDING` é atribuído para payment_method≠online |
| W002 | `core/views.py — checkout()` | Pedido criado com `payment_method=online` (ou ausente) tem `status=PENDING` e `create_checkout_pro_preference()` é chamada normalmente | presença | Se `checkout()` deixar de chamar MP para pedidos online; regressão da feature 013 |
| W003 | `core/views.py — dashboard()` | `total_orders_pending` filtra `status__in=[PENDING, CONFIRMED]` | redação | Se extração futura mostrar `filter(status=PENDING)` — indicaria que a alteração foi revertida |
| W004 | `core/models.py — Order.Status` | Enum contém `CONFIRMED = 'CONFIRMED', 'Confirmado'` entre `PENDING` e `PREPARING` | presença | Se `CONFIRMED` sumir do enum em extração futura |
| W005 | `core/models.py — Order` | Campos `payment_method`, `change_amount`, `card_type` presentes no model | presença | Se algum dos três campos sumir da extração do model `Order` |

## Observações (🟡 INFERIDO — sem peso de regressão)

- A view `update_order_status()` não valida transições de estado. `CONFIRMED → PREPARING` via manager funciona porque o manager pode avançar qualquer status. Se uma futura feature adicionar guard de transições, `CONFIRMED → PREPARING` precisa ser explicitamente permitido.
- `check_order_status()` em `core/api.py` não inclui `CONFIRMED` em `paid_statuses`. Pedidos na entrega não acessam esse endpoint, mas se o polling de status do cliente for reutilizado para outro fluxo no futuro, esta lacuna pode surgir.

## Histórico de re-extrações

<!-- Preenchido automaticamente pelo /reversa quando re-executado -->

## Arquivadas

<!-- IDs de watch items encerrados em extrações futuras -->
