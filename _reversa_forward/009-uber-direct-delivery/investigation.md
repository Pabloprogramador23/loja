# Investigation: 009-uber-direct-delivery

> Data: `2026-05-30`

---

## 1. Visão geral da API Uber Direct

O **Uber Direct** é a API de logística last-mile da Uber. O fluxo principal tem três passos:

1. **Quote** (`POST /v1/customers/{customer_id}/delivery_quotes`) — valida endereços, verifica cobertura e retorna fee + quote_id + TTL
2. **Delivery** (`POST /v1/customers/{customer_id}/deliveries`) — cria a corrida usando o `estimate_id` da cotação
3. **Webhook** — Uber envia eventos de mudança de status para URL configurada no painel do desenvolvedor

**Base URL:** `https://api.uber.com` (sandbox e produção usam a mesma URL; o ambiente é determinado pelas credenciais)

**Autenticação:** OAuth2 `client_credentials`, escopo `eats.deliveries`. Token válido ~30 dias.

---

## 2. Padrão de integração adotado no projeto

O projeto já tem um padrão estabelecido para integrações externas (ADR-003 — MercadoPago):

| Aspecto | MercadoPago (existente) | Uber Direct (nova) |
|---------|------------------------|--------------------|
| Credenciais | `Store.mercadopago_access_token` + env global | `UberDirectConfig` por Store + env global fallback |
| Cliente HTTP | SDK Python (`mercadopago`) | `httpx` assíncrono (sem SDK oficial Python adequado) |
| Webhook | FastAPI endpoint + Celery task | FastAPI endpoint + Celery task (mesmo padrão) |
| Validação webhook | 🔴 Ausente (L-04 — dívida técnica) | HMAC-SHA256 obrigatório (lição aprendida) |
| Token cache | N/A (SDK cuida) | Redis com TTL = `expires_in - 60s` |

---

## 3. Formatação de endereço para a API Uber (Brasil)

A API Uber exige `formatted_address` no formato:
```
Logradouro, Número - Bairro, Cidade - UF, CEP
```

Montagem a partir do modelo `Address` (campos: `street`, `number`, `complement`, `neighborhood`, `city`, `state`, `zip_code`):

```python
def format_address(addr) -> str:
    parts = [f"{addr.street}, {addr.number}"]
    if addr.complement:
        parts[0] += f", {addr.complement}"
    parts.append(f"{addr.neighborhood}, {addr.city} - {addr.state}")
    if addr.zip_code:
        parts.append(addr.zip_code)
    return " - ".join(parts)
# Resultado: "Av. Paulista, 1000, Apto 42 - Bela Vista, São Paulo - SP - 01310-100"
```

Para **guest checkout**, o endereço é digitado em campos separados no formulário. Os mesmos campos do modelo `Address` devem estar presentes no form de checkout (`street`, `number`, `complement`, `neighborhood`, `city`, `state`, `zip_code`), todos enviados via POST para o endpoint de cotação.

**Atenção BR:** CEP é opcional no modelo `Address`, mas melhora a precisão da cotação Uber. O sistema deve funcionar sem CEP — a API aceita endereço completo sem CEP.

---

## 4. Telefones no formato E.164

A API Uber exige telefones no formato `+5511999998888`. O campo `Order.customer_phone` armazena o telefone como fornecido pelo cliente (ex: `11999998888` ou `(11) 99999-8888`).

Normalização necessária antes de enviar ao Uber:
```python
import re
def to_e164(phone: str) -> str:
    digits = re.sub(r'\D', '', phone)
    if not digits.startswith('55'):
        digits = '55' + digits
    return '+' + digits
```

---

## 5. Cache do token OAuth2 com Redis

O projeto já usa `redis` como dependência (broker Celery). A biblioteca `redis-py` está disponível.

Estratégia de cache com proteção contra race condition (múltiplos workers):

```python
import redis
import json, time

r = redis.from_url(settings.REDIS_URL)

def get_cached_token(store_id: int) -> str | None:
    raw = r.get(f"uber_direct_token:{store_id}")
    if raw:
        data = json.loads(raw)
        if data['expires_at'] > time.time() + 60:
            return data['token']
    return None

def set_cached_token(store_id: int, token: str, expires_in: int):
    data = json.dumps({'token': token, 'expires_at': time.time() + expires_in})
    r.setex(f"uber_direct_token:{store_id}", expires_in - 60, data)
```

---

## 6. Validação HMAC-SHA256 do webhook

A Uber envia o header `X-Uber-Signature` com o HMAC-SHA256 do corpo da requisição assinado com a `webhook_signing_key`.

```python
import hmac, hashlib

def verify_uber_signature(raw_body: bytes, header_sig: str, signing_key: str) -> bool:
    if not header_sig:
        return False
    expected = hmac.new(
        signing_key.encode('utf-8'),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, header_sig)
```

**Importante:** O corpo da requisição deve ser lido como bytes **antes** do parse JSON, pois qualquer reserialização pode alterar a assinatura. No FastAPI, usar `raw_body = await request.body()` antes de `await request.json()`.

---

## 7. TTL da cotação e renovação automática

A cotação Uber tem TTL retornado no campo `expires` do response (Unix timestamp). Tipicamente 5 minutos.

Fluxo de renovação no `checkout()` Django:
1. Ler `quote_id` e `quote_expires_at` da sessão
2. Se `quote_expires_at < now()`: solicitar nova cotação via chamada assíncrona (ou via `sync_to_async` se necessário)
3. Atualizar sessão com novo `quote_id` e `quote_expires_at`
4. Prosseguir com checkout usando o novo `quote_id`

**Alternativa mais simples (MVP):** se cotação expirada, retornar erro 400 no checkout com mensagem "Cotação expirada, por favor confirme novamente a taxa de entrega" e forçar nova cotação no front via HTMX swap.

---

## 8. Alternativas avaliadas e descartadas

| Alternativa | Motivo de descarte |
|-------------|-------------------|
| SDK Python oficial Uber | Não há SDK oficial mantido para Uber Direct; `httpx` assíncrono é mais adequado |
| Polling de status (sem webhook) | Uber não recomenda polling excessivo; webhooks são o mecanismo padrão |
| Celery task para cotação (async background) | Cotação precisa de resposta em tempo real para o cliente no checkout; latência de task queue não é adequada |
| Armazenar token no banco (campo em `UberDirectConfig`) | I/O desnecessário a cada request; Redis é o lugar natural para cache volátil no projeto |
| Endpoint de despacho no FastAPI | Manager usa sessão/CSRF Django; Django view é mais seguro e consistente com o padrão atual |

---

## 9. Referências

- Documento de referência da API: `uber-direct-integration.md` (na raiz do projeto)
- Padrão de integração existente: `_reversa_sdd/code-analysis.md#2.4` (MercadoPago)
- Padrão de webhook existente: `_reversa_sdd/code-analysis.md#2.6` (FastAPI webhook MP)
- ADR relevante: `_reversa_sdd/adrs/003-pagamento-pix-mercadopago.md`
- Modelo `Address`: `_reversa_sdd/data-dictionary.md#Address`
