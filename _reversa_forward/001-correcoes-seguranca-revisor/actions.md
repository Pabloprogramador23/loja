# Actions: Correções de Segurança (Revisor)

> Identificador: `001-correcoes-seguranca-revisor`
> Data: `2026-05-26`
> Roadmap: `_reversa_forward/001-correcoes-seguranca-revisor/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 17 |
| Paralelizáveis (`[//]`) | 8 |
| Maior cadeia de dependência | 6 (T001 → T002 → T013 → T014 → T015 → T017) |

---

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Adicionar campo `mp_payment_id = CharField(max_length=64, null=True, blank=True, unique=True, db_index=True)` à classe `Order` em `models.py` | - | `[//]` | `core/models.py` | 🟢 | `[X]` |
| T002 | Executar `python manage.py makemigrations core --name add_mp_payment_id_to_order` e `python manage.py migrate`; verificar que a migration foi aplicada sem erro | T001 | - | `core/migrations/` | 🟢 | `[X]` |
| T003 | Em `settings.py`: substituir `SECRET_KEY = 'django-insecure-...'` por `config('SECRET_KEY')`; substituir `DEBUG = True` por `config('DEBUG', default=False, cast=bool)`; substituir `ALLOWED_HOSTS = ['*']` por `config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())` | - | `[//]` | `store_saas/settings.py` | 🟢 | `[X]` |
| T004 | Em `settings.py`: adicionar `MERCADOPAGO_WEBHOOK_SECRET = config('MERCADOPAGO_WEBHOOK_SECRET', default='')` logo após a linha de `MERCADOPAGO_ACCESS_TOKEN`; adicionar import de `Csv` do decouple se necessário | T003 | - | `store_saas/settings.py` | 🟢 | `[X]` |
| T005 | Criar `.env.example` na raiz do projeto com todas as variáveis: `SECRET_KEY`, `DEBUG`, `DATABASE_URL`, `REDIS_URL`, `ALLOWED_HOSTS`, `MERCADOPAGO_ACCESS_TOKEN`, `MERCADOPAGO_WEBHOOK_SECRET`, `REVERSA_TESTING`; incluir comentários explicativos e valores de exemplo seguros | - | `[//]` | `.env.example` | 🟢 | `[X]` |

---

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T006 | Em `tests_dashboard.py`: adicionar (ou criar arquivo se vazio) teste `test_order_details_modal_non_staff_returns_403` — cria usuário sem `is_staff`, faz login, GET para `/dashboard/order/1/details/`, asserta HTTP 403 | T003 | `[//]` | `core/tests_dashboard.py` | 🟢 | `[X]` |
| T007 | Em `tests_checkout.py`: localizar teste(s) de checkout e adicionar campo `customer_email` ao POST data; adicionar teste `test_checkout_guest_without_email_fails` — faz checkout sem email, asserta erro de validação | - | `[//]` | `core/tests_checkout.py` | 🟢 | `[X]` |

---

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T008 | Reescrever `TenantMiddleware.__call__`: (1) tentar resolver por `request.get_host()` extraindo subdomain (`host.split(':')[0].split('.')` com guard de comprimento mínimo 3); (2) se não resolver, tentar header `X-Tenant-Subdomain`; (3) se ainda sem tenant, checar se localhost/127.0.0.1 → usar primeiro store ativo; (4) se subdomain encontrado mas Store inativa/inexistente → `return HttpResponse(status=404)` | - | `[//]` | `core/middleware.py` | 🟢 | `[X]` |
| T009 | Em `order_details_modal` (`views.py:251-253`): substituir o bloco `if not request.user.is_staff: pass` por `if not request.user.is_staff: return HttpResponse(status=403)` | - | `[//]` | `core/views.py` | 🟢 | `[X]` |
| T010 | Em `checkout` (`views.py`): (1) adicionar leitura de `customer_email = request.POST.get('customer_email')` logo após leitura de `address`; (2) para guests (`not request.user.is_authenticated`), validar que `customer_email` não está vazio e é um email minimamente válido — retornar erro se ausente; (3) armazenar `customer_email` na sessão ou passá-lo como argumento para `create_pix_payment(order, customer_email)` | T009 | - | `core/views.py` | 🟢 | `[X]` |
| T011 | Em `create_pix_payment(order, customer_email=None)` (`payment.py`): (1) atualizar assinatura da função para aceitar `customer_email`; (2) usar `customer_email or (order.user.email if order.user else None)` em `payer.email` — erro explícito se ambos forem None; (3) após `sdk.payment().create(payment_data)` com status 201, salvar `order.mp_payment_id = response['id']; order.save(update_fields=['mp_payment_id'])` | T002, T010 | - | `core/payment.py` | 🟢 | `[X]` |
| T012 | Refatorar `process_new_order` em `tasks.py`: (1) adicionar decorator `@shared_task(bind=True, max_retries=3, default_retry_delay=60)`; (2) adicionar assinatura `def process_new_order(self, order_id):`; (3) após buscar a Order, adicionar guard `if order.status != Order.Status.PREPARING: return`; (4) remover `time.sleep(2)` e o bloco `order.status = PREPARING; order.save()`; (5) envolver restante em `try/except Exception as exc: raise self.retry(exc=exc)` | - | `[//]` | `core/tasks.py` | 🟢 | `[X]` |

---

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T013 | Em `mercadopago_webhook` (`api.py`): adicionar validação HMAC no início da função — extrair `x-signature` e `x-request-id` do request, extrair `payment_id` do payload, montar manifest `f"id:{payment_id};request-id:{x_request_id};ts:{ts}"`, verificar com `hmac.compare_digest`; retornar `HTTPException(status_code=401)` se inválido; se `MERCADOPAGO_WEBHOOK_SECRET` estiver vazio e `REVERSA_TESTING=true`, pular validação HMAC | T004, T002 | - | `core/api.py` | 🟢 | `[X]` |
| T014 | Em `mercadopago_webhook` (`api.py`): (1) remover todo o bloco `if action == "test.approved"` (backdoor); (2) adicionar bloco `if action == "test.approved" and settings.REVERSA_TESTING: ...` com aprovação via order_id somente quando env flag ativo; (3) no bloco `payment.updated`: substituir lookup por `external_reference` por `Order.objects.aget(mp_payment_id=payment_id)`; usar `order.store.mercadopago_access_token` como token do SDK; adicionar handler `elif status in ("cancelled", "expired"): await sync_to_async(cancel_order_on_pix_expiry)(order_id)` | T013 | - | `core/api.py` | 🟢 | `[X]` |
| T015 | Em `check_order_status` (`api.py:171`): adicionar parâmetro `tenant: Store = Depends(get_tenant_dependency)` à assinatura da função; atualizar query `Order.objects.aget(id=order_id)` — o TenantManager filtrará automaticamente pelo tenant via ContextVar já setado pela dependency | T014 | - | `core/api.py` | 🟢 | `[X]` |
| T016 | Em `views.py`: (1) criar função auxiliar `cancel_order_on_pix_expiry(order_id)` que busca a Order e muda status PENDING → CANCELED; (2) atualizar `update_order_status`: ao receber `new_status == CANCELED`, chamar MP SDK conforme tabela de estorno — `sdk.payment().update(mp_payment_id, {"status": "cancelled"})` para PENDING ou `sdk.payment().refund(mp_payment_id)` para PREPARING/DELIVERING; tratar falha de estorno com log (não bloquear o cancelamento) | T010 | - | `core/views.py` | 🟢 | `[X]` |

---

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T017 | Em `mercadopago_webhook` (`api.py`): adicionar `import logging` se ausente; criar `logger = logging.getLogger(__name__)`; no bloco de falha HMAC, adicionar `logger.warning("HMAC validation failed for webhook request from %s", request.client.host)` antes de retornar 401; não logar o header `x-signature` nem o segredo | T015 | - | `core/api.py` | 🟡 | `[X]` |

---

## Notas de execução

<!-- Reservado para /reversa-coding registrar avisos ou observações durante a execução. -->

---

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-26 | Versão inicial gerada por `/reversa-to-do` | reversa |
