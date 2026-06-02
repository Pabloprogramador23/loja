# Requirements: Remoção de Integrações Desnecessárias

> Identificador: `015-remocao-integracoes`
> Data: `2026-06-01`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Esta feature remove integrações externas sem uso real no único cliente atual (pequeno restaurante com motoboy próprio). As remoções são: (1) integração Uber Direct completa — modelos, cliente HTTP, webhook e configurações; (2) autenticação social via Google OAuth2 e o pacote `django-allauth` inteiro, substituído por backend customizado de email auth. O modal de autenticação no checkout é mantido, mas sem botão Google. O campo `uber_quote_id` em `Order` é removido do schema. O objetivo é reduzir superfície de falha, eliminar dependências de configuração técnica e alinhar o produto aos Princípios I, II e IV do projeto.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/code-analysis.md#2.6` | `UberDirectClient` — cliente HTTP async com `get_access_token`, `create_quote`, `create_delivery`, `verify_uber_signature` | 🟢 |
| `_reversa_sdd/code-analysis.md#1.2` | `INSTALLED_APPS` inclui `allauth`, `allauth.socialaccount`, `allauth.socialaccount.providers.google`; `UBER_SANDBOX=True` em settings | 🟢 |
| `_reversa_sdd/code-analysis.md#checkout` | Cálculo de taxa: Uber Direct ativo → usa quote da sessão; inativo → taxa estática (`delivery_fee` + `free_delivery_threshold`) | 🟢 |
| `_reversa_sdd/inventory.md#core` | `core/uber_direct.py` presente; templates incluem `auth_modal.html`, `modal_login.html`, `modal_signup.html` com social login | 🟢 |
| `_reversa_sdd/architecture.md#decisões` | ADR-003: MercadoPago é o gateway de pagamento; nenhum ADR para Uber Direct ou Google OAuth | 🟢 |
| `.reversa/principles.md#II` | Integrações essenciais apenas — Google OAuth e Uber Direct não substituem necessidade real do cliente; MercadoPago sim | 🟢 |
| `.reversa/principles.md#III` | Configuração simples, operação autônoma — Uber Direct exige `UBER_CLIENT_ID/SECRET`; Google OAuth exige OAuth2 credentials | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Dono do restaurante | Configurar a loja sem precisar de ajuda técnica | Acessa painel → não vê campos Uber Direct nem instruções OAuth; menos variáveis de ambiente para configurar |
| Cliente final | Autenticar antes do checkout | Vê modal com formulário email/senha; sem botão "Entrar com Google" |
| Desenvolvedor | Subir o projeto em ambiente novo | Menos variáveis de ambiente obrigatórias; `docker-compose up` sem credenciais Uber ou Google |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** Taxa de entrega é sempre estática — `Store.delivery_fee` com isenção por `Store.free_delivery_threshold`. Lógica de cotação dinâmica via Uber Direct é removida. 🟢
   - Origem no legado: `_reversa_sdd/code-analysis.md#checkout` (lógica de cálculo de taxa)
   - Tipo: alterada

2. **RN-02:** Autenticação de clientes aceita apenas email/senha via backend customizado. Login social via Google não é mais suportado. O pacote `django-allauth` é removido inteiramente. 🟢
   - Origem no legado: `_reversa_sdd/code-analysis.md#1.2` (`AUTHENTICATION_BACKENDS`)
   - Tipo: alterada

3. **RN-03:** O campo `uber_quote_id` é removido do modelo `Order`. Pedidos históricos com valor neste campo perdem o campo via migration (dados descartados). 🟢
   - Tipo: alterada

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Remover `core/uber_direct.py` e todos os imports no código | Must | Arquivo ausente; nenhum `ImportError` em runtime | 🟢 |
| RF-02 | Remover modelos `UberDirectConfig`, `UberDirectDelivery`, `UberDirectDeliveryEvent` com migration de remoção | Must | `python manage.py migrate` executa sem erro; tabelas não existem no banco | 🟢 |
| RF-03 | Remover campos Uber Direct do `StoreSettingsForm` e do template de configurações | Must | Painel de configurações não exibe nenhum campo Uber Direct | 🟢 |
| RF-04 | Remover endpoint webhook Uber Direct (`/api/webhooks/uber`) do FastAPI | Must | `GET /api/webhooks/uber` retorna 404 | 🟢 |
| RF-05 | Remover variáveis `UBER_*` do `settings.py` e `.env.example` | Must | Nenhuma referência a `UBER_` no settings | 🟢 |
| RF-06 | Remover `django-allauth` inteiramente do `INSTALLED_APPS`, dependências e settings | Must | `pip show django-allauth` falha; sem erros de import | 🟢 |
| RF-07 | Remover rotas `/accounts/` (callbacks allauth) do `urls.py` raiz | Must | `GET /accounts/google/login/` retorna 404 | 🟢 |
| RF-08 | Remover botão/link "Entrar com Google" de todos os templates; manter modal com email/senha | Must | Modal exibe apenas campos email e senha; nenhuma referência a social login | 🟢 |
| RF-09 | Implementar backend customizado de autenticação por email para substituir allauth | Must | Login com email/senha funciona sem `allauth` em `AUTHENTICATION_BACKENDS` | 🟢 |
| RF-10 | Cálculo de taxa de entrega no checkout usa apenas taxa estática | Must | Checkout aplica `Store.delivery_fee` ou 0 conforme threshold; sem leitura de session `uber_quote_*` | 🟢 |
| RF-11 | Remover campo `uber_quote_id` do modelo `Order` com migration | Must | Campo não existe no schema após migrate; `python manage.py migrate` sem erro | 🟢 |
| RF-12 | Remover testes relacionados ao Uber Direct e Google OAuth | Must | Suite de testes passa sem erros de import ou falhas por código removido | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Manutenibilidade | Nenhum import órfão ou referência quebrada após remoção | Risco de `ImportError` em runtime se arquivos forem removidos sem limpar todas as referências | 🟢 |
| Banco de dados | Migration de remoção das tabelas Uber Direct e do campo `uber_quote_id` deve rodar sem erro em banco existente | Banco de dev pode ter dados históricos de teste | 🟡 |
| Autenticação | Backend customizado de email auth deve manter compatibilidade com sessões Django existentes | Usuários logados não devem ser desconectados após deploy | 🟡 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Cliente faz login por email após remoção do allauth
  Dado que o cliente acessa o modal de autenticação no checkout
  Quando preenche email e senha válidos e submete o formulário
  Então é autenticado com sucesso
  E nenhum botão de "Entrar com Google" está visível

Cenário: Checkout calcula taxa estática após remoção do Uber Direct
  Dado que a loja tem delivery_fee = 5.00 e free_delivery_threshold = 50.00
  E o carrinho tem subtotal de R$ 30,00
  Quando o cliente chega ao checkout
  Então a taxa de entrega exibida é R$ 5,00

Cenário: Checkout com frete grátis após remoção do Uber Direct
  Dado que a loja tem free_delivery_threshold = 50.00
  E o carrinho tem subtotal de R$ 60,00
  Quando o cliente chega ao checkout
  Então a taxa de entrega exibida é R$ 0,00

Cenário: Painel de configurações sem seção Uber Direct
  Dado que o dono acessa Configurações da loja
  Quando a página carrega
  Então nenhum campo ou seção "Uber Direct" é exibido

Cenário: Rotas de social login inexistentes
  Dado que a rota /accounts/google/login/ existia antes da remoção
  Quando qualquer cliente acessa essa URL
  Então recebe 404 Not Found

Cenário: Suite de testes passa após remoção
  Dado que testes de Uber Direct e Google OAuth foram removidos
  Quando o desenvolvedor executa a suite completa
  Então não há erros de import nem falhas por referências a código removido
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 a RF-05 (Uber Direct) | Must | Código ativo com dependência externa — sandbox consumindo configuração e lógica de checkout |
| RF-06 a RF-09 (allauth + backend email) | Must | Pacote no `INSTALLED_APPS` cria tabelas e rotas; login por email deve continuar funcionando |
| RF-10 (taxa sempre estática) | Must | Lógica de checkout simplificada; dependência direta da remoção do Uber Direct |
| RF-11 (remover uber_quote_id) | Must | Campo morto no schema após remoção do Uber Direct |
| RF-12 (remover testes) | Must | Testes quebrados mascaram regressões reais |
| RNF autenticação | Must | Sessões existentes não podem ser invalidadas |

## 9. Esclarecimentos

### Sessão 2026-06-01

- **Q:** O que fazer com o `django-allauth`?
  **R:** Remover o allauth inteiro e adaptar a autenticação para aceitar email via backend customizado.

- **Q:** O modal de autenticação no checkout deve ser mantido?
  **R:** Manter o modal com email/senha apenas, sem botão Google.

- **Q:** O campo `uber_quote_id` em `Order` deve ser removido do modelo?
  **R:** Remover o campo com migration.

- **Q:** O que fazer com os testes relacionados às integrações removidas?
  **R:** Remover os testes dessas integrações junto com o código.

## 10. Lacunas

Nenhuma dúvida pendente.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-01 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-06-01 | Esclarecimentos integrados via `/reversa-clarify` — 4 dúvidas resolvidas, RF-11 expandido, RF-12 adicionado | reversa |
