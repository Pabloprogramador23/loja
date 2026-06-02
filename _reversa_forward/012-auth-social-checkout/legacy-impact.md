# Legacy Impact: 012-auth-social-checkout

> Data: 2026-05-30
> Feature: Autenticação Social no Checkout (011-A)

## Arquivos Afetados

| Arquivo afetado | Componente (_reversa_sdd_) | Tipo | Severidade | Justificativa |
|-----------------|---------------------------|------|------------|---------------|
| `requirements.txt` | `_reversa_sdd/dependencies.md` | regra-nova | LOW | `django-allauth[socialaccount]>=65.0.0` adicionado |
| `store_saas/settings.py` | `_reversa_sdd/architecture.md#Stack` | regra-alterada | HIGH | INSTALLED_APPS, MIDDLEWARE, AUTHENTICATION_BACKENDS, SITE_ID, allauth config |
| `store_saas/urls.py` | `_reversa_sdd/architecture.md#Rotas Django` | regra-alterada | MEDIUM | Adicionado `allauth.urls` em `/accounts/` e `accounts.urls` em `/auth/` |
| `accounts/urls.py` | `_reversa_sdd/code-analysis.md#Módulo accounts` | regra-alterada | MEDIUM | Novas rotas: modal, checkout_login, checkout_signup, password reset (4 rotas) |
| `accounts/views.py` | `_reversa_sdd/code-analysis.md#Módulo accounts` | regra-alterada | HIGH | 3 views novas; `signup_view` sem guest_order_id; `login()` com backend explícito |
| `accounts/forms.py` | `_reversa_sdd/code-analysis.md#Módulo accounts` | regra-nova | LOW | `CheckoutSignupForm` com first_name, last_name, phone, clean_email |
| `accounts/tests.py` | — | componente-novo | LOW | 7 testes: modal view, signup, login |
| `templates/base.html` | `_reversa_sdd/code-analysis.md#2.3` | regra-alterada | MEDIUM | `#auth-modal-container` adicionado antes do cart drawer |
| `templates/core/partials/cart_drawer.html` | `_reversa_sdd/code-analysis.md#2.3` | regra-alterada | HIGH | Botão "Finalizar Pedido" condicional por autenticação |
| `templates/accounts/auth_modal.html` | — (novo) | componente-novo | — | Modal com abas Google/Entrar/Cadastrar |
| `templates/accounts/partials/modal_login.html` | — (novo) | componente-novo | — | Form HTMX de login por e-mail/senha |
| `templates/accounts/partials/modal_signup.html` | — (novo) | componente-novo | — | Form HTMX de cadastro |
| `templates/registration/password_reset*.html` | — (novo, 6 arquivos) | componente-novo | — | Templates de recuperação de senha |
| `.env`, `.env.prod` | — | regra-nova | LOW | `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` adicionados |

## Diff conceitual por componente

### `signup_view` — regra-alterada (CRITICAL para RN-05)
Antes: continha bloco `guest_order_id` que vinculava pedido guest ao usuário após signup. Agora: esse bloco foi removido porque guest checkout não existe mais. Guest orders históricos já existentes no banco não são afetados.

### `checkout_signup_view` + `checkout_login_view` — componentes-novos
Novas views que tratam autenticação especificamente no contexto do checkout. Após autenticação bem-sucedida, retornam `<script>window.location.href="/checkout/";</script>` — mesmo padrão da feature 010 para evitar injeção de página completa no HTMX.

### `AUTHENTICATION_BACKENDS` — regra-nova
Antes: backend único implícito (`ModelBackend`). Agora: dois backends explícitos. Exige que `auth_login()` seja chamado com `backend=` explícito quando o usuário foi criado via `form.save()` (sem `authenticate()`).

### Botão "Finalizar Pedido" — regra-alterada
Antes: sempre `hx-post="/checkout/"`. Agora: se autenticado → `hx-post="/checkout/"`; se não → `hx-get="/auth/modal/"` abrindo o modal de identificação.

## Preservadas

- **RN-04** — Checkout valida `customer_name`, `customer_phone`, `delivery_address` (inalterado)
- **RN-07** — Snapshot de preço no `OrderItem` (inalterado)
- **RN-09** — Token MP por tenant (inalterado)
- **RN-01** — Isolamento de tenant por ContextVar (inalterado)
- **RN-12** — Acesso ao dashboard por `is_staff` (inalterado)

## Modificadas

- **RN-05** — Guest checkout eliminado. Antes: `order.user=null` com `session['guest_order_id']`. Agora: checkout exige autenticação prévia. Não há mais pedidos guest criados.
