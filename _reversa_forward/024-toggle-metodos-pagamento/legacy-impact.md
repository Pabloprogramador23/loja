# Legacy Impact: Toggle de Métodos de Pagamento

> Identificador: `024-toggle-metodos-pagamento`
> Data: `2026-06-08`
> Feature executada por: `/reversa-coding`

---

## Arquivos afetados

| Arquivo afetado | Componente (`_reversa_sdd/`) | Tipo | Severidade | Justificativa |
|-----------------|------------------------------|------|-----------|---------------|
| `core/models.py` | `architecture.md#Domínio de Negócio — Store` | delta-de-dados | LOW | +3 `BooleanField` com `default=True` — retrocompatível, sem quebra de dados existentes |
| `core/migrations/0018_store_payment_method_toggles.py` | — | delta-de-dados | LOW | Migration não-destrutiva: `AddField` × 3 com default |
| `core/context_processors.py` | `architecture.md#Padrões — Carrinho em Sessão` / `code-analysis.md#2.3` | regra-nova | LOW | Três novas chaves adicionadas ao dict retornado por `cart()` |
| `core/views.py` | `code-analysis.md#2.4 — Views de Checkout` | regra-nova | MEDIUM | Guard de `payment_method` inserido no fluxo do `checkout()` — bloqueia criação de Order com método desabilitado |
| `core/forms.py` | `code-analysis.md#StoreSettingsForm` | regra-alterada | LOW | Três campos adicionados ao `StoreSettingsForm` para configuração pelo manager |
| `templates/core/partials/cart_drawer.html` | `architecture.md#Camada de Apresentação` | regra-nova | LOW | Seletores de método de pagamento condicionados aos flags do tenant |
| `templates/core/manager/settings.html` | `architecture.md#Camada de Apresentação` | regra-nova | LOW | Seção de checkboxes de métodos de pagamento adicionada |
| `core/tests_toggle_payment_methods.py` | — | componente-novo | LOW | Suite de testes específica da feature (9 testes, todos passando) |

---

## Diff conceitual por componente

### `Store` (model)

Antes: campos de configuração operacional eram `delivery_fee`, `free_delivery_threshold`, `delivery_enabled`.

Depois: +3 flags de controle de métodos de pagamento — `payment_online_enabled`, `payment_cash_enabled`, `payment_card_enabled` — todos `default=True`. Formam um grupo lógico de configuração de "meios de pagamento aceitos" por tenant.

### `views.checkout()`

Antes: validava `payment_method` apenas contra `Order.PaymentMethod.values` (valores válidos do enum). Qualquer método do enum era aceito sem verificar configuração da loja.

Depois: guard adicional após a validação do enum — verifica se o método específico está habilitado no tenant, e se há ao menos um método habilitado. Retorna `_checkout_error()` em ambos os casos de rejeição.

### `context_processors.cart()`

Antes: expunha `delivery_enabled` além das variáveis de taxa de entrega.

Depois: expõe também `payment_online_enabled`, `payment_cash_enabled`, `payment_card_enabled` para uso direto nos templates sem passar por views individualmente.

---

## Regras preservadas

As seguintes regras 🟢 do `_reversa_sdd/domain.md` continuam intactas:

- **RN-04:** Checkout Requer Nome, Telefone e Endereço — guard novo é aditivo, não substitui validações existentes
- **RN-07:** Snapshot de Preço no OrderItem — sem alteração em `OrderItem`
- **RN-08:** Pedido de Balcão — Sem PIX, Já em Preparo — `manager_create_order` não usa o fluxo de checkout público
- **RN-09:** Token MercadoPago por Tenant — resolução de token inalterada
- **RN-12:** Acesso ao Dashboard Manager — Controle Binário — `StoreSettingsForm` ainda protegido pela view de settings
- **RN-14:** Aprovação de Pagamento via Webhook — sem alteração no webhook MP
- **RN-15:** Disponibilidade de Produto — `is_available` inalterado
- **RN-19:** Preferência de Tema Global por Usuário — `UserSettings` inalterado

---

## Regras modificadas

| Regra | Tipo de modificação | Impacto |
|-------|---------------------|---------|
| `RN-09` (indiretamente) | Contexto ampliado: mesmo que `payment_online_enabled=True`, se o token MP estiver vazio, o aviso no painel de settings orienta o manager | O guard no checkout não bloqueia por falta de token (fallback mock em dev continua funcionando) — apenas aviso visual no form |
| Fluxo de `checkout()` (`code-analysis.md#2.4`) | Novo ponto de rejeição antes da criação do pedido | Qualquer integração ou teste que assume que `payment_method` válido no enum sempre prossegue precisa ser atualizado |
