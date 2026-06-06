# Data Delta: Bugfix — Contador "Pedidos Hoje"

Nenhuma alteração no modelo de dados, migrations ou schema de banco.

O campo `Order.created_at` continua sendo armazenado em UTC pelo Django ORM — esse comportamento é correto e não muda. A correção está apenas na camada de consulta (como a data de referência é calculada), não na camada de persistência.
