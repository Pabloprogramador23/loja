# Roadmap: MP UX Checkout — Nova Aba + Rastreio para Guest

> Identificador: `018-mp-ux-checkout`
> Data: `2026-06-04`
> Requirements: `_reversa_forward/018-mp-ux-checkout/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

---

## 1. Resumo da abordagem

A feature é um **delta cirúrgico em três frentes**, sem alteração de modelo de dados:

**Frente A — Nova aba para MP:** A resposta do `checkout()` hoje emite `<script>window.location.href="{init_point}";</script>`, navegando a página inteira para fora do app. A mudança é trocar para `window.open(init_point, '_blank'); window.location.href='/payment/waiting/?order_id={id}';` — duas linhas de script. O `order_id` precisa ser incluído na resposta do checkout (já está disponível no objeto `order` criado na view).

**Frente B — Tela de espera com polling:** Nova view `payment_waiting_view` em `/payment/waiting/` + partial de status `/payment/waiting/status/` servindo HTMX polling a cada 5s. A partial retorna o fragmento de status; quando o status deixa de ser `PENDING`, ela inclui `HX-Reswap: none` e `HX-Trigger: stopPolling` para encerrar o ciclo. Sem auth. Identifica o pedido por `?order_id=` (fallback: `session['guest_order_id']`).

**Frente C — Telas de retorno do MP corrigidas:** `payment_failure_view` e `payment_pending_view` passam a carregar o `Order` da mesma forma que `payment_success_view` já faz — por `preference_id` → fallback `external_reference` → fallback `session['guest_order_id']`. Templates atualizados para exibir link de rastreio.

A detecção de "aba fechada sem pagar" é resolvida por **timeout visual no polling** (após 10 min sem mudança de status PENDING, a tela de espera exibe aviso passivo) — abordagem mais simples e alinhada ao Princípio IV, descartando `BroadcastChannel` / `window.opener` cross-origin.

---

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Utilidade antes de completude | Problema real relatado pelo usuário Pablo: guest perde o rastro do pedido; a tela some após redirect. Uso imediato. | respeita |
| II. Integrações essenciais apenas | Não adiciona nenhuma integração. Usa MercadoPago que já existe; muda apenas o comportamento de abertura. | respeita |
| III. Configuração simples, operação autônoma | Sem nova configuração necessária. O dono da loja não precisa mudar nada. | respeita |
| IV. Produto focado, não showcase | Descartado `BroadcastChannel` / `PostMessage` cross-origin. Polling simples + timeout visual resolve o caso. Solução mais simples foi adotada. | respeita |

---

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Usar `window.open` + redirect para `/payment/waiting/` no mesmo script de resposta HTMX | A resposta do checkout já é um `<script>` inline dentro do swap HTMX. Adicionar a segunda instrução não exige nova rota nem refactor. | Retornar `HX-Redirect` com header (exigiria refactor para separar a URL do script) | 🟢 |
| D-02 | Polling via HTMX na tela de espera (`hx-trigger="every 5s"`) | Padrão já usado em `/order/{id}/track/` (`_reversa_sdd/domain.md#RN-16`). Consistência com o legado. | WebSocket, SSE, long-polling (todos exigem infra extra ou mudança de arquitetura ASGI) | 🟢 |
| D-03 | Encerrar polling com `HX-Trigger: stopPolling` quando status muda | HTMX suporta parar polling via evento; alternativa seria `hx-swap-oob` para remover o elemento de polling — menos legível | Retornar corpo vazio (HTMX continua polling de qualquer forma sem instrução explícita) | 🟡 |
| D-04 | Timeout visual de 10 minutos para "aba fechada sem pagar" | MP expira preferências em 30 min. 10 min é seguro como aviso passivo. Elimina necessidade de JS cross-origin. | `BroadcastChannel` (mesma origin apenas), `window.opener` (bloqueado em nova aba sem `rel=opener`) | 🟡 |
| D-05 | `payment_waiting_view` identifica pedido por `?order_id=` com fallback `session['guest_order_id']` | Mesma lógica já usada em `payment_success_view`. Sem nova lógica de sessão. | Token único na URL (exigiria campo novo no model) | 🟢 |
| D-06 | `back_urls` do MP não mudam | MP já redireciona para `/payment/success/`, `/payment/pending/`, `/payment/failure/`. Essas views serão melhoradas, não substituídas. Rotas existentes permanecem. | Mudar `back_urls` para `/payment/waiting/` (exigiria lógica de status condicional lá, mais complexo) | 🟢 |

---

## 4. Premissas

| Premissa | Origem (`requirements.md` seção) | Risco se errada |
|----------|----------------------------------|-----------------|
| `window.open` funciona sem bloqueio de popup, pois é disparado dentro de um handler de clique de formulário (evento de usuário) | Seção 6 — RNF Compatibilidade | Se bloqueado, fallback de link clicável (RF-07) cobre; tela de espera ainda carrega | 🟡 |
| Detecção de fechamento de aba via cross-origin não é viável; polling com timeout é suficiente | Seção 10 — Lacuna `[DÚVIDA]` | Se usuário não voltar à aba original, simplesmente não vê o update — aceitável para este produto | 🟡 |

---

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `views.checkout` | `core/views.py:278` | regra-alterada | Script de resposta muda de redirect full-page para nova-aba + redirect para `/payment/waiting/` |
| `views.payment_failure_view` | `core/views.py:312` | regra-alterada | Passa a carregar `Order` por `preference_id` / `external_reference` |
| `views.payment_pending_view` | `core/views.py:307` | regra-alterada | Idem |
| `views.payment_waiting_view` | — | componente-novo | View pública; renderiza tela de espera com `order_id` |
| `views.payment_waiting_status_view` | — | componente-novo | Partial HTMX; retorna fragmento de status; encerra polling quando status muda |
| `core/urls.py` | `core/urls.py` | contrato-novo | Duas novas rotas: `/payment/waiting/` e `/payment/waiting/status/` |
| `templates/core/payment_waiting.html` | — | componente-novo | Tela de espera com número do pedido, polling HTMX, botão "Já paguei" |
| `templates/core/partials/cart_drawer.html` | `templates/core/partials/cart_drawer.html:62` | regra-alterada | Script inline: `window.location.href` → `window.open` + redirect |
| `templates/core/payment_failure.html` | `templates/core/payment_failure.html` | regra-alterada | Adiciona bloco de order + link de rastreio |
| `templates/core/payment_pending.html` | `templates/core/payment_pending.html` | regra-alterada | Idem |

---

## 6. Delta no modelo de dados

- **Sem alteração de modelo.** Nenhum campo novo, nenhuma migration necessária.
- O `order_id` já é salvo na sessão (`session['guest_order_id']`) e disponível no objeto `Order` criado no checkout.
- Detalhe completo em: `_reversa_forward/018-mp-ux-checkout/data-delta.md`

---

## 7. Delta de contratos externos

| Contrato | Tipo | Arquivo de detalhe |
|----------|------|--------------------|
| MercadoPago — `back_urls` (sem alteração de contrato, apenas documentação) | HTTP | `_reversa_forward/018-mp-ux-checkout/interfaces/mercadopago-backurls.md` |

---

## 8. Plano de migração

Sem migração de banco. Deploy é zero-downtime:

1. Deploy das novas views e templates (adição pura, sem remoção)
2. Adicionar rotas novas em `urls.py`
3. Ajustar script no `cart_drawer.html` — mudança de comportamento de frontend, sem quebra de contrato de backend
4. Ajustar `payment_failure_view` e `payment_pending_view` — backward-compatible (se `preference_id` não vier na query, fallback já existe)

---

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Browser bloqueia `window.open` antes do submit do formulário (popup blocker) | médio | baixo | Script disparado dentro de evento de submit (usuário clicou); browsers modernos permitem. Fallback: exibir link clicável se `window` retornar `null` | 
| `session['guest_order_id']` não está disponível quando guest acessa `/payment/waiting/` diretamente (ex: link externo) | baixo | baixo | A view tenta `?order_id=` primeiro; o `order_id` sempre está na URL do redirect feito pelo checkout |
| Polling mantém conexão por 10 min; impacto em recursos do servidor | baixo | baixo | Uma request a cada 5s é negligenciável; sem estado server-side no polling |
| `HX-Trigger: stopPolling` requer que o elemento tenha `hx-trigger="stopPolling"` declarado — combinação específica de HTMX | médio | médio | Documentar e testar. Alternativa de fallback: `hx-swap="delete"` no encerramento |

---

## 10. Critério de pronto

- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] Checkout online abre MP em nova aba e mantém o app aberto na tela de espera
- [ ] Tela de espera exibe status atualizado via polling sem recarregar a página
- [ ] `/payment/failure/` e `/payment/pending/` exibem número do pedido e link de rastreio para guest
- [ ] `regression-watch.md` gerado
- [ ] Testado manualmente no fluxo mock (token TEST-0000): nova aba abre `/payment/mock/`, polling detecta PREPARING

---

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-04 | Versão inicial gerada por `/reversa-plan` | reversa |
