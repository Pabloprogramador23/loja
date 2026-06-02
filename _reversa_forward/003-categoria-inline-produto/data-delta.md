# Data Delta: 003-categoria-inline-produto

> Data: `2026-05-26`
> Feature: Criação Inline de Categoria no Cadastro de Produto

---

## Mudanças no Modelo

**Nenhuma.** O modelo `Category` já existe como `TenantAwareModel` com campo `name` (CharField). Nenhum campo novo, nenhuma migration necessária.

---

## Modelo existente relevante: `Category`

```
Category (TenantAwareModel)
  ├── store: ForeignKey(Store)   ← herdado de TenantAwareModel, auto-atribuído via save()
  └── name: CharField(max_length=?)   ← campo usado na criação inline
```

A feature usa `Category.objects.get_or_create(name__iexact=nome, defaults={'name': nome})` escopo ao tenant via `TenantManager`.

---

## Migrations

**Nenhuma migration necessária.**

---

## Observação sobre `get_or_create` com TenantManager

`TenantManager.get_queryset()` injeta `.filter(store=tenant)` automaticamente. Portanto:

```python
Category.objects.get_or_create(name__iexact=nome, defaults={'name': nome})
```

…já é scoped ao tenant ativo. Se não houver categoria com aquele nome no tenant, `create` é chamado e `TenantAwareModel.save()` atribui `store = get_current_tenant()`.

**Risco:** Se o tenant não estiver no ContextVar no momento da criação (middleware falhou), `save()` levanta exceção implicitamente (campo `store` não-nullable). Isso é comportamento correto — falha explícita, não dado corrompido.
