# Interface: MercadoPago Preference API

> Contrato chamado pelo backend ao criar o Checkout Pro.

## Endpoint

`POST https://api.mercadopago.com/checkout/preferences`

## Headers

```
Authorization: Bearer {access_token}
Content-Type: application/json
```

## Request body (resumido)

```json
{
  "items": [
    {
      "id": "42",
      "title": "Classic Burger",
      "quantity": 2,
      "unit_price": 32.90,
      "currency_id": "BRL"
    }
  ],
  "payer": {
    "email": "cliente@email.com",
    "name": "João Silva"
  },
  "back_urls": {
    "success": "https://seuapp.com/payment/success/",
    "pending": "https://seuapp.com/payment/pending/",
    "failure": "https://seuapp.com/payment/failure/"
  },
  "auto_return": "approved",
  "external_reference": "123",
  "statement_descriptor": "Mock Burger"
}
```

## Response de sucesso (201)

```json
{
  "id": "123456789-abcdef",
  "init_point": "https://www.mercadopago.com.br/checkout/v1/redirect?pref_id=123456789-abcdef",
  "sandbox_init_point": "https://sandbox.mercadopago.com.br/checkout/v1/redirect?pref_id=...",
  ...
}
```

**Campos usados:**
- `id` → salvo em `Order.mp_preference_id`
- `init_point` → URL para onde o browser redireciona (produção)
- `sandbox_init_point` → idem para sandbox (tokens `TEST-`)

## Erros mapeados

| Status | Significado | Ação |
|--------|-------------|------|
| 201 | Preference criada | Redirecionar para `init_point` |
| 400 | Dados inválidos (ex: email inválido) | Retornar erro ao cliente |
| 401 | Token inválido/expirado | Verificar token no admin da loja |
| 403 | Token sem permissão | Ativar mock dev (`TEST-0000`) |

## Timeout

O SDK Python do MP não expõe timeout configurável por padrão. Adicionar timeout via `requests.Session` se necessário. Para dev, o mock não faz chamada HTTP.

## Idempotência

Não é idempotente — cada chamada cria uma nova preference. Se o checkout falhar após criar a preference mas antes de redirecionar, uma preference órfã fica no MP (sem impacto financeiro — não é uma cobrança).
