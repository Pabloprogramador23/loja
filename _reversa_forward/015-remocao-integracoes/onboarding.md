# Onboarding: Remoção de Integrações Desnecessárias

> Identificador: `015-remocao-integracoes`
> Data: `2026-06-01`
> Para: desenvolvedor que vai testar a feature pela primeira vez

---

## Pré-requisitos

- Projeto rodando localmente com `uvicorn store_saas.asgi:application --reload --port 8000`
- Banco de dados com dados de seed (`python manage.py seed_loja`)
- Nenhuma variável `UBER_*` ou `GOOGLE_*` é necessária após esta feature

---

## Cenário 1 — Login por email funciona sem allauth

1. Acesse `http://127.0.0.1:8000/` (loja1 no fallback localhost)
2. Adicione qualquer produto ao carrinho
3. Clique em **Finalizar Pedido**
4. O modal de autenticação deve aparecer
5. **Verificar:** não há botão "Entrar com Google" visível
6. Preencha email e senha de um cliente do seed (ex.: o criado pelo `seed_loja`)
7. **Verificar:** login realizado com sucesso, retorno ao checkout

---

## Cenário 2 — Checkout calcula taxa estática

1. Acesse o painel do manager: `http://127.0.0.1:8000/dashboard/`
2. Vá em **Configurações da loja**
3. **Verificar:** nenhuma seção "Uber Direct" ou "Entrega por app" visível
4. Configure **Taxa de entrega** = R$ 5,00 e **Frete grátis acima de** = R$ 50,00
5. Adicione produto(s) com subtotal < R$ 50,00 ao carrinho
6. **Verificar:** taxa de R$ 5,00 exibida no carrinho e no checkout
7. Adicione mais produto(s) até subtotal > R$ 50,00
8. **Verificar:** taxa R$ 0,00 exibido ("Frete grátis")

---

## Cenário 3 — Rotas Uber Direct e Google OAuth retornam 404

```bash
# Rota allauth (Google OAuth callback)
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/accounts/google/login/
# Esperado: 404

# Webhook Uber Direct
curl -s -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:8000/api/webhooks/uber
# Esperado: 404
```

---

## Cenário 4 — Suite de testes passa

```bash
python manage.py test
# Esperado: 0 erros, 0 falhas (testes Uber Direct e Google OAuth foram removidos)
```

---

## Cenário 5 — Banco de dados limpo

```bash
python manage.py shell -c "
from django.db import connection
tables = connection.introspection.table_names()
uber_tables = [t for t in tables if 'uber' in t.lower()]
allauth_tables = [t for t in tables if t.startswith(('account_', 'socialaccount_'))]
print('Tabelas Uber:', uber_tables)
print('Tabelas allauth:', allauth_tables)
"
# Esperado: listas vazias
```

---

## O que NÃO testar (fora do escopo)

- Funcionalidades do MercadoPago (Checkout Pro) — não afetadas
- Modo escuro — não afetado
- Pedidos de balcão — não afetados
- Cadastro de novos usuários via email — verificar que continua funcionando (não é o foco mas é regressão crítica)
