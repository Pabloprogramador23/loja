# Regression Watch: 018-mp-ux-checkout

> Feature: `018-mp-ux-checkout`
> Gerado em: `2026-06-04`
> Referência: `_reversa_forward/018-mp-ux-checkout/legacy-impact.md`

---

## Watch Items

| ID | Origem | Regra esperada após mudança | Tipo | Sinal de violação |
|----|--------|-----------------------------|------|-------------------|
| W001 | `core/views.py` — `checkout()` bloco final | Script de resposta usa `window.location.href=init_point` (same-tab redirect para o MP) | presença | Se extração futura descrever `checkout()` abrindo MP em nova aba via `window.open`, abordagem foi revertida — MP Checkout Pro não renderiza via `window.open` |
| W002 | `core/views.py` — `payment_failure_view` | View busca `Order` por `mp_preference_id` antes de renderizar o template | presença | Se extração futura descrever `payment_failure_view` como view que não carrega `Order`, regra foi revertida |
| W003 | `core/views.py` — `payment_pending_view` | Idem ao W002 para `payment_pending_view` | presença | Idem |
| W004 | `core/urls.py` | Rotas `/payment/waiting/` e `/payment/waiting/status/` existem | presença | Se extração futura não listar essas rotas, foram removidas |
| W005 | `core/views.py` — `payment_waiting_status_view` | View adiciona header `HX-Trigger: stopPolling` quando `order.status != PENDING` | presença | Se extração futura descrever a view sem esse header, lógica de encerramento de polling foi removida |

---

## Observações (sem peso de regressão)

| Origem | Nota |
|--------|------|
| `roadmap.md#D-03` | `HX-Trigger: stopPolling` pressupõe HTMX 1.8+; se a versão do HTMX mudar, retestar encerramento de polling |
| `roadmap.md#D-04` | Timeout visual de 10 min é arbitrário; pode ser ajustado sem impacto em regras de negócio |

---

## Histórico de validação manual

| Data | Resultado | Observações |
|------|-----------|-------------|
| 2026-06-04 | ✅ VALIDADO | Fluxo completo testado com MP produção + ngrok. Pedido chegou como PREPARANDO no dashboard. W001 reescrito: `window.open` descartado, same-tab confirmado como abordagem correta. |

## Histórico de re-extrações

<!-- Preenchido pelo agente reverso quando /reversa for executado novamente -->

---

## Arquivadas

<!-- Watch items removidos ou superados ficam aqui -->
