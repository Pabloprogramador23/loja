# Requirements: Painel do Restaurante + Sistema de Comandas

> Identificador: `004-painel-restaurante`
> Data: `2026-05-27`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

O restaurante precisa de um fluxo de gestão de pedidos presenciais diferente do checkout do cliente. O garçom deve poder abrir uma comanda por identificador livre ("Mesa 3", "Balcão", "Delivery João"), adicionar itens incrementalmente enquanto a mesa pede, e fechar a comanda escolhendo pagamento presencial (marca como pago, sem PIX) ou PIX (gera QR Code). Paralelamente, um bug de navegação impede o manager de voltar ao painel quando entra na área de conta do cliente — esse bug também é corrigido nesta feature.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/code-analysis.md#2.7 Dashboard Manager` | `manager_create_order` cria pedido balcão de uma vez só (sem adição incremental). Status inicial: `PREPARING`. Não suporta comanda aberta. | 🟢 |
| `_reversa_sdd/domain.md#RN-08` | Pedido balcão: status inicial `PREPARING`, sem PIX, `delivery_address = "Balcão / Retirada"`. Ponto de extensão natural para o sistema de comandas. | 🟢 |
| `_reversa_sdd/domain.md#RN-12` | Acesso ao dashboard binário via `is_staff`. Controle manual em cada view. | 🟢 |
| `_reversa_sdd/permissions.md#Matriz de Permissões — Views Django` | `GET /account/orders/` acessível a Manager — mostra pedidos pessoais como cliente, sem link de retorno ao dashboard na sidebar | 🟢 |
| `_reversa_sdd/architecture.md#Stack Tecnológica` | Frontend: HTMX + Tailwind. Sem SPA framework. Atualização incremental via HTMX é o padrão do projeto. | 🟢 |
| `_reversa_sdd/domain.md#RN-07` | `OrderItem.unit_price` é snapshot do preço no momento da criação do item. Deve ser respeitado na comanda. | 🟢 |
| `templates/base.html` (leitura direta) | Header exibe "Meus Pedidos" para todos os autenticados — aponta para `/account/orders/` (fluxo cliente), inclusive para managers. Bug de navegação confirmado. | 🟢 |
| `templates/core/account/base_account.html` (leitura direta) | Sidebar da área de conta não tem link ao painel para managers. | 🟢 |
| `_reversa_sdd/code-analysis.md#2.7` | `base_manager.html` tem sidebar desktop somente — mobile sidebar comentado como "omitted for brevity". | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Garçom / Manager | Abrir comanda para uma mesa e registrar pedidos conforme chegam | Abre "Mesa 5", adiciona 2 hambúrgueres, depois adiciona mais 1 refrigerante quando o cliente pede |
| Garçom / Manager | Fechar comanda ao final da refeição | Vê o total da mesa, escolhe "Pagamento presencial" e marca como pago |
| Garçom / Manager | Fechar comanda via PIX | Cliente pede para pagar por PIX; garçom clica "Fechar via PIX" e exibe QR Code |
| Manager | Voltar ao painel a partir da área de conta | Entrou em "Minha Conta" por engano, vê o link "Painel de Gerência" na sidebar e retorna |
| Manager (mobile) | Gerir comandas pelo celular durante o expediente | Abre o dashboard no celular, acessa a lista de comandas via sidebar off-canvas |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** Uma comanda é um `Order` com status especial `OPEN` (novo valor na máquina de estados) que indica "tab aberta, em andamento". O status `OPEN` só existe para pedidos criados pelo Manager via sistema de comandas. 🟡
   - Origem no legado: `_reversa_sdd/domain.md#RN-08` (extensão do pedido balcão)
   - Tipo: nova

2. **RN-02:** Enquanto a comanda está em `OPEN`, o Manager pode adicionar `OrderItem`s a ela a qualquer momento. Cada item usa snapshot de preço (`unit_price = product.price` no momento da adição). 🟢
   - Origem no legado: `_reversa_sdd/domain.md#RN-07`
   - Tipo: nova

3. **RN-03:** Ao fechar a comanda como **presencial**, o status avança de `OPEN` para `PREPARING` (mesmo comportamento do balcão atual). Nenhum fluxo de pagamento digital é acionado. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#RN-08`
   - Tipo: nova

4. **RN-04:** Ao fechar a comanda via **PIX**, o sistema gera o QR Code MercadoPago (mesmo fluxo de `create_pix_payment`) e o status avança para `PENDING`. O webhook de aprovação segue o fluxo normal. 🟡
   - Origem no legado: `_reversa_sdd/domain.md#RN-09` e `RN-10`
   - Tipo: nova

5. **RN-05:** O identificador da comanda é texto livre (ex.: "Mesa 3", "Varanda", "Delivery João"), máximo 50 caracteres. Armazenado no campo `delivery_address` do `Order` existente ou em novo campo `table_label`. 🟡
   - Tipo: nova

6. **RN-06:** No header global (`base.html`), o link "Meus Pedidos" para `is_staff` aponta para `/dashboard/orders/` em vez de `/account/orders/`. 🟢
   - Origem no legado: `_reversa_sdd/permissions.md`
   - Tipo: alterada

7. **RN-07:** A sidebar de `base_account.html` exibe bloco "Painel de Gerência" com link para `/dashboard/` exclusivamente para `user.is_staff`. 🟢
   - Tipo: nova

8. **RN-08:** Enquanto a comanda está em `OPEN`, o Manager pode remover qualquer `OrderItem` dela. O total é recalculado imediatamente após a remoção. 🟢
   - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Nova seção "Comandas" no painel manager com lista das comandas em aberto (status `OPEN`), mostrando identificador, número de itens e total parcial | Must | `/dashboard/comandas/` lista todas as comandas `OPEN` do tenant atual |
| RF-02 | Botão "Nova Comanda" que abre formulário com campo texto livre para identificador | Must | Ao submeter, cria `Order(status=OPEN, table_label=<texto>)` e redireciona para a tela da comanda |
| RF-03 | Tela de comanda individual mostrando: identificador, lista de itens adicionados (nome, qtd, preço unitário, subtotal), total acumulado e campo para adicionar novo item (produto + quantidade) | Must | Manager vê os itens da comanda em tempo real; adicionar item atualiza o total sem reload de página (HTMX) |
| RF-04 | Ação "Adicionar Item" na comanda: dropdown de produtos do tenant + campo quantidade + botão confirmar | Must | Item é salvo como `OrderItem` na comanda; total é atualizado via HTMX |
| RF-05 | Botão "Fechar Comanda" com escolha: "Pagamento Presencial" ou "Fechar via PIX" | Must | Botão exibe modal ou inline com as duas opções |
| RF-06 | Fechamento presencial: status vai de `OPEN` para `PREPARING`; comanda desaparece da lista de abertas | Must | Comanda fecha sem gerar PIX; aparece em `/dashboard/orders/` como `PREPARING` |
| RF-07 | Fechamento via PIX: chama `create_pix_payment`, exibe QR Code + copia-e-cola; status vai para `PENDING` | Must | QR Code é exibido; mock funciona em dev (token `TEST-0000`) |
| RF-08 | Correção de navegação: header `base.html` — "Meus Pedidos" para `is_staff` aponta para `manager_orders` | Must | Manager clica "Meus Pedidos" e vai para `/dashboard/orders/`, não para `/account/orders/` |
| RF-09 | Correção de navegação: `base_account.html` sidebar — bloco "Painel de Gerência" visível só para `is_staff` | Must | Manager em `/account/` encontra link de volta ao dashboard na sidebar |
| RF-10 | Off-canvas mobile sidebar no `base_manager.html` com botão hamburger | Should | Em viewport < 768px, o manager acessa todas as seções via sidebar off-canvas |
| RF-11 | Botão "Remover" em cada item da comanda aberta; ao confirmar, o `OrderItem` é deletado e o total atualizado via HTMX | Must | Manager remove item da comanda; total recalcula sem reload; item some da lista |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Consistência visual | Tailwind CSS exclusivo — sem novas bibliotecas de UI | `_reversa_sdd/architecture.md#Stack Tecnológica` | 🟢 |
| Interatividade | Adição de itens e atualização de total via HTMX (padrão do projeto) — sem full page reload | `_reversa_sdd/architecture.md#Stack Tecnológica` | 🟢 |
| Isolamento multi-tenant | Comandas e itens são filtrados pelo tenant ativo via `TenantManager` — nenhuma comanda de outra loja vaza | `_reversa_sdd/domain.md#RN-01` | 🟢 |
| Compatibilidade com fluxo existente | Comandas fechadas (PREPARING / PENDING) aparecem normalmente em `/dashboard/orders/` e no rastreamento público | `_reversa_sdd/domain.md#RN-08`, `RN-16` | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Abrir nova comanda e adicionar itens incrementalmente
  Dado que o Manager está em /dashboard/comandas/
  Quando clica em "Nova Comanda" e digita "Mesa 3"
  Então a comanda "Mesa 3" é criada com status OPEN e zero itens
  Quando adiciona "X-Bacon" x2
  Então a comanda mostra 2x X-Bacon e o total atualizado
  Quando adiciona "Coca-Cola" x1
  Então a comanda mostra 3 itens e o novo total sem recarregar a página

Cenário: Fechar comanda com pagamento presencial
  Dado que a comanda "Mesa 3" está OPEN com R$ 63,80 em itens
  Quando o Manager clica "Fechar Comanda" e escolhe "Pagamento Presencial"
  Então o status muda para PREPARING
  E a comanda desaparece da lista de abertas
  E aparece em /dashboard/orders/ como PREPARING

Cenário: Fechar comanda via PIX
  Dado que a comanda "Mesa 7" está OPEN com R$ 45,00 em itens
  Quando o Manager clica "Fechar Comanda" e escolhe "Fechar via PIX"
  Então o sistema gera QR Code MercadoPago
  E exibe o QR Code e o código copia-e-cola na tela
  E o status da comanda vai para PENDING

Cenário: Correção de navegação — manager no fluxo cliente
  Dado que o Manager está em /account/orders/
  Quando olha para a sidebar da área de conta
  Então vê o item "Painel de Gerência" com link para /dashboard/
  E ao clicar retorna ao dashboard de gestão

Cenário: Correção de navegação — link "Meus Pedidos" no header
  Dado que o Manager está logado (is_staff=True)
  Quando clica em "Meus Pedidos" no header global
  Então é levado para /dashboard/orders/ (pedidos da loja)
  E não para /account/orders/ (pedidos pessoais)

Cenário: Regressão — cliente não afetado
  Dado que um usuário cliente (is_staff=False) está logado
  Quando clica em "Meus Pedidos" no header
  Então vai para /account/orders/ (comportamento inalterado)
  E a área de conta não exibe o bloco "Painel de Gerência"
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 a RF-07 + RF-11 — Sistema de comandas completo | Must | Core da feature; sem isso o restaurante não tem o fluxo pedido |
| RF-08 — Correção header "Meus Pedidos" | Must | Bug de 1 linha de template; custo zero, evita confusão |
| RF-09 — Link "Painel de Gerência" na sidebar de conta | Must | Escape confiável do fluxo cliente; 5 linhas de template |
| RF-10 — Off-canvas mobile no dashboard manager | Should | Dashboard inacessível no mobile; resolve lacuna documentada, mas não bloqueia o core |

## 9. Esclarecimentos

### Sessão 2026-05-27

- **Q:** O dono da loja também pode fazer pedidos como cliente na própria loja? Como o sistema deve tratar o acesso a "Meus Pedidos"?
  **R:** O usuário quer um fluxo completamente diferente do checkout do cliente. O restaurante cria "comandas" (ex.: "Mesa 3"), adiciona itens incrementalmente e fecha com pagamento presencial ou PIX. Não é prioridade manter acesso a `/account/orders/` para o manager como cliente.

- **Q:** Depois que a comanda é aberta, o garçom pode adicionar mais itens depois?
  **R:** Sim — a comanda fica "em aberto" e o garçom vai adicionando itens conforme o cliente pede mais coisas. (opção a)

- **Q:** Quando o garçom "fecha" a comanda, o que acontece com o pagamento?
  **R:** Misto — pode escolher na hora entre pagamento presencial ou PIX. (opção c)

- **Q:** Como o restaurante identifica as comandas em aberto?
  **R:** Texto livre por enquanto — "Mesa 3", "Mesa 7" etc. Melhora depois. (opção c)

- **Q:** É possível remover um item já adicionado a uma comanda em aberto?
  **R:** Sim — o Manager pode remover qualquer item de uma comanda aberta. Total recalculado imediatamente via HTMX. (RN-08 e RF-11 adicionados)

## 10. Lacunas

> Nenhuma lacuna aberta. Todos os pontos foram esclarecidos.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-27 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-05-27 | Esclarecimentos integrados por `/reversa-clarify` — feature expandida para sistema de comandas; dúvidas de navegação resolvidas | reversa |
| 2026-05-27 | RN-08 e RF-11 adicionados: remoção de item de comanda aberta | reversa |
