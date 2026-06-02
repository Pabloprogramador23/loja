# Actions: Criação Inline de Categoria no Cadastro de Produto

> Identificador: `003-categoria-inline-produto`
> Data: `2026-05-26`
> Roadmap: `_reversa_forward/003-categoria-inline-produto/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 4 |
| Paralelizáveis (`[//]`) | 2 |
| Maior cadeia de dependência | 3 (T001 → T002 → T003) |

---

## Fase 1 — Preparação

> Omitida — nenhuma migration, nenhum scaffolding necessário. `Category` já existe como `TenantAwareModel`.

---

## Fase 2 — Testes

> Omitida — o projeto não pratica TDD formal. Verificação manual descrita em `onboarding.md`.

---

## Fase 3 — Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Em `core/forms.py`, adicionar campo `new_category_name = forms.CharField(max_length=255, required=False, label='Nova categoria', help_text='Preencha para criar e usar uma nova categoria. Deixe em branco para usar a seleção acima.')` ao `ProductForm`, após o campo `category` (fora do `Meta`) | - | - | `core/forms.py` | 🟢 | `[X]` |
| T002 | Em `core/views.py`, na view `manager_product_create`, após `form.is_valid()` e antes de `form.save()`: (1) extrair `nome = form.cleaned_data.get('new_category_name', '').strip()`; (2) se `nome` não vazio, chamar `category, _ = Category.objects.get_or_create(name__iexact=nome, defaults={'name': nome})`; (3) atribuir `form.instance.category = category` | T001 | `[//]` | `core/views.py` | 🟢 | `[X]` |
| T003 | Em `core/views.py`, na view `manager_product_edit`, aplicar a mesma lógica inline de categoria do T002: após `form.is_valid()`, extrair `new_category_name`, criar/buscar categoria e atribuir a `form.instance.category` antes do `form.save()` | T001, T002 | - | `core/views.py` | 🟢 | `[X]` |

---

## Fase 4 — Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Em `templates/core/manager/product_form.html`, na seção de Categoria (após o bloco do `{{ form.category }}`), adicionar: label "Nova categoria", input `{{ form.new_category_name }}` com a mesma classe CSS Tailwind dos outros campos, e texto de ajuda em cinza explicando que preencher este campo substitui a seleção acima | T001 | `[//]` | `templates/core/manager/product_form.html` | 🟢 | `[X]` |

---

## Fase 5 — Polimento

> Omitida — feature simples sem necessidade de logs adicionais ou mensagens de erro extra.

---

## Notas de execução

<!-- Reservado para /reversa-coding registrar avisos durante a execução. -->

---

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-26 | Versão inicial gerada por `/reversa-to-do` | reversa |
