# Roadmap: Taxa de Entrega por Restaurante

> Identificador: `007-taxa-entrega`
> Data: `2026-05-30`
> Requirements: `_reversa_forward/007-taxa-entrega/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

---

## 1. Resumo da abordagem

A feature é um delta cirúrgico sobre três camadas do legado: **modelo de dados**, **lógica de checkout** e **templates**.

No modelo, dois campos novos: `Store.delivery_fee` (valor padrão da loja) e `Store.free_delivery_threshold` (opcional, nulo = desativado), mais `Order.delivery_fee` como snapshot no momento da compra — replicando o padrão já estabelecido em `OrderItem.unit_price` (`_reversa_sdd/domain.md#RN-07`).

Na lógica, o `checkout()` em `core/views.py` recebe um incremento: calcular se o threshold está ativo e se o subtotal do carrinho o atinge, decidir o `delivery_fee` efetivo, e incluí-lo no `total_amount` e no campo snapshot do `Order`. O `manager_create_order` (balcão) sempre grava `delivery_fee=0.00`. O context processor de carrinho (`core/context_processors.py`) passa as variáveis de taxa ao template global.

Nos templates, o `cart_drawer.html` ganha uma linha de taxa de entrega entre subtotal e total, e o `manager/settings.html` ganha os campos de configuração. Nenhum contrato externo muda: o MercadoPago já recebe `order.total_amount` — com a taxa embutida o valor simplesmente aumenta conforme esperado.

A migração é backward-compatible: `delivery_fee` em `Store` e `Order` tem `default=0.00`, e `free_delivery_threshold` tem `null=True`, garantindo que pedidos e lojas existentes não sejam afetados.

---

## 2. Princípios aplicados

> `.reversa/principles.md` não encontrado — seção preenchida com base nos padrões extraídos do legado.

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| Snapshot de preço por pedido (`_reversa_sdd/domain.md#RN-07`) | `Order.delivery_fee` replica o padrão de `OrderItem.unit_price`: valor travado no momento da criação | respeita |
| Isolamento multi-tenant (`_reversa_sdd/domain.md#RN-01`) | Taxa lida de `store` já resolvido pelo TenantManager; context processor lê `request.tenant` | respeita |
| Transação atômica no checkout (`_reversa_sdd/code-analysis.md#2.3`) | Snapshot de `delivery_fee` acontece dentro do bloco `transaction.atomic()` existente | respeita |
| Balcão sem pagamento PIX (`_reversa_sdd/domain.md#RN-08`) | `manager_create_order` força `delivery_fee=0.00`, independente da configuração da loja | respeita |

---

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | `delivery_fee` como campo em `Order` (snapshot) | Consistência com `OrderItem.unit_price`; alteração futura da taxa não afeta pedidos históricos | Calcular dinamicamente na view (sem snapshot) — rejeitado: perde histórico | 🟢 |
| D-02 | `free_delivery_threshold` nullable em `Store` (`null=True, blank=True, default=None`) | `null` sinaliza "desativado" de forma explícita, sem flag booleana extra; formulário exibe o campo condicionalmente | Campo booleano separado — rejeitado: dois campos para uma informação só | 🟢 |
| D-03 | Cálculo de `delivery_fee` efetiva no `checkout()` em Python, não no template | A lógica de threshold precisa estar no servidor para garantir integridade; o template só exibe | Calcular no JS do cliente — rejeitado: facilmente manipulável | 🟢 |
| D-04 | Expor `delivery_fee` e `free_delivery_threshold` ao template via context processor existente (`core/context_processors.py`) | O context processor já injeta `cart`; adicionar variáveis de taxa segue o mesmo ponto de entrada sem criar um novo middleware | Templatetag customizada — rejeitado: mais complexidade sem ganho | 🟡 |
| D-05 | Campos de configuração adicionados ao `StoreSettings` form já existente (`core/forms.py`) | A view `manager_settings` e o template `manager/settings.html` já existem para configuração da loja | View/form novos — rejeitado: duplicação desnecessária | 🟢 |
| D-06 | `delivery_fee` no pedido de balcão sempre `0.00`, hardcoded em `manager_create_order` | Balcão = retirada presencial; cobrança de taxa de entrega não faz sentido semântico | Usar a taxa da loja mesmo no balcão — rejeitado: contradiz RN-23 | 🟢 |

---

## 4. Premissas

> Nenhum `[DÚVIDA]` residual. Seção n/a.

---

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `Store` (modelo) | `_reversa_sdd/erd-complete.md#STORE` | regra-alterada | Dois campos novos: `delivery_fee` e `free_delivery_threshold` |
| `Order` (modelo) | `_reversa_sdd/erd-complete.md#ORDER` | regra-alterada | Campo novo `delivery_fee` (snapshot) |
| `checkout()` (view) | `_reversa_sdd/code-analysis.md#2.3` | regra-alterada | Calcula `delivery_fee` efetiva (considerando threshold) e inclui no `total_amount` e no snapshot |
| `manager_create_order()` (view) | `_reversa_sdd/code-analysis.md#2.7` | regra-alterada | Força `delivery_fee=0.00` ao criar o pedido de balcão |
| `StoreSettings` (form) | `_reversa_sdd/code-analysis.md#Módulo 2` | regra-alterada | Campos `delivery_fee` e `free_delivery_threshold` adicionados |
| Context processor de carrinho | `_reversa_sdd/code-analysis.md#Módulo 2` | regra-alterada | Expõe `store_delivery_fee`, `free_delivery_threshold` e `effective_delivery_fee` ao template |
| `cart_drawer.html` (template) | `_reversa_sdd/inventory.md#partials` | regra-alterada | Linha de taxa de entrega entre subtotal e total; mensagem de entrega grátis; mensagem motivacional (Could) |
| `manager/settings.html` (template) | `_reversa_sdd/inventory.md#Templates` | regra-alterada | Campos de `delivery_fee` e `free_delivery_threshold` com toggle |
| Templates de pedido do cliente | `_reversa_sdd/inventory.md#Templates` | regra-alterada | Exibir `delivery_fee` do pedido em `account/order_detail.html` e `account/orders.html` |

---

## 6. Delta no modelo de dados

- `Store` ganha `delivery_fee` (DecimalField 10,2, default 0.00) e `free_delivery_threshold` (DecimalField 10,2, null, blank, default None)
- `Order` ganha `delivery_fee` (DecimalField 10,2, default 0.00, snapshot)
- Uma migração nova cobre os três campos
- Detalhe completo em: `_reversa_forward/007-taxa-entrega/data-delta.md`

---

## 7. Delta de contratos externos

> Nenhum contrato externo novo ou alterado. O MercadoPago recebe `order.total_amount` — que agora inclui a taxa — via `payment.py` sem mudança de interface. A assinatura de `create_pix_payment(order)` não muda.

---

## 8. Plano de migração

1. Criar a migration com os 3 campos novos (`Store.delivery_fee`, `Store.free_delivery_threshold`, `Order.delivery_fee`)
2. Aplicar migration em dev (`python manage.py migrate`); lojas e pedidos existentes recebem defaults sem intervenção manual
3. Atualizar `StoreSettings` form e view `manager_settings` (campos novos)
4. Atualizar `checkout()` com lógica de cálculo e snapshot
5. Atualizar `manager_create_order()` com `delivery_fee=0.00` explícito
6. Atualizar context processor para expor variáveis de taxa
7. Atualizar templates (`cart_drawer`, `settings`, `order_detail`)
8. Escrever testes cobrindo: taxa no checkout, isenção por threshold, balcão isento, snapshot preservado após mudança na loja

---

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| `total_amount` enviado ao MP muda — pedidos reais podem ter valor diferente do esperado se taxa já estiver configurada antes da migration | médio | baixo | Migration com default 0.00 garante que nenhuma loja existente terá taxa inesperada; Manager precisa ativar explicitamente |
| Threshold comparado com `Decimal` vs `float` causando erro de tipo | baixo | médio | Usar `Decimal` em todo o cálculo; `cart.get_total_price()` já retorna `Decimal` (`_reversa_sdd/code-analysis.md#2.2`) |
| Template do carrinho exibe taxa errada em parcial HTMX (swap sem contexto) | baixo | baixo | Context processor injeta taxa no contexto global; parciais recarregadas pelo HTMX recebem o contexto normalmente |
| `manager_create_order` esquecer de zerar a taxa | médio | baixo | Coberto por teste unitário (RF-07) |

---

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] Migration aplicada sem erro em SQLite (dev) e PostgreSQL (prod-like)
- [ ] Manager consegue configurar `delivery_fee` e `free_delivery_threshold` em `/dashboard/settings/`
- [ ] Carrinho exibe taxa correta antes do checkout
- [ ] `Order.delivery_fee` snapshot preservado após mudar a taxa da loja
- [ ] Pedido de balcão com `delivery_fee = 0.00`
- [ ] Testes passando (`python manage.py test core`)
- [ ] `regression-watch.md` gerado

---

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-30 | Versão inicial gerada por `/reversa-plan` | reversa |
