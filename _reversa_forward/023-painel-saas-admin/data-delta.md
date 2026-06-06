# Data Delta: Painel SaaS Admin

> Identificador: `023-painel-saas-admin`
> Data: `2026-06-05`

## Resumo

**Nenhuma migração de banco necessária.**

Todos os campos utilizados pelo painel SaaS já existem no modelo `Store`. A feature lê e escreve apenas em modelos existentes.

## Modelo `Store` — campos utilizados (já existentes)

| Campo | Tipo | Uso no painel |
|-------|------|---------------|
| `id` | AutoField | Chave para rotas `/saas/lojas/<id>/` e toggle |
| `name` | CharField | Listagem e detalhe |
| `subdomain` | CharField (unique) | Listagem, detalhe, botão "Ver loja" |
| `owner` | FK → User | Detalhe — exibe nome e email do Manager |
| `is_active` | BooleanField | Listagem (status badge) + toggle |
| `created_at` | DateTimeField | Listagem — coluna "Criada em" |
| `delivery_fee` | DecimalField | Detalhe |
| `mercadopago_access_token` | CharField | Detalhe — exibido mascarado |

## Annotations adicionadas em tempo de query (sem persistência)

Calculadas via `Store.objects.annotate(...)` — não persistidas em banco:

| Annotation | SQL equivalente | Uso |
|------------|----------------|-----|
| `total_orders` | `COUNT(order.id)` | Listagem |
| `orders_today` | `COUNT(order.id) WHERE order.created_at::date = TODAY` | Listagem |
| `active_products` | `COUNT(product.id) WHERE product.is_available = True` | Detalhe (opcional) |

## Modelos auxiliares criados pelo formulário de nova loja

O form `SaasCreateStoreForm` cria dois registros existentes:

| Model | Campos gravados | Observação |
|-------|----------------|------------|
| `auth.User` | `username`, `email`, `password` (hasheado), `is_staff=True` | Criado via `User.objects.create_user()` |
| `Store` | `name`, `subdomain`, `owner=user`, `is_active=True` | `store_id` atribuído explicitamente |

## Migrações

```
(nenhuma)
```
