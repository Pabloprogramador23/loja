# Data Delta: Remoção de Integrações Desnecessárias

> Identificador: `015-remocao-integracoes`
> Data: `2026-06-01`
> Base: `_reversa_sdd/code-analysis.md`, `_reversa_sdd/erd-complete.md`

---

## Resumo das mudanças

Nenhum modelo novo. Apenas remoções: 3 modelos Uber Direct, 1 campo em `Order`, e as tabelas geradas pelo allauth via migrate.

---

## Modelos removidos

### `UberDirectConfig` (tabela: `core_uberdirectconfig`)

Configuração Uber Direct por Store. Criado/atualizado via `manager_settings()` no painel.

```
UberDirectConfig
  ├── id (PK)
  ├── store (FK → Store, OneToOne) 🟢
  ├── client_id (CharField)
  ├── client_secret (CharField)
  ├── customer_id (CharField)
  ├── is_active (BooleanField)
  └── [campos de auditoria created_at/updated_at] 🟡 INFERIDO
```

**Migration:** `DROP TABLE core_uberdirectconfig`

---

### `UberDirectDelivery` (tabela: `core_uberdirectdelivery`)

Registro de cada despacho criado via Uber Direct.

```
UberDirectDelivery
  ├── id (PK)
  ├── order (FK → Order) 🟢
  ├── uber_delivery_id (CharField — ID retornado pelo Uber)
  ├── tracking_url (URLField)
  ├── status (CharField)
  ├── quote_id (CharField)
  ├── fee_cents (IntegerField)
  └── [created_at] 🟡 INFERIDO
```

**Migration:** `DROP TABLE core_uberdirectdelivery`

---

### `UberDirectDeliveryEvent` (tabela: `core_uberdirectdeliveryevent`)

Log imutável de eventos de webhook Uber recebidos.

```
UberDirectDeliveryEvent
  ├── id (PK)
  ├── delivery (FK → UberDirectDelivery)
  ├── event_type (CharField)
  ├── raw_payload (JSONField)
  └── received_at (DateTimeField)
```

**Migration:** `DROP TABLE core_uberdirectdeliveryevent`

---

## Campos removidos de modelos existentes

### `Order.uber_quote_id`

Campo que armazenava o `quote_id` retornado pelo Uber Direct no momento do checkout. Sempre será `null` para novos pedidos após a remoção do Uber Direct.

```diff
# core/models.py — Order
- uber_quote_id = models.CharField(max_length=100, blank=True, null=True)
```

**Migration:** `ALTER TABLE core_order DROP COLUMN uber_quote_id`

**Dados históricos:** pedidos existentes com valor neste campo perdem o campo. O dado não tem valor operacional após a remoção do Uber Direct.

---

## Tabelas removidas pelo allauth (via migrate após remoção das apps)

Quando `allauth`, `allauth.account` e `allauth.socialaccount` são removidos de `INSTALLED_APPS` e uma migration de reversão é criada (ou as apps são desinstaladas via `migrate <app> zero`), as seguintes tabelas são removidas:

| Tabela | App responsável |
|--------|-----------------|
| `account_emailaddress` | `allauth.account` |
| `account_emailconfirmation` | `allauth.account` |
| `socialaccount_socialaccount` | `allauth.socialaccount` |
| `socialaccount_socialapp` | `allauth.socialaccount` |
| `socialaccount_socialapp_sites` | `allauth.socialaccount` |
| `socialaccount_socialtoken` | `allauth.socialaccount` |

**Abordagem recomendada:** como essas tabelas pertencem a apps de terceiros (gerenciadas pelo allauth), a forma correta de remover é:
1. Rodar `python manage.py migrate allauth.account zero` e `python manage.py migrate allauth.socialaccount zero` **antes** de remover o pacote, para que o Django execute as migrations de reversão
2. Então remover o pacote e as entradas de `INSTALLED_APPS`

Se as tabelas estiverem vazias (ambiente de dev), usar `--fake zero` é aceitável.

---

## Tabela potencialmente removida

| Tabela | App | Condição |
|--------|-----|----------|
| `django_site` | `django.contrib.sites` | Apenas se `django.contrib.sites` for removido de INSTALLED_APPS |

Verificar ausência de `from django.contrib.sites` em todo o código antes de remover.

---

## Nenhum novo campo ou modelo

Esta feature é puramente destrutiva no schema. Nenhum campo é adicionado, nenhuma tabela é criada.
