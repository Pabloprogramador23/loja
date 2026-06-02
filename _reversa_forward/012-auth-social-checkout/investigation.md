# Investigation: 012-auth-social-checkout

> Data: `2026-05-30`

## django-allauth vs social-auth-app-django

**Escolhido: `django-allauth`**

| Critério | django-allauth | social-auth-app-django |
|----------|---------------|----------------------|
| Manutenção | Ativa (65+ releases, 2024) | Menos frequente |
| Django 5.x | Suportado | Suportado |
| Sessão Django | Integração nativa | Integração nativa |
| Configuração | Admin-based (SocialApp no banco) | Settings-based |
| Providers | 50+ | 50+ |
| Documentação | Extensa | Boa |

**Decisão:** allauth é o padrão de mercado para Django OAuth. A configuração via admin (SocialApp no banco) permite trocar credenciais sem redeploy — vantagem para SaaS multi-tenant onde cada tenant poderia ter suas próprias credenciais no futuro.

## Preservação do carrinho após login()

O carrinho está em `session['cart_{tenant_id}']`. Quando `django.contrib.auth.login()` é chamado (direto ou via allauth), Django executa internamente:

```python
request.session.cycle_key()  # Gera nova session key mas MIGRA os dados
```

Isso significa que `session['cart_1']` sobrevive ao login. Testado na prática em projetos Django 4.x e 5.x — comportamento estável.

**Risco residual:** O allauth pode chamar `flush()` em vez de `cycle_key()` em algum caso extremo. Mitigação: adicionar um signal `user_logged_in` que verifica se o cart key existe e, se não, tenta restaurar de um backup temporário na sessão.

## Modal HTMX sobre Cart Drawer

O `cart-drawer` usa `z-40` (Tailwind). O modal precisa de `z-50` ou superior para aparecer por cima.

**Estrutura recomendada:**
```html
<!-- Em base.html, fora do cart-drawer -->
<div id="auth-modal-container" class="fixed inset-0 z-50 hidden">
  <!-- Content loaded via HTMX -->
</div>
```

O botão "Finalizar Pedido" dispara:
```html
hx-get="/auth/modal/"
hx-target="#auth-modal-container"
_="on htmx:afterOnLoad remove .hidden from #auth-modal-container"
```

Isso mantém o modal fora do drawer no DOM, evitando conflitos de overflow/z-index.

## Fluxo OAuth Google com allauth

1. Usuário clica "Continuar com Google"
2. Botão faz `GET /accounts/google/login/` (allauth)  
3. allauth redireciona para `accounts.google.com/o/oauth2/auth?...`
4. Usuário autoriza no Google
5. Google redireciona para `/accounts/google/login/callback/?code=...`
6. allauth troca o code por token, obtém profile do Google
7. allauth chama `login(request, user)` → `session.cycle_key()` → carrinho preservado
8. allauth redireciona para `LOGIN_REDIRECT_URL` (atualmente `index`)
9. **Problema:** o usuário deveria ir para o checkout, não para index

**Solução:** Usar `next` parameter do allauth. Antes de redirecionar para Google, salvar na sessão `session['checkout_after_login'] = True`. Após o login, verificar na view de redirect e encaminhar para checkout.

Alternativa mais limpa: configurar `SOCIALACCOUNT_LOGIN_ON_GET = True` e usar `?next=/checkout/` na URL de login do Google.

## Password Reset com Django built-in

Django oferece 4 views prontas:
- `PasswordResetView` — formulário de e-mail
- `PasswordResetDoneView` — confirmação de envio
- `PasswordResetConfirmView` — formulário de nova senha
- `PasswordResetCompleteView` — confirmação de troca

Requerem apenas templates e um backend de e-mail configurado. Para dev, usar `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` (imprime no terminal).

## Google Cloud Console — Setup

1. Acesse [console.cloud.google.com](https://console.cloud.google.com)
2. Crie um projeto (ou use existente)
3. APIs & Services → OAuth consent screen → External → preencha nome do app
4. APIs & Services → Credentials → Create → OAuth 2.0 Client ID
5. Application type: Web application
6. Authorized JavaScript origins: `http://localhost:8000`
7. Authorized redirect URIs: `http://localhost:8000/accounts/google/login/callback/`
8. Copie Client ID e Client Secret para `.env`
