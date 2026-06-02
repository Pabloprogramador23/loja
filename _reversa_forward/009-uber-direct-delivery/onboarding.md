# Onboarding: 009-uber-direct-delivery

> Passo a passo para testar a feature após implementação.
> Data: `2026-05-30`

---

## Pré-requisitos

- [ ] Servidor rodando: `uvicorn store_saas.asgi:application --reload --port 8000`
- [ ] Worker Celery rodando: `celery -A store_saas worker -l info`
- [ ] Redis rodando: `redis-server` (ou via Docker: `docker-compose up redis`)
- [ ] Conta Uber Direct Sandbox criada no [Uber Developer Dashboard](https://developer.uber.com/)
- [ ] Credenciais Sandbox em mãos: `client_id`, `client_secret`, `customer_id`, `uber_store_id`, `webhook_signing_key`

---

## 1. Configurar variáveis de ambiente

Adicione ao `.env` (ou `store_saas/settings.py` em dev):

```env
UBER_CLIENT_ID=seu_client_id_sandbox
UBER_CLIENT_SECRET=seu_client_secret_sandbox
UBER_CUSTOMER_ID=seu_customer_id_sandbox
UBER_SANDBOX=True
```

---

## 2. Aplicar migrações

```bash
python manage.py migrate
```

Confirmar que `0011_uber_direct` aparece como `[X]`.

---

## 3. Ativar Uber Direct para a loja de teste

1. Acesse o dashboard Manager: `http://127.0.0.1:8000/manager/settings/`
2. Role até a seção **Uber Direct**
3. Preencha:
   - **Store ID Uber:** (valor do seu painel sandbox)
   - **Client ID:** (mesmo do .env, ou diferente se a loja tiver conta própria)
   - **Client Secret:** (idem)
   - **Webhook Signing Key:** (do painel Uber)
4. Marque **Ativar integração Uber Direct**
5. Salve

---

## 4. Testar cotação no checkout (cliente autenticado)

1. Acesse a loja como cliente: `http://127.0.0.1:8000/`
2. Adicione um produto ao carrinho
3. Abra o drawer do carrinho
4. Selecione um endereço cadastrado (ou cadastre um em `/account/addresses/`)
5. **Resultado esperado:** a linha "Taxa de Entrega" deve exibir um valor em R$ retornado pela API Uber Sandbox (não o valor estático da loja)
6. O total do carrinho deve incluir a taxa

---

## 5. Testar cotação no checkout (guest)

1. Certifique-se de estar deslogado
2. Adicione um produto ao carrinho
3. Abra o drawer → preencha os campos de endereço manualmente
4. **Resultado esperado:** cotação Uber exibida ao preencher os campos de rua/número/cidade/estado

---

## 6. Testar fallback (API Uber indisponível)

1. Temporariamente, defina `UBER_CLIENT_ID=invalido` no .env e reinicie o servidor
2. Adicione produto ao carrinho e tente obter cotação
3. **Resultado esperado:** mensagem "Taxa de entrega indisponível no momento"; taxa estática da loja exibida como fallback
4. Reverta o `.env` após o teste

---

## 7. Confirmar pedido com cotação Uber

1. Com cotação exibida (passo 4 ou 5), clique em **Confirmar Pedido**
2. Finalize o pagamento PIX (use o mock sandbox)
3. Verifique no admin Django (`/admin/core/order/`) que:
   - `Order.delivery_fee` = valor cotado pela Uber
   - `Order.uber_quote_id` = ID da cotação

---

## 8. Despachar entrega pelo Manager

1. Acesse o dashboard Manager: `/manager/orders/`
2. Localize o pedido no status **PREPARING**
3. Abra o modal do pedido
4. Clique em **Despachar via Uber**
5. **Resultado esperado:**
   - `UberDirectDelivery` criado com `uber_delivery_id` e `tracking_url`
   - Tracking URL exibida no modal
   - Status da entrega Uber exibido como "Pendente" ou "Agendado"

---

## 9. Testar webhook de atualização de status

Use o painel Uber Sandbox ou `curl` para simular um webhook:

```bash
# Calcular assinatura HMAC primeiro (use a webhook_signing_key)
PAYLOAD='{"event_type":"event.delivery_status","meta":{"resource_id":"DELIVERY_ID","status":"EN_ROUTE_TO_DROPOFF"}}'
SIG=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "SUA_SIGNING_KEY" | cut -d' ' -f2)

curl -X POST http://127.0.0.1:8000/api/webhooks/uber-direct \
  -H "Content-Type: application/json" \
  -H "X-Uber-Signature: $SIG" \
  -d "$PAYLOAD"
```

**Resultado esperado:**
- HTTP 200 imediato
- `UberDirectDelivery.status` atualizado para `EN_ROUTE_TO_DROPOFF`
- `Order.status` atualizado para `DELIVERING`

---

## 10. Testar webhook com assinatura inválida

```bash
curl -X POST http://127.0.0.1:8000/api/webhooks/uber-direct \
  -H "Content-Type: application/json" \
  -H "X-Uber-Signature: assinatura_errada" \
  -d '{"event_type":"event.delivery_status"}'
```

**Resultado esperado:** HTTP 401, sem alteração no banco.

---

## 11. Testar cancelamento de entrega

1. Com entrega no status `PENDING` ou `SCHEDULED`, abra o modal do pedido
2. Clique em **Cancelar Entrega Uber**
3. **Resultado esperado:**
   - API Uber chamada para cancelamento
   - `UberDirectDelivery.status = CANCELED`
   - `Order.status` permanece `PREPARING`
   - Botão "Despachar via Uber" re-habilitado para novo despacho

---

## 12. Verificar que balcão não usa Uber Direct

1. Acesse `/manager/create-order/`
2. Crie um pedido de balcão
3. Abra o modal do pedido criado
4. **Resultado esperado:** sem cotação Uber, sem botão "Despachar via Uber"
