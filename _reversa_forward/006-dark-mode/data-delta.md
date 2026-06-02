# Data Delta — Modo Escuro (Dark Mode)

> Identificador: `006-dark-mode`
> Data: `2026-05-29`
> Base de comparação: `_reversa_sdd/data-dictionary.md`, `_reversa_sdd/erd-complete.md`, `core/models.py` (legado)

## Resumo

A feature é **aditiva**. Introduz **um modelo novo** para persistir a preferência de tema de usuários autenticados. Nenhum modelo existente é alterado ou removido. A preferência de visitantes anônimos vive apenas no `localStorage` do navegador (fora do banco).

## Novo modelo: `UserSettings`

Relacionamento **OneToOne** com `auth.User`. **Não** é `TenantAwareModel` — a preferência é por usuário (global), não por loja, e não deve receber o filtro automático do `TenantManager`.

| Campo | Tipo | Restrições | Default | Observação |
|-------|------|------------|---------|------------|
| `id` | AutoField | PK | — | padrão Django |
| `user` | OneToOneField → `auth.User` | `on_delete=CASCADE`, `related_name='settings'`, `unique` | — | dono da preferência |
| `theme` | CharField(max_length=10) | `choices=[('system','Sistema'),('light','Claro'),('dark','Escuro')]` | `'system'` | preferência de tema |
| `updated_at` | DateTimeField | `auto_now=True` | — | auditoria leve (opcional) |

### Choices de `theme`

| Valor | Significado |
|-------|-------------|
| `system` | Segue `prefers-color-scheme` do SO (default, alinha com RN-02) |
| `light` | Força tema claro |
| `dark` | Força tema escuro |

## Campos removidos / alterados

Nenhum. 🟢

## Migrações necessárias

1. Migração nova (ex.: `000X_usersettings`) com `migrations.CreateModel` para `UserSettings`.
   - Dependência: última migração do app onde o modelo for criado (a numeração exata sai no `/reversa-to-do`; o legado vai até `core/migrations/0008_order_comanda_fields.py`).
2. Operação única `CreateModel` — sem `RunPython`, sem alteração de tabela existente.
3. **Sem backfill:** usuários sem registro `UserSettings` são tratados como `theme='system'` no código (`get_or_create` ou `getattr` defensivo na leitura).

## Considerações de integridade

- `on_delete=CASCADE`: ao deletar o usuário, sua preferência some junto (correto — dado órfão sem valor).
- OneToOne garante no máximo uma linha por usuário.
- Leitura defensiva evita exceção `RelatedObjectDoesNotExist` para usuários antigos sem settings.

## Fora do banco (cliente)

- `localStorage['theme']` no navegador: usado por **anônimos** (persistência) e por **todos** como camada de bootstrap anti-FOUC antes do servidor responder. Não é dado persistido no backend.
