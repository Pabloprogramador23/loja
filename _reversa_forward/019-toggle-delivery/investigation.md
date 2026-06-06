# Investigation: Toggle Delivery

> Feature: `019-toggle-delivery`
> Data: `2026-06-04`

---

## Por que não reutilizar `Store.is_active`?

`Store.is_active` é lido pelo `TenantMiddleware` em `Store.objects.get(subdomain=..., is_active=True)`. Se `is_active=False`, o middleware levanta `DoesNotExist` e o request falha com 404/500 — a loja desaparece inteiramente do sistema. Não é reversível pelo manager via UI (exige acesso ao Django Admin).

`delivery_enabled` tem semântica diferente: a loja continua existindo e visível, apenas para de aceitar pedidos. Clientes ainda podem navegar no cardápio.

---

## Padrão de toggle HTMX já existente no projeto

`views.update_order_status` (`core/views.py`) é o padrão de referência:
- Recebe `POST` com novo status
- Atualiza o model
- Retorna partial HTMX `order_row.html` com o novo estado

`toggle_delivery_view` seguirá exatamente o mesmo padrão:
- Recebe `POST` sem body (o toggle sabe o estado atual via `store.delivery_enabled`)
- Faz `store.delivery_enabled = not store.delivery_enabled; store.save(update_fields=['delivery_enabled'])`
- Retorna partial `delivery_toggle.html` com o novo estado do botão

---

## Alternativas de UX para o banner de "loja fechada" avaliadas

| Alternativa | Prós | Contras | Decisão |
|-------------|------|---------|---------|
| Banner fixo no topo do catálogo | Visível imediatamente | Ocupa espaço sempre | ✅ Adotada |
| Overlay com blur sobre o catálogo | Impacto visual forte | Bloqueia navegação, UX agressiva | ❌ |
| Página de erro 503 | Simples | Corta a vitrine; cliente não vê o cardápio | ❌ |
| Toast/notificação temporária | Não intrusivo | Some após alguns segundos, cliente pode não ver | ❌ |

---

## Alternativas de implementação do toggle descartadas

| Alternativa | Por que descartada |
|-------------|-------------------|
| Agendamento por horário de funcionamento | Escopo não pedido; aumenta complexidade com timezone/DST/feriados |
| Variável de ambiente `DELIVERY_ENABLED=false` | Exige restart do servidor; viola Princípio III |
| Feature flag via Redis/cache | Over-engineering; loja pequena, BooleanField no DB é suficiente e persistente |
| Toggle via Django Admin | Manager não tem acesso; exige conhecimento técnico |
