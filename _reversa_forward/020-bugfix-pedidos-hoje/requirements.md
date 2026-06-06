# Requirements: Bugfix — Contador "Pedidos Hoje" no Dashboard

> Identificador: `020-bugfix-pedidos-hoje`
> Data: `2026-06-04`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

O card "Pedidos Hoje" no dashboard do gestor (`/dashboard/`) exibe sempre **0** a partir das 21h (horário de Brasília), mesmo com pedidos registrados no dia. O bug ocorre porque a view usa `timezone.now().date()`, que retorna a data em UTC — após 21h de Brasília o UTC já virou o dia seguinte, tornando o filtro `created_at__date=hoje_utc` ineficaz. A correção alinha o filtro ao fuso `America/Sao_Paulo` configurado no projeto.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/code-analysis.md#core/views.py` | `dashboard()` calcula `todays_orders` com `timezone.now().date()` sem conversão de fuso | 🟢 |
| `_reversa_sdd/architecture.md#configuração` | Projeto configurado com `USE_TZ = True` e `TIME_ZONE = 'America/Sao_Paulo'` | 🟢 |
| `_reversa_sdd/domain.md#pedidos` | `Order.created_at` é armazenado em UTC pelo Django ORM | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Gestor da loja | Acompanhar volume de pedidos do dia em tempo real | Abre o dashboard à noite (após 21h) e vê 0 pedidos, mesmo tendo recebido vários |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** "Pedidos Hoje" deve contar todos os pedidos cujo `created_at` cai dentro do dia corrente no fuso `America/Sao_Paulo`, não no fuso UTC. 🟢
   - Tipo: alterada
2. **RN-02:** O mesmo critério de fuso se aplica ao cálculo de `todays_orders` e a qualquer outro filtro por data do dia no dashboard. 🟡
   - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | O card "Pedidos Hoje" deve exibir a contagem correta de pedidos do dia em horário de Brasília | Must | Às 21h30 de Brasília, pedidos criados às 20h do mesmo dia aparecem no contador | 🟢 |
| RF-02 | A correção não deve afetar a listagem "Pedidos Recentes" (que já funciona corretamente) | Must | Pedidos recentes continuam sendo exibidos na ordem correta | 🟢 |
| RF-03 | O filtro deve funcionar corretamente tanto em horário de verão quanto fora dele | Should | Contagem correta em ambos os períodos do ano | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Corretude | Usar `timezone.localdate()` ou range UTC equivalente, nunca `timezone.now().date()` para comparações de data local | Bug confirmado em produção às 21h+ | 🟢 |
| Compatibilidade | Solução deve funcionar com SQLite (dev) e PostgreSQL (produção) | Projeto usa SQLite em dev, PostgreSQL em prod | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Gestor acessa dashboard após 21h com pedidos do dia
  Dado que existem pedidos criados no dia corrente (horário de Brasília)
  E que o horário atual é posterior às 21h (horário de Brasília)
  Quando o gestor acessa /dashboard/
  Então o card "Pedidos Hoje" exibe o número correto de pedidos do dia

Cenário: Virada de dia não zera pedidos do dia anterior incorretamente
  Dado que são 23h59 de Brasília
  E existem pedidos criados ao longo do dia
  Quando o gestor acessa /dashboard/
  Então "Pedidos Hoje" conta pedidos de 00h00 a 23h59 do dia atual em Brasília

Cenário: Pedidos Recentes não são afetados
  Dado que a correção foi aplicada
  Quando o gestor acessa /dashboard/
  Então a tabela "Pedidos Recentes" continua exibindo os últimos 5 pedidos corretamente
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 | Must | Bug visível toda noite, dado inoperante para gestão |
| RF-02 | Must | Não pode introduzir regressão na listagem |
| RF-03 | Should | Horário de verão no Brasil é raro mas ocorre |

## 9. Esclarecimentos

> Nenhuma sessão de dúvidas registrada ainda. Rode `/reversa-clarify` quando houver `[DÚVIDA]` pendente.

## 10. Lacunas

Nenhuma lacuna identificada — causa do bug confirmada diretamente no código.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-04 | Versão inicial gerada por `/reversa-requirements` | reversa |
