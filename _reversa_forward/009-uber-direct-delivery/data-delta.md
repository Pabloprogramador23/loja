# Data Delta: 009-uber-direct-delivery

> Data: `2026-05-30`
> Base: `_reversa_sdd/data-dictionary.md`
> Migration alvo: `core/migrations/0011_uber_direct.py`

---

## Novo modelo: `UberDirectConfig`

Configuração Uber Direct por tenant. Opcional — lojas sem este registro não usam Uber Direct.

**Tabela:** `core_uberdirectconfig`
**Herda de:** `TenantAwareModel` (tem campo `store` + `TenantManager`)

| Campo | Tipo Django | Tipo DB | Obrigatório | Default | Constraints | Descrição |
|-------|-------------|---------|-------------|---------|-------------|-----------|
| `id` | `BigAutoField` | BIGINT | sim (PK) | auto | PK | — |
| `store` | `OneToOneField(Store)` | BIGINT | sim | — | FK CASCADE, UNIQUE, related_name=`uber_config` | Tenant proprietário (1:1) |
| `uber_store_id` | `CharField(255)` | VARCHAR(255) | sim | — | — | ID da loja no painel Uber Direct |
| `client_id` | `CharField(255)` | VARCHAR(255) | sim | — | — | OAuth2 client_id da conta Uber |
| `client_secret` | `CharField(255)` | VARCHAR(255) | sim | — | — | OAuth2 client_secret (armazenado em texto, mesma postura do MP token) |
| `webhook_signing_key` | `CharField(255)` | VARCHAR(255) | sim | — | — | Chave de assinatura HMAC para validação de webhooks |
| `is_active` | `BooleanField` | BOOLEAN | sim | `False` | — | Liga/desliga a integração sem deletar a config |
| `created_at` | `DateTimeField` | TIMESTAMP | sim | `auto_now_add` | — | — |
| `updated_at` | `DateTimeField` | TIMESTAMP | sim | `auto_now` | — | — |

**Nota:** `client_id` e `client_secret` são por tenant para suportar o modelo SaaS onde cada restaurante tem sua própria conta Uber Direct. Variáveis de ambiente globais (`UBER_CLIENT_ID`, `UBER_CLIENT_SECRET`) servem como fallback para desenvolvimento/sandbox.

---

## Novo modelo: `UberDirectDelivery`

Representa uma corrida de entrega no Uber Direct, vinculada a um pedido.

**Tabela:** `core_uberdirectdelivery`
**Herda de:** `TenantAwareModel`

| Campo | Tipo Django | Tipo DB | Obrigatório | Default | Constraints | Descrição |
|-------|-------------|---------|-------------|---------|-------------|-----------|
| `id` | `BigAutoField` | BIGINT | sim (PK) | auto | PK | — |
| `store` | `ForeignKey(Store)` | BIGINT | sim | — | FK CASCADE | Tenant (herdado) |
| `order` | `OneToOneField(Order)` | BIGINT | sim | — | FK CASCADE, UNIQUE, related_name=`uber_delivery` | Pedido associado |
| `uber_delivery_id` | `CharField(255)` | VARCHAR(255) | não | NULL | unique, null=True, blank=True | ID retornado pela Uber ao criar a entrega |
| `uber_quote_id` | `CharField(255)` | VARCHAR(255) | não | NULL | null=True, blank=True | Quote ID usado para criar a entrega |
| `fee` | `DecimalField(10,2)` | DECIMAL(10,2) | sim | `0.00` | — | Valor cobrado pela Uber (snapshot no momento do despacho) |
| `status` | `CharField(50)` | VARCHAR(50) | sim | `PENDING` | choices | Status atual da corrida (veja tabela abaixo) |
| `tracking_url` | `URLField(512)` | VARCHAR(512) | não | NULL | null=True, blank=True | URL pública de rastreamento da corrida |
| `dropoff_address` | `TextField` | TEXT | sim | — | — | Endereço de entrega (snapshot do Order.delivery_address) |
| `created_at` | `DateTimeField` | TIMESTAMP | sim | `auto_now_add` | — | — |
| `updated_at` | `DateTimeField` | TIMESTAMP | sim | `auto_now` | — | — |

**Status válidos (`UberDirectDelivery.Status` — TextChoices):**

| Valor | Label | Trigger |
|-------|-------|---------|
| `PENDING` | Pendente | Registro criado, aguardando confirmação Uber |
| `SCHEDULED` | Agendado | Uber confirmou a entrega |
| `EN_ROUTE_TO_PICKUP` | A caminho da coleta | Webhook: entregador a caminho do restaurante |
| `ARRIVED_AT_PICKUP` | No restaurante | Webhook: entregador chegou ao restaurante |
| `EN_ROUTE_TO_DROPOFF` | A caminho do cliente | Webhook: entregador saiu com o pedido → dispara `Order.status = DELIVERING` |
| `ARRIVED_AT_DROPOFF` | No endereço do cliente | Webhook: entregador chegou ao destino |
| `COMPLETED` | Entregue | Webhook: entrega concluída → dispara `Order.status = COMPLETED` |
| `FAILED` | Falhou | Webhook: falha na entrega |
| `CANCELED` | Cancelado | Cancelamento solicitado pelo Manager ou pela Uber |
| `RETURNED` | Devolvido | Webhook: entregador retornou à loja após não encontrar cliente |

---

## Novo modelo: `UberDirectDeliveryEvent`

Histórico de eventos de webhook recebidos — para auditoria, equivalente ao padrão de log do MercadoPago.

**Tabela:** `core_uberdirectdeliveryevent`

| Campo | Tipo Django | Tipo DB | Obrigatório | Default | Constraints | Descrição |
|-------|-------------|---------|-------------|---------|-------------|-----------|
| `id` | `BigAutoField` | BIGINT | sim (PK) | auto | PK | — |
| `delivery` | `ForeignKey(UberDirectDelivery)` | BIGINT | sim | — | FK CASCADE, related_name=`events` | Entrega associada |
| `event_type` | `CharField(100)` | VARCHAR(100) | sim | — | — | `event.delivery_status`, `event.courier_update`, etc. |
| `status_from` | `CharField(50)` | VARCHAR(50) | sim | `""` | blank=True | Status anterior |
| `status_to` | `CharField(50)` | VARCHAR(50) | sim | — | — | Novo status |
| `raw_payload` | `JSONField` | JSONB | sim | — | — | Payload completo do webhook para auditoria |
| `created_at` | `DateTimeField` | TIMESTAMP | sim | `auto_now_add` | — | — |

---

## Alteração em modelo existente: `Order`

Campo adicional para rastreabilidade da cotação Uber usada no checkout.

| Campo | Tipo Django | Tipo DB | Obrigatório | Default | Constraints | Descrição |
|-------|-------------|---------|-------------|---------|-------------|-----------|
| `uber_quote_id` | `CharField(255)` | VARCHAR(255) | não | `""` | blank=True | Quote ID Uber utilizado neste pedido (vazio se não Uber Direct) |

**Nota:** O `Order.delivery_fee` (feature 007) continua sendo o snapshot da taxa. Para pedidos Uber Direct, seu valor é populado com `UberDirectDelivery.fee`. Nenhum campo existente é alterado ou removido.

---

## Script de migração (esqueleto)

```python
# core/migrations/0011_uber_direct.py
class Migration(migrations.Migration):
    dependencies = [
        ('core', '0010_store_delivery_fee_order_delivery_fee'),
    ]
    operations = [
        migrations.CreateModel('UberDirectConfig', fields=[...]),
        migrations.CreateModel('UberDirectDelivery', fields=[...]),
        migrations.CreateModel('UberDirectDeliveryEvent', fields=[...]),
        migrations.AddField(
            model_name='order',
            name='uber_quote_id',
            field=models.CharField(max_length=255, blank=True, default=''),
        ),
    ]
```

---

## Índices recomendados

| Tabela | Campo(s) | Tipo | Justificativa |
|--------|----------|------|---------------|
| `core_uberdirectdelivery` | `uber_delivery_id` | UNIQUE (já em constraints) | Lookup por ID Uber no webhook |
| `core_uberdirectdelivery` | `order_id` | UNIQUE (já em OneToOne) | Join Order → Delivery |
| `core_uberdirectdeliveryevent` | `delivery_id` | B-tree | Listagem de histórico por entrega |
