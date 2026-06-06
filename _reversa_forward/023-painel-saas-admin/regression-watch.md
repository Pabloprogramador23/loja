# Regression Watch: Painel SaaS Admin

> Identificador: `023-painel-saas-admin`
> Gerado em: `2026-06-05`
> Feature: Painel SaaS admin em `/saas/` com visão cross-tenant

## Watch Items

| ID | Origem | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------|----------------------------|---------------------|-------------------|
| W001 | `_reversa_sdd/domain.md#RN-01` + `core/utils.py:set_current_tenant` | `SuperuserRequiredMixin` zera o ContextVar via `set_current_tenant(None)` antes de qualquer query em `/saas/*`; `TenantManager` retorna queryset global quando tenant é `None` | presença | Se `TenantManager.get_queryset()` passar a exigir tenant não-nulo, queries em `/saas/` retornarão vazio sem erro — bug silencioso |
| W002 | `_reversa_sdd/domain.md#RN-02` + `core/middleware.py` | `TenantMiddleware` resolve tenant via subdomínio, header ou fallback dev; `is_active=False` impede resolução e retorna 404 | presença | Se o middleware parar de filtrar `is_active=True`, uma loja desativada voltará a ser acessível depois do toggle |
| W003 | `_reversa_sdd/permissions.md#Papéis Identificados` | Acesso a `/saas/*` exige `is_superuser=True`; `is_staff=True` sem `is_superuser` redireciona para `/dashboard/` | presença | Se `SuperuserRequiredMixin.dispatch()` for removido ou contornado, qualquer Manager poderá acessar o painel SaaS |
| W004 | `_reversa_sdd/domain.md#RN-03` + `core/models.py:TenantAwareModel.save` | Criação de `Store` via `SaasCreateStoreForm.save()` atribui `store_id` explicitamente — não depende do ContextVar; `User` é criado com `is_staff=True` atomicamente | presença | Se `Store.objects.create()` passar a requerer ContextVar (via refactor do model), a criação falhará silenciosamente ou atribuirá a loja errada |
| W005 | `_reversa_sdd/architecture.md#Padrões Arquiteturais` | Prefixo `/saas/` registrado em `store_saas/urls.py` **antes** de `include('core.urls')` — sem conflito de rota | presença | Se a ordem dos includes mudar, uma rota genérica em `core.urls` pode interceptar `/saas/` antes do include correto |

## Observações (sem peso de regressão)

- 🟡 `RN-SaaS-05`: métricas calculadas em tempo real via `annotate()`. Performance aceitável até ~500 lojas. Monitorar se o projeto crescer.
- 🟡 Token MP mascarado com `token[-6:]` — dependente do formato atual do token MP (mínimo 6 chars). Se o formato mudar, revisar a lógica de mascaramento em `core/saas_views.py:SaasStoreDetailView`.

## Histórico de re-extrações

| Data | Resultado | Watch items violados | Observações |
|------|-----------|---------------------|-------------|
| — | — | — | Aguardando próxima execução de `/reversa` |

## Arquivadas

<!-- Itens arquivados quando a regra deixar de ser relevante -->
