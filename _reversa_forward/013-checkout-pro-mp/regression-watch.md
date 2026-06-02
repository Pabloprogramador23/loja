# Regression Watch: 013-checkout-pro-mp

> Feature: Checkout Pro MercadoPago (011-B)
> Gerado em: 2026-05-30

## Watch Items

| ID | Origem | Regra esperada após mudança | Tipo | Sinal de violação |
|----|--------|-----------------------------|------|-------------------|
| W001 | `core/views.py#checkout` + `core/payment.py#create_checkout_pro_preference` | Checkout redireciona browser para `init_point` (URL do MP ou `/payment/mock/` em dev) em vez de renderizar QR Code | presença | Response do checkout contém QR Code base64 ou renderiza `payment_pix.html` inline |
| W002 | `core/models.py#Order.mp_preference_id` + `core/payment.py` | `Order.mp_preference_id` é preenchido após criação da preference | presença | Campo `mp_preference_id` vazio no Order após checkout bem-sucedido |
| W003 | `core/api.py#mercadopago_webhook` | Webhook trata `payment.created` e `payment.updated`; lookup usa `external_reference` → `Order.id`; `Order.mp_payment_id` é salvo pelo webhook | redação | Order não transita para PREPARING após aprovação; `mp_payment_id` permanece vazio |
| W004 | `core/payment.py#create_checkout_pro_preference` | Token MP por tenant preservado: preference criada com `order.store.mercadopago_access_token` quando disponível | presença | Preference criada com token global mesmo quando loja tem token próprio |
| W005 | `core/views.py#payment_mock_view` | Mock dev funciona com `REVERSA_TESTING=true`; retorna 403 ou não existe quando `REVERSA_TESTING=false` | presença | Mock view processa pedidos em produção sem autenticação |

## Observações (sem peso de regressão)

| Item | Origem | Observação |
|------|--------|------------|
| O001 | `templates/core/payment_pix.html` | Template mantido mas não mais acessível pelo fluxo normal; apenas via `/payment/<id>/` com session |
| O002 | `core/api.py#mercadopago_webhook` | Em multi-tenant, o webhook usa token global para buscar `external_reference` e token da loja para verificação final — pode falhar se loja só tem token próprio (sem token global configurado) |

## Histórico de re-extrações

| Data | Extração | W001 | W002 | W003 | W004 | W005 | Notas |
|------|----------|------|------|------|------|------|-------|

## Arquivadas

<!-- Watch items resolvidos ou substituídos ficam aqui -->
