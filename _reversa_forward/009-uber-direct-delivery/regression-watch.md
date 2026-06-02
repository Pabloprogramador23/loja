# Regression Watch: 009-uber-direct-delivery

> Identificador: `009-uber-direct-delivery`
> Gerado em: `2026-05-30`
> Usado pelo `/reversa` em re-extrações futuras para detectar regressão semântica.

---

## Watch Items

| ID | Origem | Regra esperada após mudança | Tipo de verificação | Sinal de violação |
|----|--------|------------------------------|---------------------|-------------------|
| W001 | `_reversa_sdd/domain.md#RN-D01` + `core/views.py:checkout` | Quando `store.uber_config.is_active == True`, `Order.delivery_fee` reflete o valor cotado pela Uber (não `store.delivery_fee`). Quando a API Uber falha, `Order.delivery_fee` = `store.delivery_fee` (fallback). | presença | Re-extração descreve `checkout()` sem mencionar `uber_config.is_active` ou cotação dinâmica |
| W002 | `_reversa_sdd/data-dictionary.md#Order` | `Order` tem campo `uber_quote_id CharField(max_length=255, blank=True, default='')`. Preenchido no checkout quando Uber Direct ativo e quote válido. | presença | Re-extração não lista `uber_quote_id` em `Order` ou descreve o campo como ausente |
| W003 | `_reversa_sdd/architecture.md#Integrações Externas` | Tabela de integrações externas inclui Uber Direct com tipo HTTP REST bidirecional (cliente para cotação/entrega, servidor para webhook). | presença | Re-extração lista apenas MercadoPago na tabela de integrações externas |

---

## Observações (sem peso de regressão)

Itens inferidos (🟡) que podem mudar sem configurar regressão formal:

- O comportamento exato do fallback (mensagem exibida, taxa usada) pode evoluir sem impactar W001
- A estrutura interna de `UberDirectDeliveryEvent` pode mudar sem impactar os watch items acima
- O número de endpoints FastAPI para Uber Direct pode aumentar (ex: polling de status) — não configura regressão nos itens W001-W003

---

## Histórico de re-extrações

> Preenchido automaticamente pelo `/reversa` em execuções futuras. Nenhuma re-extração registrada ainda.

---

## Arquivadas

> Itens que foram verificados e podem ser removidos do watch ativo. Nenhum arquivado ainda.
