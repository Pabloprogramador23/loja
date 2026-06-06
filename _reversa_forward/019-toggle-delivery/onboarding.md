# Onboarding: Testando a Feature 019 — Toggle Delivery

> Feature: `019-toggle-delivery`
> Pré-requisito: servidor rodando via `uvicorn store_saas.asgi:application --reload --port 8000`
> Pré-requisito: migration aplicada (`python manage.py migrate`)

---

## Cenário 1 — Manager fecha a loja pelo dashboard

1. Faça login como manager (`is_staff=True`) em `http://127.0.0.1:8000`
2. Acesse `http://127.0.0.1:8000/dashboard/`
3. Localize o botão **"Fechar loja"** (verde quando aberta)
4. Clique no botão
5. **Esperado:** botão muda para **"Abrir loja"** (cinza/vermelho) sem reload de página

---

## Cenário 2 — Cliente vê banner de loja fechada

1. Com a loja fechada (cenário 1), abra uma aba anônima
2. Acesse `http://127.0.0.1:8000/catalog/`
3. **Esperado:** banner amarelo/vermelho no topo "Não estamos aceitando pedidos no momento"
4. **Esperado:** é possível navegar no catálogo normalmente (banner não bloqueia)
5. Abra o carrinho (adicione um produto)
6. **Esperado:** drawer exibe aviso e botão "Confirmar Pedido" aparece desabilitado (cinza, não clicável)

---

## Cenário 3 — POST direto no checkout bloqueado (segurança)

1. Com a loja fechada, abra o console do browser (F12)
2. Execute:
   ```javascript
   fetch('/checkout/', {
     method: 'POST',
     headers: {'X-CSRFToken': document.cookie.match(/csrftoken=([^;]+)/)[1], 'Content-Type': 'application/x-www-form-urlencoded'},
     body: 'customer_name=Teste&customer_phone=11999999999&delivery_address=Rua+Teste&payment_method=online'
   })
   ```
3. **Esperado:** response contém o drawer com mensagem de erro; **nenhum Order criado no banco**

---

## Cenário 4 — Manager reabre a loja

1. No dashboard do manager, clique em **"Abrir loja"**
2. **Esperado:** botão volta para "Fechar loja" (verde)
3. Na aba anônima do Cenário 2, recarregue o catálogo
4. **Esperado:** banner sumiu; carrinho funciona normalmente

---

## Cenário 5 — Configuração via tela de Settings

1. Acesse `http://127.0.0.1:8000/dashboard/settings/`
2. Localize o checkbox **"Aceitar pedidos online"**
3. Desmarque e salve
4. **Esperado:** loja fecha (mesmo efeito do toggle rápido)
5. Marque novamente e salve — loja abre

---

## Verificação de regressão

- [ ] Pagamentos com loja **aberta** continuam funcionando normalmente
- [ ] Taxa de entrega e threshold de frete grátis continuam calculados corretamente
- [ ] Dashboard de pedidos existentes não é afetado pelo toggle
- [ ] `Store.is_active` não foi alterado por nenhum path desta feature
