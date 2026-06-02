# Interface: MercadoPago Webhook (atualizado)

> Contrato recebido pelo backend quando MP notifica um pagamento.

## Endpoint (nosso)

`POST /api/webhooks/mercadopago`

## Actions tratados após esta feature

| Action | Quando ocorre | Tratamento |
|--------|---------------|------------|
| `payment.created` | Checkout Pro: pagamento criado (PIX pendente ou cartão aprovado imediatamente) | Buscar payment no MP; se `approved` → `update_paid_order` |
| `payment.updated` | Status do payment mudou (PIX aprovado, cartão aprovado com delay) | Mesma lógica |
| `test.approved` | Backdoor dev (`REVERSA_TESTING=true`) | Aprovação direta por `order_id` |

## Payload típico do MP (Checkout Pro)

```json
{
  "action": "payment.updated",
  "api_version": "v1",
  "data": { "id": "1234567890" },
  "date_created": "2024-01-01T00:00:00Z",
  "id": 12345,
  "live_mode": false,
  "type": "payment",
  "user_id": "987654321"
}
```

## Fluxo interno atualizado

```
1. Validar HMAC (se MERCADOPAGO_WEBHOOK_SECRET configurado)
2. action ∈ {"payment.created", "payment.updated"}?
   Sim:
     payment_id = payload["data"]["id"]
     payment_response = sdk.payment().get(payment_id)["response"]
     order_id = payment_response["external_reference"]   ← NOVO
     order = Order.objects.get(id=int(order_id))
     order.mp_payment_id = str(payment_id)              ← NOVO
     order.save(update_fields=["mp_payment_id"])
     mp_status = payment_response["status"]
     if mp_status == "approved":
       update_paid_order(order.id)
     elif mp_status in ("cancelled", "expired"):
       cancel_order_on_pix_expiry(order.id)
   Não: ignorar
3. Retornar {"status": "ok"}
```

## Diferença vs. implementação anterior

Antes: `Order.objects.get(mp_payment_id=str(payment_id))` — falhava para Checkout Pro porque `mp_payment_id` estava vazio.

Depois: `Order.objects.get(id=int(external_reference))` — funciona tanto para PIX QR Code (histórico) quanto para Checkout Pro (novo).

**Compatibilidade retroativa:** Orders históricos com `mp_payment_id` preenchido e `external_reference` correto funcionam igualmente.
