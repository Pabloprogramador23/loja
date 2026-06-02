# Actions: Melhoria de UX no Checkout do Cliente

> Identificador: `010-checkout-ux-cliente`
> Data: `2026-05-30`
> Roadmap: `_reversa_forward/010-checkout-ux-cliente/roadmap.md`

## Resumo

| Métrica | Valor |
|---------|-------|
| Total de ações | 12 |
| Paralelizáveis (`[//]`) | 5 |
| Maior cadeia de dependência | 7 (T001→T002→T006→T007→T008→T011→T012) |

## Fase 1 — Preparação

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T001 | Adicionar model `UserProfile(OneToOne→User, phone CharField max_length=20 blank=True default='')` em `core/models.py`. Não herda `TenantAwareModel`. `related_name='profile'`. | - | `[//]` | `core/models.py` | 🟢 | `[X]` |
| T002 | Criar migration `core/migrations/0012_userprofile.py` conforme o esquema em `data-delta.md`. Dependência: `0011_uber_direct` + `swappable_dependency(AUTH_USER_MODEL)`. | T001 | - | `core/migrations/0012_userprofile.py` | 🟢 | `[X]` |

## Fase 2 — Testes

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T003 | Escrever testes para `UserProfile`: (a) criação automática via `get_or_create` na view `cart_detail`; (b) atualização de `phone` após checkout bem-sucedido de usuário autenticado; (c) `get_or_create` não falha para usuário sem perfil. | T002 | `[//]` | `core/tests.py` | 🟢 | `[X]` |
| T004 | Escrever teste para `selectAddress`: verificar que a string montada inclui cidade, estado e CEP quando preenchido. Pode ser teste de integração carregando o template ou teste unitário da função JS (comentário no arquivo). | - | `[//]` | `core/tests.py` | 🟢 | `[X]` |
| T005 | Escrever teste para `save_address`: verificar que a tentativa de salvar o 4º endereço retorna HTTP 200 com mensagem de erro visível no HTML retornado (não silencia). | - | `[//]` | `core/tests.py` | 🟢 | `[X]` |

## Fase 3 — Núcleo

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T006 | Atualizar `cart_detail()` em `core/views.py`: (a) adicionar import de `UserProfile` no topo do arquivo; (b) dentro da view, chamar `UserProfile.objects.get_or_create(user=request.user)` quando autenticado; (c) passar `profile_phone=profile.phone` no contexto. | T002 | - | `core/views.py` | 🟢 | `[X]` |
| T007 | Atualizar `checkout()` em `core/views.py`: após o bloco `transaction.atomic()` (fora dele, não dentro), quando `request.user.is_authenticated` e `phone` não vazio, chamar `UserProfile.objects.update_or_create(user=request.user, defaults={'phone': phone})`. | T006 | - | `core/views.py` | 🟢 | `[X]` |
| T008 | Atualizar `save_address()` em `core/views.py`: substituir `except Exception: pass` por `except ValidationError as e:` que retorna o partial `address_list.html` com contexto `{'addresses': addresses, 'address_error': str(e)}` — exibindo o erro ao usuário em vez de suprimir. Importar `ValidationError` de `django.core.exceptions` se ainda não importado. | T007 | - | `core/views.py` | 🟢 | `[X]` |
| T009 | Corrigir função `selectAddress` em `address_list.html`: atualizar a string montada de `'${street}, ${number} - ${neighborhood}'` para `'${street}, ${number} - ${neighborhood}, ${city} - ${state}'`. Quando `zip_code` estiver preenchido, acrescentar `', CEP ${zip_code}'`. Atualizar também o argumento `onclick` nos cards de endereço para passar `city`, `state` e `zip_code`. | - | `[//]` | `templates/core/partials/address_list.html` | 🟢 | `[X]` |

## Fase 4 — Integração

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T010 | Atualizar `cart_drawer.html` com três mudanças: (a) campo `customer_phone` recebe `value="{{ profile_phone\|default:'' }}"` para usuário autenticado; (b) textarea `delivery_address` recebe `id="delivery-address-textarea"` e classe `hidden` quando `request.user.is_authenticated` e `addresses` não vazio; (c) adicionar botão "Outro endereço" com `_="on click remove .hidden from #delivery-address-textarea then add .hidden to me"` visível apenas quando textarea estiver oculto. O textarea deve permanecer no DOM em qualquer caso (não usar `{% if %}` para removê-lo). | T006 | - | `templates/core/partials/cart_drawer.html` | 🟢 | `[X]` |
| T011 | Atualizar `address_list.html`: (a) adicionar bloco `{% if address_error %}<p class="text-sm text-red-600 ...">{{ address_error }}</p>{% endif %}` no topo do partial; (b) atualizar o `onclick` de cada card para passar `city`, `state` e `zip_code` como parâmetros adicionais para a função `selectAddress` corrigida em T009. | T008, T009 | - | `templates/core/partials/address_list.html` | 🟡 | `[X]` |

## Fase 5 — Polimento

| ID | Descrição | Dependências | Paralelismo | Arquivo alvo | Confidência | Status |
|----|-----------|--------------|-------------|--------------|-------------|--------|
| T012 | Gerar `regression-watch.md` com quatro watch items: W001 — phone pré-preenchido para usuário autenticado com pedidos; W002 — string de endereço salvo contém cidade e estado; W003 — textarea permanece funcional para Uber Direct quando revelado; W004 — fluxo de visitante (guest) inalterado (campos nome + telefone + email + endereço visíveis). | T010, T011 | - | `_reversa_forward/010-checkout-ux-cliente/regression-watch.md` | 🟢 | `[X]` |

## Notas de execução

<!-- Reservado para /reversa-coding registrar avisos durante a execução. -->

## Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-30 | Versão inicial gerada por `/reversa-to-do` | reversa |
