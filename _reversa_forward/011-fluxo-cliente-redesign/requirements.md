# Requirements: Redesign do Fluxo do Cliente (Order-to-Delivery)

> Identificador: `011-fluxo-cliente-redesign`
> Data: `2026-05-30`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Redesenho completo da jornada do cliente no app web atual (HTMX + Django). O fluxo atual permite compra anônima sem localização prévia e suporta apenas PIX via QR Code. Esta especificação-mãe define o redesenho em **três features separadas**: (011-A) autenticação no checkout — modal com Google OAuth2 + cadastro/login tradicional via sessão Django; (011-B) Checkout Pro MercadoPago — preference + redirect + webhook; (011-C) pagamento na entrega — dinheiro com troco e cartão na maquininha. Login Apple e JWT foram **descartados** (web app com HTMX usa sessão Django; Apple exige infraestrutura indisponível).

> ℹ️ **Este documento é a spec-mãe.** Cada sub-feature gerará seu próprio ciclo forward (requirements → plan → to-do → coding). Comece pela que o usuário priorizar.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/domain.md#RN-04` | Checkout atual requer nome, telefone e endereço — sem etapa de localização prévia | 🟢 |
| `_reversa_sdd/domain.md#RN-05` | Guest checkout com `guest_order_id` em sessão — vinculação retroativa pós-signup | 🟢 |
| `_reversa_sdd/domain.md#RN-09` | Token MP por tenant; mock automático em dev (`TEST-0000`) | 🟢 |
| `_reversa_sdd/domain.md#RN-10` | Pagamento atual: somente PIX QR Code via `create_pix_payment()` | 🟢 |
| `_reversa_sdd/domain.md#RN-11` | Email do pagador: placeholder hardcoded para guest — bloqueio em produção real | 🔴 |
| `_reversa_sdd/architecture.md#ADR-003` | ADR-003 fixou PIX como único método; Checkout Pro é mudança de ADR | 🟢 |
| `_reversa_sdd/architecture.md#ADR-004` | Carrinho em sessão Django — sem persistência em banco | 🟢 |
| `_reversa_sdd/architecture.md#ADR-005` | Guest checkout com vinculação pós-signup — fluxo a ser substituído por auth híbrida | 🟢 |
| `_reversa_sdd/architecture.md#ADR-001` | ASGI híbrido: Django (views/sessions) + FastAPI (`/api/*`) | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Novo cliente (mobile/web) | Fazer primeiro pedido sem fricção | Informa localização → navega catálogo → carrinho → escolhe Google login → paga online → acompanha |
| Cliente recorrente autenticado | Pedir novamente com mínimo de cliques | Localização lembrada → catálogo → carrinho → paga (dados já preenchidos) |
| Cliente sem cartão/preferência offline | Pagar na entrega | Carrinho → login → seleciona "Pagar na Entrega" → informa se precisa de troco → pedido confirmado |
| Restaurante (manager) | Receber notificação do pedido | Pedido aparece no painel assim que confirmado (online ou offline) |

## 4. Regras de negócio novas ou alteradas

1. **RN-15:** Antes de exibir o catálogo, o sistema deve solicitar o endereço de entrega (texto livre ou GPS). O endereço é armazenado em sessão e pré-preenchido no checkout. 🟡
   - Tipo: nova

2. **RN-16:** No checkout, usuário não autenticado vê modal/tela de identificação com duas opções: (A) Login Social Google ou Apple; (B) Cadastro/Login tradicional com nome, e-mail, celular, endereço e senha. A opção de compra anônima (guest) é removida. 🟡
   - Origem: substitui `_reversa_sdd/domain.md#RN-05` (guest checkout)
   - Tipo: alterada (quebra retrocompatibilidade com guest flow)

3. **RN-17:** Após login/cadastro, o carrinho atual é imediatamente associado ao usuário sem ser limpo. 🟢
   - Origem: mantém a lógica de `_reversa_sdd/domain.md#RN-05` mas aplica ANTES do pedido, não após
   - Tipo: alterada

4. **RN-18:** Autenticação usa **sessão Django** em todo o fluxo web (manager + cliente). Login social Google usa `django-allauth` ou `social-auth-app-django`, que criará sessão Django padrão ao autenticar. Não há JWT. 🟢
   - Tipo: nova (Google OAuth2 via sessão Django)

5. **RN-19:** Checkout Pro MercadoPago substitui o PIX QR Code como método de pagamento online. O backend FastAPI cria uma `preference` MP e retorna o `init_point` (URL). O frontend redireciona para essa URL. O webhook MP em `/api/webhooks/mercadopago` é atualizado para tratar notificações do Checkout Pro (evento `payment.updated` com status `approved`). 🟡
   - Origem: substitui `_reversa_sdd/domain.md#RN-10` + `_reversa_sdd/architecture.md#ADR-003`
   - Tipo: alterada

6. **RN-20:** Pagamento na entrega: o cliente escolhe entre "Dinheiro" (com campo opcional de troco) ou "Cartão na Maquininha" (crédito ou débito). O pedido é gravado diretamente com status `CONFIRMED` (novo status, antes de `PREPARING`). O restaurante é notificado via painel em tempo real. 🟡
   - Tipo: nova (requer novo campo em `Order`: `payment_method`, `change_amount`, `card_type`)

7. **RN-21:** O carrinho deve ser persistido em banco (ou Redis) além da sessão, para sobreviver ao redirecionamento externo para o MercadoPago. A sessão Django pode ser encerrada durante o redirect. 🟡
   - Origem: `_reversa_sdd/architecture.md#ADR-004` (carrinho em sessão — limitação identificada)
   - Tipo: alterada

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Tela/modal de localização antes do catálogo: campo de texto para endereço ou botão "Usar minha localização" (GPS via browser) | Must | Catálogo não é exibido sem endereço definido na sessão; endereço salvo pré-preenche o checkout | 🟡 |
| RF-02 | Modal de identificação no checkout para não-autenticados: opções Google, Apple e cadastro tradicional | Must | Usuário não autenticado ao clicar "Finalizar Pedido" vê o modal antes da tela de pagamento | 🟡 |
| RF-03 | Login social Google via OAuth2: captura ID, nome e e-mail; cria ou atualiza `User`; cria sessão Django via `django-allauth` | Must | Primeiro clique cria conta; clique subsequente faz login; sessão Django ativa em ambos os casos | 🟡 |
| RF-04 | ~~Login social Apple~~ — **Descartado** | — | — | — |
| RF-05 | Cadastro/Login tradicional rápido: nome, e-mail, celular, endereço, senha; link "Esqueci minha senha" | Must | Formulário valida campos; cria ou autentica `User`; emite JWT; associa carrinho | 🟢 |
| RF-06 | Associação de carrinho ao usuário após login/cadastro sem limpeza | Must | Itens no carrinho antes do login permanecem após autenticação | 🟢 |
| RF-07 | Checkout Pro MP: FastAPI cria `preference`, retorna `init_point`; frontend redireciona | Must | Clique em "Pagar Online" redireciona para URL MP; URLs de retorno (`success`/`pending`/`failure`) trazem de volta ao app | 🟡 |
| RF-08 | Webhook MP atualizado para Checkout Pro: evento `payment` com status `approved` → pedido `PREPARING` | Must | Pagamento aprovado no MP atualiza status do pedido em até 5s via webhook | 🟡 |
| RF-09 | Pagamento na entrega — Dinheiro: campo de troco opcional ("Para quanto?") | Must | Pedido gravado com `payment_method=cash`, `change_amount` preenchido ou nulo; status `CONFIRMED` | 🟡 |
| RF-10 | Pagamento na entrega — Cartão: seleção de Crédito ou Débito | Must | Pedido gravado com `payment_method=card`, `card_type=credit\|debit`; status `CONFIRMED` | 🟡 |
| RF-11 | Notificação do restaurante ao receber pedido offline (na entrega) | Must | Novo pedido aparece no painel do manager sem refresh manual; usar polling HTMX existente ou SSE | 🟡 |
| RF-12 | Carrinho persistido em banco/Redis para sobreviver ao redirect MP | Should | Usuário que fecha o app durante redirect MP encontra o carrinho ao retornar | 🟡 |
| RF-13 | Recuperação de senha por e-mail (link "Esqueci minha senha") | Must | Usuário recebe e-mail com link de reset; senha alterada com sucesso | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Segurança | `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` **nunca** em código; apenas via variáveis de ambiente | Risco de exposição de credenciais OAuth | 🟢 |
| Compatibilidade | Django session auth unificado para manager e cliente; `django-allauth` cria sessão padrão no login social | `_reversa_sdd/architecture.md#ADR-001` — sem mudança de mecanismo de auth | 🟢 |
| Multi-tenant | Credenciais MP por tenant preservadas; preference criada com token da loja atual | `_reversa_sdd/domain.md#RN-09` | 🟢 |
| Sem regressão | Painel do manager (dashboard, pedidos, comandas, configurações) não deve ser afetado | Isolamento atual via `is_staff` | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Novo cliente acessa a loja pela primeira vez
  Dado que o usuário não está autenticado e não tem localização salva
  Quando acessa a URL da loja
  Então vê modal/tela pedindo endereço antes do catálogo
  E ao confirmar o endereço, o catálogo é exibido normalmente

Cenário: Cliente tenta finalizar pedido sem estar logado
  Dado que o carrinho tem itens e o usuário não está autenticado
  Quando clica em "Finalizar Pedido"
  Então vê modal de identificação com opções Google, Apple e cadastro tradicional
  E o carrinho não é limpo durante o processo

Cenário: Login via Google no checkout
  Dado que o modal de identificação está aberto
  Quando clica em "Continuar com Google" e autoriza
  Então uma conta é criada (ou encontrada) com o e-mail do Google
  E o carrinho é associado à conta
  E o usuário é redirecionado para escolha de pagamento

Cenário: Pagamento online via Checkout Pro
  Dado que o usuário está autenticado e tem itens no carrinho
  Quando seleciona "Pagar Online" e confirma o pedido
  Então o backend cria uma preference no MP e retorna init_point
  E o browser redireciona para a URL do Mercado Pago
  E após pagamento aprovado, o webhook atualiza o pedido para PREPARING

Cenário: Pagamento na entrega com dinheiro e troco
  Dado que o usuário está autenticado
  Quando seleciona "Pagar na Entrega" → "Dinheiro"
  Então aparece campo "Precisa de troco? Para quanto?"
  E ao confirmar, o pedido é gravado com status CONFIRMED e payment_method=cash
  E o restaurante vê o pedido no painel

Cenário: Pagamento MP retorna com falha
  Dado que o usuário foi redirecionado para o MP e o pagamento falhou
  Quando o MP redireciona para a URL de failure
  Então o usuário vê mensagem de falha com opção de tentar novamente
  E o pedido permanece em status PENDING (não é cancelado automaticamente)
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 — Localização antes do catálogo | Should | Melhora UX mas não bloqueia o pedido; pode ser fase 2 |
| RF-02/RF-05 — Modal de auth + cadastro tradicional | Must | Elimina guest checkout; bloqueia pagamento sem conta |
| RF-03 — Login Google | Must | Principal método social; requer client_id + secret |
| RF-04 — Login Apple | ~~Should~~ | **Descartado** — exige Apple Developer Account indisponível |
| RF-06 — Associação de carrinho | Must | Crítico para continuidade pós-login |
| RF-07/RF-08 — Checkout Pro + Webhook | Must | Substitui PIX QR Code; habilita cartão de crédito |
| RF-09/RF-10 — Pagamento na entrega | Must | Nova fonte de receita; independente do MP |
| RF-11 — Notificação do manager | Must | Restaurante precisa saber do pedido offline |
| RF-12 — Carrinho persistido em banco | Should | Conforto UX; sessão Django já persiste em Redis |
| RF-13 — Recuperação de senha | Must | Requisito mínimo de segurança para cadastro com senha |
| RF-11 — Notificação real-time | Should | Polling existente já parcialmente cobre |

## 9. Esclarecimentos

| # | Dúvida | Resposta | Data |
|---|--------|----------|------|
| D01 | JWT vs Session — app web ou mobile? | **App web atual (HTMX)**. Usar sessão Django em todo o fluxo. `django-allauth` cria sessão padrão no login Google. Sem JWT. | 2026-05-30 |
| D02 | Apple Sign-In disponível? | **Não**. RF-04 descartado permanentemente. Apenas Google. | 2026-05-30 |
| D03 | Feature única ou fatiada? | **Fatiada em features separadas**: 011-A auth-social-checkout, 011-B checkout-pro-mp, 011-C pagamento-entrega. | 2026-05-30 |

## 10. Lacunas

Nenhuma lacuna pendente.

**Sub-features derivadas desta spec-mãe:**

| Sub-feature | Escopo | Próximo passo |
|-------------|--------|---------------|
| `011-A` auth-social-checkout | Modal de identificação no checkout + Google OAuth2 + cadastro tradicional + recuperação de senha | Criar com `/reversa-requirements` |
| `011-B` checkout-pro-mp | Checkout Pro MP (preference + redirect + webhook) substituindo PIX QR Code | Criar após 011-A |
| `011-C` pagamento-entrega | Pagamento na entrega: dinheiro (troco) + cartão; novo status CONFIRMED | Criar após 011-B |
| `011-D` localizacao-pre-catalogo | Solicitar endereço/GPS antes de exibir o catálogo | Pode rodar em paralelo com 011-A |

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-05-30 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-05-30 | D01/D02/D03 resolvidos: app web, sem Apple, fatiado em 4 sub-features | Pablo |
