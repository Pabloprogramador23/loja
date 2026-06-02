# Actions: Pagamento na Entrega (011-C)

> Identificador: `014-pagamento-entrega`
> Data: `2026-05-31`
> Roadmap: `_reversa_forward/014-pagamento-entrega/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 13 |
| Paralelizáveis (`[//]`) | 8 |
| Maior cadeia de dependência | 4 (T001 → T002 → T007 → T008) |

---

## Fase 1, Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Adicionar `CONFIRMED = 'CONFIRMED', 'Confirmado'` ao enum `Order.Status`; criar classes internas `Order.PaymentMethod` (online/cash/card) e `Order.CardType` (credit/debit); adicionar campos `payment_method` (CharField, default `'online'`), `change_amount` (DecimalField null/blank) e `card_type` (CharField blank) ao model `Order` em `core/models.py` | - | - | `core/models.py` | 🟢 | `[X]` |
| T002 | Gerar e aplicar migration `0014_order_payment_fields` com `AddField` para os três novos campos (conforme `data-delta.md`); confirmar que `CONFIRMED` no enum não gera migration (TextChoices são só Python) | T001 | - | `core/migrations/0014_order_payment_fields.py` | 🟢 | `[X]` |

---

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Escrever testes para `checkout()` com `payment_method=cash`: (a) troco válido → Order criado com `status=CONFIRMED`, `change_amount` correto, sem chamada a `create_checkout_pro_preference`; (b) `change_amount` negativo ou string → erro de validação, Order não criado | T002 | `[//]` | `core/tests/test_checkout_delivery.py` | 🟡 |`[X]` |
| T004 | Escrever testes para `checkout()` com `payment_method=card`: crédito e débito → Order com `status=CONFIRMED`, `card_type` correto, `change_amount=None`; sem chamada a MP | T002 | `[//]` | `core/tests/test_checkout_delivery.py` | 🟡 | `[X]` |
| T005 | Escrever teste de regressão para `checkout()` com `payment_method=online` (ou ausente): Order com `status=PENDING`, `payment_method='online'`; `create_checkout_pro_preference` chamada normalmente | T002 | `[//]` | `core/tests/test_checkout_delivery.py` | 🟢 | `[X]` |
| T006 | Escrever teste para `dashboard()`: dado Order com `status=CONFIRMED`, verificar que `total_orders_pending` o inclui no contador; dado Order com `status=PENDING`, verificar que também conta | T002 | `[//]` | `core/tests/test_dashboard_confirmed.py` | 🟡 | `[X]` |

---

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T007 | Atualizar `checkout()` em `core/views.py`: ler `payment_method = request.POST.get('payment_method', 'online')`; se `cash` ou `card`: criar Order com `status=CONFIRMED`, preencher `payment_method`, `change_amount` (validado via `Decimal` com try/except → None se inválido ou negativo), `card_type`; disparar `process_new_order.delay(order.id)`; redirecionar para `/payment/success/`; se `online`: fluxo existente com `create_checkout_pro_preference()` inalterado | T002 | - | `core/views.py` | 🟡 | `[X]` |
| T008 | Atualizar `dashboard()` em `core/views.py`: mudar `filter(status=Order.Status.PENDING)` para `filter(status__in=[Order.Status.PENDING, Order.Status.CONFIRMED])` no cálculo de `total_orders_pending` | T007 | - | `core/views.py` | 🟡 | `[X]` |

---

## Fase 4, Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T009 | Atualizar `cart_drawer.html`: substituir o botão único "Finalizar Pedido" por UI de seleção com dois radio-style buttons ("Pagar Online" e "Pagar na Entrega"); ao selecionar "Pagar na Entrega", exibir via Hyperscript um bloco com sub-opções (Dinheiro / Cartão); ao selecionar Dinheiro, exibir campo `change_amount` (numérico opcional); ao selecionar Cartão, exibir radio Crédito / Débito (`card_type`); input hidden `payment_method` atualizado dinamicamente | T002 | `[//]` | `templates/core/partials/cart_drawer.html` | 🟢 | `[X]` |
| T010 | Adicionar entradas de `Order.Status.CONFIRMED` nos dicionários `status_colors` e `status_badges` em `core/api.py` (cor sugerida: `bg-green-100 text-green-800`; label: `"Confirmado"`); verificar também `check_order_status()` — não requer alteração pois pedidos na entrega não usam esse endpoint, mas adicionar comentário explicativo | T001 | `[//]` | `core/api.py` | 🟡 | `[X]` |
| T011 | Atualizar `order_modal.html`: exibir badge de método de pagamento abaixo do status (`"Online (MP)"`, `"Dinheiro"` com troco se `change_amount`, `"Cartão Crédito"` ou `"Cartão Débito"`) usando `{% if order.payment_method == 'cash' %}` etc. | T002 | `[//]` | `templates/core/partials/order_modal.html` | 🟡 | `[X]` |
| T012 | Atualizar `order_row.html`: adicionar badge compacto de método de pagamento no card do pedido na listagem do manager — mesmo padrão de condicional do T011 | T002 | `[//]` | `templates/core/manager/partials/order_row.html` | 🟡 | `[X]` |

---

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T013 | Gerar `legacy-impact.md` listando todos os arquivos modificados com tipo de mudança; gerar `regression-watch.md` com itens de vigilância: (1) fluxo online sem regressão, (2) `change_amount` inválido rejeitado, (3) pedido `CONFIRMED` visível no painel, (4) `total_orders_pending` contando `CONFIRMED` | T008, T009, T010, T011, T012 | - | `_reversa_forward/014-pagamento-entrega/` | 🟢 | `[X]` |

---

## Notas de execução

<!-- Reservado para /reversa-coding registrar avisos ou observações durante a execução. -->

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-31 | Versão inicial gerada por `/reversa-to-do` | reversa |
