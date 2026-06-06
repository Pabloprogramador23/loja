# Actions: Integração Real MercadoPago (Sandbox)

> Identificador: `017-mercadopago-sandbox`
> Data: `2026-06-02`
> Roadmap: `_reversa_forward/017-mercadopago-sandbox/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 12 |
| Paralelizáveis (`[//]`) | 6 |
| Maior cadeia de dependência | 5 (T001 → T006 → T007 → T009 → T010 → T011) |

---

## Fase 1 — Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Adicionar `customer_email = models.CharField(max_length=254, blank=True, default='')` ao modelo `Order`, após `customer_phone` | - | `[//]` | `core/models.py` | 🟢 | `[X]` |
| T002 | Adicionar `SITE_URL` ao `.env.example` com comentário explicando que é usado nos `back_urls` do Checkout Pro (ex: `SITE_URL=https://SEU-NGROK.ngrok-free.app`) | - | `[//]` | `.env.example` | 🟢 | `[X]` |

---

## Fase 2 — Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Escrever teste: checkout de guest com `customer_email` preenchido no POST → `Order.customer_email` é salvo corretamente no banco | T001 | `[//]` | `core/tests_payment_sandbox.py` | 🟢 | `[X]` |
| T004 | Escrever teste: `create_checkout_pro_preference(order)` com `order.user = None` e `order.customer_email` definido → não lança `AttributeError`, retorna dict com `init_point` | T001 | `[//]` | `core/tests_payment_sandbox.py` | 🟢 | `[X]` |
| T005 | Escrever teste: `create_pix_payment(order)` com token não-`TEST-0000` e mock de `sdk.payment().create()` retornando status 403 → retorna `None` (não retorna mock) | - | `[//]` | `core/tests_payment_sandbox.py` | 🟡 | `[X]` |

---

## Fase 3 — Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T006 | Em `views.checkout()`, incluir `customer_email=customer_email` no `Order.objects.create(...)`. O valor já era coletado e validado mas nunca persistido. | T001 | - | `core/views.py` | 🟢 | `[X]` |
| T007 | Gerar e aplicar migração Django: `0016_add_customer_email_to_order.py` | T001, T006 | - | `core/migrations/` | 🟢 | `[X]` |
| T008 | Corrigir `create_checkout_pro_preference()`: payer email/name para guest usando `order.customer_email`/`order.customer_name`; `float(item.unit_price)` → `str(item.unit_price)` | T001 | - | `core/payment.py` | 🟢 | `[X]` |
| T009 | Corrigir `create_pix_payment()`: priorizar `order.customer_email`; `float(order.total_amount)` → `str(order.total_amount)` | T001 | - | `core/payment.py` | 🟢 | `[X]` |
| T010 | Em `create_pix_payment()`, mover guard mock (`TEST-0000`) para antes do `sdk.payment().create()`. HTTP 403 real agora retorna `None`. | T009 | - | `core/payment.py` | 🟢 | `[X]` |

---

## Fase 4 — Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T011 | Verificar que `comanda_close` (PIX de balcão) funciona corretamente — `order.customer_email` é `''` nesse contexto, fallback para placeholder é aceitável. Corrigir bug colateral: `_checkout_error` não passava `session_delivery_address` ao contexto do template. | T006, T009 | - | `core/views.py` | 🟡 | `[X]` |

---

## Fase 5 — Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T012 | Substituir `print()` por `logger.error()` em `payment.py`; adicionar `import logging` e `logger = logging.getLogger(__name__)` | T008, T009, T010 | `[//]` | `core/payment.py` | 🟡 | `[X]` |

---

## Notas de execução

- **T007**: Docker não estava rodando. Migração criada manualmente (`0016_add_customer_email_to_order.py`). Aplicada via `python manage.py test` (testes confirmaram migração OK).
- **T011**: Bug colateral corrigido — `_checkout_error` não passava `session_delivery_address` ao contexto do template cart_drawer, causando `VariableDoesNotExist` no template. Corrigido junto com a verificação.
- **Testes**: 7/7 passando (`core.tests_payment_sandbox`).

---

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-02 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-06-02 | Todas as ações executadas por `/reversa-coding` | reversa |
