# Regression Watch: Correções de Segurança (Revisor)

> Feature: `001-correcoes-seguranca-revisor`
> Data: `2026-05-26`
> Gerado por: `/reversa-coding`

---

## Watch Items

| ID | Origem | Regra esperada após mudança | Tipo | Sinal de violação |
|----|--------|------------------------------|------|-------------------|
| W001 | `store_saas/settings.py` + `_reversa_sdd/store_saas/requirements.md#rf-02` | `SECRET_KEY` lido via `config('SECRET_KEY')`, sem valor literal no código | presença | `grep "django-insecure"` retorna resultado em `settings.py` |
| W002 | `core/api.py` + `_reversa_sdd/questions.md#p-03` | String literal `"test.approved"` só aparece dentro do bloco `if settings.REVERSA_TESTING` | redação | `grep -n "test.approved" core/api.py` mostra linha fora do bloco REVERSA_TESTING |
| W003 | `core/middleware.py` + `_reversa_sdd/core/multi-tenancy/design.md` | `request.get_host()` é chamado ANTES de `request.headers.get('X-Tenant-Subdomain')` no fluxo de resolução | presença | Middleware lê header antes de host, ou host está comentado |
| W004 | `core/api.py:mercadopago_webhook` + `_reversa_sdd/core/pagamento/design.md` | `hmac.compare_digest` presente na função `mercadopago_webhook`; retorna 401 antes de processar payload quando HMAC falha | presença | Função webhook não importa `hmac` ou não tem `status_code=401` |
| W005 | `core/api.py:mercadopago_webhook` + `_reversa_sdd/questions.md#p-08` | Token MP usado no webhook vem de `order.store.mercadopago_access_token`, não de `settings.MERCADOPAGO_ACCESS_TOKEN` direto | redação | Webhook usa `settings.MERCADOPAGO_ACCESS_TOKEN` sem buscar a loja primeiro |
| W006 | `core/api.py:check_order_status` + `_reversa_sdd/core/api-fastapi/requirements.md#rf-04` | `check_order_status` tem `tenant: Store = Depends(get_tenant_dependency)` na assinatura | presença | Função `check_order_status` sem parâmetro `tenant` ou sem `Depends` |
| W007 | `core/views.py:order_details_modal` + `_reversa_sdd/core/dashboard-manager/requirements.md#g-01` | Bloco `if not request.user.is_staff` retorna `HttpResponse(status=403)`, não `pass` | redação | `grep "pass" core/views.py` retorna resultado dentro de `order_details_modal` |
| W008 | `core/tasks.py:process_new_order` + `_reversa_sdd/questions.md#p-10` | Task contém guard `if order.status != Order.Status.PREPARING: return` antes de qualquer processamento | presença | Task sem o guard, ou guard após lógica de negócio |
| W009 | `core/payment.py:create_pix_payment` + `_reversa_sdd/questions.md#p-04` | Função aceita `customer_email` como parâmetro; `payer.email` não usa placeholder `"test_user_123@test.com"` | ausência | String `test_user_123` presente em `payment.py` |
| W010 | `core/payment.py` + `core/models.py` + `_reversa_sdd/questions.md#p-08` | `order.mp_payment_id` é setado e salvo após criar pagamento PIX com sucesso | presença | `create_pix_payment` não atribui `order.mp_payment_id` ou não chama `order.save()` |

---

## Observações (🟡 — sem peso de regressão)

| Observação | Contexto |
|------------|---------|
| `MERCADOPAGO_WEBHOOK_SECRET` vazio em dev não gera erro se `REVERSA_TESTING=true` | Comportamento intencional para facilitar desenvolvimento local |
| Localhost/127.0.0.1 ainda usa primeiro store ativo como fallback | Comportamento de dev preservado; não é regressão |
| `cancel_order_on_pix_expiry` definida tanto em `api.py` quanto em `views.py` | Duplicação intencional para evitar circular import; ambas têm o mesmo comportamento |

---

## Histórico de re-extrações

> Esta seção é preenchida automaticamente pelo `/reversa` quando a pipeline reversa roda novamente sobre o projeto. Cada re-extração compara os artefatos `_reversa_sdd/` com os watch items acima e registra: data, versão da extração, veredito por item (🟢 ok / 🟡 mudou / 🔴 violado).

---

## Arquivadas

> Watch items que foram verificados e confirmados como permanentemente resolvidos, ou que se tornaram irrelevantes após mudança de escopo.
