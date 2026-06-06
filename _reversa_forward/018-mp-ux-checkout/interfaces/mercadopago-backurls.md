# Interface: MercadoPago back_urls

> Feature: `018-mp-ux-checkout`
> Contrato: HTTP redirect (GET) — MP → nossa app
> Origem: `core/payment.py:51-55`

---

## Descrição

Quando o usuário conclui (ou abandona) o fluxo no MercadoPago, o MP redireciona o browser do cliente para uma das três back_urls configuradas na preference. Esta feature **não altera** as back_urls — apenas melhora as views que recebem esses redirects.

---

## URLs configuradas (sem alteração)

| Evento | URL de destino | View |
|--------|---------------|------|
| Pagamento aprovado (com `auto_return`) | `{SITE_URL}/payment/success/` | `payment_success_view` |
| Pagamento pendente | `{SITE_URL}/payment/pending/` | `payment_pending_view` |
| Pagamento recusado/falha | `{SITE_URL}/payment/failure/` | `payment_failure_view` |

---

## Query params enviados pelo MP (GET)

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `payment_id` | string | ID do pagamento no MP |
| `status` | string | `approved`, `pending`, `rejected` |
| `external_reference` | string | `order.id` (string) — nosso identificador |
| `preference_id` | string | ID da preference criada |
| `merchant_order_id` | string | ID da ordem no MP |
| `collection_status` | string | Alias de `status` em alguns fluxos |

---

## Mudança desta feature nas views receptoras

### Antes (legado)

`payment_failure_view` e `payment_pending_view` ignoravam `preference_id` e `external_reference` — não carregavam o `Order`.

### Depois (018)

As três views passam a carregar o `Order` usando a mesma lógica:

```python
order = None
if preference_id:
    order = Order.objects.filter(mp_preference_id=preference_id).first()
if order is None and external_reference:
    order = Order.objects.filter(id=external_reference).first()
if order is None:
    order_id = request.GET.get('order_id') or request.session.get('guest_order_id')
    if order_id:
        order = Order.objects.filter(id=order_id).first()
```

---

## Idempotência

O redirect do MP pode ocorrer múltiplas vezes (usuário recarrega a página de sucesso). As views são read-only em relação ao `Order` — nenhuma transição de status é feita aqui (isso é responsabilidade do webhook). Totalmente idempotente.

---

## Timeout e erros

Sem timeout configurável. Se o `Order` não for encontrado por nenhum dos métodos, a view renderiza a página sem dados de pedido (comportamento de fallback, já existia para success).
