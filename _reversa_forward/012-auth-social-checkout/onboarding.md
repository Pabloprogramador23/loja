# Onboarding: 012-auth-social-checkout

> Como configurar e testar esta feature do zero

## Pré-requisitos

- Conta Google Cloud com projeto criado
- Servidor rodando (`docker compose -f docker-compose.prod.yml up` ou `uvicorn ... --reload`)
- Superuser criado (`python manage.py createsuperuser`)

## Setup do Google OAuth (uma vez)

1. Siga as instruções em `investigation.md#Google-Cloud-Console-Setup`
2. Adicione ao `.env`:
   ```
   GOOGLE_CLIENT_ID=seu_client_id_aqui
   GOOGLE_CLIENT_SECRET=seu_client_secret_aqui
   ```
3. Reinicie o servidor
4. Acesse `/admin/sites/site/1/change/` → defina `domain=localhost:8000`, `name=loja`
5. Acesse `/admin/socialaccount/socialapp/add/` → crie o SocialApp Google conforme `data-delta.md`

## Para dev sem Google configurado

O modal exibe a aba Google como desabilitada com mensagem "Google não configurado". Teste apenas pelas abas "Entrar" e "Cadastrar".

Configure o backend de e-mail no terminal (para ver links de reset):
```python
# settings.py (dev)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

## Roteiro de testes

### Cenário 1 — Interceptação do "Finalizar Pedido"
1. Certifique-se de estar **deslogado**
2. Adicione produtos ao carrinho
3. Abra o carrinho e clique "Finalizar Pedido"
4. **Verificar:** modal de identificação aparece (não vai para checkout)
5. **Verificar:** carrinho continua com os itens após fechar o modal

### Cenário 2 — Cadastro no modal
1. No modal, aba "Cadastrar"
2. Preencha nome, e-mail novo, celular, senha
3. Clique "Criar conta"
4. **Verificar:** conta criada, sessão iniciada, carrinho preservado, redirect para checkout

### Cenário 3 — Login no modal (conta existente)
1. Deslogue e adicione itens ao carrinho
2. Abra modal → aba "Entrar"
3. Preencha e-mail e senha de conta existente
4. **Verificar:** login bem-sucedido, carrinho preservado, redirect para checkout

### Cenário 4 — Login Google
1. Com Google configurado, deslogue e adicione itens
2. Abra modal → aba "Google" → clique "Continuar com Google"
3. Autorize no Google
4. **Verificar:** conta criada/logada, carrinho preservado, redirect para checkout

### Cenário 5 — Recuperação de senha
1. No modal → aba "Entrar" → "Esqueci minha senha"
2. Informe e-mail cadastrado
3. **Verificar:** e-mail impresso no terminal (dev) com link de reset
4. Clique no link → defina nova senha → faça login

### Cenário 6 — Manager não afetado
1. Acesse `/accounts/login/` diretamente
2. Faça login com conta staff
3. **Verificar:** redirect normal para `/dashboard/`; nenhum modal aparece

### Cenário 7 — Usuário já autenticado
1. Esteja logado, adicione itens, abra carrinho
2. Clique "Finalizar Pedido"
3. **Verificar:** vai direto para o checkout sem modal

## Verificação no banco

```python
# Django shell
from allauth.socialaccount.models import SocialAccount
print(SocialAccount.objects.all())  # Lista contas Google vinculadas

from django.contrib.auth.models import User
u = User.objects.get(email='seu@gmail.com')
print(u.profile.phone)  # Phone do UserProfile
```
