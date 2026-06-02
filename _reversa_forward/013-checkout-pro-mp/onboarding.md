# Onboarding: 013-checkout-pro-mp

> Como testar esta feature do zero após implementação

## Pré-requisitos

- Servidor rodando
- Usuário criado e logado (feature 012 ativa)
- Produtos no catálogo (loja `mockburger` já tem)

## Teste em dev (sem conta MP real)

O token `TEST-0000` ativa o mock automaticamente.

1. Adicione produtos ao carrinho
2. Clique "Finalizar Pedido" → faça login se necessário
3. Clique "Finalizar Pedido" novamente no form de checkout
4. **Verificar:** browser navega para `/payment/mock/?order_id=N`
5. Clique "Simular pagamento aprovado"
6. **Verificar:** Order.status = PREPARING no Django shell:
   ```python
   from core.models import Order
   Order.objects.last().status  # deve ser 'PREPARING'
   ```

## Teste com sandbox MP real

1. Crie uma conta no [MercadoPago Developers](https://www.mercadopago.com.br/developers)
2. Obtenha um Access Token de **teste** (começa com `TEST-` mas não `TEST-0000`)
3. Configure no admin: Manager Settings → cole o token da loja
4. Adicione `SITE_URL=http://localhost:8000` ao `.env`
5. Repita o fluxo — você será redirecionado para a página real do MP sandbox
6. Use um cartão de teste do MP: [lista oficial](https://www.mercadopago.com.br/developers/pt/docs/checkout-pro/additional-content/test-cards)
7. **Verificar:** após pagar, MP redireciona para `/payment/success/?payment_id=...`
8. **Verificar:** webhook dispara (se configurado via ngrok) e pedido vai para PREPARING

## Teste do webhook localmente (ngrok)

```bash
ngrok http 8000
# Copie a URL pública, ex: https://abc123.ngrok.io
# Configure SITE_URL=https://abc123.ngrok.io no .env
# Configure a URL de webhook no painel MP: https://abc123.ngrok.io/api/webhooks/mercadopago
```

## Verificação das views de retorno

Acesse diretamente:
- `http://localhost:8000/payment/success/?payment_id=123&preference_id=pref_456&status=approved`
- `http://localhost:8000/payment/pending/?payment_id=123`
- `http://localhost:8000/payment/failure/?payment_id=123`

Todas devem renderizar sem erro, mesmo sem um Order real correspondente.

## Verificação do campo mp_preference_id

```python
from core.models import Order
o = Order.objects.last()
print(o.mp_preference_id)  # deve estar preenchido após checkout
print(o.mp_payment_id)     # preenchido após aprovação via webhook
```
