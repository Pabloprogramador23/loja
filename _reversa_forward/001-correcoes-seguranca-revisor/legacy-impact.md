# Legacy Impact: Correções de Segurança (Revisor)

> Feature: `001-correcoes-seguranca-revisor`
> Data: `2026-05-26`
> Âncora reversa: `_reversa_sdd/architecture.md`, `_reversa_sdd/domain.md`

---

## Arquivos afetados

| Arquivo afetado | Componente (`_reversa_sdd/`) | Tipo | Severidade | Justificativa |
|-----------------|------------------------------|------|------------|---------------|
| `store_saas/settings.py` | `store_saas` — configuração central | regra-alterada | HIGH | SECRET_KEY, DEBUG, ALLOWED_HOSTS movidos para env vars; sem impacto em runtime com .env correto |
| `core/models.py` | `core` — modelo Order | delta-de-dados | HIGH | Novo campo `mp_payment_id` — sem breaking change (nullable), migration aplicada |
| `core/migrations/0006_add_mp_payment_id_to_order.py` | `core` — schema | delta-de-dados | HIGH | Migration que adiciona o campo — reversível |
| `core/middleware.py` | `core/multi-tenancy` — TenantMiddleware | regra-alterada | HIGH | Inversão de prioridade: host-first antes do header; 404 para subdomain inválido |
| `core/views.py` | `core/checkout`, `core/dashboard-manager`, `core/pedidos` | regra-alterada | HIGH | Múltiplas correções: modal 403, checkout email, update_order_status com estorno |
| `core/payment.py` | `core/pagamento` — create_pix_payment | regra-alterada | HIGH | Assinatura alterada (customer_email param); salva mp_payment_id na Order |
| `core/api.py` | `core/api-fastapi` — webhook, check-status | regra-alterada | HIGH | HMAC adicionado; backdoor removido; webhook redesenhado; check-status escopado |
| `core/tasks.py` | `core/celery-tasks` — process_new_order | regra-alterada | MEDIUM | Guard + retry; remoção de status set e sleep |
| `.env.example` | `store_saas` — configuração | componente-novo | LOW | Novo artefato de documentação de ambiente |

---

## Diff conceitual por componente

### `core/multi-tenancy` (middleware.py)

**Antes:** header `X-Tenant-Subdomain` tinha prioridade; fallback localhost usava primeiro store ativo; subdomain inválido retornava `tenant=None` silenciosamente → dados sem filtro de tenant.

**Depois:** `request.get_host()` tem prioridade 1 (production); header é fallback de dev/API; subdomain válido mas sem store → HTTP 404 explícito; localhost continua usando primeiro store ativo.

### `core/api-fastapi` (api.py)

**Antes:** webhook sem autenticação; backdoor `test.approved` sempre ativo; lookup por `external_reference` + token global; check-status sem escopo de tenant.

**Depois:** HMAC-SHA256 obrigatório (ou REVERSA_TESTING=true em dev); backdoor protegido por env flag; lookup por `mp_payment_id` com token da loja correta; check-status escopado via `Depends(get_tenant_dependency)`.

### `core/pagamento` (payment.py)

**Antes:** `payer.email` usava placeholder `"test_user_123@test.com"` para convidados; `mp_payment_id` não era armazenado.

**Depois:** `customer_email` passado via parâmetro; salvo em `order.mp_payment_id` após criação bem-sucedida do PIX.

### `core/pedidos` + `core/dashboard-manager` (views.py)

**Antes:** `order_details_modal` com `pass` — não-staff acedia normalmente; `update_order_status` sem estorno MP.

**Depois:** `order_details_modal` retorna 403 para não-staff; `update_order_status` chama MP cancel/refund ao cancelar; `cancel_order_on_pix_expiry` helper adicionado.

### `core/celery-tasks` (tasks.py)

**Antes:** `process_new_order` setava `status = PREPARING` (double-set) + `time.sleep(2)` + sem retry.

**Depois:** guard `if order.status != PREPARING: return`; sem sleep; retry `max_retries=3, default_retry_delay=60`.

---

## Regras preservadas (🟢 de `_reversa_sdd/domain.md` que continuam intactas)

- **RN-01** Snapshot de preço — `OrderItem.unit_price` inalterado
- **RN-02** Carrinho por tenant — `session['cart_{tenant_id}']` inalterado
- **RN-03** Guest checkout — `guest_order_id` na sessão preservado
- **RN-04** Limite de 3 endereços — `Address.save()` inalterado
- **RN-05** TenantManager auto-filtra queries — `objects.get_queryset()` inalterado
- **RN-06** Máquina de estados Order — transições preservadas; estorno adicionado como efeito colateral de CANCELED
- **RN-07** `is_available` controla visibilidade de produto — inalterado
- **RN-08** ASGI híbrido: Django + FastAPI no mesmo processo — inalterado
- **RN-09** Celery worker sem contexto de tenant → TenantManager retorna ALL — inalterado (intencional)
- **RN-10** `Store.is_active=False` exclui loja da resolução de tenant — preservado e reforçado

---

## Regras modificadas

| Regra original | O que mudou | Watch item |
|----------------|-------------|------------|
| L-10 `SECRET_KEY` hardcoded | Movido para `config('SECRET_KEY')` — obrigatório no .env | W001 |
| L-02 Backdoor `test.approved` | Removido do código; substituído por flag `REVERSA_TESTING` | W002 |
| L-01 Tenant via header priority | Invertido: host agora é prioridade 1 | W003 |
| L-04 Webhook sem HMAC | HMAC-SHA256 adicionado; 401 para assinatura inválida | W004 |
| L-06 Token global no webhook | Webhook usa `order.store.mercadopago_access_token` | W005 |
| L-03 IDOR check-status | Adicionado `Depends(get_tenant_dependency)` | W006 |
| G-01 Modal bypass (is_staff) | `pass` substituído por `return HttpResponse(status=403)` | W007 |
| L-07 Double-set PREPARING | Guard idempotente adicionado na task Celery | W008 |
| L-05 Email placeholder guest | `customer_email` agora obrigatório e salvo via parâmetro | W009 |
| D-02 mp_payment_id ausente | Campo adicionado ao modelo + salvo em payment.py | W010 |
