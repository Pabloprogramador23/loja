# Regression Watch: 020-bugfix-pedidos-hoje

> Feature: `020-bugfix-pedidos-hoje`
> Gerado em: `2026-06-04`

## Watch Items

| ID | Origem | Regra esperada após mudança | Tipo | Sinal de violação |
|----|--------|-----------------------------|------|-------------------|
| W001 | `core/views.py` — `dashboard()` linha 398 | `today` é calculado com `timezone.localdate()`, nunca com `timezone.now().date()` | presença | Se extração futura descrever `dashboard()` calculando `today` via `timezone.now().date()`, o bugfix foi revertido |

## Histórico de re-extrações

<!-- Preenchido pelo agente reverso quando /reversa for executado novamente -->

## Arquivadas

<!-- Watch items removidos ou superados ficam aqui -->
