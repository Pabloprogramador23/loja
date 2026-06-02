# Requirements: Taxa de Entrega por Restaurante

> Identificador: `007-taxa-entrega`
> Data: `2026-05-30`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

---

## 1. Resumo executivo

Cada restaurante (Store/tenant) poderá configurar uma taxa de entrega fixa, que será exibida ao cliente durante o fluxo de carrinho e checkout, e somada automaticamente ao total do pedido. O valor da taxa é persistido como snapshot no pedido no momento da criação, garantindo que alterações futuras não afetem pedidos históricos. Pedidos de balcão (retirada) não sofrem cobrança de taxa de entrega.

---

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/erd-complete.md#STORE` | `Store` não possui campo `delivery_fee`; o campo precisa ser criado | 🟢 |
| `_reversa_sdd/erd-complete.md#ORDER` | `Order.total_amount` é o valor total do pedido; não há campo separado para taxa de entrega — precisa ser adicionado como snapshot | 🟢 |
| `_reversa_sdd/domain.md#RN-04` | Checkout valida `customer_name`, `customer_phone` e `delivery_address`; `total_amount` é calculado a partir do carrinho | 🟢 |
| `_reversa_sdd/domain.md#RN-07` | `OrderItem.unit_price` é snapshot de preço no momento da compra — mesmo padrão deve ser seguido para `delivery_fee` | 🟢 |
| `_reversa_sdd/domain.md#RN-08` | Pedido de balcão tem `delivery_address = "Balcão / Retirada"` e nasce em `PREPARING`; sem pagamento PIX | 🟢 |
| `_reversa_sdd/code-analysis.md#Módulo 2` | `StoreSettings` form em `core/forms.py` e view `manager_settings` em `/dashboard/settings/` — ponto natural de configuração da taxa | 🟡 |
| `_reversa_sdd/architecture.md#Padrões Arquiteturais` | Carrinho em sessão; `total` calculado em `cart.total`; a taxa de entrega precisa ser somada a esse valor no template e no checkout | 🟢 |

---

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Manager (gestor da loja) | Configurar a taxa de entrega da sua loja | Acessa `/dashboard/settings/`, define valor em R$ e salva |
| Cliente (autenticado ou guest) | Ver o custo total antes de confirmar o pedido | Abre o carrinho e vê subtotal dos itens + taxa de entrega + total |
| Cliente | Finalizar a compra sabendo o total exato | Confirma checkout; total do pedido já inclui a taxa de entrega |

---

## 4. Regras de negócio novas ou alteradas

1. **RN-20: Taxa de entrega configurável por loja** 🟢
   - Cada `Store` possui um campo `delivery_fee` (decimal, padrão `0.00`, mínimo `0.00`).
   - O Manager configura o valor em `/dashboard/settings/`.
   - Taxa igual a `0.00` representa entrega gratuita.
   - Tipo: **nova**

2. **RN-21: Snapshot de taxa de entrega no pedido** 🟢
   - Ao criar o `Order` no checkout, o valor de `Store.delivery_fee` é copiado para `Order.delivery_fee` (snapshot). Alterações posteriores da taxa não afetam pedidos já criados.
   - Origem no legado: `_reversa_sdd/domain.md#RN-07` (padrão de snapshot já aplicado em `OrderItem.unit_price`).
   - Tipo: **nova**

3. **RN-22: Total do pedido inclui taxa de entrega** 🟡
   - `Order.total_amount = soma dos OrderItems + Order.delivery_fee`.
   - Altera a forma como `total_amount` é calculado no checkout.
   - Origem no legado: `_reversa_sdd/domain.md#RN-04` (checkout calcula `total` a partir do carrinho).
   - Tipo: **alterada**

4. **RN-23: Pedido de balcão isento de taxa de entrega** 🟢
   - Pedidos criados via `manager_create_order` (balcão/retirada) sempre têm `delivery_fee = 0.00`, independente da configuração da loja.
   - Origem no legado: `_reversa_sdd/domain.md#RN-08` (balcão = `"Balcão / Retirada"`, sem pagamento).
   - Tipo: **nova**

5. **RN-24: Exibição da taxa no carrinho e checkout** 🟡
   - O drawer do carrinho e a tela de checkout mostram a taxa de entrega como linha separada entre o subtotal e o total. Se a taxa for `0.00`, exibir "Entrega grátis".
   - Tipo: **nova**

6. **RN-25: Valor mínimo para entrega gratuita (opcional, por loja)** 🟢
   - `Store` possui campo `free_delivery_threshold` (decimal, anulável, padrão `null`).
   - Quando `null` (padrão): o recurso está **desativado** — a taxa de entrega se aplica normalmente a todos os pedidos.
   - Quando ativado e definido com valor `> 0`: pedidos cujo subtotal de itens for **maior ou igual** ao threshold têm `delivery_fee = 0.00` automaticamente; pedidos abaixo do threshold pagam a taxa normalmente.
   - O Manager ativa o recurso marcando uma opção em `/dashboard/settings/` e informando o valor mínimo. Pode desativar voltando a desmarcar.
   - Tipo: **nova**

---

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O campo `delivery_fee` (decimal, padrão `0.00`) deve ser adicionado ao modelo `Store` | Must | Migration gerada e aplicada; campo visível no admin | 🟢 |
| RF-02 | O Manager pode definir a taxa de entrega em `/dashboard/settings/` | Must | Formulário salva o valor; valor persiste ao recarregar a página | 🟢 |
| RF-03 | O carrinho (drawer lateral) exibe subtotal, taxa de entrega e total | Must | Linha "Taxa de entrega: R$ X,XX" aparece entre subtotal e total; quando zero mostra "Entrega grátis" | 🟡 |
| RF-04 | A tela de checkout exibe a taxa de entrega antes da confirmação | Must | Total no checkout = soma dos itens + taxa de entrega correta da loja | 🟢 |
| RF-05 | O campo `delivery_fee` (snapshot) é adicionado ao modelo `Order` | Must | Migration gerada; ao criar pedido, `Order.delivery_fee` recebe o valor de `Store.delivery_fee` do momento | 🟢 |
| RF-06 | `Order.total_amount` inclui a taxa de entrega no cálculo | Must | `total_amount = subtotal_itens + delivery_fee`; verificável via admin ou teste | 🟢 |
| RF-07 | Pedidos de balcão têm `delivery_fee = 0.00` sempre | Must | Criar pedido via `manager_create_order`; `Order.delivery_fee == 0.00` independente da taxa da loja | 🟢 |
| RF-08 | O histórico de pedidos do cliente mostra a taxa de entrega do pedido | Should | Em `/account/orders/` e detalhe do pedido, exibe a taxa que foi cobrada no momento da compra | 🟡 |
| RF-09 | O Manager pode ativar/desativar o valor mínimo para entrega gratuita em `/dashboard/settings/` | Should | Checkbox (ou toggle) + campo de valor; quando desmarcado, campo some e `free_delivery_threshold = null` | 🟢 |
| RF-10 | Pedidos com subtotal ≥ threshold recebem entrega gratuita automaticamente | Should | Com threshold = 50.00 e itens = R$ 50,00 → `delivery_fee = 0.00`; com itens = R$ 49,99 → taxa normal | 🟢 |
| RF-11 | O carrinho exibe mensagem motivacional quando próximo ao threshold | Could | Ex.: "Adicione R$ X,XX para ganhar entrega grátis"; quando threshold não está ativado, mensagem não aparece | 🟡 |

---

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Consistência de dados | `delivery_fee` em `Order` é imutável após criação (snapshot) | Segue o padrão de `OrderItem.unit_price` — `_reversa_sdd/domain.md#RN-07` | 🟢 |
| Validação | `Store.delivery_fee` aceita apenas valores `>= 0.00`; formulário rejeita valores negativos com mensagem de erro | Proteção contra dados inválidos | 🟡 |
| Compatibilidade | Pedidos existentes antes da migração devem ter `delivery_fee = 0.00` (default) | Sem quebrar histórico de pedidos já criados | 🟢 |
| Tenant isolation | A taxa exibida ao cliente deve ser sempre a da loja (tenant) ativa no request | Padrão de isolamento já estabelecido em `_reversa_sdd/architecture.md#Isolamento Multi-Tenant` | 🟢 |

---

## 7. Critérios de Aceitação

```gherkin
Cenário: Manager configura taxa de entrega
  Dado que o Manager está autenticado e acessa /dashboard/settings/
  Quando preenche o campo "Taxa de entrega" com R$ 5,00 e salva
  Então o valor é persistido em Store.delivery_fee para o tenant ativo

Cenário: Cliente vê taxa de entrega no carrinho
  Dado que a loja tem delivery_fee = 5.00
  E o cliente tem itens no carrinho totalizando R$ 30,00
  Quando abre o drawer do carrinho
  Então vê "Subtotal: R$ 30,00", "Taxa de entrega: R$ 5,00" e "Total: R$ 35,00"

Cenário: Taxa zero exibe "Entrega grátis"
  Dado que a loja tem delivery_fee = 0.00
  Quando o cliente abre o drawer do carrinho
  Então vê "Entrega grátis" no lugar da linha de taxa

Cenário: Total do pedido inclui taxa de entrega
  Dado que a loja tem delivery_fee = 5.00
  E o cliente finaliza checkout com itens totalizando R$ 30,00
  Quando o pedido é criado
  Então Order.total_amount = 35.00 e Order.delivery_fee = 5.00

Cenário: Alteração da taxa não afeta pedidos históricos
  Dado que um pedido foi criado com delivery_fee = 5.00
  Quando o Manager altera a taxa da loja para 8.00
  Então o pedido histórico ainda exibe delivery_fee = 5.00

Cenário: Pedido de balcão sem taxa de entrega
  Dado que a loja tem delivery_fee = 5.00
  Quando o Manager cria um pedido de balcão via /dashboard/criar-pedido/
  Então Order.delivery_fee = 0.00 e total_amount = subtotal apenas dos itens

Cenário: Valor negativo de taxa é rejeitado
  Dado que o Manager está em /dashboard/settings/
  Quando tenta salvar delivery_fee = -1.00
  Então o formulário exibe erro de validação e não persiste o valor

Cenário: Manager ativa entrega grátis acima de valor mínimo
  Dado que o Manager está em /dashboard/settings/
  E o recurso de valor mínimo está desativado (padrão)
  Quando marca a opção de entrega grátis e informa R$ 50,00
  Então free_delivery_threshold = 50.00 é persistido na loja

Cenário: Pedido acima do threshold recebe entrega grátis
  Dado que a loja tem delivery_fee = 5.00 e free_delivery_threshold = 50.00
  E o carrinho tem itens totalizando R$ 55,00
  Quando o cliente visualiza o carrinho e finaliza o checkout
  Então vê "Entrega grátis" e Order.delivery_fee = 0.00

Cenário: Pedido abaixo do threshold paga taxa normalmente
  Dado que a loja tem delivery_fee = 5.00 e free_delivery_threshold = 50.00
  E o carrinho tem itens totalizando R$ 30,00
  Quando o cliente visualiza o carrinho
  Então vê "Taxa de entrega: R$ 5,00" e total = R$ 35,00

Cenário: Manager desativa o valor mínimo
  Dado que free_delivery_threshold = 50.00
  Quando o Manager desmarca a opção em /dashboard/settings/
  Então free_delivery_threshold = null e a taxa volta a ser cobrada em todos os pedidos
```

---

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01: campo `delivery_fee` em `Store` | Must | Base de tudo; sem isso nada funciona |
| RF-02: configuração no dashboard | Must | O Manager precisa poder definir o valor |
| RF-05: campo `delivery_fee` em `Order` (snapshot) | Must | Integridade histórica de pedidos |
| RF-06: `total_amount` inclui taxa | Must | Valor enviado ao MercadoPago deve estar correto |
| RF-03: exibição no carrinho | Must | Cliente precisa ver a taxa antes de confirmar |
| RF-04: exibição no checkout | Must | Transparência do custo na confirmação |
| RF-07: balcão isento | Must | Regra de negócio clara, não cobrar entrega em retirada |
| RF-08: histórico de pedidos | Should | Importante para transparência, mas não bloqueia a compra |
| RF-09: configurar threshold no dashboard | Should | Recurso opcional; Manager precisa de controle |
| RF-10: isenção automática quando acima do threshold | Should | Regra de negócio do threshold; depende de RF-09 |
| RF-11: mensagem motivacional no carrinho | Could | Melhora UX, mas não é bloqueante |
| RNF validação de valor negativo | Should | Proteção de dados; a UI pode dar suporte com `min=0` |

---

## 9. Esclarecimentos

### Sessão 2026-05-30

- **Q:** Deve existir um campo "entrega grátis acima de R$ X"? Se sim, como deve funcionar?
  **R:** Sim. O recurso existe, mas fica **desativado por padrão**. O Manager ativa quando quiser e define o valor mínimo. Quando desativado, a taxa se aplica normalmente a todos os pedidos.

---

## 10. Lacunas

> Nenhuma lacuna em aberto. Todos os `[DÚVIDA]` foram resolvidos.

---

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-30 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-05-30 | Esclarecimento via `/reversa-clarify`: threshold de entrega grátis confirmado como opcional; RN-25, RF-09–11 e cenários Gherkin adicionados | reversa |
