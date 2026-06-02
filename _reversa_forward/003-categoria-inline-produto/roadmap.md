# Roadmap: Criação Inline de Categoria no Cadastro de Produto

> Identificador: `003-categoria-inline-produto`
> Data: `2026-05-26`
> Requirements: `_reversa_forward/003-categoria-inline-produto/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A abordagem é um **delta mínimo sobre o `ProductForm` e suas duas views** (`manager_product_create` e `manager_product_edit` em `core/views.py`). Nenhum novo endpoint, nenhuma migração, nenhuma dependência nova.

O `ProductForm` (`core/forms.py`) receberá um campo extra não-model chamado `new_category_name` (CharField opcional). O template `product_form.html` exibirá esse campo abaixo do `<select>` de categorias existentes, com um texto de orientação.

Nas views, após `form.is_valid()`, a lógica verifica se `new_category_name` foi preenchido. Se sim, usa `Category.objects.get_or_create(name=nome)` — o `TenantManager` já filtra pelo tenant do ContextVar, e `TenantAwareModel.save()` auto-atribui a `store` na criação. A categoria retornada (nova ou existente) é atribuída a `form.instance.category` antes do `form.save()`.

O caminho crítico é: campo no form → lógica na view → campo sobrescreve seleção do `<select>` → `form.save()` salva o produto com a categoria correta. Backward compatibility total: campo em branco = comportamento anterior preservado.

## 2. Princípios aplicados

> `principles.md` não encontrado no projeto. Seção aplicada com base nos princípios implícitos do legado extraído.

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| Isolamento multi-tenant via ContextVar (`_reversa_sdd/domain.md#RN-01`) | `Category.objects.get_or_create` usa `TenantManager` — scope automático ao tenant. `TenantAwareModel.save()` auto-atribui `store` | respeita |
| Guard `user_can_manage_store` em views de manager (`_reversa_forward/002`) | Nenhuma view nova — guards existentes nas views de produto cobrem o novo comportamento | respeita |
| Delta mínimo — não redescrever a arquitetura existente | Apenas 3 arquivos tocados, sem novo model, sem nova view, sem nova rota | respeita |

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Campo `new_category_name` como campo extra no `ProductForm` (não-model) | Mantém a validação do form centralizada; não exige endpoint separado | (A) Campo direto no template sem passar pelo form — perde validação; (B) Campo no model como `__init__` override fora do Meta — mesma solução, mais complexa | 🟢 |
| D-02 | Lógica de criação/reutilização na view, não no `form.save()` | `ProductForm.save()` é método de model form — estender `save()` exigiria sobrescrever o form com lógica de view; separação de responsabilidades mais clara na view | (A) Override de `save()` no form | 🟢 |
| D-03 | `Category.objects.get_or_create(name=nome_strip)` com `.strip()` no nome | Evita duplicatas por espaços acidentais; `TenantManager` garante scope do tenant | (A) `Category.objects.create()` com `try/except IntegrityError` — mais verboso e menos idiomático | 🟢 |
| D-04 | Sem HTMX / sem endpoint dedicado de categoria | RF "O fluxo completa-se dentro do mesmo ciclo de submit" — solução server-side é mais simples e sem JS extra; stack já usa HTMX mas feature não precisa | (A) Endpoint HTMX que atualiza o `<select>` via swap — mais interativo mas complexidade desnecessária para caso de uso simples | 🟢 |

## 4. Premissas

> Nenhuma premissa adotada — requirements.md sem marcadores `[DÚVIDA]`.

| Premissa | Origem | Risco se errada |
|----------|--------|-----------------|
| n/a | n/a | n/a |

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `ProductForm` | `_reversa_sdd/code-analysis.md#Formulários` | regra-alterada | Campo extra `new_category_name` adicionado ao form |
| `manager_product_create` | `_reversa_sdd/code-analysis.md#Dashboard Manager` | regra-alterada | Lógica de categoria inline antes do `form.save()` |
| `manager_product_edit` | `_reversa_sdd/code-analysis.md#Dashboard Manager` | regra-alterada | Mesma lógica inline para edição de produto |
| `product_form.html` | template (sem spec SDD) | contrato-alterado | Campo visual e texto de ajuda adicionados |

## 6. Delta no modelo de dados

- **Nenhuma mudança no modelo** — `Category` existe e é `TenantAwareModel`. Nenhuma migration necessária.
- Detalhe completo em: `_reversa_forward/003-categoria-inline-produto/data-delta.md`

## 7. Delta de contratos externos

> Nenhum contrato externo afetado. Feature é puramente interna ao dashboard manager.

## 8. Plano de migração

n/a — nenhuma alteração de schema.

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| `new_category_name` com espaços ou capitalização diferente cria categorias quase-duplicatas ("Pizza" vs "pizza") | médio | médio | `strip()` + comparação case-insensitive no `get_or_create` via `iexact` |
| Form enviado com `new_category_name` preenchido E `category` selecionada — ambiguidade de intenção | baixo | alto | Regra clara: `new_category_name` tem prioridade sobre o `<select>`; texto de ajuda avisa o usuário |
| Tenant sem contexto ativo durante criação de categoria (raro, somente se middleware falhar) | alto | baixo | `TenantAwareModel.save()` já levanta erro se `store_id` nulo — falha explícita, não silenciosa |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] Campo "Nova categoria" visível e funcional em `/criar-produto/` e `/editar-produto/<id>/`
- [ ] Produto salvo com categoria nova aparece no catálogo da loja correta
- [ ] Categoria criada inline não aparece no `<select>` de outra loja
- [ ] Formulário sem `new_category_name` salva produto normalmente (sem regressão)
- [ ] `regression-watch.md` gerado

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-26 | Versão inicial gerada por `/reversa-plan` | reversa |
