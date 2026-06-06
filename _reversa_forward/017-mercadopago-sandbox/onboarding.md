# Onboarding: Integração Real MercadoPago (Sandbox)

> Identificador: `017-mercadopago-sandbox`
> Data: `2026-06-02`
> Para: quem vai testar o fluxo completo de pagamento sandbox pela primeira vez

---

## Pré-requisitos

- Docker rodando (`loja-web-1`, `loja-worker-1`, `loja-db-1`, `loja-redis-1`)
- Conta no MercadoPago com acesso ao painel de desenvolvedor
- ngrok instalado (ou outro túnel HTTP → HTTPS)

---

## Passo 1 — Obter as credenciais sandbox no painel MP

1. Acesse [mercadopago.com.br/developers](https://www.mercadopago.com.br/developers)
2. Vá em **Suas integrações → [Nome da sua integração]**
3. Aba **Credenciais de teste**
4. Copie o **Access token de teste** (formato: `TEST-<UUID>-...`)
5. Vá em **Webhooks → Configurar notificações**
6. Clique em **Segredo de assinatura** e copie o valor

---

## Passo 2 — Configurar o `.env`

No arquivo `.env` na raiz do projeto, preencha:

```env
MERCADOPAGO_ACCESS_TOKEN=TEST-SEU-TOKEN-SANDBOX-AQUI
MERCADOPAGO_WEBHOOK_SECRET=SEU-WEBHOOK-SECRET-AQUI
SITE_URL=https://SEU-SUBDOMINIO.ngrok-free.app
```

> ⚠️ O `SITE_URL` é necessário para os `back_urls` do Checkout Pro (telas de sucesso/pendente/falha).

---

## Passo 3 — Subir o ngrok

```bash
ngrok http 8000
```

Copie a URL HTTPS gerada (ex: `https://abc123.ngrok-free.app`).

Atualize `SITE_URL` no `.env` com essa URL.

---

## Passo 4 — Configurar o webhook no painel MP

1. Painel MP → **Suas integrações → Webhooks → Configurar notificações**
2. URL de notificação: `https://abc123.ngrok-free.app/api/webhooks/mercadopago`
3. Evento: marque **Pagamentos** (`payment`)
4. Salve

---

## Passo 5 — Reiniciar a stack

```bash
docker compose down
docker compose up -d
```

Ou, se preferir sem Docker:

```bash
# Terminal 1 — servidor
uvicorn store_saas.asgi:application --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — worker
celery -A store_saas worker -l info
```

---

## Passo 6 — Rodar a migração

```bash
docker compose exec web python manage.py migrate
```

Ou sem Docker:
```bash
python manage.py migrate
```

---

## Passo 7 — Testar o fluxo completo

### Checkout Pro (fluxo principal)

1. Acesse a loja: `http://localhost:8000`
2. Adicione produtos ao carrinho
3. Preencha nome, telefone, endereço e **email** (campo obrigatório para guest)
4. Clique em **Finalizar pedido**
5. Você deve ser redirecionado para `sandbox.mercadopago.com.br` — não para a página mock
6. No painel sandbox do MP, encontre o pagamento e clique **Aprovar**
7. O MP envia webhook → verifique nos logs do servidor: `POST /api/webhooks/mercadopago 200`
8. No dashboard da loja, o pedido deve aparecer como **Preparando**

### Verificar que o mock não está ativo

No terminal do servidor, após o checkout, você **não deve** ver o log:
```
⚠️ PIX: nenhum email de pagador disponível
```
Se aparecer, o `customer_email` não está chegando ao `Order`.

---

## Troubleshooting

| Sintoma | Causa provável | Solução |
|---------|---------------|---------|
| Ainda redirecionando para `/payment/mock/` | Token ainda começa com `TEST-0000` | Verificar `.env` e reiniciar |
| Webhook retorna 401 | Secret não configurado ou errado | Verificar `MERCADOPAGO_WEBHOOK_SECRET` no `.env` |
| Webhook retorna 401 com "Invalid signature" | URL do webhook no MP diferente da do ngrok | Reconfigurar URL no painel MP |
| `AttributeError: 'NoneType' has no attribute 'email'` | Bug do customer_email não corrigido | Garantir que a correção do `create_checkout_pro_preference` foi aplicada |
| ngrok URL diferente após restart | Plano free ngrok gera URL nova | Atualizar `SITE_URL` no `.env` e URL do webhook no painel MP |
