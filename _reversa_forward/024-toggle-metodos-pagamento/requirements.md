# Requirements: Toggle de Métodos de Pagamento

> Identificador: `024-toggle-metodos-pagamento`
> Data: `2026-06-08`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

---

## 1. Resumo executivo

O dono do restaurante precisa decidir, a qualquer momento, quais formas de pagamento aceita. Hoje o sistema oferece três métodos — **MercadoPago online** (`online`), **Dinheiro na entrega** (`cash`) e **Cartão na maquininha** (`card`) — mas todos ficam sempre disponíveis, sem controle por loja. A feature adiciona ao painel do manager um painel de toggles onde ele marca quais métodos quer ativar no dia, podendo combinar livremente (ex.: "só MP", "MP + cartão", "tudo"). O checkout apresenta apenas as opções ativas; métodos desativados ficam invisíveis ao cliente. Se o manager desativar todos, o checkout é bloqueado com aviso claro.

---

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/code-analysis.md#2.7-checkout` | `payment_method` lido do POST como `online\|cash\|card`; ramificação explícita por método | 🟢 |
| `core/models.py#PaymentMethod` | `TextChoices` com três valores: `online` (MP), `cash` (Dinheiro), `card` (Cartão na Maquininha) | 🟢 |
| `core/models.py#Store` | `delivery_enabled`, `delivery_fee`, `mercadopago_access_token` — padrão de campos de configuração por tenant já existente | 🟢 |
| `core/forms.py#StoreSettingsForm` | `StoreSettingsForm` com `fields = [..., 'delivery_enabled']` — padrão de exposição de configs no formulário de settings | 🟢 |
| `_reversa_sdd/domain.md#RN-09` | Token MP resolvido por tenant — `online` só faz sentido habilitado se `mercadopago_access_token` estiver configurado | 🟢 |
| `_reversa_forward/019-toggle-delivery` | Feature gêmea: toggle de `delivery_enabled` seguiu padrão campo booleano no Store + context processor + guard no checkout | 🟢 |
| `_reversa_sdd/domain.md#RN-12` | Acesso ao dashboard exige `is_staff` ou `owned_store == tenant` — guard reutilizável para a view dos toggles | 🟢 |

---

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Manager (dono do restaurante) | Aceitar só MP hoje porque a maquininha está com defeito | Abre o painel, desmarca "Dinheiro" e "Cartão", salva — checkout mostra só PIX |
| Manager | Fim de semana movimentado: aceitar tudo | Todos os três toggles marcados — cliente escolhe como quiser |
| Manager | Só pagamento antecipado: desabilita cash e card | Não quer lidar com troco nem maquininha na correria do almoço |
| Cliente (autenticado ou guest) | Quer pagar no dinheiro mas método está desativado | Vê apenas as opções disponíveis — sem surpresa no checkout |
| Cliente | Tenta forçar método desativado via POST direto | Backend rejeita com mensagem de erro, sem criar pedido |

---

## 4. Regras de negócio novas ou alteradas

1. **RN-024-01:** O modelo `Store` recebe três campos booleanos, todos com `default=True`: `payment_online_enabled`, `payment_cash_enabled`, `payment_card_enabled`. 🟢
   - Tipo: nova
   - Migration com `default=True` garante que lojas existentes continuam sem quebra.

2. **RN-024-02:** `views.checkout()` valida que o `payment_method` enviado no POST corresponde a um método habilitado na loja (`store.payment_<method>_enabled == True`). Se não corresponder, retorna o drawer com mensagem de erro sem criar `Order`. 🟢
   - Tipo: nova — análogo ao guard de `delivery_enabled` (RN-019-02).

3. **RN-024-03:** Se **todos os três métodos** estiverem desabilitados, o checkout é bloqueado integralmente com aviso "Nenhum método de pagamento disponível no momento." — comportamento idêntico ao `delivery_enabled=False`. 🟡
   - Tipo: nova

4. **RN-024-04:** O template do carrinho/checkout exibe apenas os seletores de método de pagamento que estiverem habilitados. Métodos desabilitados não aparecem (nem como opção desativada) para o cliente. 🟢
   - Tipo: nova

5. **RN-024-05:** O manager pode alternar os três métodos individualmente pelo painel de configurações da loja (`StoreSettingsForm`). Não há toggle rápido separado — o painel de settings é o único ponto de configuração (ao contrário do `delivery_enabled` que tem toggle rápido no dashboard). 🟡
   - Tipo: nova
   - Justificativa: mudança de métodos de pagamento é menos urgente que "fechar a loja"; o formulário de settings é suficiente.

6. **RN-024-06:** Os três flags são expostos em todos os templates via context processor `cart()` existente, adicionando as chaves `payment_online_enabled`, `payment_cash_enabled`, `payment_card_enabled`. 🟡
   - Tipo: nova

7. **RN-024-07:** O método `online` (MercadoPago) só deve ser marcável se `store.mercadopago_access_token` estiver configurado. O sistema não impede o save do flag, mas o checkout detecta a ausência do token e exibe aviso específico ao cliente. 🟡
   - Tipo: nova — derivado de RN-09 (`_reversa_sdd/domain.md#RN-09`).

---

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Três campos booleanos em `Store`: `payment_online_enabled`, `payment_cash_enabled`, `payment_card_enabled`, todos `default=True`, com migration | Must | Campos existem no banco; lojas existentes mantêm `True` após migration | 🟢 |
| RF-02 | `views.checkout()` valida `payment_method` contra os flags habilitados; rejeita método desabilitado sem criar Order | Must | POST com método desabilitado retorna drawer com mensagem de erro | 🟢 |
| RF-03 | Template do carrinho/checkout renderiza apenas os seletores de método habilitados | Must | Se `payment_cash_enabled=False`, rádio "Dinheiro" não aparece | 🟢 |
| RF-04 | Painel de settings do manager exibe três checkboxes ("Aceitar MP", "Aceitar Dinheiro", "Aceitar Cartão") | Must | Checkboxes visíveis, salvos corretamente ao submeter o form | 🟢 |
| RF-05 | Se todos os métodos estiverem desabilitados, checkout exibe aviso "Nenhum método de pagamento disponível" e bloqueia a finalização | Must | POST em `/checkout/` não cria Order; drawer mostra mensagem | 🟡 |
| RF-06 | Os três flags disponíveis em todos os templates via context processor (sem passar explicitamente por cada view) | Must | `{{ payment_online_enabled }}` acessível em qualquer template | 🟡 |
| RF-07 | Aviso no painel de settings quando `payment_online_enabled=True` mas `mercadopago_access_token` estiver vazio | Should | Texto de alerta exibido no próprio formulário, acima do checkbox do MP | 🟡 |

---

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Segurança | Guard no backend (RF-02) é obrigatório — a validação no template (RF-03) é só UX e não substitui o servidor | `_reversa_sdd/domain.md#RN-12` + padrão de checkout existente | 🟢 |
| Retrocompatibilidade | `default=True` nos três flags — lojas existentes continuam funcionando sem intervenção do manager | `core/models.py#Store` — padrão já usado em `delivery_enabled` | 🟢 |
| Consistência visual | Checkboxes no painel de settings usam mesmo estilo Tailwind + dark mode do restante do `StoreSettingsForm` | `_reversa_sdd/architecture.md#Tematização` | 🟡 |
| Isolamento multi-tenant | Flags são campos de `Store` (tenant) — cada loja tem sua própria configuração | ADR-002 — TenantAwareModel + TenantManager | 🟢 |

---

## 7. Critérios de Aceitação

```gherkin
Cenário: Manager desabilita "Dinheiro" nas configurações
  Dado que o manager está na tela de configurações da loja
  E "Aceitar Dinheiro" está marcado
  Quando desmarca "Aceitar Dinheiro" e salva
  Então payment_cash_enabled vira False no banco
  E o checkout não exibe mais o seletor "Dinheiro"

Cenário: Cliente tenta pagar com método desabilitado via POST direto
  Dado que payment_cash_enabled=False na loja
  Quando o cliente faz POST em /checkout/ com payment_method=cash
  Então recebe o drawer com mensagem "Método de pagamento não disponível"
  E nenhum Order é criado no banco

Cenário: Apenas MP habilitado — cliente só vê PIX
  Dado que payment_cash_enabled=False e payment_card_enabled=False
  E payment_online_enabled=True
  Quando o cliente abre o drawer do carrinho
  Então vê apenas a opção "Pagar com MercadoPago (PIX)"

Cenário: Todos os métodos desabilitados — checkout bloqueado
  Dado que os três flags são False
  Quando o cliente tenta finalizar o pedido
  Então vê aviso "Nenhum método de pagamento disponível no momento"
  E não consegue submeter o formulário de checkout

Cenário: MP habilitado sem token configurado
  Dado que payment_online_enabled=True
  E store.mercadopago_access_token está vazio
  Quando o manager acessa a tela de configurações
  Então vê aviso "Configure o token do MercadoPago para aceitar pagamentos online"

Cenário: MP + Cartão habilitados, sem Dinheiro
  Dado payment_online_enabled=True, payment_card_enabled=True, payment_cash_enabled=False
  Quando o cliente abre o checkout
  Então vê dois seletores: "MercadoPago (PIX)" e "Cartão na maquininha"
  E não vê o seletor "Dinheiro"
```

---

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 — Campos no model + migration | Must | Base de tudo; sem isso nada funciona |
| RF-02 — Guard no checkout (backend) | Must | Segurança: sem isso cliente burla a UI |
| RF-03 — Template filtra opções habilitadas | Must | UX principal — cliente só vê o que está disponível |
| RF-04 — Checkboxes no painel de settings | Must | Único ponto de configuração pelo manager |
| RF-06 — Context processor | Must | Dependência técnica de RF-03 e RF-05 |
| RF-05 — Bloquear checkout quando tudo desabilitado | Must | Evita estado inconsistente |
| RF-07 — Aviso de MP sem token | Should | UX de configuração; não bloqueia o fluxo principal |

---

## 9. Esclarecimentos

> Nenhuma sessão de dúvidas registrada ainda. Rode `/reversa-clarify` quando houver `[DÚVIDA]` pendente.

---

## 10. Lacunas

Nenhuma dúvida bloqueante identificada. Decisões de escopo tomadas:

- **Sem toggle rápido no dashboard** (diferente da feature 019): troca de método de pagamento é configuração planejada, não operação de urgência. O formulário de settings é suficiente.
- **Flags independentes por método**: cada método tem seu próprio boolean (não um campo de múltipla escolha), para máxima flexibilidade e compatibilidade com `StoreSettingsForm`.
- **Template filtra completamente** (sem mostrar opção desabilitada cinza): exibir opções "cinzas/bloqueadas" gera confusão ao cliente — melhor não mostrar.
- **Aviso de MP sem token** é `Should`, não `Must`: o sistema já tem fallback mock em dev (RN-10) e o token pode ser configurado depois.

---

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-08 | Versão inicial gerada por `/reversa-requirements` | reversa |
