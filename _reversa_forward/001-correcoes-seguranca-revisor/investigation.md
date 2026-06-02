# Investigation: Correções de Segurança (Revisor)

> Identificador: `001-correcoes-seguranca-revisor`
> Data: `2026-05-26`

## 1. Validação HMAC do Webhook MercadoPago

### Como o MP assina webhooks

O MercadoPago envia um header `x-signature` no formato:
```
x-signature: ts=<timestamp>,v1=<hmac_hex>
```

O HMAC é calculado sobre a string `id:<payment_id>;request-id:<x-request-id>;ts:<timestamp>` usando SHA-256 e o `MERCADOPAGO_WEBHOOK_SECRET` como chave.

### Implementação recomendada (stdlib Python)

```python
import hmac
import hashlib

def verify_mp_signature(x_signature: str, x_request_id: str, payment_id: str, secret: str) -> bool:
    parts = dict(part.split("=", 1) for part in x_signature.split(","))
    ts = parts.get("ts", "")
    v1 = parts.get("v1", "")
    manifest = f"id:{payment_id};request-id:{x_request_id};ts:{ts}"
    expected = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, v1)
```

> Nota: `hmac.compare_digest` previne timing attacks. Essencial para segredos.

### Alternativas descartadas

| Alternativa | Motivo do descarte |
|-------------|-------------------|
| Verificação via SDK MP | SDK não expõe método de verificação de assinatura na versão Python; seria monkey-patch |
| Verificação simples `==` | Vulnerável a timing attack — um atacante pode detectar diferenças de tempo entre strings para inferir o segredo |
| IP allowlist | MP não publica lista estática de IPs; solução frágil e difícil de manter |

---

## 2. Resolução de Tenant por Host

### Padrão de subdomínio no projeto

Baseado na decisão do usuário (P-09), cada loja tem subdomínio próprio: `loja-a.meusaas.com`.

### Lógica de extração do subdomínio

```python
host = request.get_host()  # ex: "loja-a.meusaas.com" ou "loja-a.meusaas.com:8000"
hostname = host.split(":")[0]  # remove porta se houver
parts = hostname.split(".")
# Para "loja-a.meusaas.com" → parts = ["loja-a", "meusaas", "com"]
# O subdomain é parts[0] quando há pelo menos 3 partes
subdomain = parts[0] if len(parts) >= 3 else None
```

### Casos edge importantes

| Host recebido | Extração | Resultado |
|---------------|----------|-----------|
| `loja-a.meusaas.com` | `loja-a` | Resolve normalmente |
| `loja-a.meusaas.com:8000` | `loja-a` | Resolve (porta removida) |
| `localhost` ou `127.0.0.1` | `None` (< 3 partes) | Fallback: primeiro store ativo |
| `meusaas.com` (raiz) | `meusaas` | Store não encontrado → 404 (ou página de marketing futura) |
| `inexistente.meusaas.com` | `inexistente` | `Store.DoesNotExist` → 404 |

### Alternativas descartadas

| Alternativa | Motivo do descarte |
|-------------|-------------------|
| Header `X-Forwarded-Host` | Requer configuração de proxy confiável; mais complexo |
| Cookie de tenant | Stateful; não escala para SEO e compartilhamento de link |
| Path prefix `/loja-a/...` | Requer mudança de todas as URLs do sistema |

---

## 3. Idempotência da Task Celery

### O problema do duplo PREPARING

Conforme documentado em `_reversa_sdd/state-machines.md#l-07`, a tarefa `process_new_order` atualmente seta `order.status = PREPARING` mesmo quando o webhook já fez isso. Race condition:

```
t=0: webhook → order.status = PREPARING → save()
t=0.1: Celery dispatched
t=2: Manager vê PREPARING → avança para DELIVERING → save()
t=2.1: Celery executa → order.status = PREPARING → save()  ← REGRESSÃO
```

### Solução adotada: guard + retry

```python
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_new_order(self, order_id):
    try:
        order = Order.objects.get(id=order_id)
        if order.status != Order.Status.PREPARING:
            return  # idempotency guard
        # ... lógica de processamento (email, estoque, etc.)
    except Order.DoesNotExist:
        pass  # já cancelado ou removido
    except Exception as exc:
        raise self.retry(exc=exc)
```

### Alternativas descartadas

| Alternativa | Motivo do descarte |
|-------------|-------------------|
| `SELECT FOR UPDATE` (lock de banco) | Over-engineering; o guard de status é suficiente e mais simples |
| Celery chord/chain | Requer reestrutura do fluxo; risco de regressão |
| Remover task completamente | Task ainda é necessária para futuras funcionalidades (email de confirmação, etc.) |

---

## 4. `python-decouple` vs `os.environ`

O projeto já tem `python-decouple` instalado e já usa `config()` para `DATABASE_URL` e `REDIS_URL` em `settings.py`. A escolha natural é estender o uso do `config()` para `SECRET_KEY`, `DEBUG` e `ALLOWED_HOSTS`.

```python
from decouple import config, Csv

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())
```

> `cast=Csv()` converte `"loja.com,*.loja.com"` para `['loja.com', '*.loja.com']` automaticamente.

---

## 5. Estorno MercadoPago

### API de cancelamento vs refund

| Status do pagamento | Endpoint MP | Descrição |
|---------------------|-------------|-----------|
| `pending` (PIX não pago) | `PUT /v1/payments/{id}` com `{"status": "cancelled"}` | Cancela o PIX antes de ser pago |
| `approved` (PIX pago) | `POST /v1/payments/{id}/refunds` | Estorna o valor já capturado |

```python
# Cancelar PIX pendente
sdk.payment().update(mp_payment_id, {"status": "cancelled"})

# Estornar pagamento aprovado
sdk.payment().refund(mp_payment_id)
```

### Tratamento de erros

O estorno pode falhar (ex: Order já estornada, prazo vencido). A view de cancelamento deve:
1. Tentar o estorno
2. Se falhar, logar o erro mas ainda marcar a Order como CANCELED (o estorno pode ser feito manualmente no painel MP)
3. Não bloquear o cancelamento da Order por falha de estorno

---

*Escala de confiança: 🟢 CONFIRMADO — 🟡 INFERIDO — 🔴 LACUNA*
