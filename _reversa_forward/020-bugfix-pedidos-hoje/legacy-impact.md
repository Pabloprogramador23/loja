# Legacy Impact: 020-bugfix-pedidos-hoje

> Data: 2026-06-04
> Feature: `020-bugfix-pedidos-hoje`

## Arquivos afetados

| Arquivo afetado | Componente | Tipo | Severidade | Justificativa |
|-----------------|------------|------|------------|---------------|
| `core/views.py` | `dashboard()` — view do painel do gestor | regra-alterada | LOW | Cálculo de "hoje" corrigido de UTC para fuso local (America/Sao_Paulo) |
| `core/tests.py` | Suite de testes do core | regra-nova | LOW | Teste de regressão adicionado para o bugfix |

## Diff conceitual por componente

### `dashboard()` em `core/views.py`

**Antes:** `today = timezone.now().date()` — retornava a data em UTC, causando contador zerado após 21h de Brasília.

**Depois:** `today = timezone.localdate()` — retorna a data no fuso `America/Sao_Paulo` configurado em settings, alinhado com o horário real do negócio.

## Regras preservadas

- `Order.created_at` continua armazenado em UTC pelo Django ORM ✅
- A listagem "Pedidos Recentes" (`Order.objects.all().order_by('-created_at')[:5]`) não foi alterada ✅
- Nenhuma migration necessária ✅
- Nenhum contrato externo alterado ✅

## Regras modificadas

| Regra | Antes | Depois |
|-------|-------|--------|
| Referência temporal para "hoje" no dashboard | `timezone.now().date()` (UTC) | `timezone.localdate()` (America/Sao_Paulo) |
