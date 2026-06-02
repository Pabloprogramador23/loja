# Roadmap: Autenticação Social no Checkout (011-A)

> Identificador: `012-auth-social-checkout`
> Data: `2026-05-30`
> Requirements: `_reversa_forward/012-auth-social-checkout/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A feature tem três eixos independentes que se encaixam em sequência:

**Eixo 1 — django-allauth:** instalar e configurar `django-allauth` com provider Google. Isso adiciona tabelas de social accounts, modifica `INSTALLED_APPS`, `MIDDLEWARE` e `URLS`. O allauth coexiste com o sistema de sessão Django existente sem conflito.

**Eixo 2 — Modal de identificação:** o botão "Finalizar Pedido" no `cart_drawer.html` verifica autenticação. Se não autenticado, faz `hx-get` para uma nova view `auth_modal_view` que retorna um partial HTMX com três abas (Google / Entrar / Cadastrar). O modal é renderizado como overlay com `z-50` sobre o drawer (`z-40`). Cada aba tem seu próprio form HTMX; sucesso redireciona para checkout via `window.location.href`.

**Eixo 3 — Preservação do carrinho:** o carrinho vive em `session['cart_{tenant_id}']`. O `login()` do Django chama `session.cycle_key()` internamente, que migra o dado da sessão antiga para a nova — o carrinho é preservado automaticamente sem nenhum código extra. O mesmo vale para o callback OAuth do allauth, que usa o mesmo `login()` do Django. Isso elimina a necessidade de qualquer lógica de migração de carrinho.

**Removido:** guest checkout (`RN-05`) é eliminado. O botão "Finalizar Pedido" bloqueia o request se não autenticado antes de criar qualquer `Order`. A lógica `session['guest_order_id']` em `signup_view` é removida.

**Recuperação de senha:** views nativas do Django (`PasswordResetView` et al.) com templates mínimos. URLs adicionadas em `accounts/urls.py`.

## 2. Princípios aplicados

Arquivo `principles.md` não encontrado — sem princípios registrados.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|---------------|--------------------------|-------------|
| D-01 | `django-allauth` para Google OAuth2 | Biblioteca madura, integra com sessão Django nativamente, suporte a múltiplos providers para o futuro | `social-auth-app-django` (menos manutenida); OAuth manual (risco de segurança alto) | 🟢 |
| D-02 | `django.contrib.sites` + `SITE_ID=1` | Requisito obrigatório do allauth para mapear o `SocialApp` ao site correto | Sem `sites`: allauth falha ao buscar credenciais do Google no banco | 🟢 |
| D-03 | Credenciais Google via `SocialApp` no banco (admin) em vez de `SOCIALACCOUNT_PROVIDERS` no settings | Permite configurar credenciais sem redeploy; manager pode trocar o client_id pelo admin Django | `SOCIALACCOUNT_PROVIDERS` direto no settings (mais simples mas exige redeploy) | 🟡 |
| D-04 | Modal como partial HTMX (`hx-get="/auth/modal/"`) retornado para `#cart-drawer-content` | Reutiliza o padrão HTMX do projeto; modal sobrepõe o drawer sem nova navegação | Página separada `/auth/checkout-login/` (quebra UX do carrinho) | 🟡 |
| D-05 | Carrinho preservado automaticamente via `session.cycle_key()` do Django `login()` | Zero código extra; comportamento garantido pelo Django core | Salvar/restaurar carrinho manualmente em Redis (complexidade desnecessária) | 🟢 |
| D-06 | Login por e-mail (não username) com `ACCOUNT_AUTHENTICATION_METHOD = 'email'` | UX mais natural; alinha com o cadastro atual (`CustomerSignupForm`) | Username login (padrão allauth) — exigiria mais um campo no modal | 🟢 |
| D-07 | Username auto-gerado a partir do e-mail: `email.split('@')[0]` + sufixo numérico se colisão | Usuário nunca digita username; compatível com `auth.User.username` obrigatório | `ACCOUNT_USERNAME_REQUIRED = False` com allauth (OK, mas anula username completamente) | 🟡 |
| D-08 | Password reset via `PasswordResetView` nativo do Django | Zero código; seguro; templates customizáveis depois | Custom reset (trabalho desnecessário) | 🟢 |

## 4. Premissas

Nenhuma — sem marcadores `[DÚVIDA]` no requirements.

## 5. Delta arquitetural

| Componente | Arquivo legado | Tipo | Resumo |
|------------|---------------|------|--------|
| `INSTALLED_APPS` | `store_saas/settings.py` | regra-alterada | Adicionar `django.contrib.sites`, `allauth`, `allauth.account`, `allauth.socialaccount`, `allauth.socialaccount.providers.google` |
| `MIDDLEWARE` | `store_saas/settings.py` | regra-alterada | Adicionar `allauth.account.middleware.AccountMiddleware` após `AuthenticationMiddleware` |
| `AUTHENTICATION_BACKENDS` | `store_saas/settings.py` | regra-nova | Adicionar `allauth.account.auth_backends.AuthenticationBackend` |
| URL raiz | `store_saas/urls.py` | regra-alterada | Adicionar `path('accounts/', include('allauth.urls'))` e `path('auth/', include('accounts.urls'))` para modal |
| `accounts/urls.py` | `accounts/urls.py` | regra-alterada | Adicionar rotas de password reset + rota `/auth/modal/` |
| `accounts/views.py` | `accounts/views.py` | regra-alterada | Adicionar `auth_modal_view`, `checkout_login_view`, `checkout_signup_view`; remover lógica `guest_order_id` de `signup_view` |
| `accounts/forms.py` | `accounts/forms.py` | regra-alterada | Estender `CustomerSignupForm` com `first_name`, `last_name` |
| `cart_drawer.html` | `templates/core/partials/cart_drawer.html` | regra-alterada | Botão "Finalizar Pedido": condicional de auth; se não autenticado → `hx-get="/auth/modal/"` |
| `auth_modal.html` | — (novo) | componente-novo | Template do modal com três abas |
| Tabelas allauth | — (novo via migration) | delta-de-dados | `socialaccount_*`, `account_emailaddress`, `django_site` |
| `signup_view` | `accounts/views.py` | regra-alterada | Remover lógica `guest_order_id` (guest checkout eliminado) |

## 6. Delta no modelo de dados

- Allauth cria suas próprias tabelas via migrations automáticas
- `django.contrib.sites` cria tabela `django_site` (migration automática)
- Nenhum model customizado novo além do que já existe
- Detalhe completo em: `_reversa_forward/012-auth-social-checkout/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| Google OAuth2 (accounts.google.com) | HTTP/OAuth2 | `interfaces/google-oauth2.md` |

## 8. Plano de migração

1. Adicionar `django-allauth` ao `requirements.txt`
2. Atualizar `settings.py`: `INSTALLED_APPS`, `MIDDLEWARE`, `AUTHENTICATION_BACKENDS`, `SITE_ID`, configurações allauth
3. Atualizar `store_saas/urls.py`: incluir `allauth.urls` e novas rotas do modal
4. Atualizar `accounts/urls.py`: rotas de password reset + `/auth/modal/`
5. Gerar e aplicar migrations (allauth + sites)
6. Criar `SocialApp` para Google no admin Django com `client_id` e `client_secret`
7. Adicionar variáveis `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` ao `.env` / `.env.prod`
8. Implementar views do modal (`auth_modal_view`, `checkout_login_view`, `checkout_signup_view`)
9. Criar templates do modal (`auth_modal.html` e suas abas)
10. Atualizar `cart_drawer.html`: botão condicional + hx-get para modal
11. Criar templates de password reset
12. Remover lógica `guest_order_id` de `signup_view`

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| `allauth.account.middleware.AccountMiddleware` conflita com `TenantMiddleware` | Alto | Baixo | Adicionar após `AuthenticationMiddleware` mas antes de `TenantMiddleware`; testar com requests de tenant |
| `session.cycle_key()` no OAuth callback não migra `cart_{tenant_id}` em versão específica do Django | Alto | Baixo | Testar explicitamente no checkout após login Google; fallback: copiar cart key manualmente no signal `user_logged_in` |
| `SocialApp` não configurado no banco → Google login falha com 500 | Alto | Alto (dev sem configuração) | Tratar graciosamente: se `GOOGLE_CLIENT_ID` vazio em env, ocultar aba Google no modal com mensagem |
| Modal HTMX abre dentro do drawer (overlay sobre overlay) com conflito de scroll/z-index | Médio | Médio | Modal usa `position: fixed` com `z-50` (Tailwind); fechar o drawer ao abrir o modal |
| Remover `guest_order_id` de `signup_view` quebra usuários que criaram conta logo após um pedido guest antigo | Baixo | Baixo | Guest checkout é eliminado — não haverá novos pedidos guest; pedidos históricos já estão vinculados |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] Login Google funciona em ambiente local (client_id configurado no admin)
- [ ] Cadastro e login tradicional no modal funcionam e preservam carrinho
- [ ] Recuperação de senha envia e-mail (configurar backend de e-mail em dev)
- [ ] Manager acessa `/dashboard/` sem interferência do allauth
- [ ] Botão "Finalizar Pedido" redireciona ao checkout quando já autenticado
- [ ] `regression-watch.md` gerado

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-30 | Versão inicial gerada por `/reversa-plan` | reversa |
