# Legacy Impact: 018-mp-ux-checkout

> Data: `2026-06-04`
> Feature: `018-mp-ux-checkout`
> Pipeline reversa de referência: `_reversa_sdd/` (re-extração 2026-05-31)

---

## Arquivos afetados

| Arquivo afetado | Componente (`_reversa_sdd/`) | Tipo | Severidade | Justificativa |
|-----------------|------------------------------|------|------------|---------------|
| `core/views.py` | `core/checkout` (`architecture.md#Fluxo principal`) | regra-alterada | LOW | Script de resposta do checkout muda de navegação full-page para nova aba + redirect para tela de espera |
| `core/views.py` | `core/pagamento` (`architecture.md#Integrações Externas`) | regra-nova | LOW | Duas novas views públicas: `payment_waiting_view` e `payment_waiting_status_view` |
| `core/views.py` | `core/pagamento` | regra-alterada | LOW | `payment_failure_view` e `payment_pending_view` agora carregam o `Order` associado |
| `core/urls.py` | `store_saas/roteamento-asgi` | contrato-novo | LOW | Duas novas rotas: `/payment/waiting/` e `/payment/waiting/status/` |
| `templates/core/payment_waiting.html` | — | componente-novo | LOW | Tela de espera pública com HTMX polling |
| `templates/core/partials/payment_waiting_status.html` | — | componente-novo | LOW | Partial de status para polling; emite `HX-Trigger: stopPolling` quando status sai de PENDING |
| `templates/core/payment_failure.html` | — | regra-alterada | LOW | Exibe número do pedido e link de rastreio quando `order` está no contexto |
| `templates/core/payment_pending.html` | — | regra-alterada | LOW | Idem |
| `core/tests_payment_ux.py` | — | componente-novo | LOW | 11 novos testes cobrindo as views novas e as alteradas |

---

## Diff conceitual por componente

### `views.checkout` (core/views.py)

**Antes:** `return HttpResponse('<script>window.location.href="{init_point}";</script>')`
**Depois:** `return HttpResponse('<script>var _mp=window.open("{init_point}","_blank");window.location.href="/payment/waiting/?order_id={order.id}";</script>')`

O comportamento do backend é idêntico — o script só muda a forma como o frontend reage. O `init_point` continua sendo a URL do MP. O order já existia antes do `return`.

### `views.payment_failure_view` e `views.payment_pending_view`

**Antes:** Renderizavam template com apenas `payment_id` no contexto.
**Depois:** Buscam `Order` por `mp_preference_id` → `external_reference` → `session['guest_order_id']`. Template recebe `order` (pode ser `None`; templates são condicionais).

### Views novas

`payment_waiting_view` e `payment_waiting_status_view` são adições puras — não alteram nenhuma view existente.

---

## Regras preservadas

As seguintes regras do `_reversa_sdd/domain.md` permanecem **intactas**:

| Regra | Status |
|-------|--------|
| RN-04: Checkout requer nome, telefone e endereço | ✅ Preservada — `checkout()` não foi alterado nessa lógica |
| RN-05: Guest order com `session['guest_order_id']` | ✅ Preservada — sessão ainda é escrita em `checkout()` linha 251 |
| RN-09: Token MP por tenant | ✅ Preservada — `create_checkout_pro_preference` não foi alterada |
| RN-10: Fallback mock em desenvolvimento | ✅ Preservada — mock continua funcionando; a nova aba abrirá `/payment/mock/` |
| RN-16: Rastreamento público em `/order/{id}/track/` | ✅ Preservada — a tela de espera usa esta rota como link |

---

## Regras modificadas

| Regra | Modificação | Observação |
|-------|-------------|------------|
| RN-14 (fluxo de pagamento MP) | O cliente **não sai mais** do app ao pagar — abre nova aba. O fluxo de webhook e aprovação é idêntico. | Mudança de UX, não de regra de negócio |
