# Regression Watch — 004-painel-restaurante

> Feature: Painel do Restaurante + Sistema de Comandas

---

## Watch Items

| ID | Origem | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------|-----------------------------|---------------------|--------------------|
| W001 | `core/views.py` — `manager_orders` | `Order.objects.exclude(status='OPEN')` deve estar presente no queryset de `manager_orders` | presença | Comandas com status OPEN aparecem na listagem `/dashboard/orders/` |
| W002 | `templates/base.html` — header nav | Para gestores (user.is_staff ou dono da loja), exibe menu administrativo completo; para clientes, exibe menu do cliente ("Meus Pedidos", vitrine, carrinho) | redação | Gestor visualiza menu de cliente com carrinho, ou não consegue acessar links do painel |
| W003 | `templates/core/manager/orders.html` — status filter tabs | Loop `{% for status_value, status_label in Order.Status.choices %}` deve ter `{% if status_value != 'OPEN' %}` envolvendo cada item | presença | Tab "Comanda Aberta" aparece na listagem de pedidos do dashboard |
| W004 | `core/models.py` — `Order.Status` | `OPEN` deve ser o primeiro entry do TextChoices | presença | Remoção ou reordenação de `OPEN` quebra os filtros `status='OPEN'` nas views de comanda |
| W005 | `core/views.py` — `comanda_close` (fluxo presencial) | Ao fechar com `payment_method=presencial`, status muda de OPEN → PREPARING e redireciona para `manager_orders` | presença | Comanda permanece OPEN após fechar como presencial, ou aparece como OPEN no dashboard |
| W006 | `core/views.py` — `comanda_close` (fluxo PIX com zero itens) | Comanda com `total_amount <= 0` via PIX retorna erro sem gerar QR Code | presença | QR Code gerado para comanda vazia, ou erro 500 |

---

## Histórico de Re-extrações

### Re-extração 2026-05-28 19:00

| ID | Veredito | Observação |
|----|----------|------------|
| W001 | 🟢 verde | `Order.objects.exclude(status='OPEN')` confirmado em `core/views.py` |
| W002 | 🟢 verde | Diferenciação completa de menus de gestor (sem carrinho) e cliente (com carrinho) confirmada em `templates/base.html` |
| W003 | 🟢 verde | Guard `{% if status_value != 'OPEN' %}` confirmado em `templates/core/manager/orders.html` |
| W004 | 🟢 verde | `OPEN` no TextChoices de `Order.Status` confirmado |
| W005 | 🟢 verde | Redirecionamento e alteração de status no fechamento presencial confirmados |
| W006 | 🟢 verde | Guard de fechamento PIX com zero itens confirmado |

### Re-extração 2026-05-27 01:00

| ID | Veredito | Observação |
|----|----------|------------|
| W001 | 🟢 verde | `Order.objects.exclude(status='OPEN')` confirmado em `core/views.py:265` |
| W002 | 🟢 verde | Bifurcação `{% if user.is_staff %}` confirmada em `templates/base.html:38-42` — manager → `manager_orders`, cliente → `account_orders` |
| W003 | 🟢 verde | Guard `{% if status_value != 'OPEN' %}` confirmado em `templates/core/manager/orders.html:21` |
| W004 | 🟢 verde | `OPEN = 'OPEN', 'Comanda Aberta'` é a primeira entry em `Order.Status` (`core/models.py:80`) |
| W005 | 🟢 verde | Fechamento presencial: `order.status = Order.Status.PREPARING` + `redirect('manager_orders')` confirmados em `core/views.py:484-486` |
| W006 | 🟢 verde | Guard de comanda vazia via PIX: `error_msg = 'Adicione ao menos um item...'` confirmado em `core/views.py:494` |

---

## Arquivadas

<!-- Watch items encerrados por obsolescência ou por serem resolvidos definitivamente -->

---

## Observações (sem peso de regressão)

- T011 (mobile sidebar) tem confidência 🟡 — a implementação usa Hyperscript `_="on click toggle .hidden"`. Se Hyperscript for removido do projeto, o off-canvas mobile deixa de funcionar mas sem impacto em lógica de negócio.
