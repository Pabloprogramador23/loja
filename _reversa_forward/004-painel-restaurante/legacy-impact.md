# Legacy Impact — 004-painel-restaurante

> Data: 2026-05-27
> Feature: Painel do Restaurante + Sistema de Comandas

---

## Arquivos Afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `core/models.py` | Order (domain model) | `regra-nova` | MEDIUM | Adicionado status `OPEN` ao TextChoices e campo `table_label` ao modelo Order |
| `core/migrations/0008_order_comanda_fields.py` | Migrations | `componente-novo` | LOW | Migration para adicionar `table_label` (campo apenas, sem constraint DB para o TextChoices) |
| `core/views.py` | Manager Views | `regra-nova` | MEDIUM | 6 novas views de comanda (`comanda_list`, `comanda_create`, `comanda_detail`, `comanda_add_item`, `comanda_remove_item`, `comanda_close`) + exclusão de `OPEN` no queryset de `manager_orders` |
| `core/urls.py` | URL Routing | `regra-nova` | LOW | 6 novas rotas sob `dashboard/comandas/` |
| `templates/core/manager/_comanda_items.html` | Manager Templates | `componente-novo` | LOW | Partial HTMX para lista de itens da comanda (target `#comanda-items`) |
| `templates/core/manager/comanda_list.html` | Manager Templates | `componente-novo` | LOW | Template de listagem de comandas abertas com formulário de criação |
| `templates/core/manager/comanda_detail.html` | Manager Templates | `componente-novo` | LOW | Template de detalhe da comanda (adicionar item, fechar, PIX) |
| `templates/core/manager/base_manager.html` | Manager Layout | `regra-alterada` | MEDIUM | Adicionado item "Comandas" na sidebar desktop + off-canvas mobile com hamburger |
| `templates/base.html` | Global Layout | `regra-alterada` | MEDIUM | Link "Meus Pedidos" agora é condicional: is_staff → "Pedidos da Loja" / cliente → "Meus Pedidos" |
| `templates/core/account/base_account.html` | Account Layout | `regra-alterada` | LOW | Sidebar de conta agora exibe "Painel de Gerência" para is_staff |
| `templates/core/manager/orders.html` | Manager Templates | `regra-alterada` | LOW | Status filter tabs excluem `OPEN`; queryset de `manager_orders` já exclui via `.exclude(status='OPEN')` |

---

## Diff Conceitual por Componente

### Order (domain model)
- Antes: `Status` tinha 5 valores (PENDING, PREPARING, DELIVERING, COMPLETED, CANCELED). Sem campo de identificador de mesa.
- Depois: `Status` tem 6 valores, com `OPEN` como primeiro entry (representa comanda aberta). Campo `table_label` armazena o identificador livre (ex: "Mesa 3").
- Invariante: `OPEN` não é um status de pedido de cliente — comandas OPEN nunca aparecem no dashboard de pedidos nem no rastreamento público.

### Manager Views
- Antes: `manager_orders` retornava todos os pedidos do tenant.
- Depois: `manager_orders` exclui status `OPEN`. 6 novas views de comanda implementam ciclo de vida completo: criação → adição de itens (HTMX) → remoção de itens (HTMX) → fechamento (presencial: OPEN→PREPARING; PIX: OPEN→PENDING).

### Navegação
- Antes: "Meus Pedidos" no header apontava para `account_orders` para todos os usuários autenticados.
- Depois: managers (is_staff) veem "Pedidos da Loja" apontando para `manager_orders`; clientes mantêm "Meus Pedidos".
- Antes: sidebar do painel de conta não tinha acesso ao dashboard de gerência.
- Depois: sidebar exibe "Painel de Gerência" para is_staff.

---

## Regras Preservadas (do domain.md)

- Isolamento multi-tenant via `TenantManager`: `Order.objects.filter(status='OPEN')` herda o filtro automático de tenant.
- `OrderItem` permanece com campos `order`, `product`, `quantity`, `unit_price`, `total_price`.
- `create_pix_payment` reutilizada sem alteração para fechar comandas via PIX.
- Checkout do cliente (fluxo normal) sem alteração.
- `account_orders` não afetada — clientes continuam vendo apenas seus pedidos.

---

## Regras Modificadas

- **`manager_orders` queryset**: antes retornava `Order.objects.all()`, agora `Order.objects.exclude(status='OPEN')`. Impacto: KPIs do dashboard que eventualmente usem o mesmo queryset não contarão comandas abertas.
- **Header "Meus Pedidos"**: comportamento agora bifurca por `user.is_staff`. Qualquer test que espere o link "Meus Pedidos" para managers precisa ser atualizado.
- **`Order.Status.choices` no template `orders.html`**: filtro tabs agora omitem `OPEN`. Tabs existentes de PENDING, PREPARING, etc. permanecem funcionais.
