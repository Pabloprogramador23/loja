# Roadmap: Melhoria de UX no Checkout do Cliente

> Identificador: `010-checkout-ux-cliente`
> Data: `2026-05-30`
> Requirements: `_reversa_forward/010-checkout-ux-cliente/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

## 1. Resumo da abordagem

A feature é um conjunto de cinco correções cirúrgicas sobre o checkout existente, sem redesenho de arquitetura. O ponto estrutural mais relevante é a criação de `UserProfile` como extensão do `User` do Django — um padrão consolidado no Django que evita sobrescrever o model de auth. O `UserProfile.phone` é populado automaticamente na view `checkout()` após cada pedido bem-sucedido de usuário autenticado, e lido na view `cart_detail()` para pré-preencher o campo.

No template `cart_drawer.html`, a lógica condicional já existente (`{% if request.user.is_authenticated %}`) é expandida: quando o usuário tem endereços salvos, o textarea é renderizado com `class="hidden"` e a lista de endereços age como seletor primário. O textarea permanece no DOM (necessário para o evento `blur` do Uber Direct), apenas oculto. Um botão "Outro endereço" alterna a visibilidade via Hyperscript.

A correção do `selectAddress` em `address_list.html` é a mudança de menor risco e maior impacto imediato: uma linha de JavaScript que passa a incluir cidade, estado e CEP na string montada.

Nenhum endpoint novo, nenhuma migration no `Order`, nenhum contrato externo alterado.

## 2. Princípios aplicados

Arquivo `principles.md` não encontrado no projeto — sem princípios registrados para verificar.

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|---------------|--------------------------|-------------|
| D-01 | `UserProfile(OneToOne→User)` para persistir `phone` | Extensão padrão Django; não toca no model `auth.User`; `get_or_create` protege usuários sem perfil | Buscar do último `Order` (descartado: sem persistência, lento em tenant com muitos pedidos); adicionar `phone` direto em `User` (descartado: exigiria custom user model com swap) | 🟢 |
| D-02 | Atualizar `profile.phone` na view `checkout()` após commit da `transaction.atomic()` | Mantém a lógica de negócio num único lugar (view); evita signal oculto difícil de rastrear | Signal `post_save` em `Order` (descartado: signals disparam em todo save, inclusive admin e seed, causando efeitos colaterais) | 🟢 |
| D-03 | Textarea `delivery_address` permanece no DOM mesmo oculto (classe `hidden`) | O atributo `hx-trigger="blur"` do Uber Direct (feature 009) exige que o elemento exista no DOM para ser incluído nas requisições HTMX | Remover o textarea do DOM via `{% if %}` (descartado: quebra Uber Direct) | 🟢 |
| D-04 | `cart_detail()` view passa `profile_phone` no contexto | O drawer é recarregado via HTMX (`hx-get="{% url 'cart_detail' %}"`); o contexto precisa estar nessa view, não num context processor global | Context processor global (descartado: executa em todo request, não só no carrinho) | 🟢 |
| D-05 | Feedback de limite de endereços via retorno JSON/HTML na view `save_address()` | A view já retorna `address_list.html` via HTMX; basta retornar o partial com mensagem de erro incluída | Flash message Django (descartado: não compatível com retorno HTMX de partial) | 🟡 |

## 4. Premissas

Nenhuma — todas as dúvidas do `requirements.md` foram resolvidas.

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `UserProfile` | — (novo) | componente-novo | Model `OneToOne→User` com campo `phone`; migration 0012 |
| `cart_detail()` | `core/views.py` | regra-alterada | Passa `profile_phone` e `addresses` no contexto do drawer |
| `checkout()` | `core/views.py` | regra-alterada | Atualiza `UserProfile.phone` após commit bem-sucedido |
| `save_address()` | `core/views.py` | regra-alterada | Retorna feedback de erro quando limite de 3 é atingido |
| `cart_drawer.html` | `templates/core/partials/cart_drawer.html` | regra-alterada | Textarea oculto quando logado com endereços; phone pré-preenchido |
| `address_list.html` | `templates/core/partials/address_list.html` | regra-alterada | `selectAddress` inclui cidade, estado e CEP na string |

## 6. Delta no modelo de dados

- Novo model `UserProfile` com FK `OneToOne→User` e campo `phone CharField(max_length=20, blank=True)`
- Nenhuma alteração em `Order`, `Address` ou outros models existentes
- Detalhe completo em: `_reversa_forward/010-checkout-ux-cliente/data-delta.md`

## 7. Delta de contratos externos

Nenhum contrato externo afetado. Todas as mudanças são em views Django e templates HTMX internos.

## 8. Plano de migração

1. Criar `UserProfile` em `core/models.py` e gerar migration `0012_userprofile.py`
2. Atualizar `cart_detail()`: importar `UserProfile`, chamar `get_or_create`, passar `profile_phone` no contexto
3. Atualizar `checkout()`: após commit da `transaction.atomic()`, chamar `UserProfile.objects.update_or_create(user=request.user, defaults={'phone': phone})`
4. Atualizar `save_address()`: capturar `ValidationError` explicitamente e retornar partial com mensagem de erro visível
5. Corrigir `selectAddress` em `address_list.html`: montar string com `city` e `state` (e `zip_code` quando presente)
6. Atualizar `cart_drawer.html`: textarea com `id="delivery-address-textarea"` + classe `hidden` quando `addresses` não vazio; botão "Outro endereço" com `_="on click remove .hidden from #delivery-address-textarea then add .hidden to me"`; campo phone com `value="{{ profile_phone }}"`

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Usuários existentes sem `UserProfile` causam `RelatedObjectDoesNotExist` | Alto | Alto (todos os usuários atuais) | Usar `get_or_create` em toda leitura; nunca acessar `user.userprofile` diretamente | 
| Textarea oculto não dispara `blur` automaticamente quando revelado pelo botão | Médio | Baixo | O evento `blur` só dispara quando o campo perde foco após edição — não há disparo automático; comportamento correto |
| `selectAddress` com cidade/estado em formato inesperado quebra cotação Uber Direct | Médio | Baixo | Uber Direct usa o textarea como string livre de endereço — a inclusão de mais informação só melhora a cotação |
| `save_address` com `except Exception: pass` mascara outros erros além do limite | Baixo | Médio | Refinar o `except` para capturar apenas `ValidationError` explicitamente |

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] Usuário logado com pedidos anteriores vê telefone pré-preenchido ao abrir o carrinho
- [ ] Clicar em endereço salvo preenche o campo com cidade e estado
- [ ] Tentar salvar 4º endereço exibe mensagem de erro visível
- [ ] Visitante (não autenticado) não percebe nenhuma diferença no fluxo
- [ ] Textarea do endereço permanece funcional para cotação Uber Direct
- [ ] `regression-watch.md` gerado

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-30 | Versão inicial gerada por `/reversa-plan` | reversa |
