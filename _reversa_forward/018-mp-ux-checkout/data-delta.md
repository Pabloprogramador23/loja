# Data Delta: MP UX Checkout

> Feature: `018-mp-ux-checkout`
> Data: `2026-06-04`

---

## Alterações no modelo de dados

**Nenhuma.** Esta feature não requer alteração de schema, novos campos ou migrations.

### Justificativa

O `Order` já possui todos os campos necessários:

| Campo | Uso nesta feature |
|-------|-------------------|
| `order.id` | Identificador na URL `/payment/waiting/?order_id=` |
| `order.status` | Lido no polling para detectar mudança de PENDING |
| `order.mp_preference_id` | Busca do order por `preference_id` nas back_urls do MP |
| `order.customer_name` | Exibido na tela de espera |
| `order.total_amount` | Exibido na tela de espera |

A sessão Django `session['guest_order_id']` (escrita em `views.checkout:251`) já persiste o vínculo guest ↔ order. Não há campo novo.

---

## Migrations necessárias

Nenhuma.

---

## Dados de sessão utilizados

| Chave | Escrita por | Lida por (nova) | Observação |
|-------|-------------|-----------------|------------|
| `session['guest_order_id']` | `views.checkout` (legado) | `payment_waiting_view`, `payment_failure_view`, `payment_pending_view` | Fallback quando `?order_id=` não está na URL |
