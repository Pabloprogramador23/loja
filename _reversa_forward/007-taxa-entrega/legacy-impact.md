# Legacy Impact: Taxa de Entrega por Restaurante

> Identificador: `007-taxa-entrega`
> Data: `2026-05-30`
> Componentes afetados: `Store`, `Order`, `checkout()`, `manager_create_order()`, context processor, 4 templates

---

## Arquivos afetados

| Arquivo afetado | Componente (`_reversa_sdd/`) | Tipo | Severidade | Justificativa |
|-----------------|------------------------------|------|------------|---------------|
| `core/models.py` | `_reversa_sdd/erd-complete.md#STORE` | delta-de-dados | MEDIUM | 2 campos novos em `Store`: `delivery_fee` e `free_delivery_threshold` |
| `core/models.py` | `_reversa_sdd/erd-complete.md#ORDER` | delta-de-dados | MEDIUM | 1 campo novo em `Order`: `delivery_fee` (snapshot) |
| `core/migrations/0010_*.py` | — | delta-de-dados | LOW | Migration backward-compatible; defaults garantem sem impacto em dados existentes |
| `core/forms.py` | `_reversa_sdd/code-analysis.md#2.7` | regra-alterada | LOW | `StoreSettingsForm` aceita e persiste os 2 novos campos |
| `core/views.py` | `_reversa_sdd/code-analysis.md#2.3` | regra-alterada | HIGH | `checkout()` passa a calcular `effective_fee` e snapshot em `Order.delivery_fee`; `total_amount` agora inclui a taxa |
| `core/views.py` | `_reversa_sdd/code-analysis.md#2.7` | regra-alterada | LOW | `manager_create_order()` força `delivery_fee=0.00` explicitamente |
| `core/context_processors.py` | `_reversa_sdd/code-analysis.md#Módulo 2` | regra-alterada | LOW | Contexto de template enriquecido com 4 variáveis de taxa |
| `templates/core/partials/cart_drawer.html` | `_reversa_sdd/inventory.md#partials` | regra-alterada | MEDIUM | Drawer agora exibe subtotal + taxa separados; total via `cart_total_with_fee` |
| `templates/core/manager/settings.html` | `_reversa_sdd/inventory.md#Templates` | regra-nova | LOW | Seção de configuração de taxa de entrega adicionada |
| `templates/core/account/order_detail.html` | `_reversa_sdd/inventory.md#Templates` | regra-nova | LOW | Linha de taxa de entrega exibida no detalhe do pedido |
| `templates/core/account/orders.html` | `_reversa_sdd/inventory.md#Templates` | regra-nova | LOW | Anotação de taxa de entrega na lista de pedidos |

---

## Diff conceitual por componente

### `Store` (modelo)
Dois campos opcionais adicionados. Ambos com default que preserva comportamento anterior (`delivery_fee=0.00`, `free_delivery_threshold=None`). Nenhuma loja existente tem comportamento alterado sem ação do Manager.

### `Order` (modelo)
Campo `delivery_fee` adicionado com `default=Decimal('0.00')`. Pedidos existentes no banco recebem `0.00` — histórico preservado sem distorção.

### `checkout()` (view)
**Regra RN-04 alterada:** além de validar `name`, `phone` e `address`, agora calcula `effective_fee` antes do `transaction.atomic()` e inclui esse valor no `Order.objects.create()`. O `total_amount` enviado ao MercadoPago agora pode ser maior que o subtotal dos itens.

### `manager_create_order()` (view)
**Regra RN-08 reforçada:** `delivery_fee=Decimal('0.00')` explícito impede que configuração futura da loja vaze para pedidos de balcão.

### Context processor `cart`
Antes retornava apenas `{'cart': cart_obj}`. Agora retorna também `store_delivery_fee`, `free_delivery_threshold`, `effective_delivery_fee`, `cart_total_with_fee` e `threshold_gap`. Todos os templates que usavam `cart` continuam funcionando; as novas variáveis são aditivas.

---

## Regras preservadas

| Regra | Origem | Status |
|-------|--------|--------|
| RN-01: Isolamento de tenant | `_reversa_sdd/domain.md#RN-01` | ✅ Preservada — taxa lida de `request.tenant` |
| RN-03: Auto-atribuição de tenant em save | `_reversa_sdd/domain.md#RN-03` | ✅ Preservada — sem alteração em `TenantAwareModel.save()` |
| RN-05: Guest checkout e vinculação | `_reversa_sdd/domain.md#RN-05` | ✅ Preservada — lógica de `guest_order_id` intacta |
| RN-06: Limite de 3 endereços | `_reversa_sdd/domain.md#RN-06` | ✅ Preservada — sem toque em `Address` |
| RN-07: Snapshot de preço no OrderItem | `_reversa_sdd/domain.md#RN-07` | ✅ Preservada — `OrderItem.unit_price` não tocado |
| RN-09: Token MP por tenant | `_reversa_sdd/domain.md#RN-09` | ✅ Preservada — `payment.py` não tocado |
| RN-12: Acesso ao dashboard | `_reversa_sdd/domain.md#RN-12` | ✅ Preservada — guard `user_can_manage_store` intacto |
| RN-19: Preferência de tema | `_reversa_sdd/domain.md#RN-19` | ✅ Preservada — `UserSettings` não tocado |

---

## Regras modificadas

| Regra | Origem | Natureza da mudança |
|-------|--------|---------------------|
| RN-04: Checkout requer nome, telefone e endereço | `_reversa_sdd/domain.md#RN-04` | **Ampliada** — `total_amount` agora = subtotal + `effective_delivery_fee`; `delivery_fee` snapshot gravado |
| RN-08: Pedido de balcão sem PIX | `_reversa_sdd/domain.md#RN-08` | **Reforçada** — `delivery_fee=0.00` explícito no create; semântica preservada, implementação enrijecida |
