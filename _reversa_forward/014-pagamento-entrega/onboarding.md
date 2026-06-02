# Onboarding: Pagamento na Entrega (014)

> Guia executável para testar a feature do zero
> Pré-requisito: feature 013 (Checkout Pro MP) já implementada e funcionando

---

## 0. Pré-requisitos

1. **Servidor rodando:**
   ```
   uvicorn store_saas.asgi:application --reload --port 8000
   ```
2. **Celery rodando** (para notificação ao restaurante):
   ```
   celery -A store_saas worker -l info
   ```
3. **Loja ativa** com pelo menos um produto disponível
4. **Usuário manager** com acesso ao painel (`/manager/`)
5. **Migration aplicada:**
   ```
   python manage.py migrate core
   ```

---

## 1. Verificação do model

Confirme que os novos campos aparecem no shell:

```bash
python manage.py shell
>>> from core.models import Order
>>> Order.Status.CONFIRMED
<Order.Status.CONFIRMED: 'CONFIRMED'>
>>> [c for c in Order.PaymentMethod.choices]
[('online', 'Online (MP)'), ('cash', 'Dinheiro'), ('card', 'Cartão na Maquininha')]
>>> Order._meta.get_field('payment_method').default
'online'
>>> Order._meta.get_field('change_amount').null
True
```

---

## 2. Cenário A — Pagar com Dinheiro (troco informado)

**Objetivo:** Criar pedido com `payment_method=cash`, `change_amount=50.00`, sem chamar MP.

1. Abra `http://127.0.0.1:8000` (ou subdomínio da loja)
2. Adicione pelo menos um produto ao carrinho
3. Abra o carrinho (drawer lateral)
4. Preencha **Nome**, **Telefone** e **Endereço de entrega**
5. Na seção de pagamento, selecione **"Pagar na Entrega"**
6. Selecione **"Dinheiro"**
7. No campo "Precisa de troco? Para quanto?", informe **50**
8. Clique em **"Confirmar Pedido"**

**Resultado esperado:**
- Browser navega para `/payment/success/` (sem abrir página do MercadoPago)
- No shell: `Order.objects.last().status` → `'CONFIRMED'`
- No shell: `Order.objects.last().payment_method` → `'cash'`
- No shell: `Order.objects.last().change_amount` → `Decimal('50.00')`

---

## 3. Cenário B — Pagar com Cartão Débito

1. Repita o fluxo acima até a seção de pagamento
2. Selecione **"Pagar na Entrega"** → **"Cartão"** → **"Débito"**
3. Confirme o pedido

**Resultado esperado:**
- `Order.objects.last().payment_method` → `'card'`
- `Order.objects.last().card_type` → `'debit'`
- `Order.objects.last().change_amount` → `None`
- `Order.objects.last().status` → `'CONFIRMED'`

---

## 4. Cenário C — Pagar Online (sem regressão)

1. Repita o fluxo mas selecione **"Pagar Online"**
2. Confirme

**Resultado esperado:**
- Browser abre página do MercadoPago (init_point)
- `Order.objects.last().status` → `'PENDING'`
- `Order.objects.last().payment_method` → `'online'`

---

## 5. Verificação no Painel do Manager

1. Abra `http://127.0.0.1:8000/manager/orders/`
2. **O pedido criado nos cenários A e B deve aparecer** com status "Confirmado"
3. Badge de método de pagamento deve exibir "Dinheiro" ou "Cartão Débito"
4. Para o cenário A: troco de R$ 50,00 deve estar visível no modal do pedido

**Verificação extra — dashboard:**
1. Abra `http://127.0.0.1:8000/manager/`
2. O contador de **"Pedidos Pendentes"** deve incluir os pedidos `CONFIRMED`

---

## 6. Verificação da notificação Celery

Após o Cenário A ou B, verifique o log do Celery worker:

```
[INFO] Received task: core.tasks.process_new_order[...]
[INFO] Task core.tasks.process_new_order[...] succeeded
```

Confirma que o restaurante foi notificado via Celery sem intervenção do webhook MP.

---

## 7. Cenário de erro — troco inválido

1. Selecione "Pagar na Entrega" → "Dinheiro"
2. No campo de troco, informe **-10** ou **"abc"**
3. Confirme

**Resultado esperado:**
- Pedido não criado
- Mensagem de erro de validação exibida no checkout
- `Order.objects.count()` não aumentou

---

## 8. Checklist de aceite

- [ ] Pedido na entrega criado com `status=CONFIRMED`
- [ ] `payment_method`, `change_amount`, `card_type` persistidos corretamente
- [ ] Sem redirect para MP no fluxo na entrega
- [ ] Celery task disparada e logada
- [ ] Pedido `CONFIRMED` visível no painel `/manager/orders/`
- [ ] Badge de método de pagamento exibido no card/modal
- [ ] Dashboard conta pedido `CONFIRMED` em "Pedidos Pendentes"
- [ ] Fluxo "Pagar Online" inalterado (sem regressão com feature 013)
- [ ] `change_amount` inválido rejeitado com erro
