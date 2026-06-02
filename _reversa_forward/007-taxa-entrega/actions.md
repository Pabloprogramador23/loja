# Actions: Taxa de Entrega por Restaurante

> Identificador: `007-taxa-entrega`
> Data: `2026-05-30`
> Roadmap: `_reversa_forward/007-taxa-entrega/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 12 |
| Paralelizáveis (`[//]`) | 6 |
| Maior cadeia de dependência | 4 (T001 → T005 → T006 → T012) |

## Fase 1, Preparação

<!-- Setup, scaffolding, migrações iniciais, configuração de infraestrutura local. -->

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Adicionar ao `Store` em `core/models.py`: `delivery_fee = DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(0)])` e `free_delivery_threshold = DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None, validators=[MinValueValidator(0)])`. Adicionar ao `Order`: `delivery_fee = DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))`. Importar `Decimal` de `decimal` e `MinValueValidator` de `django.core.validators` se ainda não importados. | - | - | `core/models.py` | 🟢 | `[X]` |
| T002 | Gerar a migration para os três novos campos: `python manage.py makemigrations core`. Confirmar que o arquivo gerado contém três `AddField` (dois em `store`, um em `order`) com os defaults corretos. | T001 | - | `core/migrations/0010_*.py` | 🟢 | `[X]` |
| T003 | Atualizar `StoreSettings` form em `core/forms.py`: adicionar `delivery_fee` (widget `NumberInput`, step 0.01, min 0) e `free_delivery_threshold` (widget `NumberInput`, step 0.01, min 0, required=False) à lista de `fields`. Adicionar `clean_free_delivery_threshold` que converte string vazia para `None`. | T001 | - | `core/forms.py` | 🟢 | `[X]` |

## Fase 2, Testes

<!-- Testes de modelo: defaults, nullable e validação de valor negativo. -->

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T004 | Escrever testes em `core/tests.py` cobrindo: `Store.delivery_fee` default é `Decimal('0.00')`; `Store.free_delivery_threshold` default é `None`; `Order.delivery_fee` default é `Decimal('0.00')`; `MinValueValidator` rejeita `delivery_fee` negativo em `Store`. | T001 | `[//]` | `core/tests.py` | 🟢 | `[X]` |

## Fase 3, Núcleo

<!-- Lógica de cálculo no checkout e força-zero no balcão; context processor. -->

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T005 | Atualizar `checkout()` em `core/views.py`: antes do `transaction.atomic()`, calcular `subtotal = cart.get_total_price()` e `effective_fee = Decimal('0.00') if (store.free_delivery_threshold is not None and subtotal >= store.free_delivery_threshold) else store.delivery_fee`. Passar `total_amount=subtotal + effective_fee` e `delivery_fee=effective_fee` no `Order.objects.create(...)`. `store` é `request.tenant`. | T001 | - | `core/views.py` | 🟢 | `[X]` |
| T006 | Na mesma `core/views.py`, atualizar `manager_create_order()`: adicionar `delivery_fee=Decimal('0.00')` explicitamente no `Order.objects.create(...)` (passo 3a do algoritmo de balcão). Garantir que o import de `Decimal` já existe no arquivo. | T005 | - | `core/views.py` | 🟢 | `[X]` |
| T007 | Atualizar `core/context_processors.py`: no context processor `cart`, adicionar ao dicionário retornado: `store_delivery_fee`, `free_delivery_threshold`, `effective_delivery_fee`, `cart_total_with_fee` e `threshold_gap`. Calcular `effective_delivery_fee` aplicando a lógica de threshold vs subtotal. Tratar ausência de tenant. | T001 | `[//]` | `core/context_processors.py` | 🟡 | `[X]` |

## Fase 4, Integração

<!-- Templates: configuração no dashboard, drawer do carrinho, histórico de pedidos. -->

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T008 | Atualizar `templates/core/manager/settings.html`: adicionar seção "Taxa de Entrega" com campo numérico para `delivery_fee` e bloco condicional com checkbox + campo para `free_delivery_threshold`. O campo de threshold fica oculto quando desmarcado (JS inline). Variantes `dark:` nos novos elementos. | T003 | `[//]` | `templates/core/manager/settings.html` | 🟢 | `[X]` |
| T009 | Atualizar `templates/core/partials/cart_drawer.html`: linha de subtotal, linha de taxa de entrega ("Grátis" ou valor), mensagem motivacional via `threshold_gap`, total via `cart_total_with_fee`. Variantes `dark:`. | T007 | `[//]` | `templates/core/partials/cart_drawer.html` | 🟡 | `[X]` |
| T010 | Atualizar `templates/core/account/order_detail.html`: linha "Taxa de Entrega" entre itens e total; "Grátis" quando `order.delivery_fee == 0`. Variantes `dark:`. | T001 | `[//]` | `templates/core/account/order_detail.html` | 🟡 | `[X]` |
| T011 | Atualizar `templates/core/account/orders.html`: exibir taxa de entrega como anotação secundária no total de cada pedido. Variantes `dark:`. | T001 | `[//]` | `templates/core/account/orders.html` | 🟡 | `[X]` |

## Fase 5, Polimento

<!-- Testes de integração do fluxo completo. -->

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T012 | Escrever testes em `core/tests_checkout.py` cobrindo: (a) taxa somada ao total; (b) isenção quando subtotal ≥ threshold; (c) cobrança quando subtotal < threshold; (d) snapshot preservado após mudança na loja. | T005, T006 | - | `core/tests_checkout.py` | 🟢 | `[X]` |

## Notas de execução

- **T007 expandido:** context processor `cart` passou a retornar também `cart_total_with_fee` (subtotal + effective_fee como Decimal) e `threshold_gap` (diferença para o threshold quando ativo e taxa > 0), evitando uso do filtro `add` do Django (não confiável com Decimal).
- **Validação:** 28 testes passam (8 novos: 6 de modelo + 4 de checkout + fee), migration 0010 aplicada sem erro, `python manage.py check` limpo.

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-30 | Versão inicial gerada por `/reversa-to-do` | reversa |
| 2026-05-30 | Todas as ações executadas por `/reversa-coding` | reversa |
