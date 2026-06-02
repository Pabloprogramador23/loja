# Onboarding: Taxa de Entrega por Restaurante

> Identificador: `007-taxa-entrega`
> Data: `2026-05-30`
> Para: desenvolvedor ou testador que vai validar a feature pela primeira vez

---

## Pré-requisitos

- Servidor rodando: `uvicorn store_saas.asgi:application --reload --port 8000`
- Banco migrado: `python manage.py migrate`
- Dados de seed: `python manage.py seed_loja` (se banco vazio)
- Acesso a um usuário Manager (staff): use o superuser criado pelo seed

---

## Cenário 1 — Configurar taxa de entrega

1. Acesse `http://127.0.0.1:8000/dashboard/settings/` logado como Manager
2. Localize o campo **Taxa de entrega (R$)** — deve exibir `0,00` por padrão
3. Digite `5,00` e salve
4. Recarregue a página e confirme que o valor persistiu

---

## Cenário 2 — Verificar taxa no carrinho

1. Abra o catálogo: `http://127.0.0.1:8000/`
2. Adicione qualquer produto ao carrinho
3. Abra o drawer do carrinho (ícone de carrinho ou botão flutuante)
4. Verifique a linha **"Taxa de entrega: R$ 5,00"** entre o subtotal e o total
5. Confirme que o **Total** = subtotal dos itens + R$ 5,00

---

## Cenário 3 — Finalizar pedido com taxa

1. Com itens no carrinho, preencha nome, telefone e endereço
2. Clique em **Finalizar pedido**
3. Na tela de pagamento PIX, confirme que o valor do QR Code inclui a taxa
4. No Django Admin (`/admin/core/order/`), abra o pedido criado e verifique:
   - `delivery_fee = 5.00`
   - `total_amount = subtotal + 5.00`

---

## Cenário 4 — Entrega grátis acima de valor mínimo

1. Em `/dashboard/settings/`, ative a opção **Entrega grátis acima de** e informe `R$ 50,00`
2. Salve e volte ao catálogo
3. **Subtotal abaixo do threshold (ex: R$ 30,00):** carrinho deve mostrar "Taxa de entrega: R$ 5,00"
4. **Subtotal igual ou acima (ex: R$ 50,00):** carrinho deve mostrar "Entrega grátis"

---

## Cenário 5 — Pedido de balcão isento

1. Acesse `/dashboard/criar-pedido/` como Manager
2. Selecione produtos e crie o pedido
3. No Admin, abra o pedido de balcão e confirme `delivery_fee = 0.00`

---

## Cenário 6 — Snapshot preservado

1. Configure taxa `5,00` e finalize um pedido
2. Volte a `/dashboard/settings/` e altere a taxa para `10,00`
3. Abra o pedido antigo em `/account/orders/` (ou no Admin) e confirme que ainda mostra `delivery_fee = 5.00`

---

## Rodar os testes

```bash
python manage.py test core
```

Espera: todos os testes passam, incluindo os novos de taxa de entrega.
