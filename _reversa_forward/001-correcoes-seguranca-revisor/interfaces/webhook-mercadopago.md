# Interface: Webhook MercadoPago

> Feature: `001-correcoes-seguranca-revisor`
> Contrato: HTTP POST — recebido pelo sistema (inbound)
> Endpoint: `POST /api/webhooks/mercadopago`
> Handler: `core/api.py:mercadopago_webhook`

---

## Descrição

Endpoint FastAPI que recebe notificações assíncronas do MercadoPago sobre mudanças de status de pagamento PIX. Após esta feature, o endpoint valida a assinatura HMAC antes de processar qualquer dado.

---

## Request

### Headers obrigatórios

| Header | Tipo | Exemplo | Descrição |
|--------|------|---------|-----------|
| `x-signature` | string | `ts=1234567890,v1=abc123...` | Assinatura HMAC-SHA256 gerada pelo MP |
| `x-request-id` | string | `f9c5b8a1-...` | ID único do request, usado no manifest HMAC |
| `content-type` | string | `application/json` | Sempre JSON do MP |

### Body (JSON)

```json
{
  "action": "payment.updated",
  "data": {
    "id": "1234567890"
  }
}
```

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `action` | string | Tipo de evento — `"payment.updated"` para mudanças de status |
| `data.id` | string | ID do pagamento no MercadoPago (`mp_payment_id`) |

---

## Fluxo de processamento (versão corrigida)

```
1. Ler x-signature e x-request-id do header
2. Extrair payment_id de payload["data"]["id"]
3. Validar HMAC:
   manifest = f"id:{payment_id};request-id:{x_request_id};ts:{ts}"
   expected = hmac.new(WEBHOOK_SECRET, manifest, sha256).hexdigest()
   if not hmac.compare_digest(expected, v1):
       return 401
4. Buscar Order por mp_payment_id:
   order = Order.objects.get(mp_payment_id=payment_id)
   → se não encontrar: return 404
5. Usar token correto da loja:
   sdk = mercadopago.SDK(order.store.mercadopago_access_token)
6. Consultar status no MP:
   payment_info = sdk.payment().get(payment_id)
   status = payment_info["response"]["status"]
7. Despachar por status:
   "approved"  → update_paid_order(order_id)
   "cancelled" | "expired" → cancel_order_on_pix_expiry(order_id)
   outros      → ignorar
8. return {"status": "ok"}
```

---

## Responses

| HTTP | Condição | Body |
|------|----------|------|
| 200 | Processado com sucesso (ou evento ignorado) | `{"status": "ok"}` |
| 401 | HMAC inválido ou ausente | `{"detail": "Invalid signature"}` |
| 404 | `mp_payment_id` não encontrado em nenhuma Order | `{"detail": "Order not found"}` |
| 422 | Body JSON malformado (FastAPI automático) | FastAPI default validation error |

---

## Comportamento especial em ambiente de teste

Se `REVERSA_TESTING=true` estiver definido **e** `MERCADOPAGO_WEBHOOK_SECRET` estiver ausente:
- A validação HMAC é pulada
- O endpoint aceita payload no formato `{"action": "test.approved", "order_id": N}` para aprovar um pedido pelo ID diretamente

> Este comportamento existe apenas para facilitar testes de desenvolvimento. **Nunca deve estar ativo em produção.**

---

## Idempotência

O campo `mp_payment_id` tem constraint `UNIQUE` na tabela `core_order`. Se o MP re-enviar o mesmo webhook (comportamento normal do MP em caso de timeout na resposta), a segunda execução:
- Encontra a mesma Order
- Já está em status `PREPARING` (ou maior)
- `update_paid_order` só processa se `order.status == PENDING` → operação segura

---

## Configuração necessária

```env
MERCADOPAGO_WEBHOOK_SECRET=<valor do painel MP → Integrações → Webhooks>
```

Para obter o valor: painel MercadoPago → Suas integrações → Webhooks → Segredo de assinatura.

---

## Referências

- `_reversa_sdd/core/pagamento/design.md` — fluxo webhook corrigido
- `_reversa_sdd/questions.md#p-05` — decisão HMAC (D-06)
- `_reversa_sdd/questions.md#p-08` — decisão mp_payment_id (D-02)
- MercadoPago Docs: Segurança de notificações via assinatura digital
