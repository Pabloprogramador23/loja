# Interface: Uber Direct — Criação e Cancelamento de Entrega

> Contrato: HTTP REST (cliente — o sistema chama a API Uber)
> Disparado pela view Django `request_uber_delivery()` (staff-only)

---

## 1. Criar Entrega

**Método:** `POST`
**URL:** `https://api.uber.com/v1/customers/{customer_id}/deliveries`
**Auth:** `Authorization: Bearer {oauth2_token}`

### Request

```json
{
  "estimate_id": "dqt_AI6aDfhsSNqsVNTG03QKxg",
  "external_order_id": "LOJA_PEDIDO_98765",
  "pickup": {
    "location": {
      "address": "Endereço do restaurante (Store)"
    },
    "contact": {
      "name": "Nome do Restaurante",
      "phone": "+5511999998888"
    }
  },
  "dropoff": {
    "location": {
      "address": "Endereço do cliente (Order.delivery_address)"
    },
    "contact": {
      "name": "Nome do cliente (Order.customer_name)",
      "phone": "+5511977776666"
    },
    "dropoff_notes": ""
  },
  "order_items": [
    {
      "name": "Nome do produto",
      "quantity": 1,
      "price": 3500,
      "currency_code": "BRL"
    }
  ],
  "order_summary": {
    "total_value": 3500,
    "currency_code": "BRL"
  }
}
```

| Campo | Fonte no sistema |
|-------|-----------------|
| `estimate_id` | `Order.uber_quote_id` (salvo no checkout) |
| `external_order_id` | `f"LOJA_PEDIDO_{order.id}"` |
| `pickup.contact.phone` | `UberDirectConfig.store_phone` ou `Store` — 🔴 campo a definir no modelo |
| `dropoff.contact.name` | `Order.customer_name` |
| `dropoff.contact.phone` | `Order.customer_phone` normalizado para E.164 |
| `order_items[*].price` | `OrderItem.unit_price * 100` (centavos) |
| `order_summary.total_value` | `Order.total_amount * 100` (centavos) |

**Nota:** preços são enviados em centavos (inteiros). `R$ 35,00 → 3500`.

### Response de sucesso (HTTP 200)

```json
{
  "id": "del_XPTO123",
  "status": "pending",
  "tracking_url": "https://track.uber.com/abc123",
  "fee": {
    "value": 850,
    "currency_code": "BRL"
  }
}
```

| Campo | Mapeamento |
|-------|-----------|
| `id` | `UberDirectDelivery.uber_delivery_id` |
| `status` | `UberDirectDelivery.status = PENDING` (inicial) |
| `tracking_url` | `UberDirectDelivery.tracking_url` |

### Erros relevantes

| HTTP | Situação | Ação |
|------|----------|------|
| 400 `estimate_expired` | Quote TTL expirado | Retornar erro ao Manager: "Cotação expirada. Solicite nova cotação." |
| 400 `estimate_already_used` | Quote já usado | Verificar se `UberDirectDelivery` já existe para o Order |
| 401 | Token expirado | Renovar token e retry 1× |
| 422 | Dados inválidos (telefone, endereço) | Logar campos inválidos; exibir mensagem ao Manager |
| 5xx | Falha Uber | Exibir "Falha ao acionar entrega Uber. Tente novamente." |

---

## 2. Cancelar Entrega

**Método:** `POST`
**URL:** `https://api.uber.com/v1/customers/{customer_id}/deliveries/{delivery_id}/cancel`
**Auth:** `Authorization: Bearer {oauth2_token}`
**Body:** vazio `{}`

### Pré-condição

Cancelamento só disponível quando `UberDirectDelivery.status` ∈ {`PENDING`, `SCHEDULED`}. Após `EN_ROUTE_TO_PICKUP`, sujeito a taxa de cancelamento (responsabilidade do restaurante — fora do escopo desta feature).

### Response de sucesso (HTTP 200)

```json
{}
```

Resposta vazia confirma o cancelamento.

### Após cancelamento no sistema

1. `UberDirectDelivery.status = CANCELED`
2. `Order.status` permanece `PREPARING` (Manager pode solicitar novo despacho ou encerrar manualmente)
3. Log de evento em `UberDirectDeliveryEvent`

### Erros relevantes

| HTTP | Situação | Ação |
|------|----------|------|
| 400 `already_canceled` | Já cancelado | Atualizar status local se divergente |
| 400 `cannot_cancel` | Muito tarde (entregador a caminho) | Exibir "Cancelamento não permitido neste estágio" |
| 404 | Delivery não encontrado | Erro de consistência — logar e alertar |

---

## 3. Consultar Status (polling opcional)

**Método:** `GET`
**URL:** `https://api.uber.com/v1/customers/{customer_id}/deliveries/{delivery_id}`

Usado apenas como fallback se um webhook não for recebido. Não é o mecanismo principal — webhooks são o padrão.

**Idempotência:** GET é idempotente por natureza.
**Timeout configurado:** 10 segundos para criação/cancelamento; 5 segundos para polling.
