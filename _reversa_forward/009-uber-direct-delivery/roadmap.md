# Roadmap: Integração Uber Direct — Cotação Dinâmica e Despacho

> Identificador: `009-uber-direct-delivery`
> Data: `2026-05-30`
> Requirements: `_reversa_forward/009-uber-direct-delivery/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A feature é implementada em três camadas independentes, cada uma entregando valor por si só:

**Camada 1 — Configuração por loja:** novo modelo `UberDirectConfig` (tenant-aware, herda `TenantAwareModel`) armazena `uber_store_id` e credenciais OAuth2 por restaurante. Segue o padrão já estabelecido pelo campo `Store.mercadopago_access_token` (ADR-003). O formulário de Configurações da loja recebe novos campos.

**Camada 2 — Cotação em tempo real no checkout:** um novo endpoint FastAPI assíncrono recebe endereço formatado (montado a partir do `Address` cadastrado ou do formulário de checkout para guests), chama a API Uber Direct e retorna fee + quote_id. O HTMX do drawer do carrinho dispara esse endpoint ao selecionar/confirmar endereço. O `quote_id` é guardado na sessão Django com chave `uber_quote_{tenant_id}`. No `views.checkout()`, se a loja tem Uber Direct ativo, o `quote_id` da sessão substitui o cálculo de `effective_delivery_fee` da feature 007.

**Camada 3 — Despacho e rastreamento pelo Manager:** nova view Django (staff-only, POST) chama `UberDirectClient.create_delivery()` usando o `quote_id` salvo no Order. Um novo modelo `UberDirectDelivery` persiste o ciclo de vida da corrida Uber. Um endpoint FastAPI para webhook Uber valida assinatura HMAC-SHA256, responde 200 imediatamente e despacha task Celery para atualizar `UberDirectDelivery.status` e `Order.status`.

O cliente OAuth2 Uber (`core/uber_direct.py`) usa `httpx` assíncrono (nova dependência) e cacheia o token no Redis com chave `uber_direct_token:{store_id}`, seguindo o padrão de cache já existente no projeto para o broker Celery.

## 2. Princípios aplicados

> `principles.md` não encontrado — nenhum princípio registrado formalmente no projeto. Seção mantida por completude.

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| Multi-tenancy via ContextVar (ADR-002) | `UberDirectConfig` herda `TenantAwareModel`; cliente Uber resolve credenciais pelo tenant do ContextVar | respeita |
| Credenciais externas por tenant (ADR-003) | Segue o padrão do `mercadopago_access_token` — credenciais por loja, fallback global via env var | respeita |
| Processamento assíncrono via Celery (ADR-006) | Webhook Uber processado por task Celery com retentativas, igual ao MercadoPago | respeita |
| Snapshot de preço no Order (RN-D03) | `Order.delivery_fee` continua sendo snapshot — agora populado com o valor cotado pela Uber | respeita |
| Não-bloqueio do checkout por falha externa (RN-D09) | Cotação Uber com erro não impede o checkout; fallback para taxa estática | respeita |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|---------------|--------------------------|-------------|
| D-01 | Endpoint de cotação em FastAPI (assíncrono), chamado via HTMX do drawer | Chamada externa à API Uber é I/O-bound; FastAPI async evita bloquear o thread pool Django. Padrão já estabelecido para endpoints de alta performance no projeto (`_reversa_sdd/architecture.md#ADR-001`) | Django view síncrona (bloquearia worker); Celery task (latência adicional, UX pior) | 🟢 |
| D-02 | `quote_id` armazenado na sessão Django com chave `uber_quote_{tenant_id}` | Segue exatamente o padrão do carrinho (`cart_{tenant_id}`); isolamento multi-tenant garantido sem nova tabela | Campo temporário em `Order` (Order ainda não existe no momento da cotação); localStorage (sem acesso server-side) | 🟢 |
| D-03 | Credenciais Uber (`client_id`, `client_secret`, `webhook_signing_key`) armazenadas no modelo `UberDirectConfig` por tenant | Segue `Store.mercadopago_access_token` (ADR-003); permite que cada restaurante use sua própria conta Uber | Apenas env vars globais (não escala para SaaS multi-tenant); secrets manager externo (fora do escopo) | 🟢 |
| D-04 | Token OAuth2 cacheado no Redis com chave `uber_direct_token:{store_id}` e TTL = `expires_in - 60s` | Redis já é dependência do projeto (broker Celery); caching evita latência de autenticação a cada cotação | Cache em memória do processo (perde no restart; não funciona com múltiplos workers); campo no banco (I/O desnecessário) | 🟢 |
| D-05 | Webhook Uber no FastAPI: resposta 200 imediata + task Celery para processamento | Mesmo padrão do webhook MercadoPago (`_reversa_sdd/code-analysis.md#2.6`); Uber exige resposta rápida | Processar síncronamente no request (risco de timeout Uber); Django view (não é async-first) | 🟢 |
| D-06 | Despacho de entrega via Django view (POST, `@staff_required`) | Ação iniciada pelo Manager no dashboard Django; usa sessão/CSRF naturalmente; segue padrão `manager_create_order` | FastAPI endpoint (exigiria auth extra fora do padrão atual do projeto) | 🟢 |
| D-07 | `UberDirectDelivery` como modelo separado (não campos no `Order`) | Ciclo de vida independente com 9 status próprios; histórico de webhooks em `UberDirectDeliveryEvent`; evita poluir `Order` com ~8 campos | Campos diretos em `Order` (acoplamento alto; impacta queries de pedidos sem Uber) | 🟡 |
| D-08 | `httpx` como cliente HTTP assíncrono | Suporte nativo a async/await; integração natural com FastAPI; sem dependência do loop de eventos Django | `aiohttp` (API menos ergonômica); `requests` (síncrono, bloqueante) | 🟡 |

## 4. Premissas

Nenhuma dúvida aceita como premissa — todas as 3 `[DÚVIDA]` foram resolvidas no `/reversa-clarify` em 2026-05-30.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| API FastAPI (`core/api.py`) | `_reversa_sdd/code-analysis.md#2.6` | contrato-novo | Dois novos endpoints: `POST /api/uber-direct/quote` e `POST /api/webhooks/uber-direct` |
| Django views (`core/views.py`) | `_reversa_sdd/code-analysis.md#2.7` | regra-alterada + componente-novo | `checkout()` passa a consumir `quote_id` da sessão; novas views `request_uber_delivery()` e `cancel_uber_delivery()` |
| Checkout — cálculo de taxa (`core/views.py:checkout`) | `_reversa_sdd/code-analysis.md#2.3` | regra-alterada | `effective_delivery_fee` (feature 007) substituído por `uber_quote_fee` quando Uber Direct ativo; fallback para lógica feature 007 em caso de erro |
| Celery tasks (`core/tasks.py`) | `_reversa_sdd/code-analysis.md#Celery` | componente-novo | Nova task `process_uber_webhook(delivery_id, status, payload)` com `max_retries=3` |
| Modelos de dados (`core/models.py`) | `_reversa_sdd/data-dictionary.md` | componente-novo | Dois novos modelos: `UberDirectConfig` e `UberDirectDelivery` |
| Settings (`store_saas/settings.py`) | `_reversa_sdd/code-analysis.md#1` | regra-alterada | Quatro novas variáveis de ambiente: `UBER_CLIENT_ID`, `UBER_CLIENT_SECRET`, `UBER_CUSTOMER_ID`, `UBER_SANDBOX` |
| Formulário de configurações (`core/forms.py`) | `_reversa_sdd/code-analysis.md#Formulários` | regra-alterada | `StoreSettingsForm` recebe campos de configuração Uber Direct |
| Cart drawer (`templates/core/partials/cart_drawer.html`) | `_reversa_sdd/code-analysis.md#2.2` | regra-alterada | Trigger HTMX para cotação Uber ao selecionar endereço |
| Dashboard Manager — modal de pedido | `_reversa_sdd/code-analysis.md#2.7` | regra-alterada | Botão "Despachar via Uber" e exibição de status/tracking_url |
| Integrações externas | `_reversa_sdd/architecture.md#Integrações Externas` | componente-novo | Uber Direct API adicionada como segunda integração externa |

## 6. Delta no modelo de dados

Dois novos modelos Django. Nenhum campo existente é removido ou renomeado.

- `UberDirectConfig`: configuração Uber por tenant (1:1 com Store, opcional)
- `UberDirectDelivery`: entidade de entrega Uber vinculada a um Order (0..1 : 1)
- `Order`: recebe campo `uber_quote_id` (nullable, CharField) para rastreabilidade da cotação usada no checkout
- Detalhe completo em: `_reversa_forward/009-uber-direct-delivery/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| Uber Direct — cotação de frete | HTTP REST (cliente) | `_reversa_forward/009-uber-direct-delivery/interfaces/uber-quote.md` |
| Uber Direct — criação e cancelamento de entrega | HTTP REST (cliente) | `_reversa_forward/009-uber-direct-delivery/interfaces/uber-delivery.md` |
| Uber Direct — webhook de status | HTTP REST (servidor) | `_reversa_forward/009-uber-direct-delivery/interfaces/uber-webhook.md` |

## 8. Plano de migração

1. Adicionar `httpx` ao `requirements.txt`
2. Criar `core/uber_direct.py` com `UberDirectClient` (OAuth2 + cache Redis + métodos da API)
3. Adicionar modelos `UberDirectConfig` e `UberDirectDelivery` em `core/models.py`; adicionar `uber_quote_id` ao `Order`
4. Gerar migration `0011_*` cobrindo os três deltas
5. Adicionar task `process_uber_webhook` em `core/tasks.py`
6. Adicionar endpoints FastAPI (`/uber-direct/quote` e `/webhooks/uber-direct`) em `core/api.py`
7. Adicionar views Django (`request_uber_delivery`, `cancel_uber_delivery`) em `core/views.py`; atualizar `checkout()`
8. Atualizar `core/urls.py` com as novas rotas
9. Atualizar `core/forms.py` (`StoreSettingsForm` com campos Uber)
10. Atualizar templates: `cart_drawer.html`, `settings.html`, modal de pedidos, novo partial `uber_delivery_status.html`
11. Adicionar variáveis de ambiente ao `.env.example` (ou documentação equivalente)

Nenhuma migração de dados existentes é necessária — todos os novos campos são nullable ou têm default.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| `httpx` não está em `requirements.txt` — build pode quebrar | Alto | Alta | Adicionar `httpx` como primeira ação da implementação |
| Race condition no refresh do token OAuth2 com múltiplos workers Celery | Médio | Baixa | Usar `SET NX` (Redis `setnx`) para garantir que apenas um worker renova o token por vez |
| Quote TTL expirado entre cotação e confirmação do checkout (>5 min) | Médio | Média | RF-07: re-cotar automaticamente no `checkout()` se `quote_id` expirado; exibir novo valor ao cliente antes de confirmar |
| CEP opcional em `Address` pode causar imprecisão na cotação Uber | Baixo | Média | Montar `formatted_address` com todos os campos disponíveis; se CEP presente, incluir; sem CEP ainda funciona com rua + número + bairro + cidade + UF |
| Uber Direct sem cobertura para o endereço destino | Médio | Média | RN-D09: fallback para taxa estática + mensagem "entrega Uber não disponível para este endereço" |
| Cancelamento após coleta gera taxa de retorno (RN logística reversa) | Médio | Baixa | RF-05 limita cancelamento a status `PENDING`/`SCHEDULED`; UI deve alertar sobre possíveis taxas |
| Credenciais Uber armazenadas em banco (sem criptografia) | Alto | Baixa | Mesma postura atual do `mercadopago_access_token`; aceitável para MVP; criptografia de campos sensíveis como melhoria futura |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `checkout()` com Uber Direct ativo salva `Order.delivery_fee` com valor cotado pela Uber
- [ ] `UberDirectDelivery` criado ao despachar; `tracking_url` visível no modal
- [ ] Webhook Uber com assinatura válida atualiza `UberDirectDelivery.status`; inválido retorna 401
- [ ] Fallback para taxa estática quando API Uber retorna erro no checkout
- [ ] Testes cobrindo: cotação OK, cotação com erro (fallback), despacho, webhook válido, webhook inválido, pedido de balcão sem cotação
- [ ] `regression-watch.md` gerado

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-30 | Versão inicial gerada por `/reversa-plan` | reversa |
