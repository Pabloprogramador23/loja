# Regression Watch: 012-auth-social-checkout

> Feature: Autenticação Social no Checkout (011-A)
> Gerado em: 2026-05-30

## Watch Items

| ID | Origem | Regra esperada após mudança | Tipo | Sinal de violação |
|----|--------|-----------------------------|------|-------------------|
| W001 | `templates/core/partials/cart_drawer.html` + `accounts/views.py#auth_modal_view` | Botão "Finalizar Pedido" para usuário não autenticado abre modal de identificação (não prossegue para checkout) | presença | Request de checkout sem auth passa direto; modal não aparece |
| W002 | `accounts/views.py#checkout_signup_view` + `_reversa_sdd/architecture.md#ADR-004` | Carrinho (`session['cart_{tenant_id}']`) preservado após login/cadastro no modal — `session.cycle_key()` migra os dados | presença | Itens do carrinho somem após autenticação no modal |
| W003 | `store_saas/settings.py` + `accounts/views.py#login_view` | Manager acessa `/dashboard/` via `/accounts/login/` sem interferência do allauth; `is_staff` continua como controle de acesso | presença | Manager vê modal de checkout ou é barrado pelo allauth |
| W004 | `allauth.socialaccount` + `accounts/views.py#checkout_signup_view` | Login Google cria `User` na primeira vez; autentica existente na segunda — sem duplicar usuário por e-mail | ausência | Dois `User` com mesmo e-mail após logins Google consecutivos |

## Observações (sem peso de regressão)

| Item | Origem | Observação |
|------|--------|------------|
| O001 | `store_saas/settings.py#GOOGLE_CLIENT_ID` | Se `GOOGLE_CLIENT_ID` vazio, aba Google oculta no modal — comportamento esperado em dev sem credenciais |
| O002 | `accounts/views.py#checkout_login_view` | Login por e-mail depende de busca por `User.objects.get(email=email)` — pode falhar silenciosamente se usuário tiver múltiplos registros com mesmo e-mail (não deve ocorrer com `clean_email` em `CheckoutSignupForm`) |

## Histórico de re-extrações

| Data | Extração | W001 | W002 | W003 | W004 | Notas |
|------|----------|------|------|------|------|-------|

## Arquivadas

<!-- Watch items resolvidos ou substituídos ficam aqui -->
