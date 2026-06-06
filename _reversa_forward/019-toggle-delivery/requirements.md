# Requirements: Toggle Delivery — Loja Aberta/Fechada

> Identificador: `019-toggle-delivery`
> Data: `2026-06-04`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

---

## 1. Resumo executivo

O manager precisa de um interruptor para pausar o recebimento de pedidos online quando o restaurante estiver fechado ou indisponível. Com a loja "fechada", o cliente vê um aviso claro no catálogo e no carrinho, e o checkout é bloqueado. O manager ativa/desativa pelo painel com um clique — sem precisar alterar nenhuma configuração técnica. Quando a loja volta a aceitar pedidos, basta religar o toggle.

Atende a pedido explícito do cliente final (dono do restaurante) com uso imediato e recorrente — toda noite ou nos dias de folga.

---

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/architecture.md#Domínio de Negócio` | `Store.is_active` — controla se a loja existe no sistema, mas não é o mecanismo correto para "fechado temporariamente" (desativar via is_active remove a loja do TenantMiddleware) | 🟢 |
| `_reversa_sdd/domain.md#RN-02` | Tenant resolvido por subdomain; `is_active=False` retorna `DoesNotExist` no middleware — não é reversível com facilidade pelo manager | 🟢 |
| `_reversa_sdd/architecture.md#ADR-005` | Guest checkout em `views.checkout()` — ponto de bloqueio natural para a nova regra | 🟢 |
| `core/models.py#Store` | `Store` já tem `delivery_fee`, `free_delivery_threshold`, `is_active` — padrão de campo de configuração simples no modelo | 🟢 |
| `core/forms.py#StoreSettingsForm` | `StoreSettingsForm` já expõe campos de configuração da loja; padrão para adicionar novo campo | 🟢 |
| `core/context_processors.py` | Context processor `cart()` já expõe dados da loja a todos os templates — ponto ideal para expor `delivery_enabled` | 🟢 |
| `_reversa_sdd/architecture.md#Princípios` | Princípio III: configuração simples, operação autônoma — o toggle deve estar a um clique no painel, sem variável de ambiente | 🟢 |

---

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Manager (dono do restaurante) | Fechar o delivery rapidamente ao fim do expediente | Acessa o dashboard, clica "Fechar loja" — imediatamente nenhum novo pedido entra |
| Manager | Reabrir pela manhã | Clica "Abrir loja" no dashboard — catálogo volta ao normal para os clientes |
| Cliente (guest ou autenticado) | Tentar fazer um pedido com a loja fechada | Vê banner "Não estamos aceitando pedidos no momento" no catálogo e carrinho bloqueado |

---

## 4. Regras de negócio novas ou alteradas

1. **RN-019-01:** O modelo `Store` recebe campo `delivery_enabled = BooleanField(default=True)`. Quando `False`, a loja não aceita novos pedidos online. 🟢
   - Tipo: nova
   - **Diferença de `is_active`:** `is_active=False` remove a loja do sistema inteiro (middleware retorna 404). `delivery_enabled=False` mantém a loja visível — clientes podem navegar no catálogo, mas não conseguem finalizar pedido.

2. **RN-019-02:** `views.checkout()` verifica `request.tenant.delivery_enabled` antes de processar qualquer pedido. Se `False`, retorna erro no drawer do carrinho: "A loja não está aceitando pedidos no momento." 🟢
   - Tipo: nova
   - Aplica-se a todos os métodos de pagamento (online, dinheiro, cartão).

3. **RN-019-03:** O catálogo (`/catalog/` e `/`) exibe banner de aviso quando `delivery_enabled=False`. O banner não impede a navegação — o cliente pode continuar vendo o cardápio. 🟢
   - Tipo: nova

4. **RN-019-04:** O drawer do carrinho exibe aviso e desabilita o botão "Confirmar Pedido" quando `delivery_enabled=False`. 🟢
   - Tipo: nova

5. **RN-019-05:** O manager pode alternar `delivery_enabled` diretamente pelo dashboard (botão de toggle rápido) **e** pela tela de configurações da loja. O toggle do dashboard é a ação principal — não exige salvar um formulário inteiro. 🟢
   - Tipo: nova

6. **RN-019-06:** O `delivery_enabled` é exposto a todos os templates via context processor `cart()` já existente, adicionando a chave `delivery_enabled` ao dict retornado. 🟡
   - Tipo: nova

---

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Campo `delivery_enabled` no modelo `Store`, `default=True`, com migration | Must | Campo existe no banco; loja existente mantém `True` após migration | 🟢 |
| RF-02 | `views.checkout()` bloqueia pedido quando `store.delivery_enabled=False`, retornando erro no drawer | Must | POST em `/checkout/` com loja fechada retorna o drawer com mensagem de erro, sem criar Order | 🟢 |
| RF-03 | Banner de aviso no catálogo e na home quando `delivery_enabled=False` | Must | Banner visível e legível; não bloqueia navegação | 🟢 |
| RF-04 | Drawer do carrinho exibe aviso e botão "Confirmar Pedido" desabilitado quando `delivery_enabled=False` | Must | Botão com `disabled` e mensagem clara; usuário não consegue submeter o form | 🟢 |
| RF-05 | Botão de toggle rápido no dashboard do manager ("Abrir loja" / "Fechar loja") que alterna `delivery_enabled` via POST sem recarregar a página inteira | Must | Um clique alterna o estado; feedback visual imediato; sem formulário completo | 🟢 |
| RF-06 | Campo `delivery_enabled` exposto no `StoreSettingsForm` como alternativa ao toggle rápido | Should | Checkbox visível na tela de configurações; salva junto com os demais campos | 🟢 |
| RF-07 | `delivery_enabled` disponível em todos os templates via context processor | Must | `{{ delivery_enabled }}` acessível em qualquer template sem passar explicitamente | 🟡 |

---

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Usabilidade | Toggle rápido no dashboard — a um clique, sem navegação extra | Princípio III: operação autônoma | 🟢 |
| Segurança | A view do toggle rápido exige `is_staff` ou `owned_store == tenant` (mesmo guard usado em `views.dashboard`) | `_reversa_sdd/domain.md#RN-12` — controle binário de Manager | 🟢 |
| Consistência visual | Banner de "loja fechada" usa padrão visual do sistema (Tailwind, dark mode compatível) | `_reversa_sdd/architecture.md#Tematização` | 🟡 |
| Retrocompatibilidade | Migration com `default=True` garante que lojas existentes continuam abertas sem intervenção | `core/models.py#Store` | 🟢 |

---

## 7. Critérios de Aceitação

```gherkin
Cenário: Manager fecha a loja pelo dashboard
  Dado que o manager está logado e a loja está aberta (delivery_enabled=True)
  Quando clica em "Fechar loja" no dashboard
  Então delivery_enabled vira False no banco
  E o botão muda para "Abrir loja" imediatamente

Cenário: Cliente tenta pedir com loja fechada
  Dado que delivery_enabled=False
  Quando o cliente acessa o catálogo
  Então vê o banner "Não estamos aceitando pedidos no momento"
  E o drawer do carrinho exibe aviso e botão "Confirmar Pedido" desabilitado

Cenário: Cliente tenta forçar checkout via POST com loja fechada
  Dado que delivery_enabled=False
  Quando o cliente faz POST direto em /checkout/
  Então recebe o drawer com mensagem de erro e nenhum Order é criado no banco

Cenário: Manager reabre a loja
  Dado que delivery_enabled=False
  Quando clica em "Abrir loja" no dashboard
  Então delivery_enabled vira True
  E clientes voltam a conseguir fazer pedidos imediatamente

Cenário: Configuração via tela de Settings
  Dado que o manager está na tela de configurações da loja
  Quando desmarca o checkbox "Aceitar pedidos online" e salva
  Então delivery_enabled vira False com o mesmo efeito do toggle rápido
```

---

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 — Campo no model + migration | Must | Base de tudo |
| RF-02 — Bloqueio no checkout | Must | Segurança: sem isso cliente burla a UI |
| RF-03 — Banner no catálogo | Must | Feedback claro para o cliente final |
| RF-04 — Drawer desabilitado | Must | UX: o cliente vê o motivo antes de tentar |
| RF-05 — Toggle rápido no dashboard | Must | Operação cotidiana do dono do restaurante |
| RF-07 — Context processor | Must | Dependência técnica dos demais RF |
| RF-06 — Campo no StoreSettingsForm | Should | Alternativa; toggle rápido já cobre o caso |

---

## 9. Esclarecimentos

> Nenhuma sessão de dúvidas registrada ainda.

---

## 10. Lacunas

Nenhuma dúvida bloqueante. Decisão de escopo tomada:
- `delivery_enabled=False` bloqueia **todos** os métodos de pedido online (dinheiro, cartão, pix) — não só o pagamento online. Justificativa: "loja fechada" significa que não há ninguém para preparar ou entregar nada.

---

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-04 | Versão inicial gerada por `/reversa-requirements` | reversa |
