# Onboarding: 010-checkout-ux-cliente

> Como testar esta feature do zero após implementação

## Pré-requisitos

- Servidor rodando (`docker compose -f docker-compose.prod.yml up` ou `uvicorn store_saas.asgi:application --reload`)
- Loja `mockburger` criada com produtos (já feito nesta sessão)
- Superuser criado

## Roteiro de teste

### Cenário 1 — Usuário com histórico de pedidos (RF-01: phone pré-preenchido)

1. Faça login como `restaurante` / `senha123` em `http://localhost:8000/accounts/login/`
2. Adicione qualquer produto ao carrinho
3. Abra o carrinho (ícone no header)
4. **Verificar:** campo "Telefone" aparece preenchido com o telefone do último pedido deste usuário

### Cenário 2 — Endereço salvo com cidade e estado (RF-02: string completa)

1. Ainda logado, vá em "Meus Endereços" no carrinho → "Novo Endereço"
2. Preencha: Rua Baturité, 118, Centro, Fortaleza, CE, CEP 60410-350
3. Salve o endereço
4. Clique no endereço salvo
5. **Verificar:** o campo de endereço recebe `"Rua Baturité, 118 - Centro, Fortaleza - CE, CEP 60410-350"`

### Cenário 3 — Lista de endereços oculta o textarea (RF-03)

1. Logado com ao menos 1 endereço salvo, abra o carrinho
2. **Verificar:** o textarea de endereço livre NÃO está visível inicialmente
3. Clique em "Outro endereço"
4. **Verificar:** o textarea aparece

### Cenário 4 — Feedback de limite (RF-04)

1. Salve 3 endereços (limite máximo)
2. Tente salvar um 4º
3. **Verificar:** aparece mensagem de erro "Você já atingiu o limite de 3 endereços salvos"

### Cenário 5 — Visitante sem regressão (RF-06)

1. Saia da conta (logout)
2. Adicione produto ao carrinho e abra o drawer
3. **Verificar:** vê os campos nome, telefone, e-mail e endereço livre — fluxo idêntico ao anterior

### Cenário 6 — Uber Direct não regrediu (RNF)

1. (Requer loja com Uber Direct configurado e ativo)
2. Abra o carrinho logado, selecione um endereço salvo
3. Clique em "Outro endereço" para revelar o textarea
4. Edite o endereço e clique fora do campo
5. **Verificar:** a cotação Uber Direct é chamada e a taxa de entrega atualizada

## Verificação em banco

```python
# No Django shell
from core.models import UserProfile
p = UserProfile.objects.get(user__username='restaurante')
print(p.phone)  # Deve mostrar o telefone do último pedido
```
