# Onboarding: Toggle de Métodos de Pagamento

> Identificador: `024-toggle-metodos-pagamento`
> Data: `2026-06-08`
> Para: quem vai testar esta feature pela primeira vez

---

## Pré-requisitos

- Servidor rodando via `uvicorn store_saas.asgi:application --reload --port 8000`
- Banco migrado (`python manage.py migrate`)
- Loja ativa com manager logado (usuário `is_staff=True` ou dono da loja)
- Browser em `http://127.0.0.1:8000` (ou subdomínio configurado)

---

## Cenário 1 — Desabilitar "Dinheiro" e verificar o checkout

1. Acesse o painel do manager → **Configurações da Loja**
2. Na seção "Métodos de Pagamento", desmarque **"Aceitar Dinheiro"**
3. Salve o formulário
4. Abra o catálogo como cliente (aba anônima ou outro usuário)
5. Adicione um produto ao carrinho
6. Abra o drawer do carrinho
7. **Resultado esperado:** o seletor "Dinheiro" não aparece — apenas "MercadoPago" e "Cartão"
8. Tente forçar via curl/Postman: `POST /checkout/ payment_method=cash`
9. **Resultado esperado:** resposta contém o drawer com mensagem "Método de pagamento não disponível"

---

## Cenário 2 — Apenas MercadoPago habilitado

1. No painel de settings, desmarque "Aceitar Dinheiro" e "Aceitar Cartão"
2. Mantenha "Aceitar MercadoPago" marcado
3. Salve
4. Como cliente, abra o carrinho
5. **Resultado esperado:** apenas o seletor "Pagar com MercadoPago" visível
6. Finalize o pedido normalmente — fluxo de pagamento online deve funcionar normalmente

---

## Cenário 3 — Todos os métodos desabilitados

1. No painel de settings, desmarque os três checkboxes
2. Salve
3. Como cliente, tente finalizar um pedido
4. **Resultado esperado:** aviso "Nenhum método de pagamento disponível no momento" — sem possibilidade de submeter o checkout

---

## Cenário 4 — Aviso de MP sem token

1. No painel de settings, apague o campo "Token MercadoPago"
2. Salve
3. Reabra a tela de settings
4. **Resultado esperado:** aviso amarelo acima do checkbox "Aceitar MercadoPago" indicando que o token não está configurado

---

## Cenário 5 — Reabrir todos os métodos

1. No painel de settings, marque os três checkboxes novamente
2. Salve
3. Como cliente, abra o carrinho
4. **Resultado esperado:** todos os três seletores de método voltam a aparecer

---

## Verificação rápida via Django Shell

```python
# python manage.py shell
from core.models import Store
s = Store.objects.first()

# Verificar estado atual
print(s.payment_online_enabled, s.payment_cash_enabled, s.payment_card_enabled)

# Desabilitar dinheiro
s.payment_cash_enabled = False
s.save()

# Confirmar
s.refresh_from_db()
print(s.payment_cash_enabled)  # False
```
