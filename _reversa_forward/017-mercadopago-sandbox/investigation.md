# Investigation: Integração Real MercadoPago (Sandbox)

> Identificador: `017-mercadopago-sandbox`
> Data: `2026-06-02`

---

## 1. Diagnóstico do estado atual

### Por que o QR Code sandbox não aparece hoje?

O token padrão no `.env.example` é `TEST-00000000-0000-0000-0000-000000000000`. O guard em `core/payment.py:104`:

```python
if result.get("status") == 403 or token.startswith("TEST-0000"):
```

Essa condição ativa o mock **antes** de chamar a API do MP quando o token começa com `TEST-0000`. Tokens sandbox reais começam com `TEST-` seguido de UUID real (ex: `TEST-1234abcd-...`), então o mock **não ativaria** com um token real de sandbox. O código está correto para esse caso; o problema é só de configuração.

### Por que o webhook rejeita tudo com 401?

Em `core/api.py` (webhook):
```python
elif not settings.REVERSA_TESTING:
    raise HTTPException(status_code=401, detail="Webhook secret not configured")
```

Com `MERCADOPAGO_WEBHOOK_SECRET=''` (default) e `REVERSA_TESTING=false`, toda notificação real é rejeitada. Correto por segurança, mas bloqueia sandbox.

### Por que o email do convidado não chega ao MP?

Fluxo atual:
1. `checkout()` coleta `customer_email = request.POST.get('customer_email')` ✅
2. `Order.objects.create(...)` — `customer_email` **não está nos campos** ❌
3. `create_checkout_pro_preference(order)` usa `order.user.email` — lança `AttributeError` para guest ❌
4. `create_pix_payment(order)` chamado sem argumento de email — usa `guest@placeholder.invalid` ❌

---

## 2. Tokens MercadoPago — anatomia

| Tipo | Formato | Comportamento no sistema atual |
|------|---------|-------------------------------|
| Mock dummy | `TEST-0000…` | Ativa fallback mock sem chamar API |
| Sandbox real | `TEST-<UUID-real>` | Chama API sandbox do MP (correto) |
| Produção | `APP_USR-<UUID>` | Chama API produção do MP |

O token sandbox é obtido em: **painel MP → Suas integrações → Credenciais de teste → Access token**.

---

## 3. Fluxo Checkout Pro vs PIX — quando cada um é usado?

Analisando `core/views.py`:

- Checkout online (`payment_method == 'online'`) → `create_checkout_pro_preference()` → redirect para `sandbox_init_point`
- Balcão/cartão/dinheiro → `process_new_order.delay()` → sem MP
- PIX via cart drawer (view diferente, `checkout_pix_view`) → `create_pix_payment(order)`

O Checkout Pro é o fluxo principal do checkout online. O PIX direto é um fluxo alternativo no cart drawer.

---

## 4. Padrão de `transaction_amount` na SDK MP Python

A SDK Python do MP (`mercadopago`) aceita tanto `float` quanto `str` para valores monetários. A documentação oficial recomenda evitar `float` para valores financeiros por causa de imprecisão IEEE 754.

Opções:
- `float(order.total_amount)` → pode virar `0.10000000000000001`
- `str(order.total_amount)` → `"0.10"` — preserva precisão, MP aceita
- `Decimal(order.total_amount)` → MP SDK v2 pode não serializar corretamente para JSON

**Decisão: usar `str(order.total_amount)`** (ver D-04 no roadmap).

---

## 5. HMAC do webhook MP — formato

O MP envia o header `x-signature` no formato:
```
ts=1668005070,v1=<sha256-hex>
```

O manifest para cálculo é:
```
id:<payment_id>;request-id:<x-request-id>;ts:<ts>
```

O código já implementa isso corretamente em `core/api.py`. O `MERCADOPAGO_WEBHOOK_SECRET` é obtido em: **painel MP → Suas integrações → Webhooks → Segredo de assinatura**.

---

## 6. Expor localhost para o MP (ngrok)

O MP exige uma URL HTTPS pública para enviar webhooks. Em desenvolvimento local:

```bash
ngrok http 8000
```

A URL gerada (ex: `https://abc123.ngrok-free.app`) deve ser configurada em:
- Painel MP → Suas integrações → Webhooks → URL de notificação
- Evento a escutar: `payment` (cobrirá `payment.created` e `payment.updated`)

Importante: o plano free do ngrok gera URL nova a cada restart. Para desenvolvimento, basta reconfigurar no painel MP após cada restart do ngrok.

---

## 7. Simular aprovação de pagamento no sandbox MP

Após gerar um QR Code real via Checkout Pro ou PIX:

1. Acesse o painel do MP sandbox
2. Encontre o pagamento pelo ID salvo em `Order.mp_payment_id`
3. Clique em "Aprovar" — MP envia webhook para a URL configurada
4. Verifique `Order.status` no dashboard da loja

Alternativamente, usar o `REVERSA_TESTING=true` + `action=test.approved` no webhook ainda funciona para testes unitários sem ngrok.
