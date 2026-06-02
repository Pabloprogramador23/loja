# Requirements: Melhoria de UX no Checkout do Cliente

> Identificador: `010-checkout-ux-cliente`
> Data: `2026-05-30`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

O checkout atual exige que clientes autenticados preencham manualmente nome, telefone e endereço a cada pedido — mesmo tendo endereços salvos no sistema. O campo de seleção de endereço salvo preenche o textarea sem cidade e estado, gerando registros de entrega incompletos. Esta feature corrige essas inconsistências e torna o checkout inteligente ao contexto do usuário: logado ou visitante, com ou sem histórico de pedidos.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/domain.md#RN-04` | Checkout valida `customer_name`, `customer_phone` e `delivery_address` — sem distinção entre usuário logado e visitante | 🟢 |
| `_reversa_sdd/domain.md#RN-06` | Limite de 3 endereços por `(user, store)`; erro de limite não exibe feedback ao usuário | 🟢 |
| `_reversa_sdd/domain.md#RN-05` | Guest order e vinculação pós-signup; sessão guarda apenas um `guest_order_id` | 🟢 |
| `_reversa_sdd/code-analysis.md#2.3` | `checkout()` em `views.py`: phone não é pré-preenchido do perfil; `selectAddress` em `address_list.html` monta string sem cidade/estado | 🟢 |
| `_reversa_sdd/domain.md#Glossário` | `Address` tem campos estruturados (street, number, neighborhood, city, state, zip_code); `Order.delivery_address` é TextField livre | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Cliente autenticado com endereços salvos | Finalizar pedido sem redigitar dados | Seleciona endereço salvo com um clique, telefone já preenchido, clica em "Finalizar Pedido" |
| Cliente autenticado sem endereços salvos | Fazer primeiro pedido sem fricção | Preenche telefone (único campo novo) e digita endereço livremente; sistema salva o endereço automaticamente |
| Visitante (guest) | Comprar sem criar conta | Preenche nome, telefone, e-mail e endereço — fluxo atual mantido |
| Cliente autenticado retornando | Repetir pedido sem redigitar | Telefone pré-preenchido do último pedido; endereços salvos disponíveis para seleção |

## 4. Regras de negócio novas ou alteradas

1. **RN-10:** Para usuário autenticado, o campo `customer_phone` no checkout deve ser pré-preenchido com o telefone do pedido mais recente do usuário na loja atual, se existir. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#RN-04` (alterada — passa a diferenciar autenticado de visitante)
   - Tipo: alterada

2. **RN-11:** A string `delivery_address` gerada pela seleção de endereço salvo deve incluir cidade e estado no formato: `{street}, {number} - {neighborhood}, {city} - {state}`. Quando zip_code estiver preenchido, acrescentar `, CEP {zip_code}`. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#RN-04` (bug de omissão de dados)
   - Tipo: alterada

3. **RN-12:** Para usuário autenticado com pelo menos um endereço salvo, o textarea de endereço livre deve ser substituído pela lista de endereços salvos como primeira opção. A opção "Outro endereço" revela o textarea. Usuários sem endereços salvos veem diretamente o textarea. 🟡
   - Tipo: nova

4. **RN-13:** Ao realizar checkout com sucesso, se o usuário estiver autenticado e o endereço digitado livremente não coincidir com nenhum endereço salvo, o sistema deve oferecer salvá-lo (não forçar). 🟡
   - Tipo: nova

5. **RN-14:** O limite de 3 endereços (`_reversa_sdd/domain.md#RN-06`) deve exibir mensagem de feedback visível ao usuário quando atingido, em vez de falhar silenciosamente. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#RN-06`
   - Tipo: alterada

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Pré-preencher `customer_phone` com o telefone do pedido mais recente do usuário autenticado na loja atual | Must | Campo telefone aparece preenchido ao abrir o carrinho quando usuário está logado e tem pedidos anteriores | 🟢 |
| RF-02 | Corrigir `selectAddress` para incluir cidade e estado na string de endereço | Must | Ao clicar num endereço salvo, o textarea recebe `"{rua}, {nº} - {bairro}, {cidade} - {estado}"` | 🟢 |
| RF-03 | Exibir lista de endereços salvos como modo padrão para usuário autenticado com endereços | Must | Usuário logado com endereços vê a lista; o textarea está oculto até clicar em "Outro endereço" | 🟡 |
| RF-04 | Exibir feedback visual quando limite de 3 endereços é atingido | Must | Tentar salvar 4º endereço exibe mensagem de erro no form, não falha silenciosamente | 🟢 |
| RF-05 | Oferecer salvar endereço digitado livremente após checkout bem-sucedido de usuário autenticado | Should | Modal ou banner aparece após conclusão do pedido quando endereço não está na lista salva e limite não foi atingido | 🟡 |
| RF-06 | Manter fluxo atual (nome + telefone + e-mail + endereço) inalterado para visitantes | Must | Visitante sem login vê todos os campos sem alteração | 🟢 |
| RF-07 | Campo nome pré-preenchido para usuário logado (já existente) deve permanecer funcionando | Must | `request.user.get_full_name()` continua preenchendo o campo nome | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Compatibilidade HTMX | Todas as alterações no `cart_drawer.html` devem manter compatibilidade com `hx-target="#cart-content"` e `hx-trigger="updateCart from:body"` | O drawer é renderizado via HTMX; qualquer quebra de target interrompe a UX | 🟢 |
| Sem regressão — checkout visitante | O fluxo de guest não deve ser afetado por nenhuma das mudanças | RN-05 e RN-04 são críticos para faturamento | 🟢 |
| Sem regressão — Uber Direct | A lógica de cotação via `blur` no textarea deve ser preservada quando o textarea estiver visível | Feature 009 depende do evento `hx-trigger="blur"` no `delivery_address` | 🟢 |
| Performance | A query de "último pedido do usuário" deve usar `.first()` com `order_by('-created_at')` e não carregar todos os pedidos | Baixo risco mas evita N+1 se chamado dentro do context processor | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Cliente logado com endereços salvos abre o carrinho
  Dado que o usuário está autenticado
  E possui ao menos um endereço salvo na loja
  Quando abre o drawer do carrinho
  Então vê a lista de endereços salvos (não o textarea livre)
  E o campo telefone está pré-preenchido com o telefone do último pedido

Cenário: Cliente logado seleciona endereço salvo
  Dado que o usuário está autenticado e vê a lista de endereços
  Quando clica em um endereço salvo
  Então o campo oculto delivery_address recebe "{rua}, {nº} - {bairro}, {cidade} - {estado}"
  E o endereço selecionado fica visualmente destacado

Cenário: Cliente logado quer digitar outro endereço
  Dado que o usuário está autenticado e vê a lista de endereços
  Quando clica em "Outro endereço"
  Então o textarea de endereço livre aparece
  E o atributo hx-trigger="blur" do Uber Direct permanece funcional se a loja tiver Uber ativo

Cenário: Cliente logado atinge limite de endereços salvos
  Dado que o usuário tem 3 endereços salvos
  Quando tenta salvar um 4º endereço
  Então vê a mensagem "Você já atingiu o limite de 3 endereços salvos" no formulário
  E nenhum endereço é criado no banco

Cenário: Visitante finaliza pedido (sem regressão)
  Dado que o usuário não está autenticado
  Quando abre o carrinho
  Então vê os campos nome, telefone, e-mail e endereço livre
  E pode finalizar o pedido normalmente sem necessidade de login

Cenário: Endereço selecionado tem cidade e estado no registro do pedido
  Dado que um pedido é criado via seleção de endereço salvo
  Quando o pedido é salvo no banco
  Então Order.delivery_address contém cidade e estado do Address selecionado
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 — Pré-preenchimento de telefone | Must | Elimina fricção em todo pedido repetido; zero risco de regressão |
| RF-02 — Correção da string de endereço | Must | Bug ativo: city/state ausentes em todos os pedidos via endereço salvo |
| RF-03 — Lista de endereços como modo padrão | Must | UX core para usuários que já cadastraram endereços |
| RF-04 — Feedback de limite de endereços | Must | Bug ativo: falha silenciosa causa confusão ao usuário |
| RF-06 — Manter fluxo visitante | Must | Não pode regredir — fluxo crítico de faturamento |
| RF-05 — Oferecer salvar endereço pós-checkout | Should | Melhoria conveniente, mas não bloqueia o pedido |
| RNF — Compatibilidade Uber Direct | Must | Feature 009 em produção, não pode regredir |

## 9. Esclarecimentos

| # | Dúvida | Resposta | Data |
|---|--------|----------|------|
| D-01 | Persistência do telefone: buscar do último `Order` ou criar `UserProfile` com campo `phone`? | **Criar `UserProfile`** com campo `phone`. Atualizado a cada checkout bem-sucedido. | 2026-05-30 |

**Decisão D-01 — impacto no escopo:**
- Nova migration: `UserProfile(OneToOne→User, phone: CharField blank=True)`
- Signal `post_save` em `Order` (ou lógica no `checkout()`) atualiza `UserProfile.phone` após cada pedido de usuário autenticado
- `cart_detail` view passa `profile.phone` no contexto para pré-preencher o campo

## 10. Lacunas

Nenhuma lacuna pendente.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-30 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-05-30 | D-01 resolvida: UserProfile com campo phone | Pablo |
