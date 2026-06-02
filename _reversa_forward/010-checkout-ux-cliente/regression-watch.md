# Regression Watch: 010-checkout-ux-cliente

> Feature: Melhoria de UX no Checkout do Cliente
> Gerado em: 2026-05-30

## Watch Items

| ID | Origem | Regra esperada após mudança | Tipo | Sinal de violação |
|----|--------|-----------------------------|------|-------------------|
| W001 | `core/views.py#cart_detail` + `core/models.py#UserProfile` | Usuário autenticado com pedido anterior vê campo telefone pré-preenchido ao abrir o carrinho | presença | Campo `customer_phone` vazio para usuário com `UserProfile.phone` não vazio |
| W002 | `templates/core/partials/address_list.html#selectAddress` | String gerada ao clicar em endereço salvo inclui cidade e estado no formato `{rua}, {nº} - {bairro}, {cidade} - {estado}` | redação | `Order.delivery_address` sem cidade/estado quando criado via seleção de endereço salvo |
| W003 | `templates/core/partials/cart_drawer.html#delivery-address-textarea` | Textarea `delivery_address` permanece no DOM (apenas oculto) quando usuário logado tem endereços; evento `blur` do Uber Direct funciona ao revelar o textarea | presença | Textarea ausente do DOM; cotação Uber Direct não disparada após revelar o textarea |
| W004 | `core/views.py#checkout` + `templates/core/partials/cart_drawer.html` | Visitante não autenticado vê nome, telefone, e-mail e endereço livre sem alteração | presença | Campos ausentes ou comportamento diferente para usuário não autenticado |

| W005 | `accounts/forms.py#CustomerSignupForm` | Cadastro de cliente exige campo email obrigatório; `user.email` salvo e usado pelo MercadoPago | presença | Signup sem campo email; `user.email` vazio após cadastro |
| W006 | `core/views.py#checkout` + `core/urls.py` | Checkout bem-sucedido redireciona browser para `/payment/<id>/` via `window.location.href`; página de pagamento carrega sem header duplicado | presença | Header duplicado no DOM; `payment_pix.html` renderizado dentro do cart drawer |

## Observações (sem peso de regressão)

| Item | Origem | Observação |
|------|--------|------------|
| O001 | `core/views.py#save_address` | Feedback de erro de limite (🟡 INFERIDO) — depende de `ValidationError.message` ter texto legível; pode variar conforme mensagem do model |

## Histórico de re-extrações

| Data | Extração | W001 | W002 | W003 | W004 | Notas |
|------|----------|------|------|------|------|-------|

## Arquivadas

<!-- Watch items resolvidos ou substituídos ficam aqui -->
