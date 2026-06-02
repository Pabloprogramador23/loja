# Data Delta: Correções de Segurança (Revisor)

> Identificador: `001-correcoes-seguranca-revisor`
> Data: `2026-05-26`
> Fonte ERD: `_reversa_sdd/erd-complete.md`

## Sumário de mudanças

| Tabela | Operação | Campo | Tipo |
|--------|----------|-------|------|
| `core_order` | ADD COLUMN | `mp_payment_id` | VARCHAR(64), NULL, UNIQUE, INDEX |

---

## Detalhamento: `core_order.mp_payment_id`

### Definição Django (models.py)

```python
mp_payment_id = models.CharField(
    max_length=64,
    null=True,
    blank=True,
    unique=True,
    db_index=True,
)
```

### Rationale de cada atributo

| Atributo | Valor | Razão |
|----------|-------|-------|
| `max_length=64` | 64 chars | IDs do MercadoPago são numéricos longos (ex: `1234567890`); 64 é margem segura |
| `null=True` | True | Orders de balcão e orders não-pagas não têm payment_id |
| `blank=True` | True | Formulário/admin: campo opcional em criação manual |
| `unique=True` | True | Um payment_id MP corresponde a exatamente uma Order; previne processar o mesmo webhook duas vezes |
| `db_index=True` | True | Webhook lookup é `Order.objects.get(mp_payment_id=id)` — deve ser O(log n) |

### SQL gerado (PostgreSQL)

```sql
ALTER TABLE core_order ADD COLUMN mp_payment_id VARCHAR(64) NULL;
CREATE UNIQUE INDEX core_order_mp_payment_id_uniq ON core_order (mp_payment_id) WHERE mp_payment_id IS NOT NULL;
```

> Nota: Django gera o índice parcial automaticamente quando `unique=True` + `null=True` em PostgreSQL moderno.

### Impacto em dados existentes

| Cenário | Comportamento |
|---------|---------------|
| Orders já existentes (antes da migration) | `mp_payment_id = NULL` — sem impacto |
| Orders PENDING sem PIX criado | `mp_payment_id = NULL` até `create_pix_payment()` ser chamado |
| Orders PREPARING/pagas antes desta feature | `mp_payment_id = NULL` — webhook já processou, não haverá re-notificação |
| Orders criadas após esta feature | `mp_payment_id` preenchido no retorno do `sdk.payment().create()` |

### Migration Django

```bash
python manage.py makemigrations core --name add_mp_payment_id_to_order
python manage.py migrate
```

Arquivo gerado: `core/migrations/000X_add_mp_payment_id_to_order.py`

---

## Campos NÃO alterados nesta feature

| Tabela | Campo | Motivo de manter |
|--------|-------|-----------------|
| `core_order` | `customer_name`, `customer_phone`, `delivery_address` | Sem alteração |
| `core_order` | `status`, `total_amount` | Máquina de estados e estorno são lógica de view/task, não de schema |
| `core_store` | `mercadopago_access_token` | Já existe; apenas passa a ser usado no webhook (antes usava `settings.MERCADOPAGO_ACCESS_TOKEN`) |

---

## Campos que PODERIAM ser adicionados (fora do escopo desta feature)

| Campo sugerido | Tabela | Justificativa para futuro |
|----------------|--------|--------------------------|
| `customer_email` em `Order` | `core_order` | Persistir o email do convidado para rastreio; atualmente só vai para o MP no PIX |
| `refund_id` | `core_order` | ID do estorno no MP para rastrear tentativas de refund |

---

*Escala de confiança: 🟢 CONFIRMADO — 🟡 INFERIDO — 🔴 LACUNA*
