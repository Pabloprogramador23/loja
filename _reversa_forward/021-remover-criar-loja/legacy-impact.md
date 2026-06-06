# Legacy Impact: 021-remover-criar-loja

> Feature: `021-remover-criar-loja`
> Data: `2026-06-05`
> Gerado por: `/reversa-coding`

## Arquivos afetados

| Arquivo afetado | Componente (`_reversa_sdd/`) | Tipo | Severidade | Justificativa |
|-----------------|------------------------------|------|------------|---------------|
| `accounts/urls.py` | `accounts/autenticacao` | contrato-removido | LOW | Rota pública `/criar-loja/` removida; nenhum cliente externo dependia dela |
| `accounts/views.py` | `accounts/autenticacao` | componente-extinto | LOW | `criar_loja_view` removida; import de `transaction` também removido como dead code |
| `accounts/forms.py` | `accounts/autenticacao` | componente-extinto | LOW | `StoreRegistrationForm`, `RESERVED_SUBDOMAINS`, `subdomain_validator` removidos |
| `templates/accounts/criar_loja.html` | `accounts/autenticacao` | componente-extinto | LOW | Template deletado; sem referências remanescentes |
| `templates/accounts/login.html` | `accounts/autenticacao` | regra-alterada | LOW | Link de entrada "🏪 Crie sua loja" removido da tela de login |

## Diff conceitual por componente

### `accounts/autenticacao`

**Antes:** o módulo expunha três fluxos de registro: cliente (`signup_view`), loja (`criar_loja_view`) e checkout modal (`checkout_signup_view`). A tela de login apresentava dois links de ação — "Criar uma conta nova" e "🏪 Crie sua loja".

**Depois:** o módulo expõe dois fluxos de registro: cliente (`signup_view`) e checkout modal (`checkout_signup_view`). A tela de login apresenta apenas o link "Criar uma conta nova". A criação de Store é possível exclusivamente via Django Admin (`/admin/`) por superuser.

O model `Store` e seu registro no Admin não foram tocados.

## Regras preservadas

| Regra | Fonte | Status |
|-------|-------|--------|
| RN-05 Pedido de convidado e vinculação pós-signup | `_reversa_sdd/domain.md#RN-05` | 🟢 intacta — `signup_view` não alterada |
| RN-12 Acesso ao dashboard — controle binário | `_reversa_sdd/domain.md#RN-12` | 🟢 intacta — lógica de staff não alterada |
| RN-01 Isolamento de tenant por ContextVar | `_reversa_sdd/domain.md#RN-01` | 🟢 intacta — nenhum middleware alterado |

## Regras modificadas

| Regra | Fonte | Mudança |
|-------|-------|---------|
| (implícita) Auto-cadastro de Store por visitante anônimo | `accounts/views.py:criar_loja_view` | **Removida** — a regra deixa de existir no sistema |
