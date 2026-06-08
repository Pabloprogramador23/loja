# Roadmap: Toggle de Métodos de Pagamento

> Identificador: `024-toggle-metodos-pagamento`
> Data: `2026-06-08`
> Requirements: `_reversa_forward/024-toggle-metodos-pagamento/requirements.md`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA

---

## 1. Resumo da abordagem

A feature segue exatamente o padrão já estabelecido pela feature `019-toggle-delivery`: **campos booleanos no modelo `Store` + guard no `views.checkout()` + exposição via context processor existente + checkboxes no `StoreSettingsForm`**.

Três campos são adicionados ao `Store`: `payment_online_enabled`, `payment_cash_enabled`, `payment_card_enabled`, todos `default=True` (retrocompatível). Uma única migration cobre os três.

O `views.checkout()` recebe um guard logo após a leitura do `payment_method` do POST: se o método enviado não estiver habilitado na loja, retorna o drawer com erro sem criar `Order`. O guard de "todos desabilitados" é verificado antes de qualquer renderização do drawer do carrinho, tanto no template quanto no backend.

O `context_processors.cart()` já existente recebe três novas chaves (`payment_online_enabled`, `payment_cash_enabled`, `payment_card_enabled`) lidas de `request.tenant`. Os templates do carrinho e do checkout filtram os seletores de método com `{% if payment_cash_enabled %}` etc. — sem lógica nova na view.

O `StoreSettingsForm` ganha três checkboxes no bloco de configurações de pagamento, abaixo dos campos de taxa de entrega já existentes. Nenhuma URL nova é necessária — o formulário já tem sua view e sua rota.

Não há integração externa nova, não há mudança na máquina de estados de `Order`, não há novo endpoint FastAPI.

---

## 2. Princípios aplicados

| Princípio | Como a feature se relaciona | Status |
|-----------|------------------------------|--------|
| I. Utilidade antes de completude | O dono do restaurante tem uso imediato e concreto: desabilitar dinheiro/cartão quando a maquininha falha ou quando quer só MP antecipado | respeita |
| II. Integrações essenciais apenas | Nenhuma integração externa nova. Apenas configuração de comportamento interno | respeita |
| III. Configuração simples, operação autônoma | O manager controla tudo pelo painel — sem variável de ambiente, sem contato com o desenvolvedor | respeita |
| IV. Produto focado, não showcase | Solução mais simples possível: três booleans + um guard + três checkboxes. Sem feature flag engine, sem regras dinâmicas | respeita |

---

## 3. Decisões técnicas

| ID | Decisão | Justificativa | Alternativas descartadas | Confidência |
|----|---------|----------------|--------------------------|-------------|
| D-01 | Três campos booleanos independentes em `Store` (não um campo `accepted_payment_methods` JSON/Array) | Padrão já usado por `delivery_enabled`; mais simples de validar no form e no backend; sem cast necessário | JSONField com lista de strings; IntegerField com bitmask | 🟢 |
| D-02 | Guard no `views.checkout()` após leitura do `payment_method` do POST | Ponto único de criação de `Order` — qualquer bypass de UI passa por aqui; análogo ao guard de `delivery_enabled` já existente | Guard no serializer/form; guard na URL | 🟢 |
| D-03 | Filtro no template via `{% if payment_cash_enabled %}` (não renderizar opção desabilitada) | UX mais limpa: o cliente não vê opção indisponível. Template filtra, backend valida | Renderizar opção cinza/disabled | 🟡 |
| D-04 | Configuração via `StoreSettingsForm` exclusivamente (sem toggle rápido no dashboard) | Troca de método de pagamento é decisão planejada, não operação de urgência. Toggle rápido no dashboard seria custo de implementação sem ganho real de UX | Toggle rápido na página de pedidos (como o delivery_enabled) | 🟡 |
| D-05 | Aviso de MP sem token como texto de alerta no form (não bloqueio de save) | Bloquear o save quando `payment_online_enabled=True` sem token quebraria lojas em dev com mock. O aviso visual é suficiente | Validação `clean()` no form que rejeita o save | 🟡 |
| D-06 | Nenhuma URL nova necessária | `manager_settings()` já existe; `StoreSettingsForm` já tem `POST /dashboard/settings/` | — | 🟢 |

---

## 4. Premissas

Nenhuma dúvida `[DÚVIDA]` não resolvida no `requirements.md`. Sem premissas forçadas.

---

## 5. Delta arquitetural

| Componente | Arquivo de origem no legado | Tipo de mudança | Resumo |
|------------|------------------------------|-----------------|--------|
| `Store` (model) | `core/models.py` | regra-alterada | +3 campos booleanos: `payment_online_enabled`, `payment_cash_enabled`, `payment_card_enabled` |
| `views.checkout` | `core/views.py` | regra-alterada | Guard pós-leitura do `payment_method`: rejeita método desabilitado e bloqueia se todos desabilitados |
| `context_processors.cart` | `core/context_processors.py` | regra-alterada | +3 chaves no dict retornado: `payment_online_enabled`, `payment_cash_enabled`, `payment_card_enabled` |
| `StoreSettingsForm` | `core/forms.py` | regra-alterada | +3 campos no `fields` + 3 checkboxes no template de settings |
| Template carrinho/checkout | `templates/` (drawer do cart) | regra-alterada | Seletores de `payment_method` condicionais via `{% if %}` |
| Template settings | `templates/dashboard_settings.html` ou equivalente | regra-alterada | Seção "Métodos de Pagamento" com 3 checkboxes + aviso MP sem token |

---

## 6. Delta no modelo de dados

Três campos booleanos novos em `Store`, todos `default=True`. Migration única não-destrutiva.

Detalhe completo em: `_reversa_forward/024-toggle-metodos-pagamento/data-delta.md`

---

## 7. Delta de contratos externos

Nenhum contrato externo afetado. A feature é puramente interna (modelo + views Django + templates HTMX). Sem novo endpoint FastAPI, sem novo webhook, sem integração com MercadoPago ou Uber Direct.

---

## 8. Plano de migração

1. Criar migration `core/migrations/XXXX_store_payment_methods_toggles.py` com `AddField` para os três novos booleanos, todos `default=True`
2. Aplicar migration no banco de desenvolvimento (`python manage.py migrate`)
3. Verificar que lojas existentes mantêm os três flags como `True` após a migration
4. Deploy em produção: a migration é non-destructive e retrocompatível — lojas existentes continuam aceitando todos os métodos até o manager decidir alterar

---

## 9. Riscos e mitigações

| Risco | Impacto | Probabilidade | Mitigação |
|-------|---------|---------------|-----------|
| Manager desabilita todos os métodos sem perceber | Alto — checkout bloqueado para todos os clientes | Baixo — requer desmarcar 3 checkboxes explicitamente | Aviso no form quando todos estiverem desmarcados; mensagem clara no checkout do cliente |
| Template filtra opção mas backend não está sincronizado | Médio — cliente vê método que o backend rejeita (ou vice-versa) | Baixo — implementação em par (guard + filtro) | Guard no backend é obrigatório independente do template; testar com POST direto |
| Aviso de MP sem token não visto pelo manager | Baixo — MP fica habilitado sem token, clientes com mock podem tentar pagar online e cair no fallback mock | Médio — manager pode não ler o aviso | Aviso em cor destacada (amarelo/laranja) acima do checkbox do MP |
| `context_processors.cart` chamado sem tenant (request sem loja resolvida) | Baixo — KeyError ou AttributeError | Baixo — TenantMiddleware sempre resolve ou retorna 404 antes | Leitura defensiva com `getattr(request, 'tenant', None)` |

---

## 10. Critério de pronto

- [ ] Migration aplicada sem erro; lojas existentes com três flags `True`
- [ ] `views.checkout()` rejeita `payment_method` desabilitado via POST direto (sem criar Order)
- [ ] Checkout bloqueado quando todos os três flags são `False`
- [ ] Template do carrinho não exibe seletor de método desabilitado
- [ ] `StoreSettingsForm` salva os três flags corretamente
- [ ] Aviso de MP sem token visível no form de settings quando aplicável
- [ ] Context processor expõe os três flags em todos os templates
- [ ] Todas as ações do `actions.md` marcadas `[X]`
- [ ] `regression-watch.md` gerado

---

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-06-08 | Versão inicial gerada por `/reversa-plan` | reversa |
