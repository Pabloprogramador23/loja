# Regression Watch: Integração Real MercadoPago (Sandbox)

> Identificador: `017-mercadopago-sandbox`
> Gerado por: `/reversa-coding` em `2026-06-02`
> Fonte: `legacy-impact.md#Regras modificadas`

---

## Watch Items

| ID | Origem | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------|-----------------------------|--------------------|-------------------|
| W001 | `_reversa_sdd/domain.md#RN-10` / `core/payment.py:create_pix_payment` | Mock de PIX ativa **apenas** quando `token.startswith("TEST-0000")`. Token real + HTTP 403 retorna `None`, não o payload mock. | presença | Se futura extração indicar que 403 cai em mock, a regra foi revertida |
| W002 | `_reversa_sdd/domain.md#RN-11` / `core/payment.py:create_pix_payment` | Email do pagador PIX prioriza `order.customer_email`, depois argumento `customer_email`, depois `order.user.email`, com `guest@placeholder.invalid` apenas como fallback final. | redação | Se futura extração mostrar `payer_email = customer_email or order.user.email` sem `order.customer_email`, a prioridade foi revertida |
| W003 | `_reversa_sdd/domain.md#RN-09` / `core/payment.py` | Token por tenant permanece: `order.store.mercadopago_access_token or settings.MERCADOPAGO_ACCESS_TOKEN` em ambas as funções de pagamento. | presença | Se futura extração mostrar uso de token global hardcoded sem fallback de tenant, a regra foi removida |
| W004 | `_reversa_sdd/architecture.md#Domínio de Negócio` / `core/models.py:Order` | `Order.customer_email` existe como `CharField(max_length=254, blank=True, default='')`. | presença | Se campo ausente na extração futura, foi removido ou renomeado |
| W005 | `core/views.py:checkout` | `Order.objects.create(...)` inclui `customer_email=customer_email` — email do guest é persistido no pedido. | presença | Se extração futura mostrar `Order.objects.create` sem `customer_email`, o campo está sendo descartado novamente |

---

## Observações (sem peso de regressão)

- `unit_price` em Checkout Pro e `transaction_amount` em PIX foram alterados de `float` para `str` — melhoria de precisão numérica. Regra inferida 🟡, não incluída como watch item crítico.
- `_checkout_error` agora passa `session_delivery_address` — correção de bug de template. Não era regra documentada.

---

## Histórico de re-extrações

<!-- Preenchido automaticamente pelo /reversa quando rodar nova extração com esta feature ativa. -->

---

## Arquivadas

<!-- Itens removidos de watch após confirmação de estabilidade. -->
