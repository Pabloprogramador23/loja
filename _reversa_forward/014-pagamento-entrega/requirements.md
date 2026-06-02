# Requirements: Pagamento na Entrega (011-C)

> Identificador: `014-pagamento-entrega`
> Data: `2026-05-30`
> Spec-mãe: `_reversa_forward/011-fluxo-cliente-redesign/requirements.md`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

O checkout atual só suporta pagamento online via Checkout Pro MP (feature 013). Esta feature adiciona **pagamento na entrega** como segunda opção, sem integração com MP. O cliente escolhe entre "Pagar Online" ou "Pagar na Entrega"; neste caso seleciona "Dinheiro" (com campo de troco opcional) ou "Cartão na Maquininha" (crédito ou débito). O pedido é criado com o novo status `CONFIRMED` — confirmado e aguardando preparo — sem nenhuma chamada ao MP. O restaurante vê o pedido imediatamente no painel. Três novos campos são adicionados ao model `Order`: `payment_method`, `change_amount` e `card_type`. A máquina de estados do Order recebe o novo estado inicial `CONFIRMED`.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/state-machines.md#Order` | Estados atuais: PENDING, PREPARING, DELIVERING, COMPLETED, CANCELED. CONFIRMED não existe — **novo estado inicial** | 🟢 |
| `_reversa_sdd/domain.md#RN-08` | Pedido de balcão nasce em PREPARING sem PIX; padrão semelhante ao pagamento na entrega | 🟢 |
| `_reversa_sdd/code-analysis.md#2.3` | `checkout()` em `core/views.py`: cria Order com status PENDING e chama `create_checkout_pro_preference()` — fluxo a ser ramificado | 🟢 |
| `_reversa_sdd/domain.md#RN-04` | Checkout valida `customer_name`, `customer_phone`, `delivery_address` — campos obrigatórios preservados | 🟢 |
| `_reversa_sdd/architecture.md#ADR-006` | Notificação ao restaurante via Celery + polling HTMX no painel já existente | 🟢 |
| `_reversa_forward/013-checkout-pro-mp` | Checkout Pro implementado; `checkout()` atualizado para chamar `create_checkout_pro_preference()` — ponto de ramificação desta feature | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Cliente sem cartão/conta MP | Pagar na entrega com dinheiro | Checkout → "Pagar na Entrega" → "Dinheiro" → informa troco → pedido confirmado |
| Cliente prefere cartão presencial | Pagar na entrega com cartão | Checkout → "Pagar na Entrega" → "Cartão" → seleciona crédito ou débito → pedido confirmado |
| Restaurante | Receber pedido sem pagamento online | Pedido aparece no painel com status "Confirmado" e método de pagamento visível |
| Cliente online | Pagar online normalmente | Escolhe "Pagar Online" → fluxo Checkout Pro (inalterado) |

## 4. Regras de negócio novas ou alteradas

1. **RN-38:** O formulário de checkout exibe dois botões: "Pagar Online" (chama `create_checkout_pro_preference()`, fluxo atual) e "Pagar na Entrega" (exibe seletor de método). 🟡
   - Tipo: nova

2. **RN-39:** Ao selecionar "Pagar na Entrega", o cliente vê duas sub-opções: Dinheiro e Cartão na Maquininha. A seleção de Dinheiro exibe dinamicamente o campo "Precisa de troco? Para quanto?" (valor numérico opcional). A seleção de Cartão exibe escolha Crédito / Débito. 🟡
   - Tipo: nova

3. **RN-40:** Novo status `CONFIRMED` na máquina de estados do `Order`. Pedidos com pagamento na entrega nascem em `CONFIRMED` diretamente, sem passar por `PENDING`. A transição para `PREPARING` ocorre quando o manager aceita/inicia o preparo. 🟡
   - Origem: amplia `_reversa_sdd/state-machines.md#Order`
   - Tipo: nova (novo estado no enum `Order.Status`)

4. **RN-41:** Ao confirmar pagamento na entrega, o `checkout()` cria o `Order` com: `status=CONFIRMED`, `payment_method` preenchido (`cash` ou `card`), `change_amount` (Decimal ou None), `card_type` (`credit`, `debit` ou None). Nenhuma chamada ao MP é feita. 🟡
   - Tipo: nova

5. **RN-42:** Após criar um pedido na entrega, o sistema dispara `process_new_order.delay(order.id)` imediatamente (mesmo mecanismo de pedido aprovado via webhook), garantindo que o restaurante seja notificado via Celery. 🟡
   - Origem: `_reversa_sdd/architecture.md#ADR-006`
   - Tipo: nova

6. **RN-43:** O painel do manager exibe o método de pagamento do pedido: "Online (MP)", "Dinheiro" (com troco se aplicável), "Cartão Crédito" ou "Cartão Débito". O status `CONFIRMED` deve ser tratado no dashboard de forma equivalente a `PREPARING` para fins de visibilidade imediata. 🟡
   - Tipo: nova

7. **RN-44:** `Order.payment_method` tem valor padrão `online` para todos os pedidos criados pelo fluxo do Checkout Pro (retrocompatibilidade). 🟢
   - Tipo: nova (campo com default)

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Tela de checkout exibe escolha entre "Pagar Online" e "Pagar na Entrega" antes de confirmar | Must | Dois botões/opções visíveis; seleção muda o comportamento do submit | 🟡 |
| RF-02 | Seleção de "Pagar na Entrega" exibe sub-opções: Dinheiro e Cartão | Must | Sub-opções aparecem dinamicamente ao selecionar "Pagar na Entrega" | 🟡 |
| RF-03 | Seleção de Dinheiro exibe campo "Precisa de troco? Para quanto?" (opcional) | Must | Campo aparece ao clicar Dinheiro; campo desaparece ao clicar Cartão | 🟡 |
| RF-04 | Seleção de Cartão exibe opções Crédito / Débito | Must | Botões Crédito e Débito aparecem ao clicar Cartão | 🟡 |
| RF-05 | `checkout()` aceita `payment_method` do POST; cria Order com status `CONFIRMED`, campos de pagamento preenchidos, sem chamar MP | Must | Order salvo no banco com `status=CONFIRMED`, `payment_method`, `change_amount`, `card_type` corretos | 🟢 |
| RF-06 | `process_new_order.delay()` disparado após criar pedido na entrega | Must | Task Celery executada; restaurante notificado via painel | 🟡 |
| RF-07 | Após confirmar pedido na entrega, cliente vê tela de confirmação (não redireciona para MP) | Must | Browser navega para `/payment/success/` ou equivalente, sem abrir página MP | 🟡 |
| RF-08 | Painel do manager exibe pedidos `CONFIRMED` junto com `PENDING` e `PREPARING` | Must | Pedidos na entrega aparecem no painel imediatamente após criação | 🟡 |
| RF-09 | Painel exibe método de pagamento por pedido | Should | Coluna/badge "Dinheiro", "Cartão Crédito", "Cartão Débito" ou "Online" visível no card/modal do pedido | 🟡 |
| RF-10 | Fluxo "Pagar Online" permanece inalterado | Must | Checkout Pro MP funciona identicamente ao estado atual da feature 013 | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Retrocompatibilidade | `Order.payment_method` tem default `online`; Orders históricos sem o campo devem funcionar | Migration com `default='online'` | 🟢 |
| Sem regressão MP | O fluxo Checkout Pro (feature 013) não pode ser afetado | `create_checkout_pro_preference()` chamada apenas quando `payment_method=online` | 🟢 |
| Segurança | `change_amount` e `card_type` vêm do POST do cliente — validar que `change_amount` é numérico positivo ou None | Input de usuário não confiável | 🟢 |
| Visibilidade | Status `CONFIRMED` deve ser incluído nas queries do dashboard que hoje mostram apenas `PENDING` | `_reversa_sdd/domain.md#RN-13` (KPIs do dashboard) | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Cliente escolhe pagar com dinheiro e informa troco
  Dado que o usuário está autenticado e tem itens no carrinho
  Quando seleciona "Pagar na Entrega" → "Dinheiro" e informa troco de R$ 50
  E confirma o pedido
  Então Order é criado com status=CONFIRMED, payment_method=cash, change_amount=50.00
  E browser navega para tela de confirmação (sem abrir MP)
  E o pedido aparece no painel do restaurante

Cenário: Cliente escolhe pagar com cartão de débito
  Dado que o usuário está autenticado e tem itens no carrinho
  Quando seleciona "Pagar na Entrega" → "Cartão" → "Débito"
  E confirma o pedido
  Então Order criado com status=CONFIRMED, payment_method=card, card_type=debit, change_amount=None

Cenário: Cliente escolhe pagar online (sem regressão)
  Dado que o usuário está autenticado e tem itens no carrinho
  Quando seleciona "Pagar Online" e confirma
  Então browser redireciona para init_point do MP (fluxo feature 013 inalterado)
  E Order criado com status=PENDING, payment_method=online

Cenário: Painel exibe pedido na entrega imediatamente
  Dado que um pedido CONFIRMED foi criado
  Quando o manager abre o painel de pedidos
  Então o pedido aparece com status visível e método de pagamento "Dinheiro" ou "Cartão"

Cenário: change_amount inválido é rejeitado
  Dado que o cliente seleciona Dinheiro e informa troco = -10 ou "abc"
  Quando confirma o pedido
  Então o sistema retorna erro de validação sem criar o Order
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01/02/03/04 — UX de seleção de pagamento | Must | Sem seleção o cliente não chega ao fluxo na entrega |
| RF-05 — Order com status CONFIRMED e campos de pagamento | Must | Core da feature |
| RF-06 — process_new_order.delay() | Must | Sem isso o restaurante não é notificado |
| RF-07 — Tela de confirmação sem MP | Must | UX esperada pelo cliente |
| RF-08 — Painel mostra CONFIRMED | Must | Restaurante precisa ver o pedido |
| RF-10 — Sem regressão Online | Must | Feature 013 não pode quebrar |
| RF-09 — Badge de método de pagamento no painel | Should | Informação útil mas não bloqueia o pedido |

## 9. Esclarecimentos

> Nenhuma sessão de dúvidas registrada ainda.

## 10. Lacunas

Nenhuma lacuna pendente.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-30 | Versão inicial gerada por `/reversa-requirements` | reversa |
