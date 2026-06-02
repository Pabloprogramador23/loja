# Interface: Uber Direct — Cotação de Frete (Quote)

> Contrato: HTTP REST (cliente — o sistema chama a API Uber)
> Endpoint interno que expõe esta cotação ao front: `POST /api/uber-direct/quote` (FastAPI)

---

## Endpoint Uber Direct (externo)

**Método:** `POST`
**URL:** `https://api.uber.com/v1/customers/{customer_id}/delivery_quotes`
**Auth:** `Authorization: Bearer {oauth2_token}`
**Content-Type:** `application/json`

### Request (enviado pelo sistema à Uber)

```json
{
  "pickup": {
    "store_id": "uber-store-id-da-loja"
  },
  "dropoff_address": {
    "formatted_address": "Av. Paulista, 1000 - Bela Vista, São Paulo - SP, 01310-100",
    "apt_floor_suite": "Apto 42"
  },
  "pickup_times": [0]
}
```

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| `pickup.store_id` | sim | `UberDirectConfig.uber_store_id` do tenant |
| `dropoff_address.formatted_address` | sim | Montado a partir dos campos `Address` ou do formulário de checkout |
| `dropoff_address.apt_floor_suite` | não | `Address.complement` quando presente |
| `pickup_times` | sim | `[0]` = entrega imediata (ASAP) |

### Response de sucesso (HTTP 200)

```json
{
  "id": "dqt_AI6aDfhsSNqsVNTG03QKxg",
  "kind": "estimate",
  "duration": 1800,
  "expires": 1748650000,
  "fee": {
    "value": 850,
    "currency_code": "BRL"
  },
  "pickup": { "... ": "..." },
  "dropoff": { "...": "..." }
}
```

| Campo | Tipo | Uso no sistema |
|-------|------|---------------|
| `id` | string | `quote_id` armazenado na sessão Django e no `Order.uber_quote_id` |
| `expires` | Unix timestamp | TTL da cotação; armazenado na sessão para verificação no checkout |
| `fee.value` | inteiro (centavos) | Dividir por 100 → `Decimal` para `Order.delivery_fee` |

### Erros relevantes

| HTTP | Código Uber | Significado | Ação do sistema |
|------|-------------|-------------|-----------------|
| 400 | `invalid_params` | Endereço malformado | Exibir "Endereço inválido para entrega Uber" |
| 404 | `not_found` | Sem cobertura para o endereço | Exibir "Entrega Uber não disponível para este endereço"; usar fallback taxa estática |
| 401 | `unauthorized` | Token expirado | Renovar token e retry automático (1×) |
| 429 | `rate_limit` | Limite de requisições | Usar fallback taxa estática; logar warning |
| 5xx | — | Falha interna Uber | Fallback taxa estática; logar erro |
| Timeout | — | API inacessível | Fallback taxa estática; logar erro |

---

## Endpoint interno (FastAPI — exposto ao front)

**Método:** `POST`
**URL:** `/api/uber-direct/quote`
**Auth:** Header `X-Tenant-Subdomain` (padrão FastAPI do projeto)

### Request (front → FastAPI)

```json
{
  "street": "Av. Paulista",
  "number": "1000",
  "complement": "Apto 42",
  "neighborhood": "Bela Vista",
  "city": "São Paulo",
  "state": "SP",
  "zip_code": "01310-100"
}
```

Todos os campos de endereço estruturado são aceitos. `zip_code` e `complement` são opcionais.

### Response de sucesso (HTTP 200)

```json
{
  "quote_id": "dqt_AI6aDfhsSNqsVNTG03QKxg",
  "fee": "8.50",
  "fee_display": "R$ 8,50",
  "expires_at": 1748650000,
  "available": true
}
```

### Response de fallback (HTTP 200 — API Uber com erro)

```json
{
  "available": false,
  "message": "Taxa de entrega indisponível no momento",
  "fallback_fee": "5.00",
  "fallback_fee_display": "R$ 5,00"
}
```

O front exibe `fee_display` quando `available: true`, e `message` + `fallback_fee_display` quando `available: false`.

**Idempotência:** não aplicável (cotação sempre retorna novo quote_id).
**Timeout configurado no cliente:** 5 segundos para a chamada à Uber Direct.
