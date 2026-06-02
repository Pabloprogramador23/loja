# Interface: Uber Direct — Webhook de Status

> Contrato: HTTP REST (servidor — a Uber chama o sistema)
> Endpoint: `POST /api/webhooks/uber-direct` (FastAPI)
> Padrão: mesmo de `/api/webhooks/mercadopago` — resposta 200 imediata + Celery task

---

## Endpoint

**Método:** `POST`
**URL:** `https://seu-dominio.com/api/webhooks/uber-direct`
**Configurar em:** Uber Developer Dashboard → Webhooks

---

## Payload recebido

### event.delivery_status (mudança de status)

```json
{
  "event_type": "event.delivery_status",
  "event_id": "evt_abc123",
  "meta": {
    "resource_id": "del_XPTO123",
    "resource_href": "https://api.uber.com/v1/customers/.../deliveries/del_XPTO123",
    "status": "EN_ROUTE_TO_DROPOFF",
    "tracking_url": "https://track.uber.com/abc123"
  }
}
```

### event.courier_update (localização do entregador)

```json
{
  "event_type": "event.courier_update",
  "event_id": "evt_xyz456",
  "meta": {
    "resource_id": "del_XPTO123",
    "location": {
      "lat": -23.5505,
      "lng": -46.6333
    }
  }
}
```

*Nota: `event.courier_update` é recebido mas não processado nesta versão — armazenado em `UberDirectDeliveryEvent.raw_payload` para uso futuro (rastreamento em mapa).*

---

## Validação de assinatura

**Header:** `X-Uber-Signature`
**Algoritmo:** HMAC-SHA256
**Chave:** `UberDirectConfig.webhook_signing_key` do tenant

```python
# Fluxo de validação no FastAPI
raw_body = await request.body()
signature = request.headers.get("x-uber-signature", "")
# Identificar tenant pelo delivery_id → UberDirectDelivery → Store → UberDirectConfig
is_valid = hmac.compare_digest(
    hmac.new(signing_key.encode(), raw_body, hashlib.sha256).hexdigest(),
    signature
)
if not is_valid:
    raise HTTPException(status_code=401)
```

**Problema:** para validar a assinatura, é necessário saber o tenant antes de validar. Solução: lookup por `meta.resource_id` (uber_delivery_id) para encontrar o `UberDirectConfig` e sua `signing_key`.

Se o `uber_delivery_id` não for encontrado → retornar 404 (não 401), pois pode ser webhook de outra loja ou corrida não registrada.

---

## Mapeamento de status → ações do sistema

| `meta.status` recebido | `UberDirectDelivery.status` | Ação em `Order` |
|------------------------|------------------------------|------------------|
| `pending` | `PENDING` | — |
| `scheduled` | `SCHEDULED` | — |
| `en_route_to_pickup` | `EN_ROUTE_TO_PICKUP` | — |
| `arrived_at_pickup` | `ARRIVED_AT_PICKUP` | — |
| `en_route_to_dropoff` | `EN_ROUTE_TO_DROPOFF` | `Order.status = DELIVERING` |
| `arrived_at_dropoff` | `ARRIVED_AT_DROPOFF` | — |
| `completed` | `COMPLETED` | `Order.status = COMPLETED` |
| `failed` | `FAILED` | — (Manager decide) |
| `canceled` | `CANCELED` | — (Manager decide) |
| `returned` | `RETURNED` | — (Manager decide; possível taxa de retorno) |

---

## Fluxo de processamento

```
POST /api/webhooks/uber-direct
    │
    ├─ Ler raw_body (bytes)
    ├─ Lookup UberDirectDelivery por meta.resource_id
    │      └─ 404 se não encontrado
    ├─ Validar assinatura HMAC com signing_key do tenant
    │      └─ 401 se inválida
    ├─ Retornar HTTP 200 {} (imediato — Uber exige resposta rápida)
    └─ Dispatch: process_uber_webhook.delay(delivery_id, status, payload)
           │
           └─ [Celery Worker]
                  ├─ select_for_update() em UberDirectDelivery
                  ├─ Atualizar status
                  ├─ Se tracking_url no payload → atualizar
                  ├─ Criar UberDirectDeliveryEvent (auditoria)
                  ├─ Se status ∈ {EN_ROUTE_TO_DROPOFF} → Order.status = DELIVERING
                  ├─ Se status = COMPLETED → Order.status = COMPLETED
                  └─ Salvar com transaction.atomic()
```

---

## Idempotência

Webhooks podem ser reenviados pela Uber em caso de timeout/falha. A task Celery deve ser idempotente:
- Comparar `status_from` atual com o novo status antes de salvar
- Se já no status alvo (ou em status posterior), logar e retornar sem modificar

---

## Retentativas Celery

```python
@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def process_uber_webhook(self, delivery_id: str, status: str, payload: dict):
    try:
        with transaction.atomic():
            delivery = UberDirectDelivery.objects.select_for_update().get(
                uber_delivery_id=delivery_id
            )
            # ... processar ...
    except UberDirectDelivery.DoesNotExist:
        raise self.retry(exc=Exception(f"Delivery {delivery_id} não encontrado"))
    except Exception as e:
        raise self.retry(exc=e)
```

---

## Resposta ao Uber

- **Sucesso:** `HTTP 200 {}` (corpo vazio)
- **Assinatura inválida:** `HTTP 401`
- **Delivery não encontrado:** `HTTP 404`
- **Erro interno:** `HTTP 500` — Uber tentará reenviar automaticamente

A resposta deve ser enviada em menos de **5 segundos**. Por isso o processamento pesado é sempre no Celery.
