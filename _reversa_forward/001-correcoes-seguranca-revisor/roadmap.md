# Roadmap: Correções de Segurança (Revisor)

> Identificador: `001-correcoes-seguranca-revisor`
> Data: `2026-05-26`
> Requirements: `_reversa_forward/001-correcoes-seguranca-revisor/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A feature é executada como **série de patches cirúrgicos** em 7 arquivos existentes, mais a criação de 2 novos arquivos (`.env.example` e a migration Django). Nenhum componente novo é introduzido — todos os pontos de entrada, dependências e infraestrutura já existem. A ordem de aplicação é determinada por dependências: as variáveis de ambiente e a migration de modelo vêm primeiro (pré-requisitos para o webhook redesenhado), seguidos de middleware e views, depois a reescrita do webhook, e por último Celery e ajustes de async.

O ponto mais complexo é o **redesenho do webhook** (`core/api.py:186-215`): o endpoint atual usa token global, não valida HMAC e contém backdoor. A versão corrigida requer que a Order já tenha `mp_payment_id` (adicionado em `core/payment.py` na criação do PIX), que o header `x-signature` seja verificado com HMAC-SHA256 antes de qualquer processamento, e que o token MP seja lido de `order.store.mercadopago_access_token`. Todas essas dependências são paralelas e podem ser desenvolvidas na mesma sessão, desde que a migration rode antes dos testes.

O segundo ponto mais sensível é o **middleware de tenant** (`core/middleware.py`): a lógica atual está invertida — header tem prioridade, host é fallback de localhost. A inversão para host-first é necessária para produção com subdomínios próprios e não quebra o fluxo de desenvolvimento (localhost continua usando primeiro store ativo como fallback).

## 2. Princípios aplicados

Nenhum arquivo `principles.md` encontrado em `.reversa/`. A feature segue os princípios implícitos do framework Reversa e boas práticas de segurança Django/FastAPI.

| Princípio implícito | Como a feature se relaciona | Status |
|---------------------|------------------------------|--------|
| Non-destructive sobre dados | Migration usa `null=True` — sem dados perdidos | respeita |
| Delta mínimo — não redesenhar além do necessário | Nenhum componente novo; patches cirúrgicos | respeita |
| Segredos nunca em código | Toda feature move segredos para env vars | respeita |
| Isolamento de tenant garantido pelo ORM | Webhook corrigido usa `order.store.token` — sem bypass | respeita |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|---------------|--------------------------|-------------|
| DT-01 | Usar `python-decouple` (`config()`) para env vars em `settings.py` | Já está instalado (`dependencies.md`); padrão do projeto (DATABASE_URL e REDIS_URL já usam) | `os.environ.get()` direto (menos ergonômico, sem .env file suporte nativo) | 🟢 |
| DT-02 | `mp_payment_id` como `CharField(null=True, unique=True, db_index=True)` | Orders existentes não têm o campo; nullable sem valor default preserva dados; unique previne processar webhook duas vezes para o mesmo pagamento | IntegerField (MP IDs são strings); não-nullable (quebraria Orders existentes) | 🟢 |
| DT-03 | HMAC validado via `hmac.compare_digest` da stdlib Python | Resistente a timing attack; sem dependência adicional; exatamente como MP documenta | Verificação de string simples (`==`) — vulnerável a timing attack | 🟢 |
| DT-04 | Webhook busca `Order.objects.get(mp_payment_id=payment_id)` antes de usar token da loja | Quebra o chicken-and-egg: sem mp_payment_id não sabemos qual store usar; com ele o token correto é `order.store.mercadopago_access_token` | Token global em settings (viola isolamento multi-tenant); header X-Tenant-Subdomain no webhook (MP não envia) | 🟢 |
| DT-05 | Backdoor substituído por `REVERSA_TESTING=true` env flag | Mantém capacidade de teste sem expor no código de produção; flag desativada por default | Remover sem substituto (bloqueia testes manuais rápidos); manter backdoor (inaceitável em produção) | 🟢 |
| DT-06 | `TenantMiddleware` inverte prioridade: host primeiro, depois header | Produção usa subdomínios próprios (confirmado pelo usuário); header como fallback funciona para dev/curl sem conflitar | Manter header como prioridade (manteria L-01 em produção) | 🟢 |
| DT-07 | `customer_email` como campo no formulário de checkout (POST) e na Order (para convidados) | MP exige `payer.email` válido; convidados não têm `user.email`; campo obrigatório em vez de placeholder | Auto-gerar email falso (cria pedidos não notificáveis no MP); exigir login (quebra guest checkout) | 🟢 |
| DT-08 | `process_new_order` Celery: guard `if order.status != PREPARING: return` antes de qualquer lógica | Idempotência garantida sem locks; resolve race condition de L-07 sem complexidade de distributed locks | `SELECT FOR UPDATE` (over-engineering para este caso); ignorar e redesenhar o status handling | 🟢 |
| DT-09 | `render_to_string` em FastAPI via `await sync_to_async(render_to_string)(template, context)` | Handlers FastAPI são async; `render_to_string` Django é síncrono; `asgiref.sync_to_async` já importado em `api.py` | Mover templates para Jinja2 puro (over-engineering); manter bloqueante (funciona mas degrada sob carga) | 🟢 |
| DT-10 | `order_details_modal` retorna `HttpResponse(status=403)` para não-staff | `HttpResponse` já importado em `views.py:246`; consistente com demais views que usam redirect/HttpResponse | Levantar `PermissionDenied` (produziria 403 mas via exception handler, menos explícito) | 🟢 |

## 4. Premissas

Nenhuma premissa de `[DÚVIDA]` — todas as 23 perguntas foram respondidas. Sem `[DÚVIDA]` no `requirements.md`.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `TenantMiddleware` | `core/middleware.py` | regra-alterada | Inverter prioridade: host-first, header como fallback dev; 404 para subdomain inválido |
| `order_details_modal` | `core/views.py:249-256` | regra-alterada | Substituir `pass` por `return HttpResponse(status=403)` |
| `checkout` view | `core/views.py:121-176` | regra-alterada | Adicionar leitura de `customer_email` para convidados; validar obrigatoriedade |
| `create_pix_payment` | `core/payment.py` | regra-alterada | Usar `customer_email` em `payer.email`; salvar `payment_id` de volta na Order |
| `mercadopago_webhook` | `core/api.py:186-215` | regra-alterada | Adicionar HMAC, remover backdoor, redesenhar lookup por `mp_payment_id` |
| `check_order_status` | `core/api.py:171-182` | regra-alterada | Adicionar `Depends(get_tenant_dependency)` para scoping por tenant |
| `process_new_order` | `core/tasks.py` | regra-alterada | Remover status set e sleep; adicionar guard + retry |
| `settings.py` | `store_saas/settings.py` | regra-alterada | Mover `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` para env vars |
| `Order` model | `core/models.py` | regra-alterada | Adicionar campo `mp_payment_id` |
| `.env.example` | (novo) | componente-novo | Documento de referência para configuração do ambiente |
| Migration `mp_payment_id` | (nova) | componente-novo | Migration Django para o novo campo |

## 6. Delta no modelo de dados

- Resumo: Um campo novo na tabela `core_order`: `mp_payment_id` (varchar 64, nullable, unique, indexed). Orders de balcão e orders ainda não pagas terão `NULL` nesse campo.
- Detalhe completo em: `_reversa_forward/001-correcoes-seguranca-revisor/data-delta.md`

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| Webhook MercadoPago | HTTP POST | `_reversa_forward/001-correcoes-seguranca-revisor/interfaces/webhook-mercadopago.md` |

## 8. Plano de migração

1. **Configurar `.env`** — criar o arquivo com base em `.env.example`; gerar nova `SECRET_KEY` com `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
2. **Aplicar migration** — `python manage.py makemigrations core --name add_mp_payment_id_to_order` e `python manage.py migrate`
3. **Reiniciar o servidor** — todas as env vars precisam estar carregadas antes do processo subir
4. **Configurar `MERCADOPAGO_WEBHOOK_SECRET`** — obter o valor no painel MP → Integrações → Webhooks → segredo de assinatura; adicionar ao `.env`
5. **Testar com REVERSA_TESTING=true** — validar o fluxo de aprovação sem precisar de webhook real antes do deploy

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Orders existentes com PIX aprovado mas sem `mp_payment_id` | Médio — webhook de re-notificação não encontraria a Order | Baixo — ambiente ainda não está em produção | Migration com `null=True`; Orders existentes não serão afetadas (já aprovadas) |
| `MERCADOPAGO_WEBHOOK_SECRET` não configurado em dev | Baixo — HMAC falharia para todos os webhooks em dev | Alto — dev não tem esse segredo configurado | Webhook verifica: se `MERCADOPAGO_WEBHOOK_SECRET` estiver ausente e `REVERSA_TESTING=true`, aceita sem HMAC (apenas em ambiente de teste) |
| `customer_email` quebra forms de checkout existentes | Médio — campo novo obrigatório; templates podem não ter o input | Médio — depende da implementação dos templates HTML | Verificar templates de checkout antes de tornar o campo obrigatório na view; adicionar campo gradualmente |
| Inversão de prioridade no middleware quebra dev local | Baixo — localhost continua com fallback para primeiro store ativo | Baixo — lógica de fallback preservada | Testar localmente antes de deploy |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `grep -r "SECRET_KEY\s*=\s*'" store_saas/settings.py` retorna zero resultados
- [ ] `grep -r "test.approved" core/` retorna zero resultados
- [ ] Migration aplicada sem erro; campo `mp_payment_id` presente em `\d core_order`
- [ ] Request para modal de pedido por usuário não-staff retorna HTTP 403
- [ ] Request para webhook com `x-signature` inválido retorna HTTP 401
- [ ] Checkout de convidado sem `customer_email` retorna erro de validação
- [ ] `regression-watch.md` gerado

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-26 | Versão inicial gerada por `/reversa-plan` | reversa |
