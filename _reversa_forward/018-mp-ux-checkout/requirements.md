# Requirements: MP UX Checkout — Nova Aba + Rastreio para Guest

> Identificador: `018-mp-ux-checkout`
> Data: `2026-06-04`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

---

## 1. Resumo executivo

A feature resolve dois problemas de UX no fluxo de pagamento online via MercadoPago:

1. **Redirecionamento destrutivo**: ao clicar em "Confirmar Pedido" com método online, o app faz `window.location.href = init_point`, navegando para fora da loja e abandonando o contexto da sessão. O correto é abrir o MP em nova aba, mantendo na aba original uma tela de espera que exibe o status do pedido em polling.

2. **Guest sem visibilidade pós-checkout**: após voltar do MP (seja por sucesso, falha ou abandono), o cliente não-autenticado não tem nenhuma tela dedicada mostrando seu pedido. Ele recebe a mesma devolução que usuários cadastrados — mas apenas na tela de sucesso. Nas telas de falha e pending o order não é carregado, e não há tela de espera que o oriente enquanto o MP está aberto. Guests devem ter a mesma rastreabilidade de pedido que usuários autenticados.

---

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/flowcharts/core-checkout.md#invariantes` | `return script → init_point` — navegação full-page fora do app | 🟢 |
| `_reversa_sdd/flowcharts/core-payment.md#create_checkout_pro_preference` | `back_urls: success/pending/failure` + `auto_return: approved` — retorno configurado no MP | 🟢 |
| `_reversa_sdd/domain.md#RN-05` | `session['guest_order_id'] = order.id` — único vínculo do pedido guest com a sessão | 🟢 |
| `_reversa_sdd/domain.md#RN-16` | `/order/{id}/track/` já existe com polling HTMX a cada 5s | 🟢 |
| `_reversa_sdd/architecture.md#ADR-005` | Guest checkout com vinculação pós-signup; sessão guarda apenas um `guest_order_id` | 🟢 |
| `core/views.py#payment_success_view` | Carrega order via `preference_id` ou `session['guest_order_id']`; mas `payment_failure_view` e `payment_pending_view` não carregam order | 🟢 |
| `core/views.py#checkout` | `HttpResponse('<script>window.location.href="{init_point}";</script>')` — saída full-page | 🟢 |

---

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Cliente guest | Pagar com MP e saber o que aconteceu com o pedido | Abre MP em nova aba, paga, fecha a aba, e a tela do app já mostra o pedido confirmado |
| Cliente guest — falha | Tentar pagar, ter cartão recusado no MP, voltar ao app | Fecha a aba do MP, vê tela de espera informando falha, com link para rastrear/tentar novamente |
| Cliente autenticado | Pagar com MP sem perder o contexto do app | Idem ao guest: nova aba para MP, aba original não some |
| Cliente guest — abandono | Abrir MP, não pagar, fechar a aba | Tela de espera detecta timeout e exibe status atual (PENDING) com instrução |

---

## 4. Regras de negócio novas ou alteradas

1. **RN-018-01:** Ao gerar o `init_point` do Checkout Pro, o frontend deve abrir a URL em nova aba (`window.open(url, '_blank')`) em vez de navegar na aba atual. 🟢
   - Origem no legado: `core/views.py:278` — `window.location.href`
   - Tipo: alterada

2. **RN-018-02:** Após abrir a nova aba do MP, a aba original exibe uma tela de espera (`/payment/waiting/?order_id=<id>`) com polling do status do pedido a cada 5s via HTMX. Quando o status mudar de PENDING para qualquer outro, a tela exibe o resultado final. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#RN-16` — polling já existe em `/order/{id}/track/`
   - Tipo: nova

3. **RN-018-03:** A tela de espera é acessível sem autenticação e identifica o pedido por `order_id` via query string. Guest identifica o pedido via `session['guest_order_id']` (já persiste hoje) ou via `order_id` explícito na URL. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#RN-05`
   - Tipo: nova

4. **RN-018-04:** As `back_urls` do MP já existem (`success`, `pending`, `failure`). As views correspondentes devem carregar o order em todos os três casos — não apenas em success — e exibir o link de rastreio e status adequado. 🟡
   - Origem no legado: `core/views.py#payment_pending_view` e `payment_failure_view` não carregam order hoje
   - Tipo: alterada

5. **RN-018-05:** A tela de espera detecta quando a aba do MP é fechada (via `window.opener` ou `postMessage`) e, se o status ainda for PENDING após fechar, exibe aviso "Aguardando confirmação do MercadoPago…" com link para rastrear. 🟡
   - Tipo: nova

---

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Ao confirmar pedido online, o frontend abre o `init_point` em nova aba em vez de navegar na aba atual | Must | A aba do app permanece aberta com a tela de espera; nova aba abre no MP | 🟢 |
| RF-02 | A tela de espera em `/payment/waiting/` exibe o número do pedido e faz polling a cada 5s via HTMX | Must | O status atualiza visualmente sem recarregar a página inteira | 🟢 |
| RF-03 | Quando o status muda de PENDING, a tela de espera reflete o novo estado (PREPARING, CANCELED) e para o polling | Must | Após webhook MP aprovar, a tela exibe "Pedido confirmado!" sem interação do usuário | 🟢 |
| RF-04 | As views `payment_failure_view` e `payment_pending_view` carregam o order associado ao `preference_id` ou `external_reference` | Must | Guest acessa `/payment/failure/?preference_id=X` e vê o pedido + link de rastreio | 🟢 |
| RF-05 | Guest vê link para `/order/{id}/track/` em todas as telas de retorno do MP (success, pending, failure, waiting) | Must | Link está visível e funcional sem login | 🟢 |
| RF-06 | A tela de espera tem botão "Já paguei — verificar agora" que força polling imediato | Should | Clique atualiza status sem aguardar os 5s | 🟡 |
| RF-07 | Se a nova aba do MP for fechada sem pagamento confirmado e o status ainda for PENDING, a tela de espera exibe aviso e instrução | Should | Aviso: "Não recebemos confirmação. Verifique se o pagamento foi concluído." com link para rastrear | 🟡 |

---

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Segurança | A tela de espera e as views de retorno do MP não expõem dados sensíveis (valor, endereço) sem sessão associada | Proteção equivalente ao `/order/{id}/track/` existente (público, mas mínimo) | 🟢 |
| Compatibilidade | `window.open` funciona em todos os browsers modernos; verificar se bloqueadores de popup interferem — fornecer fallback com link clicável | `_reversa_sdd/architecture.md#Stack` — HTMX + Hyperscript em uso | 🟡 |
| Observabilidade | Log de warning quando `payment_failure_view` não encontra order via `preference_id` | Padrão do projeto: `logger.warning` em `core/views.py` | 🟢 |

---

## 7. Critérios de Aceitação

```gherkin
Cenário: Guest paga com sucesso no MP (nova aba)
  Dado que um guest preencheu o checkout e selecionou "Pagar Online"
  Quando clica em "Confirmar Pedido"
  Então uma nova aba abre com a URL do MercadoPago
  E a aba original exibe a tela de espera com o número do pedido
  E o polling HTMX atualiza o status a cada 5s
  Quando o webhook do MP aprova o pagamento
  Então a tela de espera exibe "Pedido confirmado!" com link para rastrear

Cenário: Guest falha no pagamento e volta ao app
  Dado que um guest foi redirecionado para o MP em nova aba
  Quando o pagamento é recusado e o MP redireciona para /payment/failure/
  Então a tela de failure exibe o número do pedido e link para /order/{id}/track/

Cenário: Guest fecha a aba do MP sem pagar
  Dado que a tela de espera está ativa em polling
  Quando a aba do MP é fechada e o status ainda é PENDING
  Então a tela de espera exibe aviso "Aguardando confirmação do MercadoPago"
  E exibe link para rastrear o pedido

Cenário: Popup bloqueado pelo browser
  Dado que o browser do usuário bloqueia popups
  Quando o checkout tenta abrir nova aba e falha
  Então a tela exibe link clicável "Clique aqui para abrir o MercadoPago" como fallback

Cenário: Usuário autenticado — comportamento equivalente
  Dado que um usuário logado confirmou pedido online
  Quando o MP abre em nova aba
  Então o fluxo é idêntico ao do guest: tela de espera + polling + link de rastreio
```

---

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 — Abre MP em nova aba | Must | Evita perda de sessão e contexto do app; melhoria crítica de UX |
| RF-02 — Tela de espera com polling | Must | Substitui a navegação saindo do app; necessária para RF-01 funcionar |
| RF-03 — Polling reflete status final | Must | Sem isso a tela de espera não tem utilidade |
| RF-04 — Failure/pending carregam order | Must | Guest sem order nas telas de falha = sem nenhuma rastreabilidade |
| RF-05 — Link de rastreio para guest em todas as telas | Must | Paridade com usuário autenticado |
| RF-06 — Botão "Já paguei — verificar agora" | Should | Melhora UX mas não bloqueia o fluxo |
| RF-07 — Detecção de fechamento da aba | Should | Útil mas complexidade extra; polling eventual cobre o caso |

---

## 9. Esclarecimentos

> Nenhuma sessão de dúvidas registrada ainda. Rode `/reversa-clarify` quando houver `[DÚVIDA]` pendente.

---

## 10. Lacunas

- 🟡 [DÚVIDA] A detecção de fechamento de aba via `window.opener` ou `BroadcastChannel` depende de ambas as abas serem na mesma origem — confirmar se o `init_point` do sandbox MP é origin diferente (esperado: sim, MP é externo, portanto detecção cross-origin não é possível via `postMessage`). Solução alternativa: timeout no polling (ex.: 10min sem mudança de status exibe aviso).

---

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-04 | Versão inicial gerada por `/reversa-requirements` | reversa |
