# Investigation: MP UX Checkout — Nova Aba + Rastreio para Guest

> Feature: `018-mp-ux-checkout`
> Data: `2026-06-04`

---

## Problema 1 — Abertura do MP em nova aba

### Por que `window.open` dentro de submit não é bloqueado por popup blockers?

Browsers bloqueiam `window.open` apenas quando **não há gesto do usuário** na call stack. Um submit de formulário é gesto direto do usuário. O script retornado pelo servidor é executado pelo HTMX dentro do swap, que ocorre na thread da resposta ao clique — ainda dentro do gesto. Browsers modernos (Chrome, Firefox, Safari) permitem.

**Evidência:** MDN — "Popups opened synchronously during user gesture are not blocked."

**Risco residual:** Popup blockers de extensão (uBlock, Brave Shield) são mais agressivos e podem bloquear mesmo com gesto. Mitigação: verificar retorno de `window.open` e exibir link de fallback se `null`.

```javascript
// Padrão defensivo a usar no script de resposta:
const mp = window.open(init_point, '_blank');
if (!mp) {
  // Fallback: renderizar link clicável na tela de espera
}
window.location.href = '/payment/waiting/?order_id=' + order_id;
```

---

## Problema 2 — HTMX polling com encerramento

### Como parar o polling quando o status muda?

HTMX suporta duas estratégias para parar um polling:

**Opção A — `HX-Trigger: stopPolling` no response header:**
```python
response = render(request, 'partial.html', ctx)
if status_changed:
    response['HX-Trigger'] = 'stopPolling'
return response
```
O elemento deve ter `hx-trigger="every 5s, stopPolling"`. Quando o header chega, HTMX dispara o evento e encerra o ciclo.

**Opção B — Retornar corpo vazio com `hx-swap="none"`:**
Não encerra o polling — HTMX vai continuar tentando.

**Opção C — Remover o elemento de polling via `hx-swap-oob="true"` com target vazio:**
Funciona mas é mais verboso.

**Escolha:** Opção A é a mais limpa e documentada. `HX-Trigger: stopPolling` + `hx-trigger="every 5s, stopPolling from:body"` no elemento.

---

## Problema 3 — "Aba fechada sem pagar" — detecção cross-origin

### Por que `window.opener` e `BroadcastChannel` não funcionam?

`window.opener` é `null` quando a aba filha é aberta com `rel="noopener"` ou via `window.open` com `noopener` nas features. Mesmo sem isso, acessar `window.opener` da aba do MP (domínio externo) para sinalizar de volta é bloqueado pela same-origin policy.

`BroadcastChannel` e `localStorage` events funcionam apenas entre tabs/frames da **mesma origem**. `mercadopago.com.br` ≠ `localhost`/`domínio da loja`.

**Conclusão:** Detecção de fechamento cross-origin não é viável no browser sem infraestrutura server-side adicional. A abordagem de **polling com timeout visual** (após 10 min sem mudança, exibir aviso) é a solução correta para este produto.

---

## Padrão de identificação de pedido na tela de espera

A tela `/payment/waiting/` precisa identificar o pedido sem exigir login. Três fontes possíveis:

| Fonte | Disponibilidade | Prioridade |
|-------|----------------|------------|
| `?order_id=` na URL (colocado pelo checkout) | Sempre presente no fluxo normal | 1ª |
| `session['guest_order_id']` | Presente se a sessão não foi perdida | 2ª |
| `?preference_id=` (enviado pelo MP nas back_urls) | Presente nas telas success/failure/pending | 1ª para essas telas |

O checkout redirect para `/payment/waiting/?order_id={order.id}` garante que o `order_id` sempre esteja na URL — não dependemos apenas da sessão.

---

## Alternativas de UX avaliadas e descartadas

| Alternativa | Por que descartada |
|-------------|-------------------|
| Redirect full-page para MP (comportamento atual) | Usuário perde contexto do app; guest perde `session['guest_order_id']` se browser não preserva sessão em nova aba | 
| Embed MP em iframe | MP proíbe via `X-Frame-Options: DENY` na resposta | 
| Modal/drawer com iframe | Mesmo problema do iframe acima | 
| WebSocket para push de status | Exigiria refactor de ASGI + infra de channels; overkill para este produto | 
| SSE (Server-Sent Events) | Possível com FastAPI, mas adiciona endpoint novo e complexidade; polling HTMX já resolve com menos código |
