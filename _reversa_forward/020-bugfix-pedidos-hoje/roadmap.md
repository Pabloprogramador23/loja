# Roadmap: Bugfix — Contador "Pedidos Hoje" no Dashboard

> Identificador: `020-bugfix-pedidos-hoje`
> Data: `2026-06-04`
> Requirements: `_reversa_forward/020-bugfix-pedidos-hoje/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A `dashboard()` em `core/views.py` contém uma única linha defeituosa:

```python
today = timezone.now().date()  # retorna data UTC, não Brasília
```

A correção substitui por `timezone.localdate()`, que retorna a data corrente no fuso configurado em `TIME_ZONE = 'America/Sao_Paulo'`. A chamada `__date` do ORM Django, quando combinada com `localdate()`, gera o range UTC correto tanto em SQLite quanto em PostgreSQL.

Nenhum modelo, migration, template ou rota é alterado. O delta é cirúrgico: uma linha em `core/views.py`. Junto com a correção, adiciona-se um teste unitário que simula o acesso após as 21h de Brasília (i.e., quando UTC já é o dia seguinte) e verifica que o contador retorna o valor correto.

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Utilidade antes de completude | Bug impede dado operacional real toda noite; correção tem uso imediato | respeita |
| IV. Produto focado, não showcase | Solução mais simples possível (`localdate()`), sem abstrações novas | respeita |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|---------------|--------------------------|-------------|
| D-01 | Usar `timezone.localdate()` | API nativa do Django, retorna data no `TIME_ZONE` configurado, sem código manual | `datetime.date.today()` (ignora USE_TZ), range UTC manual (mais código, mesmo resultado) | 🟢 |
| D-02 | Manter o lookup `__date` no ORM | Django com `localdate()` gera SQL correto em SQLite e PostgreSQL | `__gte`/`__lt` com range explícito (válido mas verboso para um bugfix trivial) | 🟢 |
| D-03 | Adicionar teste com `time_machine` ou `freeze_time` | Garante que o bug não regride em deploys futuros | Sem teste (risco de regressão silenciosa) | 🟢 |

## 4. Premissas

Nenhuma premissa adotada — causa do bug confirmada diretamente no código.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|-----------------------------|-----------------|--------|
| `dashboard()` | `core/views.py:398` | regra-alterada | `timezone.now().date()` → `timezone.localdate()` |

## 6. Delta no modelo de dados

Nenhuma alteração no modelo de dados.
Detalhe completo em: `_reversa_forward/020-bugfix-pedidos-hoje/data-delta.md`

## 7. Delta de contratos externos

Nenhum contrato externo afetado.

## 8. Plano de migração

n/a — nenhuma migration necessária.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| `timezone.localdate()` não disponível na versão do Django instalada | médio | baixo | Disponível desde Django 2.0; projeto usa Django 4+ | 🟢 |
| Teste de timezone depender de biblioteca externa não instalada (`freezegun`) | baixo | médio | Verificar se `freezegun` está no requirements; se não, usar `unittest.mock.patch` em `django.utils.timezone.localdate` | 🟡 |

## 10. Critério de pronto

- [ ] Linha `today = timezone.now().date()` substituída por `today = timezone.localdate()`
- [ ] Teste cobrindo acesso ao dashboard após 21h de Brasília retorna contador correto
- [ ] Dashboard acessado manualmente após as 21h mostra "Pedidos Hoje" > 0 quando há pedidos do dia
- [ ] `regression-watch.md` gerado

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-04 | Versão inicial gerada por `/reversa-plan` | reversa |
