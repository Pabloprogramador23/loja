# Legacy Impact: Painel SaaS Admin

> Identificador: `023-painel-saas-admin`
> Data: `2026-06-05`

## Arquivos Afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|----------------|------------|------|------------|---------------|
| `store_saas/urls.py` | ASGI Router / URL Root | regra-alterada | LOW | Adicionado `path('saas/', include('core.saas_urls'))` antes de `core.urls` |
| `core/saas_urls.py` | URL Root | componente-novo | LOW | 4 novas rotas sob `/saas/` — isoladas, sem conflito com rotas existentes |
| `core/saas_views.py` | Views Django | componente-novo | LOW | 4 views + `SuperuserRequiredMixin`; não altera views existentes |
| `core/forms.py` | Forms | regra-nova | LOW | `SaasCreateStoreForm` adicionado ao final do arquivo; sem alteração nas classes existentes |
| `core/tests_saas.py` | Testes | componente-novo | LOW | 14 testes novos; arquivo isolado |
| `templates/core/saas/` | Camada de Apresentação | componente-novo | LOW | 4 templates + 1 partial; não altera templates existentes |

## Diff Conceitual por Componente

### `store_saas/urls.py`
Único ponto de alteração em arquivo existente. O include `/saas/` foi inserido antes de `core.urls` para evitar que rotas genéricas do core interceptem o prefixo. Nenhuma rota existente foi removida ou modificada.

### `core/saas_views.py` (novo)
`SuperuserRequiredMixin` é um padrão novo no projeto — até aqui, proteção de rota era feita com decorators (`@login_required` + `if not is_staff`). O mixin introduz verificação `is_superuser` e a chamada explícita a `set_current_tenant(None)`, que até agora era responsabilidade exclusiva do `TenantMiddleware`. A semântica é preservada: o middleware fará o reset via token no `finally` após o response.

### `core/forms.py`
`SaasCreateStoreForm` é a primeira Form não-ModelForm que cria registros em múltiplas tabelas. Introduz `transaction.atomic()` dentro do método `save()` — padrão já usado em `accounts/views.py:criar_loja_view`. Nenhuma form existente foi alterada.

## Regras Preservadas

Todas as regras 🟢 do `_reversa_sdd/domain.md` não listadas em "Modificadas" permanecem intactas, especialmente:

- **RN-01** (isolamento TenantManager): preservado — mixin zera o ContextVar explicitamente, não contorna o manager
- **RN-02** (resolução de tenant): preservado — toggle `is_active` usa o mesmo campo que o middleware verifica
- **RN-03** (auto-atribuição de tenant): preservado — `SaasCreateStoreForm` atribui `store_id` explicitamente, não conflita
- **RN-07** (snapshot de preço): não tocado
- **RN-08** (pedido de balcão): não tocado

## Regras Modificadas

Nenhuma regra existente foi modificada ou removida. Todas as adições são net-new.
