# Data Delta: Integração Real MercadoPago (Sandbox)

> Identificador: `017-mercadopago-sandbox`
> Data: `2026-06-02`
> Modelo de referência: `_reversa_sdd/erd-complete.md`

---

## 1. Mudanças no modelo

### Tabela `core_order` — campo novo

| Campo | Tipo Django | Tipo SQL | Nullable | Default | Motivo |
|-------|-------------|----------|----------|---------|--------|
| `customer_email` | `CharField(max_length=254, blank=True, default='')` | `VARCHAR(254) NOT NULL DEFAULT ''` | Não (default vazio) | `''` | Persistir email do guest para passar ao MP |

**Posição no modelo:** junto dos campos `customer_name` e `customer_phone` (linha ~111 de `core/models.py`).

---

## 2. Migração Django

```bash
python manage.py makemigrations core --name="add_customer_email_to_order"
python manage.py migrate
```

Arquivo esperado: `core/migrations/NNNN_add_customer_email_to_order.py`

Conteúdo gerado automaticamente pelo Django — nenhuma migration manual necessária.

**Compatibilidade com dados existentes:** `default=''` garante que rows existentes recebam string vazia. Sem `UPDATE` em massa, sem risco de lock em tabelas grandes.

---

## 3. Campos não afetados

Todos os demais campos de `Order` permanecem inalterados:
- `customer_name`, `customer_phone`, `delivery_address` — sem alteração
- `mp_payment_id`, `mp_preference_id` — sem alteração
- `status`, `total_amount`, `payment_method` — sem alteração

---

## 4. Sem novas tabelas

Esta feature não cria nenhuma nova tabela. Apenas o campo `customer_email` é adicionado à tabela existente `core_order`.
