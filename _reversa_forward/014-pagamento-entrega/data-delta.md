# Data Delta: 014-pagamento-entrega

> Data: `2026-05-30`

## Alterações no model Order

### Novo valor no enum Order.Status

```python
class Status(models.TextChoices):
    OPEN = 'OPEN', 'Comanda Aberta'
    PENDING = 'PENDING', 'Pendente'
    CONFIRMED = 'CONFIRMED', 'Confirmado'      # NOVO
    PREPARING = 'PREPARING', 'Preparando'
    DELIVERING = 'DELIVERING', 'Em trânsito'
    COMPLETED = 'COMPLETED', 'Concluído'
    CANCELED = 'CANCELED', 'Cancelado'
```

### Novos campos

```python
class PaymentMethod(models.TextChoices):
    ONLINE = 'online', 'Online (MP)'
    CASH = 'cash', 'Dinheiro'
    CARD = 'card', 'Cartão na Maquininha'

class CardType(models.TextChoices):
    CREDIT = 'credit', 'Crédito'
    DEBIT = 'debit', 'Débito'

payment_method = models.CharField(
    max_length=10,
    choices=PaymentMethod.choices,
    default=PaymentMethod.ONLINE,
)
change_amount = models.DecimalField(
    max_digits=10, decimal_places=2,
    null=True, blank=True,
    help_text='Valor para troco quando payment_method=cash. None = sem troco necessário.',
)
card_type = models.CharField(
    max_length=10,
    choices=CardType.choices,
    blank=True, default='',
    help_text='Tipo de cartão quando payment_method=card.',
)
```

**Nota:** `PaymentMethod` e `CardType` podem ser classes aninhadas em `Order` ou classes top-level. Classes aninhadas são mais comuns no padrão Django para choices.

## Migration: `0014_order_payment_fields`

```python
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0013_order_mp_preference_id'),
    ]
    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.CharField(
                choices=[('online', 'Online (MP)'), ('cash', 'Dinheiro'), ('card', 'Cartão na Maquininha')],
                default='online', max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='change_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='card_type',
            field=models.CharField(
                blank=True, default='',
                choices=[('credit', 'Crédito'), ('debit', 'Débito')],
                max_length=10,
            ),
        ),
    ]
```

**Nota sobre `CONFIRMED` no enum:** enums Django `TextChoices` não geram migrations — são apenas validação Python. Adicionar `CONFIRMED` ao enum não requer migration; apenas atualiza o código.

## Retrocompatibilidade

Orders históricos: `payment_method` receberá `'online'` (default da migration). `change_amount` = None. `card_type` = `''`. Todos compatíveis com as novas constraints.
