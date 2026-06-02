# Requirements: Integração Uber Direct — Cotação Dinâmica e Despacho de Entrega

> Identificador: `009-uber-direct-delivery`
> Data: `2026-05-30`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Integrar o serviço de logística de última milha **Uber Direct** ao fluxo de compra da plataforma. A feature entrega dois resultados distintos: (a) **cotação dinâmica no checkout** — ao selecionar um endereço de entrega, o cliente vê imediatamente o valor real da taxa cobrada pela Uber, substituindo a taxa fixa configurada pelo restaurante; (b) **despacho de entrega pelo restaurante** — após a confirmação de pagamento, o Manager pode solicitar a entrega via Uber Direct diretamente do dashboard, acompanhar o status em tempo real e cancelar se necessário.

O legado já possui `Address` estruturado com campos suficientes para montar o endereço formatado exigido pela API, `Order.delivery_fee` para snapshot da taxa (feature 007), e infraestrutura de filas assíncronas (Celery + Redis) reutilizável para o processamento de webhooks.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/architecture.md#Integrações Externas` | Único gateway externo atual é MercadoPago. Uber Direct será a segunda integração externa, seguindo o padrão de credenciais por tenant (ADR-003). | 🟢 |
| `_reversa_sdd/domain.md#RN-04` | Checkout exige `delivery_address` como string; o modelo `Address` estruturado existe e seus campos serão usados para montar o `formatted_address` da API Uber. | 🟢 |
| `_reversa_sdd/data-dictionary.md#Address` | Campos `street`, `number`, `complement`, `neighborhood`, `city`, `state`, `zip_code` disponíveis. CEP é opcional no modelo atual — relevante para precisão da cotação. | 🟢 |
| `_reversa_sdd/data-dictionary.md#Order` | `delivery_fee` (feature 007) armazena snapshot da taxa no momento do checkout. Para pedidos Uber Direct, esse valor virá da cotação dinâmica. | 🟢 |
| `_reversa_sdd/data-dictionary.md#Store` | `delivery_fee` + `free_delivery_threshold` (feature 007). Quando Uber Direct estiver ativo para a loja, a cotação dinâmica substitui o valor estático na exibição ao cliente. | 🟢 |
| `_reversa_sdd/code-analysis.md#2.6` | FastAPI já recebe webhooks do MercadoPago via `POST /api/webhooks/mercadopago`. O endpoint Uber seguirá o mesmo padrão com adição de validação HMAC. | 🟢 |
| `_reversa_sdd/code-analysis.md#Celery` | `process_new_order` como padrão de task Celery assíncrona a ser reutilizado para processar webhooks Uber com retentativas automáticas. | 🟢 |
| `_reversa_sdd/code-analysis.md#2.3` | Checkout calcula `effective_delivery_fee` localmente via context processor. Quando Uber Direct estiver ativo, esse valor passa a ser a cotação retornada pela API. | 🟢 |
| `_reversa_sdd/architecture.md#Dívidas Técnicas` | L-04 (webhook MercadoPago sem validação HMAC) é lição aprendida: webhook Uber Direct deve obrigatoriamente validar assinatura antes de processar. | 🟢 |
| `_reversa_sdd/domain.md#RN-08` | Pedidos de balcão têm `delivery_address = "Balcão / Retirada"` e não passam pelo fluxo de entrega. Uber Direct não se aplica a esses pedidos. | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Cliente autenticado | Ver o custo real de entrega antes de confirmar o pedido | Seleciona endereço cadastrado no checkout → cotação Uber aparece no resumo do carrinho em tempo real |
| Cliente anônimo (guest) | Ver o custo de entrega sem precisar se cadastrar | Digita endereço manualmente no formulário de checkout → cotação Uber é solicitada e exibida em tempo real |
| Manager | Solicitar entrega via Uber sem sair do dashboard | Pedido em PREPARING → clica "Despachar via Uber" → entregador alocado pela Uber |
| Manager | Acompanhar status da entrega | Vê status Uber atualizado no modal do pedido; acessa link de rastreamento para compartilhar com o cliente |
| Manager | Cancelar entrega antes da coleta | Entregador ainda não saiu para coletar → cancela a corrida diretamente no painel |
| Manager / Admin SaaS | Configurar credenciais Uber Direct por restaurante | Acessa configurações da loja, cadastra o Store ID Uber e ativa a integração |

## 4. Regras de negócio novas ou alteradas

1. **RN-D01:** Quando a loja tem Uber Direct configurado e ativo, a taxa de entrega exibida no checkout e gravada no pedido é **exclusivamente** o valor retornado pela cotação dinâmica da Uber. O `store.delivery_fee` estático é completamente ignorado na exibição ao cliente, sendo utilizado apenas como fallback quando a API Uber retornar erro. O `free_delivery_threshold` também é ignorado — com Uber Direct ativo, isenção de frete não existe; o cliente sempre paga o valor exato cotado pela Uber. 🟢
   - Altera: `_reversa_sdd/domain.md#RN-04` (checkout), feature 007 (cálculo de taxa e isenção)
   - Tipo: alterada

2. **RN-D02:** A cotação Uber possui validade (TTL fornecido pela API, tipicamente 5 minutos). O `quote_id` deve ser utilizado para criar a entrega antes de expirar. Se o cliente demorar além do TTL para confirmar o pedido, uma nova cotação deve ser solicitada automaticamente. 🟡
   - Tipo: nova

3. **RN-D03:** O `Order.delivery_fee` continua sendo snapshot da taxa no momento do checkout. Para pedidos com Uber Direct ativo, esse valor reflete a cotação Uber aceita. Para pedidos de lojas sem Uber Direct, o comportamento da feature 007 permanece inalterado. 🟢
   - Altera: `_reversa_sdd/data-dictionary.md#Order` — mesma coluna, fonte do valor muda quando Uber Direct está ativo
   - Tipo: alterada

4. **RN-D04:** O despacho via Uber Direct só pode ser solicitado pelo Manager quando o pedido está no status `PREPARING`. Pedidos `PENDING` (aguardando pagamento), `DELIVERING`, `COMPLETED` ou `CANCELED` não permitem novo despacho. 🟡
   - Origem no legado: `_reversa_sdd/domain.md#RN-12` (acesso manager é binário)
   - Tipo: nova

5. **RN-D05:** Pedidos de balcão (`delivery_address = "Balcão / Retirada"`) não devem gerar cotação Uber durante o checkout nem exibir botão de despacho no painel do Manager. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#RN-08`
   - Tipo: nova

6. **RN-D06:** O token OAuth2 Uber Direct (válido aproximadamente 30 dias) deve ser cacheado no Redis e renovado automaticamente quando expirar ou quando a API retornar HTTP 401. 🟡
   - Tipo: nova

7. **RN-D07:** Webhooks recebidos do Uber Direct devem ser validados por assinatura HMAC-SHA256 (Código de Autenticação de Mensagem baseado em Hash) antes de qualquer processamento. Requisições com assinatura ausente ou inválida retornam HTTP 401 sem processamento. 🟢
   - Origem no legado: `_reversa_sdd/architecture.md#Dívidas Técnicas` (L-04 — lição aprendida com MercadoPago)
   - Tipo: nova

8. **RN-D08:** A URL de rastreamento (`tracking_url`) retornada pela Uber após o despacho deve ser armazenada e exibida no modal de detalhes do pedido para o Manager. 🟡
   - Tipo: nova

9. **RN-D09:** Falha na cotação Uber (timeout, erro 5xx, ou loja sem cobertura) não bloqueia o checkout. O sistema deve exibir mensagem informativa e permitir prosseguir com a taxa estática da loja (`store.delivery_fee`) como fallback — único cenário onde o valor estático é utilizado com Uber Direct ativo. 🟡
   - Tipo: nova

10. **RN-D10:** A cotação Uber Direct está disponível para clientes anônimos (guest checkout). O endereço para cotação é o digitado manualmente no formulário de checkout. O `formatted_address` é montado a partir dos campos preenchidos pelo guest (sem `Address` persistido). 🟢
    - Altera: RF-01 (abrange autenticados e guests)
    - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O sistema deve exibir a cotação de frete Uber Direct no resumo do carrinho quando o usuário informa um endereço de entrega e a loja tem Uber Direct ativo — tanto para usuários autenticados (endereço salvo) quanto para guests (endereço digitado manualmente) | Must | Endereço informado → taxa exibida em ≤ 3s sem recarregar a página; total do carrinho atualiza incluindo a taxa; fallback para taxa estática em caso de erro | 🟢 |
| RF-02 | O sistema deve criar a entrega Uber Direct ao confirmar despacho pelo Manager | Must | Manager clica "Despachar via Uber" → API Uber cria entrega com `estimate_id` válido → `UberDirectDelivery` salvo com `uber_delivery_id` e `tracking_url` | 🟢 |
| RF-03 | O Manager deve poder visualizar o status atual da entrega Uber no modal do pedido | Must | Modal exibe status Uber (último recebido por webhook) e link de rastreamento; atualiza após webhook | 🟡 |
| RF-04 | O status do pedido (`Order.status`) deve ser atualizado para `DELIVERING` automaticamente quando a Uber confirmar que o entregador está a caminho do cliente | Should | Webhook com status `EN_ROUTE_TO_DROPOFF` → `Order.status = DELIVERING` | 🟡 |
| RF-05 | O Manager deve poder cancelar a entrega Uber Direct antes de o entregador coletar o pedido | Should | Botão "Cancelar Entrega" disponível enquanto `UberDirectDelivery.status` for `PENDING` ou `SCHEDULED`; ao cancelar, API Uber é chamada e status local atualizado para `CANCELED` | 🟡 |
| RF-06 | O Manager deve poder configurar e ativar as credenciais Uber Direct por loja | Must | Formulário em Configurações da loja permite salvar `uber_store_id`, ativar/desativar integração; ao ativar, checkout começa a exibir cotação dinâmica | 🟢 |
| RF-07 | O sistema deve renovar a cotação automaticamente se o TTL expirar antes do cliente confirmar o pedido | Should | Se `quote_id` inválido no momento do checkout → nova cotação solicitada; cliente vê valor atualizado antes de confirmar | 🟡 |
| RF-08 | Pedidos de balcão não devem exibir cotação Uber nem permitir despacho | Must | `delivery_address = "Balcão / Retirada"` → sem cotação no checkout; sem botão de despacho no modal | 🟢 |
| RF-09 | Falha na cotação Uber não deve impedir o checkout | Must | Erro na API Uber → mensagem "Taxa de entrega indisponível; valor estimado pode ser diferente" → checkout prossegue com taxa estática | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Desempenho | Cotação Uber deve ser obtida em ≤ 3s p95 para não degradar o checkout | Latência da API Uber Direct é externa e variável; requisição deve ser não-bloqueante e com timeout configurado | 🟡 |
| Segurança | Credenciais Uber (client_id, client_secret, webhook signing key) devem ser armazenadas via variáveis de ambiente ou campo de banco encriptado, nunca em texto plano em settings versionados | Padrão do projeto: `MERCADOPAGO_ACCESS_TOKEN` via env var | 🟢 |
| Segurança | Webhook Uber deve validar assinatura HMAC-SHA256 antes de processar qualquer evento | Lição aprendida de L-04 (webhook MercadoPago sem validação HMAC) | 🟢 |
| Resiliência | Falha total da Uber Direct (API fora do ar) não deve afetar pedidos de lojas sem Uber Direct ativo | Configuração por tenant — loja sem Uber Direct configurado não é impactada | 🟢 |
| Resiliência | Webhooks processados devem ter retentativa automática em caso de falha transiente (ex: banco indisponível) | Padrão Celery com `max_retries=3` já usado em `process_new_order` | 🟡 |
| Multi-tenant | Credenciais e configuração Uber Direct são por tenant; a ausência de configuração em uma loja não afeta outras | Padrão estabelecido pelo MercadoPago (ADR-003) | 🟢 |
| Observabilidade | Erros de integração Uber (falha na cotação, falha no despacho, webhook inválido) devem ser registrados em log com o ID do pedido | Projeto sem observabilidade formal — logging Python padrão é suficiente neste estágio | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Cliente autenticado recebe cotação Uber ao selecionar endereço
  Dado que a loja tem Uber Direct ativo e configurado
  E o cliente está autenticado com ao menos um endereço cadastrado
  Quando o cliente seleciona um endereço no resumo do carrinho
  Então a linha "Taxa de Entrega" exibe o valor cotado pela Uber em ≤ 3 segundos
  E o total do carrinho é atualizado para incluir a taxa cotada
  E o quote_id é associado à sessão do cliente para uso no checkout

Cenário: Falha na cotação Uber não bloqueia o checkout
  Dado que a loja tem Uber Direct ativo
  E a API Uber retorna erro (timeout ou HTTP 5xx)
  Quando o cliente seleciona o endereço
  Então o sistema exibe "Taxa de entrega indisponível no momento"
  E o checkout prossegue com a taxa estática configurada na loja

Cenário: Manager despacha pedido em PREPARING via Uber Direct
  Dado que o pedido está no status PREPARING
  E a loja tem Uber Direct ativo
  Quando o Manager clica em "Despachar via Uber" no modal do pedido
  Então o sistema cria a entrega na API Uber com o quote_id associado ao pedido
  E um registro UberDirectDelivery é salvo com uber_delivery_id e tracking_url
  E a tracking_url é exibida no modal do pedido

Cenário: Webhook Uber atualiza status do pedido para DELIVERING
  Dado que uma entrega Uber Direct foi criada para o pedido
  Quando a Uber envia webhook com evento de status "EN_ROUTE_TO_DROPOFF"
  Então o UberDirectDelivery.status é atualizado para EN_ROUTE_TO_DROPOFF
  E o Order.status é atualizado para DELIVERING

Cenário: Webhook com assinatura inválida é rejeitado
  Dado que o endpoint de webhook Uber recebe um POST
  Quando o header de assinatura está ausente ou incorreto
  Então o sistema retorna HTTP 401
  E nenhuma atualização de pedido ou entrega ocorre

Cenário: Manager cancela entrega antes da coleta
  Dado que a entrega Uber está no status PENDING ou SCHEDULED
  Quando o Manager clica em "Cancelar Entrega Uber" no modal
  Então o sistema chama a API de cancelamento da Uber
  E o UberDirectDelivery.status é atualizado para CANCELED
  E o Order.status permanece em PREPARING (pronto para novo despacho ou encerramento manual)

Cenário: Manager ativa Uber Direct nas configurações da loja
  Dado que o Manager acessa as Configurações da loja
  Quando preenche o uber_store_id e ativa a integração
  Então ao próximo checkout de cliente autenticado com endereço salvo a cotação dinâmica é exibida
  E o store.delivery_fee estático é exibido apenas como fallback quando a cotação falhar

Cenário: Guest recebe cotação Uber ao digitar endereço manualmente
  Dado que a loja tem Uber Direct ativo e configurado
  E o cliente não está autenticado (guest checkout)
  Quando o cliente preenche o endereço manualmente no formulário de checkout
  Então a linha "Taxa de Entrega" exibe o valor cotado pela Uber em ≤ 3 segundos
  E o total é atualizado incluindo a taxa

Cenário: Pedido de balcão ignora Uber Direct
  Dado que a loja tem Uber Direct ativo
  E o Manager está criando um pedido de balcão
  Quando o pedido é criado com delivery_address "Balcão / Retirada"
  Então nenhuma cotação Uber é solicitada durante a criação
  E o modal desse pedido não exibe botão de despacho Uber
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 — Cotação dinâmica no checkout | Must | Proposta central para o cliente; sem isso a feature não entrega valor visível |
| RF-02 — Despacho pelo Manager | Must | Fecha o ciclo logístico; sem isso o restaurante ainda despacha fora da plataforma |
| RF-06 — Configuração de credenciais por loja | Must | Pré-requisito para RF-01 e RF-02 |
| RF-08 — Exclusão de pedidos de balcão | Must | Evita bug crítico: despachar entrega para "Balcão / Retirada" é inválido |
| RF-09 — Fallback em caso de falha Uber | Must | Falha na Uber não pode derrubar o checkout de lojas com Uber ativo |
| RF-03 — Status Uber no painel Manager | Must | Manager precisa saber o estado da corrida sem abrir outro sistema |
| RNF Segurança HMAC webhook | Must | Lição aprendida de L-04; webhook sem validação é risco de injeção de status |
| RNF Credenciais via env var | Must | Padrão de segurança do projeto; não negociável |
| RF-04 — Sincronização Order ↔ status Uber | Should | Automatiza transição para DELIVERING; pode ser feito manualmente como fallback |
| RF-05 — Cancelamento de entrega | Should | Operacionalmente útil, mas não bloqueia o fluxo principal |
| RF-07 — Renovação de cotação expirada | Should | Melhora UX mas pode ser mitigado com mensagem clara de "cotação expirada, refaça" |

## 9. Esclarecimentos

### Sessão 2026-05-30

- **Q:** Quando Uber Direct está ativo na loja, o `store.delivery_fee` estático é completamente ignorado ou coexiste com outro modo de entrega?
  **R:** Substituição total — Uber Direct ativo substitui completamente o `store.delivery_fee` na exibição ao cliente. O valor estático só é usado como fallback quando a API Uber retornar erro.

- **Q:** Com Uber Direct ativo, o `free_delivery_threshold` continua valendo (restaurante absorve custo Uber ao atingir o threshold)?
  **R:** Não — com Uber Direct ativo a isenção de frete não existe. O cliente sempre paga exatamente o valor cotado pela Uber.

- **Q:** A cotação Uber funciona para guests (via endereço digitado manualmente) ou apenas para autenticados com endereço cadastrado?
  **R:** Para todos — guests também recebem cotação Uber usando o endereço digitado manualmente no formulário de checkout.

## 10. Lacunas

Nenhuma lacuna pendente — todas as dúvidas foram resolvidas na sessão de esclarecimentos de 2026-05-30.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-30 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-05-30 | 3 dúvidas resolvidas por `/reversa-clarify` (taxa estática, isenção, guest) | reversa |
