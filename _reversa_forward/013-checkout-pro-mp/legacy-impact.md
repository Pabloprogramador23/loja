# Legacy Impact: 013-checkout-pro-mp

> Data: 2026-05-30
> Feature: Checkout Pro MercadoPago (011-B)

## Arquivos Afetados

| Arquivo afetado | Componente (_reversa_sdd_) | Tipo | Severidade | Justificativa |
|-----------------|---------------------------|------|------------|---------------|
| `core/models.py` | `_reversa_sdd/architecture.md#Módulo core` | delta-de-dados | LOW | Campo `mp_preference_id` adicionado ao Order |
| `core/migrations/0013_order_mp_preference_id.py` | `_reversa_sdd/architecture.md#delta-de-dados` | delta-de-dados | LOW | Migration aditiva |
| `store_saas/settings.py` | `_reversa_sdd/architecture.md#Stack` | regra-nova | LOW | `SITE_URL` adicionado |
| `core/payment.py` | `_reversa_sdd/code-analysis.md#2.4` | regra-alterada | HIGH | Nova função `create_checkout_pro_preference()`; `create_pix_payment()` mantida inativa |
| `core/views.py` | `_reversa_sdd/code-analysis.md#2.3` | regra-alterada | HIGH | `checkout()` usa preference; 4 novas views de retorno |
| `core/urls.py` | `_reversa_sdd/architecture.md#Rotas Django` | regra-nova | LOW | 4 novas rotas `/payment/success|pending|failure|mock/` |
| `core/api.py` | `_reversa_sdd/code-analysis.md#Webhook` | regra-alterada | HIGH | Webhook trata `payment.created`; lookup por `external_reference` |
| `core/tests_checkout_pro.py` | — | componente-novo | LOW | 8 testes |
| `templates/core/payment_success.html` | — | componente-novo | — | Tela de pagamento aprovado |
| `templates/core/payment_pending.html` | — | componente-novo | — | Tela de pagamento pendente |
| `templates/core/payment_failure.html` | — | componente-novo | — | Tela de pagamento falhou |
| `templates/core/payment_mock.html` | — | componente-novo | — | Simulador dev |

## Diff conceitual por componente

### `create_checkout_pro_preference()` — componente-novo em payment.py
Substitui funcionalmente `create_pix_payment()` no fluxo de checkout. Usa `sdk.preference().create()` em vez de `sdk.payment().create()`. Retorna `init_point` (URL) em vez de QR Code. Mock dev preservado: token `TEST-0000` retorna URL local `/payment/mock/`.

### `checkout()` — regra-alterada
Antes: chamava `create_pix_payment()`, salvava na sessão, renderizava `payment_pix.html`. Agora: chama `create_checkout_pro_preference()`, redireciona para `init_point` via `window.location.href`.

### `mercadopago_webhook` — regra-alterada
Antes: tratava apenas `payment.updated`, buscava Order por `mp_payment_id`. Agora: trata `payment.created` e `payment.updated`; busca Order por `external_reference` (= `order.id`) com fallback para `mp_payment_id`; salva `mp_payment_id` no Order após encontrá-lo.

## Preservadas

- **RN-09** — Token MP por tenant: `create_checkout_pro_preference` resolve token identicamente a `create_pix_payment`
- **RN-10** — Mock dev: preservado com adaptação para Checkout Pro
- **RN-14** — Webhook: transição `PENDING → PREPARING` após aprovação MP mantida
- **RN-01** — Isolamento de tenant por ContextVar (não tocado)
- **RN-12** — Acesso ao dashboard por `is_staff` (não tocado)

## Modificadas

- **RN-10** (parcialmente alterada) — Mock agora retorna URL local `/payment/mock/` em vez de QR Code hardcoded. Comportamento de mock preservado, formato alterado.
- **RN-14** (expandida) — Webhook agora trata `payment.created` além de `payment.updated`, e usa `external_reference` como chave de lookup primária.
