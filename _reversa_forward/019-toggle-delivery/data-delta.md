# Data Delta: Toggle Delivery

> Feature: `019-toggle-delivery`
> Data: `2026-06-04`

---

## Alterações no modelo `Store`

### Campo novo

```python
delivery_enabled = models.BooleanField(
    default=True,
    help_text="Quando False, a loja não aceita novos pedidos online."
)
```

| Atributo | Valor |
|----------|-------|
| Tipo | `BooleanField` |
| `default` | `True` |
| `null` | `False` (não-nulo) |
| `blank` | `False` |
| Índice | Não necessário (lido por request, não filtrado em bulk) |

### Migration

**Nome:** `0017_store_delivery_enabled`

```python
migrations.AddField(
    model_name='store',
    name='delivery_enabled',
    field=models.BooleanField(
        default=True,
        help_text='Quando False, a loja não aceita novos pedidos online.'
    ),
)
```

- Migration não-destrutiva: apenas `ADD COLUMN` com default
- Todas as lojas existentes recebem `delivery_enabled=True` automaticamente
- Zero downtime; sem backfill necessário

---

## Campos removidos

Nenhum.

---

## Impacto em queries existentes

Nenhuma query existente é afetada. O campo é lido apenas em:
1. `context_processors.cart()` — uma leitura por request
2. `views.checkout()` — uma leitura por POST de checkout
3. `views.toggle_delivery_view()` — uma leitura + uma escrita por clique do manager
