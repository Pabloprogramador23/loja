# Data Delta: 013-checkout-pro-mp

> Data: `2026-05-30`

## Novo campo no model Order

```python
# core/models.py — dentro da classe Order
mp_preference_id = models.CharField(
    max_length=255,
    blank=True,
    default='',
    db_index=True,
)
```

**Motivo:** Rastreabilidade entre o pedido e a preference MP. Útil para debug e para o painel do manager. Não é usado no lookup do webhook (que usa `external_reference` → `order.id`).

## Migration: `0013_order_mp_preference_id`

```python
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0012_userprofile'),
    ]
    operations = [
        migrations.AddField(
            model_name='order',
            name='mp_preference_id',
            field=models.CharField(blank=True, db_index=True, default='', max_length=255),
        ),
    ]
```

## Novo setting

```python
# store_saas/settings.py
SITE_URL = config('SITE_URL', default='http://localhost:8000')
```

Adicionar também em `.env`:
```
SITE_URL=http://localhost:8000
```

E em `.env.prod`:
```
SITE_URL=https://seu-dominio.com
```

## Estrutura da preference MP

```python
preference_data = {
    "items": [
        {
            "id": str(item.product.id),
            "title": item.product.name,
            "quantity": item.quantity,
            "unit_price": float(item.unit_price),
            "currency_id": "BRL",
        }
        for item in order.items.all()
    ],
    "payer": {
        "email": order.user.email,
        "name": order.user.get_full_name() or order.user.username,
    },
    "back_urls": {
        "success": f"{SITE_URL}/payment/success/",
        "pending": f"{SITE_URL}/payment/pending/",
        "failure": f"{SITE_URL}/payment/failure/",
    },
    "auto_return": "approved",
    "external_reference": str(order.id),
    "statement_descriptor": order.store.name[:22],  # MP limita a 22 chars
}
```

## Models não alterados

`UserProfile`, `Store`, `Address`, `UberDirectConfig`, `UberDirectDelivery` — sem alteração.
