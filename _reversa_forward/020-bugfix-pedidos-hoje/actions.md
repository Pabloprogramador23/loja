# Actions: Bugfix — Contador "Pedidos Hoje" no Dashboard

> Identificador: `020-bugfix-pedidos-hoje`
> Data: `2026-06-04`
> Roadmap: `_reversa_forward/020-bugfix-pedidos-hoje/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 3 |
| Paralelizáveis (`[//]`) | 0 |
| Maior cadeia de dependência | 3 |

## Fase 1, Preparação

Nenhuma ação de preparação necessária — sem migration, sem dependência nova.

## Fase 2, Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Escrever teste `test_todays_orders_after_9pm_brasilia` em `core/tests.py` (ou arquivo de teste adequado): usar `unittest.mock.patch('django.utils.timezone.localdate', return_value=date(2026, 6, 4))` para simular que são 22h de Brasília; criar um pedido com `created_at` no dia 2026-06-04 (UTC); chamar a view de dashboard via `self.client.get('/dashboard/')` e assertar que `todays_orders == 1` no contexto | - | - | `core/tests.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T002 | Em `core/views.py`, na função `dashboard()` (linha 398), substituir `today = timezone.now().date()` por `today = timezone.localdate()` | T001 | - | `core/views.py` | 🟢 | `[X]` |

## Fase 4, Integração

Nenhuma integração externa afetada.

## Fase 5, Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Gerar `regression-watch.md` na `feature-dir` documentando o watch item: "`dashboard()` usa `timezone.localdate()` para calcular `today`, nunca `timezone.now().date()`" | T002 | - | `_reversa_forward/020-bugfix-pedidos-hoje/regression-watch.md` | 🟢 | `[X]` |

## Notas de execução

<!-- Reservado para /reversa-coding registrar avisos durante a execução. -->

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-04 | Versão inicial gerada por `/reversa-to-do` | reversa |
