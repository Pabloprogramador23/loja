# Data Delta: 011-fluxo-cliente-redesign (011-D)

> Data: `2026-05-31`
> Escopo: RF-01 — Localização Pré-Catálogo

## Alterações no modelo de dados

**Nenhuma.** Esta feature não adiciona, altera ou remove campos de nenhum model Django.

## Novo dado de sessão

| Chave | Tipo | Descrição | Lifecycle |
|-------|------|-----------|-----------|
| `session['session_delivery_address']` | `str` | Endereço de entrega fornecido pelo cliente antes do catálogo. Pode ser texto livre ou coordenadas GPS brutas. | Criado em `POST /save-location/`. Lido em `catalog()` e `cart_detail()`. Sobrescrito em cada novo `POST /save-location/`. Expira com a sessão Django. |

## Retrocompatibilidade

- Sessões existentes sem a chave `session_delivery_address` são tratadas como `''` via `request.session.get('session_delivery_address', '')`.
- Nenhum dado histórico é afetado.

## Migrations necessárias

Nenhuma.
