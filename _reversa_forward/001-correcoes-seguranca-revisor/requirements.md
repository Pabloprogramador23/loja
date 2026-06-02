# Requirements: Correções de Segurança (Revisor)

> Identificador: `001-correcoes-seguranca-revisor`
> Data: `2026-05-26`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Implementação das 10 decisões arquiteturais (D-01 a D-10) e 2 correções adicionais (G-01, L-03) identificadas pelo Revisor durante a análise reversa do sistema `loja`. A feature elimina vulnerabilidades críticas que impediriam um deploy seguro em produção: segredos hardcoded, tenant isolation quebrado, webhook sem autenticação, backdoor de teste exposto, e bypass de autorização no dashboard. Afeta desenvolvedores que fazem o deploy e clientes convidados que pagam via PIX.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/architecture.md#dividas-tecnicas` | L-01 a L-10 e G-01 documentados como dívidas, todos marcados ✅ RESOLVIDO com decisão | 🟢 |
| `_reversa_sdd/domain.md#regras-de-negocio` | RN-01 a RN-18 — regras de negócio confirmadas no código | 🟢 |
| `_reversa_sdd/questions.md` | 23 perguntas respondidas pelo usuário, incluindo todas as 10 decisões arquiteturais | 🟢 |
| `_reversa_sdd/confidence-report.md#decisoes-arquiteturais` | D-01 a D-10 documentados com impacto | 🟢 |
| `_reversa_sdd/core/multi-tenancy/design.md#decisao-versao-corrigida` | Fluxo corrigido: host → header → 404 | 🟢 |
| `_reversa_sdd/core/pagamento/design.md#webhook-corrigido` | Webhook: HMAC + mp_payment_id + token por loja | 🟢 |
| `_reversa_sdd/core/api-fastapi/requirements.md#rf-06-rf-07` | HMAC obrigatório; backdoor removido via env flag | 🟢 |
| `_reversa_sdd/core/dashboard-manager/requirements.md#g-01` | `order_details_modal` — `pass` é no-op; decisão: 403 | 🟢 |
| `_reversa_sdd/store_saas/requirements.md#rf-02` | Todas as env vars documentadas, incluindo MERCADOPAGO_WEBHOOK_SECRET | 🟢 |
| `_reversa_sdd/core/pedidos/design.md#maquina-de-estados` | Máquina de estados expandida com estorno automático | 🟢 |
| `_reversa_sdd/core/checkout/requirements.md#rf-02b` | customer_email obrigatório para convidados | 🟢 |
| `_reversa_sdd/core/celery-tasks/requirements.md` | Guard + retry; remoção do time.sleep(2) | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Desenvolvedor / DevOps | Fazer deploy seguro em produção sem segredos hardcoded | Configurar `.env` com todas as variáveis e confirmar que SECRET_KEY, DEBUG e tokens MP não estão no código |
| Gestor da Loja (staff) | Acessar detalhes de pedidos no dashboard | Abrir modal de pedido — acesso liberado somente para staff |
| Cliente Convidado | Concluir compra via PIX sem criar conta | Informar e-mail no checkout para receber QR Code vinculado |
| Sistema (Webhook MP) | Notificar pagamento aprovado ou expirado | Requisição recebida com assinatura HMAC válida; Order localizada por mp_payment_id |
| Atacante (adversarial) | Explorar vulnerabilidades existentes | Tentativas bloqueadas: HMAC inválido → 401; subdomain inválido → 404; non-staff modal → 403 |

## 4. Regras de negócio novas ou alteradas

1. **RN-SEC-01:** `SECRET_KEY` deve ser lida exclusivamente de `os.environ.get('SECRET_KEY')`. Nunca hardcoded. 🟢
   - Tipo: alterada
   - Origem: `_reversa_sdd/questions.md#p-01` (D-07)

2. **RN-SEC-02:** `DEBUG` deve ter default `False` em produção: `os.environ.get('DEBUG', 'False') == 'True'`. 🟢
   - Tipo: alterada
   - Origem: `_reversa_sdd/questions.md#p-02`

3. **RN-SEC-03:** Resolução de tenant usa `request.get_host()` como prioridade 1 (produção com subdomínios próprios). Header `X-Tenant-Subdomain` é fallback apenas para dev/API. Subdomain inválido → HTTP 404. 🟢
   - Tipo: alterada (substituição da lógica atual que depende só do header)
   - Origem: `_reversa_sdd/questions.md#p-09` (D-01), `_reversa_sdd/core/multi-tenancy/design.md`

4. **RN-SEC-04:** O campo `mp_payment_id` deve ser armazenado na `Order` no momento da criação do pagamento PIX. Usado pelo webhook para localizar o pedido correto e usar o token MP da loja correta. 🟢
   - Tipo: nova
   - Origem: `_reversa_sdd/questions.md#p-08` (D-02)

5. **RN-SEC-05:** Webhook MP (`POST /api/webhooks/mercadopago`) deve validar assinatura HMAC-SHA256 via header `x-signature` e `MERCADOPAGO_WEBHOOK_SECRET` usando `hmac.compare_digest`. Requisição sem assinatura válida → HTTP 401. 🟢
   - Tipo: nova (webhook atual não valida)
   - Origem: `_reversa_sdd/questions.md#p-05` (D-06)

6. **RN-SEC-06:** O backdoor `if payment_data.get('status') == 'test.approved'` deve ser removido. Em ambiente de testes, usar a flag de ambiente `REVERSA_TESTING=true` que ativa fixture de webhook em vez do backdoor. 🟢
   - Tipo: alterada (remoção + substituição)
   - Origem: `_reversa_sdd/questions.md#p-03` (D-08)

7. **RN-SEC-07:** `order_details_modal` deve retornar HTTP 403 para usuários não-staff. O `pass` atual (no-op) é substituído por `return HttpResponse(status=403)`. 🟢
   - Tipo: alterada (correção de bug de autorização)
   - Origem: `_reversa_sdd/questions.md#p-06` (G-01)

8. **RN-SEC-08:** Campo `customer_email` é obrigatório no checkout de convidados. É usado como `payer.email` na criação do pagamento PIX no MP. 🟢
   - Tipo: nova
   - Origem: `_reversa_sdd/questions.md#p-04` (D-05)

9. **RN-SEC-09:** `check_order_status` (FastAPI) deve ser escopado ao tenant via `Depends(get_tenant_dependency)`. Rastreamento público de pedido é mantido — sem autenticação de usuário, mas scoped à loja do subdomínio. 🟢
   - Tipo: alterada
   - Origem: `_reversa_sdd/questions.md#p-07` (L-03, D-01)

10. **RN-SEC-10:** Webhook com `status=cancelled` ou `status=expired` do MP deve acionar `cancel_order_on_pix_expiry`, que move a Order de PENDING para CANCELED. 🟢
    - Tipo: nova
    - Origem: `_reversa_sdd/questions.md#p-13` (D-04)

11. **RN-SEC-11:** Ao cancelar uma Order pelo dashboard, o sistema deve chamar a API de estorno/cancelamento do MP automaticamente: PENDING → `sdk.payment().cancel(mp_payment_id)`; PREPARING/DELIVERING → `sdk.payment().refund(mp_payment_id)`. Pedidos balcão (sem `mp_payment_id`) → sem chamada MP. 🟢
    - Tipo: nova
    - Origem: `_reversa_sdd/questions.md#p-14` (D-03)

12. **RN-SEC-12:** Task Celery `process_new_order` não deve setar status para PREPARING (isso já ocorre antes do dispatch). Guard obrigatório: `if order.status != PREPARING: return`. Retry: `max_retries=3`, backoff de 60s. Remover `time.sleep(2)`. 🟢
    - Tipo: alterada
    - Origem: `_reversa_sdd/questions.md#p-10` (D-09)

13. **RN-SEC-13:** `render_to_string` em handlers FastAPI async deve usar `await sync_to_async(render_to_string)(template, context)` para evitar bloqueio do event loop. 🟢
    - Tipo: alterada
    - Origem: `_reversa_sdd/questions.md#p-18` (D-10)

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Mover `SECRET_KEY`, `DEBUG` e `ALLOWED_HOSTS` para variáveis de ambiente em `settings.py` | Must | `grep -r "SECRET_KEY\s*=" store_saas/settings.py` não retorna valor literal; app sobe com `.env` configurado | 🟢 |
| RF-02 | Mover `MERCADOPAGO_ACCESS_TOKEN` e `MERCADOPAGO_WEBHOOK_SECRET` para variáveis de ambiente | Must | Token MP lido via `os.environ.get('MERCADOPAGO_ACCESS_TOKEN')`; ausência da var gera erro explícito na inicialização | 🟢 |
| RF-03 | Criar `.env.example` com todas as variáveis necessárias | Must | Arquivo presente na raiz do projeto com: `SECRET_KEY`, `DEBUG`, `DATABASE_URL`, `REDIS_URL`, `ALLOWED_HOSTS`, `MERCADOPAGO_ACCESS_TOKEN`, `MERCADOPAGO_WEBHOOK_SECRET` | 🟢 |
| RF-04 | Corrigir `TenantMiddleware`: resolução por host como prioridade 1; header como fallback; 404 para subdomain inválido | Must | Request para `loja-a.meusaas.com` retorna dados da loja A; request sem host válido retorna 404 | 🟢 |
| RF-05 | Adicionar migration para `Order.mp_payment_id` (CharField, max_length=64, null=True, blank=True, unique=True, db_index=True) | Must | Migration aplicada sem erro; campo presente no schema | 🟢 |
| RF-06 | Armazenar `mp_payment_id` na Order ao criar pagamento PIX | Must | Após criação PIX no MP, `order.mp_payment_id = payment_response['id']`; campo salvo | 🟢 |
| RF-07 | Adicionar validação HMAC-SHA256 no webhook MP usando `x-signature` + `MERCADOPAGO_WEBHOOK_SECRET` | Must | Request sem header `x-signature` → HTTP 401; assinatura inválida → HTTP 401; assinatura válida → processamento normal | 🟢 |
| RF-08 | Webhook busca Order por `mp_payment_id`; usa token do `order.store.mercadopago_access_token` | Must | Webhook com `mp_payment_id` inexistente → HTTP 404; com id válido → usa token correto da loja | 🟢 |
| RF-09 | Remover backdoor `test.approved`; substituir por flag `REVERSA_TESTING` | Must | `grep -r "test.approved" core/` retorna zero resultados; com `REVERSA_TESTING=true` o sistema aceita webhook de teste via fixture | 🟢 |
| RF-10 | Corrigir `order_details_modal`: substituir `pass` por `return HttpResponse(status=403)` para non-staff | Must | Usuário autenticado não-staff recebe HTTP 403 ao acessar o endpoint; staff acessa normalmente | 🟢 |
| RF-11 | Campo `customer_email` obrigatório no formulário de checkout para convidados | Must | Checkout de convidado sem e-mail retorna erro de validação; e-mail é enviado ao MP como `payer.email` | 🟢 |
| RF-12 | Scopar `check_order_status` ao tenant via `Depends(get_tenant_dependency)` | Should | Request para `/api/orders/{id}/status` com subdomain de loja errada → pedido não encontrado (filtrado pelo tenant) | 🟢 |
| RF-13 | Webhook: `status=cancelled` ou `status=expired` → auto-cancelar Order (PENDING → CANCELED) | Should | Webhook MP com status cancelled chega → Order move para CANCELED; sem interação manual | 🟢 |
| RF-14 | Cancelamento de Order via dashboard → estorno/cancelamento automático no MP | Should | Cancelar Order PENDING via dashboard chama `sdk.payment().cancel(mp_payment_id)`; PREPARING/DELIVERING chama refund; balcão sem mp_payment_id não chama MP | 🟢 |
| RF-15 | Celery: adicionar guard + retry em `process_new_order`; remover `time.sleep(2)` e double-set de status | Should | Task com Order em status diferente de PREPARING retorna early sem processar; task falha → retry automático após 60s (máx 3 tentativas) | 🟢 |
| RF-16 | Substituir `render_to_string` por `await sync_to_async(render_to_string)` nos handlers FastAPI | Could | Handlers FastAPI não bloqueiam o event loop ao renderizar templates; testado com carga concorrente | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Segurança | Nenhum segredo hardcoded no código após a feature | L-10: `SECRET_KEY` literal no settings.py confirmado pelo Scout | 🟢 |
| Segurança | Webhook MP autenticado por HMAC-SHA256 antes de qualquer processamento | L-04: webhook atual não valida assinatura; risco de replay e spoofing | 🟢 |
| Segurança | Tenant isolation por host — não baseado apenas em header manipulável | L-01: fallback-only permitia `tenant=None` em produção com dados sem filtro | 🟢 |
| Segurança | Dashboard: acesso a dados de pedido restrito a staff | G-01: `pass` no-op confirmado em `views.py:249` | 🟢 |
| Integridade | `mp_payment_id` único por Order — evita processamento duplicado de webhooks | D-02: campo indexed + unique previne race condition de webhook | 🟢 |
| Confiabilidade | Task Celery idempotente via guard de status | D-09: duplo PREPARING detectado; race condition documentada | 🟢 |
| Observabilidade | Log explícito quando HMAC falha (com IP do request, sem expor o segredo) | Boa prática para detecção de ataques | 🟡 |
| Compatibilidade | Migration aplicável sem downtime em dados existentes (`mp_payment_id` nullable) | Orders existentes não têm mp_payment_id — nullable permite convivência | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Variáveis de ambiente obrigatórias não configuradas
  Dado que o arquivo .env não existe ou não tem SECRET_KEY
  Quando a aplicação tenta inicializar
  Então a aplicação lança ImproperlyConfigured com mensagem indicando qual variável falta

Cenário: Resolução de tenant por host (produção)
  Dado que a loja "loja-a" tem subdomain "loja-a" e está ativa
  Quando uma request chega com Host: loja-a.meusaas.com
  Então request.tenant é a loja "loja-a" e todos os querysets são filtrados para ela

Cenário: Subdomain inválido retorna 404
  Dado que não existe loja com subdomain "inexistente"
  Quando uma request chega com Host: inexistente.meusaas.com
  Então a resposta é HTTP 404 (não 200 com dados de outro tenant)

Cenário: Webhook MP com HMAC válido é processado
  Dado que MERCADOPAGO_WEBHOOK_SECRET está configurado como "secret-123"
  E existe uma Order com mp_payment_id "pay-001" em status PENDING
  Quando o MP envia POST /api/webhooks/mercadopago com x-signature válido e status=approved
  Então a Order move para PAID e o pagamento é registrado

Cenário: Webhook MP com HMAC inválido é rejeitado
  Dado qualquer configuração de MERCADOPAGO_WEBHOOK_SECRET
  Quando o MP envia POST /api/webhooks/mercadopago com x-signature incorreto ou ausente
  Então a resposta é HTTP 401 e nenhuma Order é modificada

Cenário: Backdoor removido — test.approved rejeitado
  Dado que REVERSA_TESTING não está definido
  Quando webhook recebe status=test.approved
  Então o status é tratado como desconhecido e ignorado (sem aprovação automática)

Cenário: Non-staff tenta acessar modal de pedido
  Dado que o usuário está autenticado mas NÃO tem is_staff=True
  Quando faz GET para /dashboard/orders/{id}/details/
  Então a resposta é HTTP 403

Cenário: Staff acessa modal de pedido
  Dado que o usuário está autenticado E tem is_staff=True
  Quando faz GET para /dashboard/orders/{id}/details/
  Então a resposta é HTTP 200 com os dados do pedido

Cenário: Checkout de convidado sem e-mail falha
  Dado que o usuário não está autenticado (convidado)
  Quando submete o checkout sem preencher o campo customer_email
  Então o formulário retorna erro de validação no campo customer_email

Cenário: PIX expirado auto-cancela pedido
  Dado que existe uma Order em status PENDING com mp_payment_id "pay-001"
  Quando o MP envia webhook com status=expired para mp_payment_id "pay-001"
  Então a Order move para CANCELED automaticamente

Cenário: Cancelamento de Order PENDING com PIX dispara cancelamento no MP
  Dado que existe uma Order em status PENDING com mp_payment_id "pay-001"
  Quando staff cancela o pedido via dashboard
  Então sdk.payment().cancel("pay-001") é chamado
  E a Order move para CANCELED

Cenário: Cancelamento de pedido balcão (sem PIX) não chama MP
  Dado que existe uma Order em status PENDING sem mp_payment_id (pedido balcão)
  Quando staff cancela o pedido via dashboard
  Então nenhuma chamada MP é feita
  E a Order move para CANCELED
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 (env vars settings) | Must | SECRET_KEY hardcoded é bloqueante para qualquer deploy seguro |
| RF-02 (env vars MP tokens) | Must | Token MP hardcoded expõe credenciais financeiras |
| RF-03 (.env.example) | Must | Sem .env.example o deploy é inviável para qualquer desenvolvedor novo |
| RF-04 (tenant por host) | Must | L-01: tenant=None em produção expõe dados de todos os tenants |
| RF-05 (migration mp_payment_id) | Must | Pré-requisito para RF-06, RF-07, RF-08 e RF-13 |
| RF-06 (salvar mp_payment_id) | Must | Sem este campo o webhook não sabe qual loja usar |
| RF-07 (HMAC webhook) | Must | L-04: webhook sem autenticação permite spoofing de pagamentos |
| RF-08 (webhook por mp_payment_id) | Must | L-06: token global causaria falha em ambiente multi-tenant real |
| RF-09 (remover backdoor) | Must | L-02: backdoor em código de produção é risco crítico de segurança |
| RF-10 (403 no modal) | Must | G-01: qualquer usuário autenticado acessa dados de pedidos de qualquer loja |
| RF-11 (customer_email obrigatório) | Must | L-05: sem e-mail o PIX falha silenciosamente com placeholder |
| RF-12 (check-status por tenant) | Should | L-03: IDOR moderado — rastreamento cross-tenant possível mas requer conhecimento do ID |
| RF-13 (PIX expirado → CANCELED) | Should | D-04: sem isso Orders ficam PENDING para sempre após expiração do QR Code |
| RF-14 (estorno automático) | Should | D-03: sem estorno automático o gestor precisa estornar manualmente no painel MP |
| RF-15 (Celery guard + retry) | Should | D-09: race condition documentada; max_retries previne perda silenciosa de pedidos |
| RF-16 (render_to_string async) | Could | D-10: melhoria de qualidade; sem impacto imediato em produção de baixa carga |

## 9. Esclarecimentos

> Nenhuma sessão de dúvidas registrada ainda. Rode `/reversa-clarify` quando houver `[DÚVIDA]` pendente.

## 10. Lacunas

Nenhuma lacuna aberta. Todos os pontos foram resolvidos durante a sessão de revisão (`_reversa_sdd/questions.md` — 23/23 respondidas).

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-26 | Versão inicial gerada por `/reversa-requirements` | reversa |
