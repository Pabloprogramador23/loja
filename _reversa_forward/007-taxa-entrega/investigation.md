# Investigation: Taxa de Entrega por Restaurante

> Identificador: `007-taxa-entrega`
> Data: `2026-05-30`

---

## Padrões aplicados do legado

### Snapshot de valor no pedido
O sistema já usa snapshot em `OrderItem.unit_price` (`core/models.py`, confirmado em `_reversa_sdd/domain.md#RN-07`). A decisão de replicar o padrão em `Order.delivery_fee` é direta — sem nova abstração.

### Context processor global
`core/context_processors.py` já injeta `cart` em todos os templates via `TEMPLATES[0]['OPTIONS']['context_processors']`. Adicionar variáveis de taxa nesse mesmo ponto é o caminho de menor resistência e alinha com o padrão existente.

### StoreSettings form
`core/forms.py` já tem `StoreSettings` form e a view `manager_settings` já salva campos de configuração da loja. Estender o form com dois campos novos não requer nova view nem nova rota.

---

## Alternativas avaliadas e descartadas

| Alternativa | Por que descartada |
|-------------|-------------------|
| Calcular taxa de entrega no frontend (JS) | Fácil de manipular; `total_amount` enviado ao MP teria que ser recalculado no backend de qualquer forma |
| Campo booleano `free_delivery_active` separado do threshold | Dois campos para uma informação: `free_delivery_threshold IS NULL` já codifica o estado desativado |
| Novo modelo `DeliveryConfig` (FK para `Store`) | Over-engineering para um único valor por loja; `Store` é o lugar natural para configurações da loja |
| Taxa calculada dinamicamente sem snapshot | Perde rastreabilidade histórica; não segue o padrão estabelecido no legado |

---

## Pontos de atenção

### Decimal vs float
`cart.get_total_price()` já retorna `Decimal` (código em `core/cart.py`). Todos os cálculos de taxa devem usar `Decimal` para evitar imprecisão. A comparação com `free_delivery_threshold` deve ser `Decimal >= Decimal`.

### HTMX e contexto de taxa no carrinho
O `cart_drawer.html` é trocado via HTMX swap. O context processor injeta dados no contexto da view que responde ao HTMX request — desde que a view chame `render()` com o contexto completo, as variáveis de taxa estarão disponíveis. Verificar que a view que serve o drawer (provavelmente `add_to_cart` ou `cart_detail`) passa o contexto global corretamente.

### `transaction_amount` no MercadoPago
`payment.py` usa `float(order.total_amount)` para montar o payload do PIX. Com a taxa embutida em `total_amount`, o valor enviado ao MP aumenta automaticamente — sem mudança de código em `payment.py`.

### Pedido de balcão e total recalculado
Em `manager_create_order`, o total é recalculado somando `product.price * quantity` (sem snapshots). O campo `delivery_fee=0.00` deve ser passado explicitamente no `Order.objects.create(...)` para garantir que balcão nunca cobre taxa, mesmo que a loja tenha `delivery_fee > 0`.

---

## Referências internas

| Artefato | Seção relevante |
|----------|----------------|
| `_reversa_sdd/domain.md` | RN-04 (checkout), RN-07 (snapshot), RN-08 (balcão) |
| `_reversa_sdd/code-analysis.md` | 2.2 (cart), 2.3 (checkout), 2.4 (payment), 2.7 (manager) |
| `_reversa_sdd/erd-complete.md` | STORE, ORDER |
