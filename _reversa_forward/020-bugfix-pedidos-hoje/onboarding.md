# Onboarding: Bugfix — Contador "Pedidos Hoje"

## Pré-requisitos

- Servidor rodando em `http://localhost:8000`
- Estar logado como gestor (staff)
- Ter ao menos um pedido criado no dia atual

## Passo a passo para validar o bugfix

### 1. Verificar o problema original (opcional, se horário < 21h)

Se o horário local for antes das 21h, o bug não se manifesta naturalmente — pule para o passo 3.

Se for após as 21h de Brasília:
1. Antes de aplicar a correção, acesse `http://localhost:8000/dashboard/`
2. Confirme que "Pedidos Hoje" exibe **0** mesmo havendo pedidos do dia na tabela "Pedidos Recentes"

### 2. Aplicar a correção

A correção já foi aplicada em `core/views.py`. O servidor recarregou automaticamente.

### 3. Verificar o resultado

1. Acesse `http://localhost:8000/dashboard/`
2. Confira o card **"Pedidos Hoje"**
3. O número deve corresponder à quantidade de pedidos criados no dia corrente (horário de Brasília)
4. Compare com a tabela "Pedidos Recentes" — os pedidos do dia devem estar listados lá

### 4. Verificar que "Pedidos Recentes" não foi afetado

1. A tabela de pedidos recentes deve continuar exibindo os últimos 5 pedidos em ordem decrescente
2. Os dados de cada linha (ID, cliente, total, status, data) devem estar corretos

## Resultado esperado

| Card | Antes do bugfix (após 21h) | Depois do bugfix |
|------|---------------------------|------------------|
| Pedidos Hoje | 0 (incorreto) | N (número real do dia) |
| Vendas Totais | correto | sem alteração |
| Pedidos Pendentes | correto | sem alteração |
| Pedidos Recentes | correto | sem alteração |
