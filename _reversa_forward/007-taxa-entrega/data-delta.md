# Data Delta: Taxa de Entrega por Restaurante

> Identificador: `007-taxa-entrega`
> Data: `2026-05-30`
> Fonte base: `_reversa_sdd/erd-complete.md` (🟢 CONFIRMADO)

---

## Resumo

| Modelo | Operação | Campo(s) |
|--------|----------|---------|
| `Store` | ADD | `delivery_fee`, `free_delivery_threshold` |
| `Order` | ADD | `delivery_fee` |
| Demais modelos | sem alteração | — |

---

## `Store` — campos novos

### `delivery_fee`

| Atributo | Valor |
|----------|-------|
| Tipo Django | `DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))` |
| Tipo DB | `DECIMAL(10, 2)` |
| Nulo | não |
| Default | `0.00` |
| Validação | `MinValueValidator(0)` |
| Semântica | Taxa de entrega fixa cobrada em todos os pedidos online da loja. `0.00` = entrega gratuita. |

### `free_delivery_threshold`

| Atributo | Valor |
|----------|-------|
| Tipo Django | `DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None)` |
| Tipo DB | `DECIMAL(10, 2)` nullable |
| Nulo | sim |
| Default | `None` (feature desativada) |
| Validação | `MinValueValidator(0)` quando não nulo |
| Semântica | Quando definido e `subtotal_itens >= threshold`, a `delivery_fee` efetiva é `0.00`. `None` = recurso desativado. |

---

## `Order` — campo novo

### `delivery_fee`

| Atributo | Valor |
|----------|-------|
| Tipo Django | `DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))` |
| Tipo DB | `DECIMAL(10, 2)` |
| Nulo | não |
| Default | `0.00` |
| Semântica | **Snapshot** do valor de entrega cobrado no momento da criação do pedido. Imutável após `Order.objects.create(...)`. Segue o padrão de `OrderItem.unit_price`. |
| Fonte do valor | Calculado no `checkout()` com base em `Store.delivery_fee` e `Store.free_delivery_threshold` no momento da compra. Pedidos de balcão sempre `0.00`. |

---

## Migration esperada

**Nome provável:** `core/migrations/0010_store_delivery_fee_order_delivery_fee.py`

**Operações:**
```python
migrations.AddField(
    model_name='store',
    name='delivery_fee',
    field=models.DecimalField(
        max_digits=10, decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)]
    ),
),
migrations.AddField(
    model_name='store',
    name='free_delivery_threshold',
    field=models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True, default=None,
        validators=[MinValueValidator(0)]
    ),
),
migrations.AddField(
    model_name='order',
    name='delivery_fee',
    field=models.DecimalField(
        max_digits=10, decimal_places=2,
        default=Decimal('0.00')
    ),
),
```

**Impacto em dados existentes:**
- Lojas existentes: `delivery_fee = 0.00`, `free_delivery_threshold = None` → sem mudança de comportamento
- Pedidos existentes: `delivery_fee = 0.00` → histórico de totais inalterado (o `total_amount` já gravado não muda)

---

## ERD delta (fragmento)

```
STORE {
    ...
    + decimal delivery_fee           -- default 0.00
    + decimal free_delivery_threshold -- nullable, default null
}

ORDER {
    ...
    + decimal delivery_fee           -- snapshot, default 0.00
}
```

---

## Lógica de cálculo (pseudo-código no checkout)

```python
store = request.tenant
subtotal = cart.get_total_price()          # Decimal, já existente

threshold = store.free_delivery_threshold  # None ou Decimal
if threshold is not None and subtotal >= threshold:
    effective_fee = Decimal('0.00')
else:
    effective_fee = store.delivery_fee     # Decimal, default 0.00

total = subtotal + effective_fee

# Dentro de transaction.atomic():
order = Order.objects.create(
    ...
    total_amount=total,
    delivery_fee=effective_fee,            # snapshot
)
```

---

*Escala de confiança: 🟢 CONFIRMADO — 🟡 INFERIDO — 🔴 LACUNA*
