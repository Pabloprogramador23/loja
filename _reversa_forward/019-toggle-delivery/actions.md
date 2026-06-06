# Actions: Toggle Delivery — Loja Aberta/Fechada

> Identificador: `019-toggle-delivery`
> Data: `2026-06-04`
> Roadmap: `_reversa_forward/019-toggle-delivery/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 16 |
| Paralelizáveis (`[//]`) | 9 |
| Maior cadeia de dependência | 5 (T001 → T002 → T004 → T005 → T006) |

---

## Fase 1 — Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Adicionar campo `delivery_enabled = models.BooleanField(default=True, help_text="Quando False, a loja não aceita novos pedidos online.")` ao modelo `Store` em `core/models.py` | - | `[//]` | `core/models.py` | 🟢 | `[X]` |
| T002 | Criar migration `core/migrations/0017_store_delivery_enabled.py` com `migrations.AddField(model_name='store', name='delivery_enabled', field=models.BooleanField(default=True, ...))` | T001 | - | `core/migrations/0017_store_delivery_enabled.py` | 🟢 | `[X]` |
| T003 | Adicionar rota em `core/urls.py`: `path('dashboard/toggle-delivery/', views.toggle_delivery_view, name='toggle_delivery')` | - | `[//]` | `core/urls.py` | 🟢 | `[X]` |

---

## Fase 2 — Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Criar `core/tests_toggle_delivery.py`. Testes para `toggle_delivery_view`: (a) POST por manager → `delivery_enabled` flipa; (b) POST por usuário não-manager → HTTP 403; (c) estado persiste no banco após o toggle | T001, T003 | - | `core/tests_toggle_delivery.py` | 🟢 | `[X]` |
| T005 | No mesmo arquivo, testes para `checkout()` com `delivery_enabled=False`: POST em `/checkout/` com store fechada → response contém mensagem de erro no drawer; nenhum `Order` criado | T004 | - | `core/tests_toggle_delivery.py` | 🟢 | `[X]` |
| T006 | No mesmo arquivo, teste para o context processor: request com tenant → dict retornado contém chave `delivery_enabled` com valor correto (`True` quando aberta, `False` quando fechada) | T005 | - | `core/tests_toggle_delivery.py` | 🟢 | `[X]` |

---

## Fase 3 — Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T007 | Atualizar `context_processors.cart()` em `core/context_processors.py`: adicionar `'delivery_enabled': tenant.delivery_enabled if tenant else True` ao dict retornado | T001 | `[//]` | `core/context_processors.py` | 🟢 | `[X]` |
| T008 | Adicionar `toggle_delivery_view(request)` em `core/views.py`: verifica `user_can_manage_store(request)` → retorna 403 se falhar; faz `store = request.tenant; store.delivery_enabled = not store.delivery_enabled; store.save(update_fields=['delivery_enabled'])`; renderiza partial `core/manager/partials/delivery_toggle.html` com `{'delivery_enabled': store.delivery_enabled}` | T003 | `[//]` | `core/views.py` | 🟢 | `[X]` |
| T009 | Adicionar guard no início do corpo de `checkout()` em `core/views.py`, logo após a verificação de carrinho vazio (linha ~176): `if not store.delivery_enabled: return _checkout_error(request, cart, 'A loja não está aceitando pedidos no momento.')` — lendo `store = request.tenant` antes da guard | T008 | - | `core/views.py` | 🟢 | `[X]` |

---

## Fase 4 — Integração (templates e forms)

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T010 | Adicionar `delivery_enabled` aos `fields` de `StoreSettingsForm` em `core/forms.py` e incluir widget `CheckboxInput` com classes Tailwind dark mode: `{'class': 'h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 dark:border-gray-600 dark:bg-gray-700'}`. Adicionar label `'Aceitar pedidos online'` | T001 | `[//]` | `core/forms.py` | 🟢 | `[X]` |
| T011 | Criar `templates/core/manager/partials/delivery_toggle.html`: botão HTMX `hx-post="{% url 'toggle_delivery' %}" hx-target="#delivery-toggle-btn" hx-swap="outerHTML"`. Se `delivery_enabled=True`: botão verde "🟢 Loja aberta — Fechar". Se `False`: botão vermelho/cinza "🔴 Loja fechada — Abrir". Incluir `{% csrf_token %}` no form wrapper | T008 | `[//]` | `templates/core/manager/partials/delivery_toggle.html` | 🟢 | `[X]` |
| T012 | Atualizar `templates/core/manager/dashboard.html`: adicionar `<div id="delivery-toggle-btn">{% include 'core/manager/partials/delivery_toggle.html' %}</div>` em posição de destaque no topo do dashboard (antes dos KPIs) | T011 | - | `templates/core/manager/dashboard.html` | 🟢 | `[X]` |
| T013 | Atualizar `templates/core/partials/cart_drawer.html`: no topo da seção do formulário de checkout (`{% if cart|length > 0 %}`), adicionar bloco `{% if not delivery_enabled %}<div class="...aviso...">A loja não está aceitando pedidos no momento.</div>{% endif %}`. No botão "Confirmar Pedido": adicionar `{% if not delivery_enabled %}disabled{% endif %}` e classes de desabilitado | T007 | `[//]` | `templates/core/partials/cart_drawer.html` | 🟢 | `[X]` |
| T014 | Atualizar `templates/core/catalog.html`: adicionar banner `{% if not delivery_enabled %}<div class="bg-amber-50 dark:bg-amber-900/40 border-b border-amber-200 dark:border-amber-700 text-amber-800 dark:text-amber-200 text-sm font-medium px-4 py-2 text-center">⏸ Não estamos aceitando pedidos no momento. Volte mais tarde!</div>{% endif %}` logo abaixo do `{% block content %}` ou antes do catálogo | T007 | `[//]` | `templates/core/catalog.html` | 🟢 | `[X]` |
| T015 | Atualizar `templates/core/index.html`: adicionar o mesmo banner de T014 (pode ser um `{% include %}` do mesmo partial ou cópia inline) | T007 | `[//]` | `templates/core/index.html` | 🟡 | `[X]` |

---

## Fase 5 — Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T016 | Adicionar `logger.info('Store %s delivery_enabled set to %s by user %s', store.id, store.delivery_enabled, request.user)` em `toggle_delivery_view` após o `save()`, usando o `logger` já importado em `views.py` | T008 | - | `core/views.py` | 🟢 | `[X]` |

---

## Notas de execução

<!-- Reservado para /reversa-coding registrar avisos durante a execução. -->

---

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-04 | Versão inicial gerada por `/reversa-to-do` | reversa |
