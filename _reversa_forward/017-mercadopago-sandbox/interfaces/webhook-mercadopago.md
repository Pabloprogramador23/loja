# Interface: POST /api/webhooks/mercadopago

> Identificador: `017-mercadopago-sandbox`
> Tipo: HTTP recebido (MP → sistema)
> Implementado em: `core/api.py` (FastAPI)

---

## Descrição

Endpoint que recebe notificações de pagamento do MercadoPago. Valida a assinatura HMAC, consulta o pagamento na API do MP e transiciona o pedido de `PENDING` para `PREPARING` quando aprovado.

---

## Request (enviado pelo MP)

**Método:** `POST`
**Path:** `/api/webhooks/mercadopago`
**Content-Type:** `application/json`

### Headers obrigatórios (quando HMAC ativo)

| Header | Formato | Exemplo |
|--------|---------|---------|
| `x-signature` | `ts=<epoch>,v1=<sha256hex>` | `ts=1668005070,v1=abc123...` |
| `x-request-id` | UUID | `a7fce0c2-...` |

### Body

```json
{
  "action": "payment.updated",
  "data": {
    "id": "12345678"
  }
}
```

| Campo | Tipo | Valores conhecidos |
|-------|------|-------------------|
| `action` | string | `payment.created`, `payment.updated` |
| `data.id` | string | ID do pagamento no MP |

---

## Processamento interno

```
POST /api/webhooks/mercadopago
    │
    ├── HMAC válido? ──NÃO──► 401 Invalid signature
    │
    ├── Secret configurado? ──NÃO e REVERSA_TESTING=false──► 401 Not configured
    │
    ├── action == test.approved e REVERSA_TESTING=true ──► aprovar por order_id direto (dev only)
    │
    └── action == payment.updated ou payment.created
            │
            ├── Buscar pagamento na API MP (sdk_global com token global)
            ├── mp_status == "approved"?
            │       ├── Buscar Order por external_reference (checkout pro) OU mp_payment_id (pix)
            │       └── update_paid_order(order.id) → PENDING → PREPARING + process_new_order.delay()
            └── outros status → ignorar, retornar 200
```

---

## Responses

| Status | Quando | Body |
|--------|--------|------|
| `200` | Processado com sucesso | `{"status": "ok"}` |
| `401` | HMAC inválido | `{"detail": "Invalid signature"}` |
| `401` | Secret não configurado | `{"detail": "Webhook secret not configured"}` |

---

## Idempotência

`update_paid_order()` tem guard `if order.status != PENDING: return` — chamadas repetidas para o mesmo pedido já aprovado são ignoradas. O webhook é idempotente. 🟢

---

## Cálculo do HMAC (para testes)

```python
import hmac, hashlib

secret = "SEU_WEBHOOK_SECRET"
payment_id = "12345678"
request_id = "a7fce0c2-..."
ts = "1668005070"

manifest = f"id:{payment_id};request-id:{request_id};ts:{ts}"
signature = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
header = f"ts={ts},v1={signature}"
```

---

## Configuração no painel MP (sandbox)

- URL: `https://<ngrok-url>/api/webhooks/mercadopago`
- Eventos: `Pagamentos` (`payment`)
- Secret: copiar de **Suas integrações → Webhooks → Segredo de assinatura**
