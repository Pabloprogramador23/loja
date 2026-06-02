# Actions: Autenticação Social no Checkout (011-A)

> Identificador: `012-auth-social-checkout`
> Data: `2026-05-30`
> Roadmap: `_reversa_forward/012-auth-social-checkout/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 21 |
| Paralelizáveis (`[//]`) | 6 |
| Maior cadeia de dependência | 9 (T001→T003→T004→T005→T011→T012→T016→T020→T021) |

## Fase 1 — Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Adicionar `django-allauth[socialaccount]>=65.0.0` ao `requirements.txt` | - | `[//]` | `requirements.txt` | 🟢 | `[X]` |
| T002 | Adicionar `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` ao `.env` e `.env.prod` com valores placeholder e comentário de como obter no Google Cloud Console | - | `[//]` | `.env`, `.env.prod` | 🟢 | `[X]` |
| T003 | Atualizar `store_saas/settings.py`: (a) adicionar `django.contrib.sites`, `allauth`, `allauth.account`, `allauth.socialaccount`, `allauth.socialaccount.providers.google` ao `INSTALLED_APPS`; (b) adicionar `allauth.account.middleware.AccountMiddleware` ao `MIDDLEWARE` após `AuthenticationMiddleware`; (c) definir `AUTHENTICATION_BACKENDS` com `ModelBackend` + `AuthenticationBackend`; (d) `SITE_ID = 1`; (e) configurações allauth: `ACCOUNT_AUTHENTICATION_METHOD = 'email'`, `ACCOUNT_EMAIL_REQUIRED = True`, `ACCOUNT_USERNAME_REQUIRED = False`, `ACCOUNT_EMAIL_VERIFICATION = 'none'`; (f) ler `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` via `config()` | T001 | - | `store_saas/settings.py` | 🟢 | `[X]` |
| T004 | Atualizar `store_saas/urls.py`: adicionar `path('accounts/', include('allauth.urls'))` antes das demais rotas para evitar colisão com `accounts/` existente | T003 | - | `store_saas/urls.py` | 🟢 | `[X]` |
| T005 | Atualizar `accounts/urls.py`: (a) adicionar `path('modal/', views.auth_modal_view, name='auth_modal')`; (b) adicionar as 4 rotas nativas de password reset do Django (`PasswordResetView`, `PasswordResetDoneView`, `PasswordResetConfirmView`, `PasswordResetCompleteView`) com `name` padrão do Django | T004 | - | `accounts/urls.py` | 🟢 | `[X]` |
| T006 | Aplicar migrations: `python manage.py migrate` para criar tabelas do allauth (`account_emailaddress`, `socialaccount_*`) e do sites framework (`django_site`) | T003 | - | *(shell)* | 🟢 | `[X]` |

## Fase 2 — Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T007 | Escrever testes para `auth_modal_view`: (a) usuário não autenticado → GET `/auth/modal/` retorna 200 com conteúdo do modal; (b) usuário autenticado → GET `/auth/modal/` retorna script de redirect para `/checkout/` | T006 | `[//]` | `accounts/tests.py` | 🟡 | `[X]` |
| T008 | Escrever testes para `checkout_signup_view`: (a) POST com dados válidos cria `User` + `UserProfile.phone` + login + 200 com redirect script; (b) POST com e-mail duplicado retorna erro inline sem criar usuário | T006 | `[//]` | `accounts/tests.py` | 🟢 | `[X]` |
| T009 | Escrever testes para `checkout_login_view`: (a) credenciais válidas → login + redirect script; (b) credenciais inválidas → 200 com mensagem de erro no HTML, sessão não iniciada | T006 | `[//]` | `accounts/tests.py` | 🟢 | `[X]` |

## Fase 3 — Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T010 | Criar `CheckoutSignupForm` em `accounts/forms.py`: herda de `CustomerSignupForm`, adiciona `first_name` (CharField obrigatório) e `last_name` (CharField obrigatório); mantém `email`, `phone` (celular), `password1`, `password2`; sobrescreve `save()` para popular `user.first_name` e `user.last_name` | - | `[//]` | `accounts/forms.py` | 🟢 | `[X]` |
| T011 | Implementar `auth_modal_view` em `accounts/views.py`: (a) se `request.user.is_authenticated` → retorna `HttpResponse('<script>window.location.href="/checkout/"</script>')`; (b) caso contrário → renderiza `accounts/auth_modal.html` com contexto `{'google_enabled': bool(settings.GOOGLE_CLIENT_ID)}` | T005 | - | `accounts/views.py` | 🟡 | `[X]` |
| T012 | Implementar `checkout_signup_view` em `accounts/views.py` (`@require_POST`): valida `CheckoutSignupForm`; se válido: salva user com `first_name`/`last_name`, salva `UserProfile.phone`, chama `auth_login(request, user)`, retorna `HttpResponse('<script>window.location.href="/checkout/"</script>')`; se inválido: retorna partial `modal_signup.html` com form e erros | T011, T010 | - | `accounts/views.py` | 🟢 | `[X]` |
| T013 | Implementar `checkout_login_view` em `accounts/views.py` (`@require_POST`): lê `email` e `password` do POST; chama `authenticate(request, username=email, password=password)` — funciona porque `AuthenticationBackend` do allauth suporta login por email; se user: `auth_login(request, user)` + redirect script; se None: retorna partial `modal_login.html` com `{'error': 'E-mail ou senha incorretos.'}` | T011 | - | `accounts/views.py` | 🟢 | `[X]` |
| T014 | Remover de `signup_view` em `accounts/views.py` o bloco `guest_order_id = request.session.get('guest_order_id')` e todo o código de vinculação retroativa de pedido guest (guest checkout eliminado) | T011 | - | `accounts/views.py` | 🟢 | `[X]` |

## Fase 4 — Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T015 | Adicionar em `templates/base.html`, antes do `</body>`, um `<div id="auth-modal-container" class="fixed inset-0 z-50 hidden bg-black/50"></div>` — container HTMX para o modal, fora do `#cart-drawer` para evitar conflito de z-index | T011 | - | `templates/base.html` | 🟡 | `[X]` |
| T016 | Criar `templates/accounts/auth_modal.html`: overlay com `z-50`, botão fechar (`_="on click add .hidden to #auth-modal-container"`), três abas (Google / Entrar / Cadastrar) com troca via Hyperscript; aba Google mostra botão `<a href="/accounts/google/login/?next=/checkout/">` se `google_enabled`, ou aviso se não; abas Entrar e Cadastrar carregam os partials via `{% include %}` | T015 | - | `templates/accounts/auth_modal.html` | 🟡 | `[X]` |
| T017 | Criar `templates/accounts/partials/modal_login.html`: form `hx-post="/auth/modal/login/" hx-target="#auth-modal-container" hx-swap="innerHTML"`; campos email e password; exibe `{{ error }}` se presente; link "Esqueci minha senha" → `{% url 'password_reset' %}` | T013 | - | `templates/accounts/partials/modal_login.html` | 🟢 | `[X]` |
| T018 | Criar `templates/accounts/partials/modal_signup.html`: form `hx-post="/auth/modal/signup/" hx-target="#auth-modal-container" hx-swap="innerHTML"`; campos first_name, last_name, email, phone, password1, password2; exibe erros de form inline | T012 | - | `templates/accounts/partials/modal_signup.html` | 🟢 | `[X]` |
| T019 | Criar 4 templates mínimos de password reset: `templates/registration/password_reset.html` (form com campo email), `password_reset_done.html` (instrução de verificar e-mail), `password_reset_confirm.html` (form nova senha), `password_reset_complete.html` (confirmação). Todos estendem `base.html` com Tailwind | T005 | `[//]` | `templates/registration/` | 🟢 | `[X]` |
| T020 | Atualizar `cart_drawer.html`: substituir o botão "Finalizar Pedido" por lógica condicional — se `request.user.is_authenticated`: mantém `hx-post="{% url 'checkout' %}"` atual; se não: adiciona `hx-get="{% url 'auth_modal' %}" hx-target="#auth-modal-container" hx-swap="innerHTML" _="on htmx:afterOnLoad remove .hidden from #auth-modal-container"` | T016 | - | `templates/core/partials/cart_drawer.html` | 🟡 | `[X]` |

## Fase 5 — Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T021 | Gerar `regression-watch.md` com watch items: W001 — botão "Finalizar Pedido" exige autenticação (não autenticado vê modal, não checkout); W002 — carrinho preservado após login/cadastro no modal; W003 — manager acessa `/dashboard/` sem interferência do allauth; W004 — login Google cria conta ou autentica existente sem duplicar usuário | T020 | - | `_reversa_forward/012-auth-social-checkout/regression-watch.md` | 🟢 | `[X]` |

## Notas de execução

<!-- Reservado para /reversa-coding registrar avisos durante a execução. -->

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-30 | Versão inicial gerada por `/reversa-to-do` | reversa |
