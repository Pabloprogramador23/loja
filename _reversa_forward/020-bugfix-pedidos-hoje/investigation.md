# Investigation: Bugfix — Contador "Pedidos Hoje"

## Causa raiz

Django com `USE_TZ = True` armazena todos os datetimes em UTC no banco. `timezone.now()` retorna o instante atual em UTC. Chamar `.date()` sobre um datetime UTC extrai a data UTC — que pode ser um dia à frente da data local quando o fuso tem offset negativo.

**America/Sao_Paulo é UTC-3 (e UTC-2 em horário de verão).**

Portanto, a partir das **21h00 (horário padrão)** ou **22h00 (horário de verão)** de Brasília, `timezone.now().date()` já retorna o dia seguinte em UTC. O filtro `created_at__date=amanhã_utc` não encontra pedidos criados no dia corrente de Brasília, retornando 0.

## Solução adotada: `timezone.localdate()`

`django.utils.timezone.localdate()` é equivalente a:

```python
timezone.now().astimezone(get_current_timezone()).date()
```

Retorna a data local no fuso definido por `TIME_ZONE` nas settings (`America/Sao_Paulo`). Disponível desde Django 2.0.

## Comportamento do lookup `__date` com `localdate()`

Quando o ORM recebe `created_at__date=localdate()`, Django compara datas extraídas do campo `created_at` (armazenado em UTC) com a data local informada. Em PostgreSQL, Django usa `AT TIME ZONE` para converter corretamente. Em SQLite, a função `django_date_extract` é aplicada diretamente ao valor UTC armazenado — o que significa que a comparação é feita contra a data UTC do campo, não a local.

**Implicação prática:** Para SQLite em dev, `localdate()` melhora o problema mas pode ainda apresentar divergência na janela de 1-3h antes da meia-noite local (quando UTC já virou mas o campo ainda está no dia anterior local). Em PostgreSQL (produção), a conversão é feita corretamente pelo banco.

**Se isso for um problema:** substituir por range explícito:

```python
import datetime
local_today = timezone.localdate()
start = timezone.make_aware(datetime.datetime.combine(local_today, datetime.time.min))
end   = timezone.make_aware(datetime.datetime.combine(local_today, datetime.time.max))
todays_orders = Order.objects.filter(created_at__gte=start, created_at__lte=end).count()
```

Esta versão é portável e inequívoca para qualquer banco. Para o bugfix imediato, `localdate()` resolve o caso concreto (acesso após 21h com pedidos do dia anterior em UTC). O range explícito é registrado como opção futura se necessário.

## Verificação de disponibilidade

```python
from django.utils import timezone
timezone.localdate()  # Django >= 2.0
```

Projeto usa Django 4.x — sem risco.

## Biblioteca de teste

O teste precisa simular um horário específico (22h de Brasília). Opções:

| Opção | Disponível no projeto? | Preferência |
|-------|----------------------|-------------|
| `freezegun` / `time-machine` | Verificar requirements.txt | ✅ se instalado |
| `unittest.mock.patch('django.utils.timezone.localdate', return_value=date(2026,6,4))` | Sempre disponível | ✅ fallback |

Usar mock direto evita dependência externa — preferível pelo princípio IV (produto focado).
