# Actions: Checkout Pro MercadoPago (011-B)

> Identificador: `013-checkout-pro-mp`
> Data: `2026-05-30`
> Roadmap: `_reversa_forward/013-checkout-pro-mp/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 17 |
| Paralelizáveis (`[//]`) | 10 |
| Maior cadeia de dependência | 7 (T003→T008→T009→T010→T012→T013→T017) |

## Fase 1 — Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Adicionar campo `mp_preference_id = CharField(max_length=255, blank=True, default='', db_index=True)` à classe `Order` em `core/models.py`, logo após o campo `mp_payment_id` existente | - | - | `core/models.py` | 🟡 | `[X]` |
| T002 | Criar migration `core/migrations/0013_order_mp_preference_id.py` conforme `data-delta.md`; dependência: `0012_userprofile` | T001 | - | `core/migrations/0013_order_mp_preference_id.py` | 🟢 | `[X]` |
| T003 | Adicionar `SITE_URL = config('SITE_URL', default='http://localhost:8000')` em `store_saas/settings.py`; adicionar `SITE_URL=http://localhost:8000` em `.env`; adicionar `SITE_URL=https://seu-dominio.com` (placeholder) em `.env.prod` | - | `[//]` | `store_saas/settings.py`, `.env`, `.env.prod` | 🟡 | `[X]` |

## Fase 2 — Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Escrever testes para `create_checkout_pro_preference()`: (a) token `TEST-0000` retorna init_point local (`/payment/mock/`) e salva `mp_preference_id='MOCK_PREF_{id}'`; (b) token real: mockar SDK e verificar que `mp_preference_id` é salvo no Order | T002 | `[//]` | `core/tests_checkout.py` | 🟡 | `[X]` |
| T005 | Escrever teste para `checkout()` view atualizado: POST com carrinho e usuário autenticado → response contém `window.location.href` apontando para um init_point (mock ou real) | T002 | `[//]` | `core/tests_checkout.py` | 🟡 | `[X]` |
| T006 | Escrever testes para as 3 views de retorno: `payment_success_view` retorna 200 com conteúdo de sucesso; `payment_pending_view` retorna 200; `payment_failure_view` retorna 200; todas funcionam sem Order correspondente nos query params | T002 | `[//]` | `core/tests_checkout.py` | 🟡 | `[X]` |
| T007 | Escrever testes para webhook atualizado: (a) action `payment.created` dispara `update_paid_order` quando status é `approved`; (b) lookup usa `external_reference` do payment response (não `mp_payment_id`); (c) `order.mp_payment_id` é preenchido pelo webhook | T002 | `[//]` | `core/tests_uber.py` ou novo `core/tests_webhook.py` | 🟡 | `[X]` |

## Fase 3 — Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T008 | Implementar `create_checkout_pro_preference(order)` em `core/payment.py`: (a) resolver token (tenant ou global, igual ao `create_pix_payment`); (b) se mock → salvar `mp_preference_id='MOCK_PREF_{id}'` no order e retornar `{'init_point': f'/payment/mock/?order_id={order.id}', 'preference_id': 'MOCK_PREF_{id}'}`; (c) senão: montar `preference_data` com `items` (iterar `order.items.all()`), `payer` (email e nome do user), `back_urls` usando `settings.SITE_URL`, `auto_return='approved'`, `external_reference=str(order.id)`, `statement_descriptor=order.store.name[:22]`; (d) chamar `sdk.preference().create(preference_data)`; (e) salvar `order.mp_preference_id = response['id']`; (f) retornar `{'init_point': response['init_point'], 'preference_id': response['id']}` | T003 | - | `core/payment.py` | 🟡 | `[X]` |
| T009 | Atualizar `checkout()` em `core/views.py`: substituir chamada `create_pix_payment(order, customer_email=payer_email)` por `create_checkout_pro_preference(order)`; substituir render de `payment_pix.html` por `HttpResponse(f'<script>window.location.href="{result["init_point"]}";</script>')`; manter `session[f'payment_data_{order.id}']` para compatibilidade, ou remover se não mais usado | T008 | - | `core/views.py` | 🟡 | `[X]` |
| T010 | Adicionar 4 novas views em `core/views.py`: (a) `payment_success_view(request)`: lê `payment_id`, `preference_id`, `status` de `request.GET`; renderiza `core/payment_success.html`; (b) `payment_pending_view(request)`: renderiza `core/payment_pending.html`; (c) `payment_failure_view(request)`: renderiza `core/payment_failure.html`; (d) `payment_mock_view(request)`: apenas quando `settings.REVERSA_TESTING`; lê `order_id` de GET; chama `update_paid_order(order_id)`; redireciona para `/payment/success/` | T009 | - | `core/views.py` | 🟡 | `[X]` |
| T011 | Atualizar `mercadopago_webhook` em `core/api.py`: (a) adicionar `"payment.created"` ao `if action == "payment.updated":` → `if action in ("payment.updated", "payment.created"):`; (b) após `sdk.payment().get(payment_id)`, ler `order_id = payment_response.get("external_reference")`; (c) fazer lookup `await Order.objects.aget(id=int(order_id))` em vez de `aget(mp_payment_id=str(payment_id))`; (d) salvar `order.mp_payment_id = str(payment_id)` + `await order.asave(update_fields=["mp_payment_id"])` antes de chamar `update_paid_order` | T002 | `[//]` | `core/api.py` | 🟡 | `[X]` |

## Fase 4 — Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T012 | Adicionar 4 novas rotas em `core/urls.py`: `path('payment/success/', views.payment_success_view, name='payment_success')`, `path('payment/pending/', views.payment_pending_view, name='payment_pending')`, `path('payment/failure/', views.payment_failure_view, name='payment_failure')`, `path('payment/mock/', views.payment_mock_view, name='payment_mock')` | T010 | - | `core/urls.py` | 🟢 | `[X]` |
| T013 | Criar `templates/core/payment_success.html`: estende `base.html`; ícone de check verde; "Pedido confirmado!"; número do pedido se disponível nos GET params; link para acompanhar pedido (`/order/{id}/track/`) | T012 | `[//]` | `templates/core/payment_success.html` | 🟡 | `[X]` |
| T014 | Criar `templates/core/payment_pending.html`: estende `base.html`; ícone de relógio amarelo; "Pagamento em processamento"; instrução de verificar e-mail ou aguardar aprovação do PIX | T012 | `[//]` | `templates/core/payment_pending.html` | 🟡 | `[X]` |
| T015 | Criar `templates/core/payment_failure.html`: estende `base.html`; ícone de X vermelho; "Pagamento não concluído"; botão "Tentar novamente" que leva de volta ao catálogo | T012 | `[//]` | `templates/core/payment_failure.html` | 🟡 | `[X]` |
| T016 | Criar `templates/core/payment_mock.html`: estende `base.html`; aviso de ambiente de desenvolvimento; botão "Simular pagamento aprovado" que faz GET para `/payment/mock/?order_id={order_id}` | T012 | `[//]` | `templates/core/payment_mock.html` | 🟡 | `[X]` |

## Fase 5 — Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T017 | Gerar `regression-watch.md` com watch items: W001 — checkout redireciona para init_point (não renderiza QR Code); W002 — mp_preference_id salvo no Order após checkout; W003 — webhook trata payment.created e atualiza Order.status para PREPARING; W004 — token por tenant preservado na preference; W005 — mock dev funciona sem conta MP real | T013, T014, T015, T016 | - | `_reversa_forward/013-checkout-pro-mp/regression-watch.md` | 🟢 | `[X]` |

## Notas de execução

<!-- Reservado para /reversa-coding registrar avisos durante a execução. -->

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-30 | Versão inicial gerada por `/reversa-to-do` | reversa |
