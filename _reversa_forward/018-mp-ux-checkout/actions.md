# Actions: MP UX Checkout — Nova Aba + Rastreio para Guest

> Identificador: `018-mp-ux-checkout`
> Data: `2026-06-04`
> Roadmap: `_reversa_forward/018-mp-ux-checkout/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 14 |
| Paralelizáveis (`[//]`) | 4 |
| Maior cadeia de dependência | 7 (T001 → T005 → T006 → T007 → T008 → T009 → T012/T013) |

---

## Fase 1 — Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Adicionar 2 rotas em `core/urls.py`: `path('payment/waiting/', views.payment_waiting_view, name='payment_waiting')` e `path('payment/waiting/status/', views.payment_waiting_status_view, name='payment_waiting_status')` | - | - | `core/urls.py` | 🟢 | `[X]` |

---

## Fase 2 — Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T002 | Criar `core/tests_payment_ux.py`. Escrever testes para `payment_waiting_view`: (a) GET com `?order_id=<id_válido>` → 200 e contexto contém `order`; (b) GET sem `order_id` e sem sessão → 200 com `order=None` (não quebra) | T001 | - | `core/tests_payment_ux.py` | 🟢 | `[X]` |
| T003 | No mesmo `tests_payment_ux.py`, escrever testes para `payment_waiting_status_view`: (a) order com `status=PENDING` → response 200, sem header `HX-Trigger`; (b) order com `status=PREPARING` → response 200, header `HX-Trigger` contém `stopPolling` | T002 | - | `core/tests_payment_ux.py` | 🟡 | `[X]` |
| T004 | No mesmo `tests_payment_ux.py`, escrever testes para `payment_failure_view` e `payment_pending_view` atualizadas: GET com `?preference_id=<mp_preference_id>` → contexto contém `order` correto | T003 | - | `core/tests_payment_ux.py` | 🟢 | `[X]` |

---

## Fase 3 — Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T005 | Adicionar `payment_waiting_view(request)` em `core/views.py`: lê `order_id` de `request.GET.get('order_id')` → fallback `request.session.get('guest_order_id')`; busca `Order` (sem exigir auth); passa `order` ao template `core/payment_waiting.html` | T001 | - | `core/views.py` | 🟢 | `[X]` |
| T006 | Adicionar `payment_waiting_status_view(request)` em `core/views.py`: lê `order_id` igual ao T005; busca `order`; se `order.status != PENDING` adiciona `response['HX-Trigger'] = 'stopPolling'` ao response; renderiza `core/partials/payment_waiting_status.html` com `order` | T005 | - | `core/views.py` | 🟡 | `[X]` |
| T007 | Atualizar `payment_failure_view` em `core/views.py`: adicionar lookup de `order` por `preference_id` → `external_reference` → `session['guest_order_id']` (mesma lógica de `payment_success_view`); passar `order` ao template | T006 | - | `core/views.py` | 🟢 | `[X]` |
| T008 | Atualizar `payment_pending_view` em `core/views.py`: idem ao T007 | T007 | - | `core/views.py` | 🟢 | `[X]` |
| T009 | Alterar o bloco final de `checkout()` em `core/views.py` (linha ~278): substituir `HttpResponse(f'<script>window.location.href="{init_point}";</script>')` por `HttpResponse(f'<script>var _mp=window.open("{init_point}","_blank");window.location.href="/payment/waiting/?order_id={order.id}";</script>')` | T008 | - | `core/views.py` | 🟢 | `[X]` |

---

## Fase 4 — Integração (templates)

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T010 | Criar `templates/core/payment_waiting.html` estendendo `base.html`: exibir número do pedido (`order.id`), status legível, div `#waiting-status` com `hx-get="{% url 'payment_waiting_status' %}?order_id={{ order.id }}"`, `hx-trigger="every 5s, stopPolling from:body"`, `hx-target="#waiting-status"`, `hx-swap="innerHTML"`. Incluir JS de timeout visual de 10 min: `setTimeout(function(){ /* exibir aviso passivo */ }, 600000)`. Incluir link de fallback para abrir MP manualmente | T006 | `[//]` | `templates/core/payment_waiting.html` | 🟢 | `[X]` |
| T011 | Criar `templates/core/partials/payment_waiting_status.html`: partial retornado pelo polling. Mostra status atual. Se `order.status == 'PENDING'`, exibe "Aguardando confirmação do MercadoPago…" com spinner. Se `order.status == 'PREPARING'`, exibe "✅ Pedido confirmado!" com link para `/order/{{ order.id }}/track/`. Se `order.status == 'CANCELED'`, exibe "❌ Pedido cancelado" com link para início | T006 | `[//]` | `templates/core/partials/payment_waiting_status.html` | 🟡 | `[X]` |
| T012 | Atualizar `templates/core/payment_failure.html`: adicionar bloco condicional `{% if order %}` com número do pedido, link `{% url 'order_track' order.id %}` "Acompanhar pedido #{{ order.id }}" e mensagem de orientação para guest. Manter botão "Tentar novamente" existente | T007 | `[//]` | `templates/core/payment_failure.html` | 🟢 | `[X]` |
| T013 | Atualizar `templates/core/payment_pending.html`: idem ao T012 — adicionar bloco `{% if order %}` com número do pedido e link de rastreio | T008 | `[//]` | `templates/core/payment_pending.html` | 🟢 | `[X]` |

---

## Fase 5 — Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T014 | Adicionar `logger.warning('018 order not found: preference_id=%s external_ref=%s', preference_id, external_reference)` nos branches de fallback de `payment_failure_view` e `payment_pending_view` quando `order` permanecer `None` após todas as tentativas de lookup | T008 | - | `core/views.py` | 🟢 | `[X]` |

---

## Notas de execução

<!-- Reservado para /reversa-coding registrar avisos durante a execução. -->

---

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-04 | Versão inicial gerada por `/reversa-to-do` | reversa |
