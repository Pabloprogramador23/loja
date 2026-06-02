# Investigation: 013-checkout-pro-mp

> Data: `2026-05-30`

## PIX QR Code vs Checkout Pro — diferenças práticas

| Aspecto | PIX QR Code (atual) | Checkout Pro (novo) |
|---------|---------------------|---------------------|
| API MP usada | `payment().create()` | `preference().create()` |
| Métodos aceitos | Só PIX | PIX + cartão crédito + cartão débito + outros |
| Onde o cliente paga | No app (QR inline) | Na página do MP (redirect) |
| Fluxo de retorno | Polling no app | `back_urls` configuradas |
| Artefato principal | `qr_code` + `qr_code_base64` | `init_point` (URL) |
| Webhook disparado | `payment.updated` | `payment.created` e/ou `payment.updated` |

## Webhook do Checkout Pro — diferença crítica de lookup

No fluxo atual (PIX QR Code):
1. `checkout()` cria o payment → MP retorna `payment_id`
2. `order.mp_payment_id = payment_id` → salvo imediatamente
3. Webhook chega com `data.id = payment_id` → `Order.objects.get(mp_payment_id=payment_id)` ✅

No Checkout Pro:
1. `checkout()` cria a **preference** → MP retorna `preference_id` e `init_point`
2. `order.mp_preference_id = preference_id` → salvo; `mp_payment_id` está vazio
3. Usuário paga no MP → MP cria um **payment** vinculado à preference
4. Webhook chega com `data.id = payment_id` (do payment, não da preference)
5. `Order.objects.get(mp_payment_id=payment_id)` → FALHA (campo vazio) ❌

**Solução:** No webhook, após `sdk.payment().get(payment_id)`, usar `response['external_reference']` (= `order.id`) para encontrar o Order:

```python
payment_response = sdk.payment().get(payment_id)["response"]
order_id = payment_response.get("external_reference")
order = await Order.objects.aget(id=int(order_id))
order.mp_payment_id = str(payment_id)
await order.asave(update_fields=["mp_payment_id"])
```

## back_urls e localhost

O MP aceita `localhost` nas `back_urls` em ambiente sandbox. Para produção, o domínio precisa ser HTTPS. `SITE_URL` resolve isso sem código condicional.

## auto_return

`"auto_return": "approved"` instrui o MP a redirecionar automaticamente para `back_urls.success` após aprovação, sem precisar que o usuário clique em um botão. Para `pending` e `failure`, o redirecionamento é sempre automático.

## statement_descriptor

Campo opcional que aparece na fatura do cartão. MP limita a 22 caracteres. Usar `order.store.name[:22]` é suficiente.

## external_reference

Campo livre da preference/payment. MP envia de volta no webhook no response do `payment().get()`. Usar `order.id` (inteiro como string) é o padrão recomendado pela documentação MP para rastreabilidade.
