# Data Delta: Toggle de Métodos de Pagamento

> Identificador: `024-toggle-metodos-pagamento`
> Data: `2026-06-08`
> Fonte do legado: `core/models.py#Store`, `_reversa_sdd/erd-complete.md`

---

## 1. Entidades afetadas

### `Store` — três campos novos

| Campo | Tipo Django | Default | Null | Blank | Help text |
|-------|-------------|---------|------|-------|-----------|
| `payment_online_enabled` | `BooleanField` | `True` | não | não | `"Aceitar pagamento online via MercadoPago (PIX/Checkout Pro)."` |
| `payment_cash_enabled` | `BooleanField` | `True` | não | não | `"Aceitar pagamento em dinheiro na entrega."` |
| `payment_card_enabled` | `BooleanField` | `True` | não | não | `"Aceitar pagamento com cartão na maquininha."` |

**Posição recomendada no model:** após `delivery_enabled` (linha ~41 em `core/models.py`), agrupando todos os campos de configuração de operação.

**Sem alteração em:** `Order`, `OrderItem`, `PaymentMethod` choices (os valores `online`, `cash`, `card` são mantidos intactos — apenas a *disponibilidade* muda, não o vocabulário).

---

## 2. Migration

**Nome sugerido:** `core/migrations/XXXX_store_payment_method_toggles.py`

**Tipo:** `AddField` × 3 — non-destructive, retrocompatível.

```python
# Conteúdo esperado da migration (gerado via makemigrations)
operations = [
    migrations.AddField(
        model_name='store',
        name='payment_online_enabled',
        field=models.BooleanField(
            default=True,
            help_text='Aceitar pagamento online via MercadoPago (PIX/Checkout Pro).'
        ),
    ),
    migrations.AddField(
        model_name='store',
        name='payment_cash_enabled',
        field=models.BooleanField(
            default=True,
            help_text='Aceitar pagamento em dinheiro na entrega.'
        ),
    ),
    migrations.AddField(
        model_name='store',
        name='payment_card_enabled',
        field=models.BooleanField(
            default=True,
            help_text='Aceitar pagamento com cartão na maquininha.'
        ),
    ),
]
```

**Efeito em dados existentes:** lojas já cadastradas recebem `True` nos três campos — comportamento idêntico ao atual (todos os métodos disponíveis). Sem intervenção manual do manager.

---

## 3. Sem mudança no schema de `Order`

`Order.payment_method` continua com os mesmos choices (`online`, `cash`, `card`). O campo registra *qual método foi usado* — a nova feature controla *quais métodos estão disponíveis*, não modifica o registro histórico.

---

## 4. Índices

Nenhum índice novo necessário. Os três campos são consultados apenas em `request.tenant` (objeto já carregado em memória pelo middleware) — não são usados em queries de listagem ou filtro.

---

## 5. Admin Django

Os três campos aparecem automaticamente no Django Admin para `Store` após a migration. Nenhuma configuração adicional necessária no `admin.py`.
