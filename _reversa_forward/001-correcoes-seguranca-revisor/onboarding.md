# Onboarding: Correções de Segurança (Revisor)

> Feature: `001-correcoes-seguranca-revisor`
> Para: desenvolvedor que vai testar pela primeira vez após a implementação

---

## Pré-requisitos

- Python 3.12 instalado
- Docker + docker-compose (para PostgreSQL + Redis) **ou** SQLite local
- Acesso à pasta do projeto: `C:\Users\Pablo\Desktop\loja`

---

## Passo 1 — Criar o `.env`

Copie o `.env.example` e preencha as variáveis:

```bash
cp .env.example .env
```

Edite o `.env` com valores reais para o seu ambiente. No mínimo para testes locais:

```env
SECRET_KEY=<gere com: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0
ALLOWED_HOSTS=localhost,127.0.0.1
MERCADOPAGO_ACCESS_TOKEN=TEST-000...
MERCADOPAGO_WEBHOOK_SECRET=<opcional em dev, pode deixar vazio>
REVERSA_TESTING=true
```

---

## Passo 2 — Aplicar a migration

```bash
python manage.py migrate
```

Verifique que a migration `core/migrations/000X_add_mp_payment_id_to_order.py` foi aplicada. O campo `mp_payment_id` deve aparecer no schema.

---

## Passo 3 — Subir o servidor

```bash
python -m uvicorn store_saas.asgi:application --reload --port 8000
```

---

## Passo 4 — Verificar variáveis de ambiente (checagem rápida)

Abra `http://localhost:8000/admin/` e confirme que o Django sobe sem `ImproperlyConfigured`. Se subiu, as env vars estão corretas.

---

## Passo 5 — Testar autorização no dashboard

### 5a. Criar usuário non-staff (se não existir)

```bash
python manage.py shell -c "
from django.contrib.auth.models import User
User.objects.create_user('testuser', 'test@test.com', 'senha123')
"
```

### 5b. Logar como non-staff

Acesse `http://localhost:8000/accounts/login/` com o usuário criado.

### 5c. Tentar acessar modal de pedido

Com qualquer pedido existente (ID `N`):
```
GET http://localhost:8000/dashboard/order/N/details/
```

**Esperado:** HTTP 403 (antes desta feature: HTTP 200 com dados do pedido)

### 5d. Logar como staff e confirmar acesso

```bash
python manage.py shell -c "
from django.contrib.auth.models import User
User.objects.filter(username='admin').update(is_staff=True)
"
```

Re-acessar o mesmo endpoint → **Esperado:** HTTP 200

---

## Passo 6 — Testar tenant por host

O teste de host-based tenant requer que o `TenantMiddleware` corrigido esteja ativo.

### 6a. Criar uma loja de teste

```bash
python manage.py shell -c "
from core.models import Store
Store.objects.get_or_create(name='Loja A', subdomain='loja-a')
"
```

### 6b. Simular request com Host correto (via curl)

```bash
curl -H "Host: loja-a.localhost" http://localhost:8000/
```

**Esperado:** Página da Loja A carregada (não erro 404)

### 6c. Subdomain inválido

```bash
curl -H "Host: inexistente.localhost" http://localhost:8000/
```

**Esperado:** HTTP 404

---

## Passo 7 — Testar checkout de convidado com email

1. Acesse o catálogo em `http://localhost:8000/`
2. Adicione um produto ao carrinho
3. Vá ao checkout sem estar logado
4. Tente submeter o formulário **sem** preencher o campo `customer_email`

**Esperado:** Mensagem de erro pedindo o email

5. Preencha um email válido e submeta
6. O PIX deve ser gerado com o email correto no MP (ou mock em dev)

---

## Passo 8 — Testar webhook com REVERSA_TESTING=true

Com `REVERSA_TESTING=true` no `.env`, o backdoor oficial de teste está ativo.

### 8a. Crie um pedido (via checkout ou shell)

```bash
python manage.py shell -c "
from core.models import Order, Store
store = Store.objects.first()
order = Order.objects.create(
    store=store, customer_name='Teste', customer_phone='11999999999',
    delivery_address='Rua Teste, 1', total_amount='50.00', status='PENDING',
    mp_payment_id='TEST_PAY_001'
)
print('Order ID:', order.id)
"
```

### 8b. Dispare o webhook de teste

```bash
curl -X POST http://localhost:8000/api/webhooks/mercadopago \
  -H "Content-Type: application/json" \
  -d '{"action": "test.approved", "order_id": <ID_DO_PEDIDO>}'
```

**Esperado:** `{"status": "ok", "mode": "test"}` e Order mudada para PREPARING no banco

### 8c. Testar com assinatura inválida (sem REVERSA_TESTING)

Remova `REVERSA_TESTING` do `.env`, reinicie o servidor e tente:

```bash
curl -X POST http://localhost:8000/api/webhooks/mercadopago \
  -H "Content-Type: application/json" \
  -H "x-signature: ts=123,v1=invalido" \
  -H "x-request-id: req-001" \
  -d '{"action": "payment.updated", "data": {"id": "123"}}'
```

**Esperado:** HTTP 401

---

## Passo 9 — Testar Celery task (guard)

```bash
# Terminal 1 — worker
celery -A store_saas worker --loglevel=info

# Terminal 2 — disparar task manualmente com Order não-PREPARING
python manage.py shell -c "
from core.tasks import process_new_order
from core.models import Order
order = Order.objects.filter(status='COMPLETED').first()
if order:
    process_new_order.delay(order.id)
    print('Task disparada para Order', order.id, 'status:', order.status)
"
```

**Esperado:** No log do worker: task retornada sem processar (guard ativado)

---

## O que NÃO esperar neste onboarding

- Estorno automático não é testável sem conta MP real
- `render_to_string` via `sync_to_async` — mudança transparente, sem comportamento visível
- PIX real — dev usa mock quando `MERCADOPAGO_ACCESS_TOKEN` começa com `TEST-0000`
