# Roadmap: Pagamento na Entrega (011-C)

> Identificador: `014-pagamento-entrega`
> Data: `2026-05-30`
> Requirements: `_reversa_forward/014-pagamento-entrega/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A feature é puramente interna — sem novos contratos externos. Tem quatro eixos:

**Eixo 1 — Model:** três novos campos em `Order` (`payment_method`, `change_amount`, `card_type`) e um novo valor no enum `Order.Status` (`CONFIRMED`). Uma migration aditiva.

**Eixo 2 — checkout() view:** o POST passa a incluir `payment_method`. Se `cash` ou `card`: criar Order com `status=CONFIRMED`, preencher campos de pagamento, disparar `process_new_order.delay()` e redirecionar para `/payment/success/` (sem chamar MP). Se `online`: fluxo existente com `create_checkout_pro_preference()` inalterado.

**Eixo 3 — UX do carrinho:** o `cart_drawer.html` troca o botão único "Finalizar Pedido" por uma UI de seleção de pagamento com dois caminhos e campos dinâmicos. HTMX e Hyperscript já usados no projeto cobrem a interatividade sem JavaScript extra.

**Eixo 4 — Painel do manager:** o status `CONFIRMED` é incluído nas queries de listagem de pedidos. Badge de método de pagamento é exibido no card/modal do pedido.

## 2. Princípios aplicados

Arquivo `principles.md` não encontrado — sem princípios registrados.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|---------------|--------------------------|-------------|
| D-01 | `CONFIRMED = 'CONFIRMED', 'Confirmado'` como novo valor no enum `Order.Status` | Preserva o padrão de máquina de estados existente; sem quebrar queries que filtram por `PENDING` | Status separado `DELIVERY_PENDING` (descartado: redundante, semântica idêntica a CONFIRMED) | 🟢 |
| D-02 | `payment_method` como `CharField` com choices, default `'online'` | Retrocompatibilidade: Orders históricos recebem `online` sem migration de dados; choices evitam valores arbitrários | Campo booleano `is_delivery` (descartado: não modela Dinheiro vs Cartão) | 🟢 |
| D-03 | `change_amount` como `DecimalField(null=True, blank=True)` | Valor ausente = sem troco; Decimal garante precisão monetária; nullable sem default evita 0.00 implícito | `CharField` (descartado: sem validação numérica automática) | 🟢 |
| D-04 | `card_type` como `CharField(blank=True, default='')` com choices `credit`/`debit` | Blank padrão para pedidos sem cartão; choices limitam valores possíveis | Enum separado (descartado: overkill para dois valores) | 🟢 |
| D-05 | Ramificar no `checkout()` por `payment_method` vindo do POST | Mantém toda a lógica em um lugar; checkout já tem a estrutura de `transaction.atomic()` | View separada para pedido na entrega (descartado: duplicaria validação de endereço/phone/cart) | 🟡 |
| D-06 | `process_new_order.delay(order.id)` para notificar o restaurante em pedidos na entrega | Reutiliza o mecanismo Celery existente; equivalente ao fluxo de webhook MP | Notificação síncrona via SSE (descartado: complexidade desnecessária) | 🟢 |
| D-07 | `CONFIRMED` incluído nas queries do dashboard junto com `PENDING` e `PREPARING` | Restaurante precisa ver o pedido imediatamente; `CONFIRMED` semanticamente equivale a "aguardando preparo" | Status separado com filtro próprio (descartado: UX confusa para o manager) | 🟡 |
| D-08 | UI dinâmica via Hyperscript no template (já usado no projeto) | Sem dependência nova; consistente com o padrão do `cart_drawer.html` atual | Alpine.js / vanilla JS (descartado: introduziria nova dependência) | 🟢 |

## 4. Premissas

Nenhuma — sem marcadores `[DÚVIDA]`.

## 5. Delta arquitetural

| Componente | Arquivo legado | Tipo | Resumo |
|------------|---------------|------|--------|
| `Order.Status` | `core/models.py` | regra-nova | Novo valor `CONFIRMED` no enum |
| `Order.payment_method` | `core/models.py` | delta-de-dados | Novo campo CharField |
| `Order.change_amount` | `core/models.py` | delta-de-dados | Novo campo DecimalField nullable |
| `Order.card_type` | `core/models.py` | delta-de-dados | Novo campo CharField blank |
| Migration `0014` | `core/migrations/` | delta-de-dados | Migration aditiva, 3 campos + enum |
| `checkout()` | `core/views.py` | regra-alterada | Ramificação por `payment_method` |
| `dashboard()` | `core/views.py` | regra-alterada | `total_orders_pending` inclui `CONFIRMED` |
| `manager_orders()` | `core/views.py` | regra-alterada | Listagem inclui `CONFIRMED` |
| `cart_drawer.html` | `templates/core/partials/cart_drawer.html` | regra-alterada | UI de seleção de pagamento |
| `order_modal.html` | `templates/core/partials/order_modal.html` | regra-alterada | Badge de método de pagamento |
| `order_row.html` | `templates/core/manager/partials/order_row.html` | regra-alterada | Badge de método de pagamento |

## 6. Delta no modelo de dados

- `Order.Status.CONFIRMED` — novo valor de enum
- `Order.payment_method` — `CharField(max_length=10, choices=[...], default='online')`
- `Order.change_amount` — `DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)`
- `Order.card_type` — `CharField(max_length=10, blank=True, default='')`
- Detalhe completo em: `_reversa_forward/014-pagamento-entrega/data-delta.md`

## 7. Delta de contratos externos

Nenhum — feature 100% interna.

## 8. Plano de migração

1. Adicionar `CONFIRMED` ao enum `Order.Status` em `core/models.py`
2. Adicionar campos `payment_method`, `change_amount`, `card_type` ao model `Order`
3. Gerar e aplicar migration `0014_order_payment_fields`
4. Atualizar `checkout()`: ler `payment_method` do POST; ramificar fluxo
5. Atualizar `dashboard()` e `manager_orders()`: incluir `CONFIRMED`
6. Atualizar `cart_drawer.html`: UI de seleção com Hyperscript
7. Atualizar `order_modal.html` e `order_row.html`: badge de método de pagamento

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| `change_amount` recebendo string não numérica do POST | Alto | Médio | `try/except Decimal(change_amount)` com fallback para None |
| `CONFIRMED` não incluído em alguma query de status → pedido desaparece do painel | Alto | Médio | Buscar todas as ocorrências de `Order.Status.PENDING` nas views e templates |
| `payment_method` ausente no POST de pedido online → default não aplicado | Baixo | Baixo | `request.POST.get('payment_method', 'online')` com default explícito |
| `process_new_order` Celery falha silenciosamente → restaurante não notificado | Médio | Baixo | Task já tem retry no legado; comportamento preservado |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] Pedido na entrega criado com `status=CONFIRMED` e campos preenchidos
- [ ] Pedido `CONFIRMED` visível no painel do restaurante
- [ ] Badge de método de pagamento exibido no modal do pedido
- [ ] Fluxo "Pagar Online" inalterado (sem regressão)
- [ ] `regression-watch.md` gerado

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-30 | Versão inicial gerada por `/reversa-plan` | reversa |
