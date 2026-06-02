# Data Delta: 004-painel-restaurante

> Data: `2026-05-27`
> Fonte base: `_reversa_sdd/erd-complete.md`, `core/models.py`

## Modelo: `Order`

### Campos novos

| Campo | Tipo Django | Parâmetros | Valor padrão | Obrigatório | Motivo |
|-------|-------------|------------|--------------|-------------|--------|
| `table_label` | `CharField` | `max_length=100, blank=True, default=''` | `''` (string vazia) | Não (para pedidos comuns) | Identificador textual da comanda ("Mesa 3", "Varanda", etc.) |

### Valores novos em TextChoices

Campo: `Order.status` (`CharField`, `max_length=20`)

| Valor (DB) | Label | Posição na sequência | Usado por |
|------------|-------|---------------------|-----------|
| `OPEN` | `Comanda Aberta` | Antes de `PENDING` (início lógico do ciclo de comanda) | `comanda_create`, `comanda_add_item`, `comanda_remove_item` |

**Máquina de estados atualizada:**

```
[início] → OPEN       via comanda_create (novo)
OPEN     → PREPARING  via comanda_close(presencial) (novo)
OPEN     → PENDING    via comanda_close(pix) (novo)
OPEN     → CANCELED   via update_order_status (existente — não bloquear)

[início] → PENDING    via checkout() (inalterado)
[início] → PREPARING  via manager_create_order() (inalterado)
PENDING  → PREPARING  via webhook (inalterado)
... demais transições inalteradas
```

### Nenhum campo removido

Nenhum campo existente é alterado ou removido.

## Migration

**Arquivo:** `core/migrations/0008_order_comanda_fields.py`

```python
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0007_store_owner'),  # última migration existente
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='table_label',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
```

> **Nota:** Adicionar `OPEN` ao `Status` TextChoices não gera operação de migration no Django (`CharField` com `choices` não cria constraint DB). A migration acima cobre apenas o novo campo `table_label`.

## Impacto em queries existentes

| Query / View | Impacto | Ação necessária |
|---|---|---|
| `manager_orders` — lista todos os pedidos do tenant | Comandas `OPEN` aparecerão na lista de pedidos | Adicionar filtro `exclude(status='OPEN')` para não poluir o dashboard de pedidos com comandas abertas |
| `dashboard` KPIs (`PENDING`, `COMPLETED`, `today`) | Comandas `OPEN` não contam como `PENDING` nem `COMPLETED` — sem impacto nos KPIs atuais | Nenhuma |
| `order_track` — rastreamento público | Não expõe comandas `OPEN` pois exige `order_id` explícito | Nenhuma (baixo risco) |
| `account_orders` — pedidos do cliente | Comandas `OPEN` têm `user=None` — não aparecem na lista do cliente | Nenhuma |

## Sem novas tabelas

O sistema de comandas não cria novas tabelas. Reutiliza `core_order` e `core_orderitem` com os campos e relacionamentos existentes.
