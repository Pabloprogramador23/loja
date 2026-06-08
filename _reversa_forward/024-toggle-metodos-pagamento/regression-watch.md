# Regression Watch: Toggle de Métodos de Pagamento

> Identificador: `024-toggle-metodos-pagamento`
> Criado por: `/reversa-coding` em `2026-06-08`
> Como usar: em re-extrações futuras do Reversa, verificar cada item desta tabela contra os artefatos gerados em `_reversa_sdd/`. Atualizar a seção "Histórico de re-extrações" com o veredito.

---

## Watch Items

| ID | Origem | Regra esperada após a mudança | Tipo | Sinal de violação |
|----|--------|-------------------------------|------|-------------------|
| W001 | `core/models.py#Store` → `_reversa_sdd/code-analysis.md` | `Store` documentado com os campos `payment_online_enabled`, `payment_cash_enabled`, `payment_card_enabled` (todos `BooleanField`, `default=True`) | presença | Campos ausentes no ERD ou no code-analysis |
| W002 | `core/views.py#checkout` → `_reversa_sdd/code-analysis.md#2.4` | Fluxo do `checkout()` documentado com guard de `payment_method` contra flags do tenant, antes da criação do `Order` | presença | Guard não mencionado no fluxo do checkout |
| W003 | `core/context_processors.py` → `_reversa_sdd/code-analysis.md#2.3` | `cart()` documentado como retornando as três chaves `payment_*_enabled` | presença | Chaves ausentes na tabela de variáveis do context processor |
| W004 | `core/forms.py#StoreSettingsForm` → `_reversa_sdd/code-analysis.md` | `StoreSettingsForm.fields` inclui `payment_online_enabled`, `payment_cash_enabled`, `payment_card_enabled` | presença | Campos ausentes nos fields do form |
| W005 | `_reversa_sdd/domain.md#RN-04` | RN-04 (checkout requer name, phone, address) permanece documentada e intacta — o guard de payment_method é adicional, não substitui | redação | RN-04 desapareceu ou foi fundida com a nova regra |

---

## Observações (sem peso de regressão)

> Itens 🟡 INFERIDOS — monitorar mas não bloquear re-extração.

- O aviso visual de "MP sem token" no template de settings é comportamento da camada de apresentação, não necessariamente capturado na extração reversa automática.
- A lógica de auto-seleção do método padrão no hidden input (`value="{% if payment_online_enabled %}online{% elif ...%}"`) é detalhe de template — pode não aparecer no code-analysis.

---

## Histórico de re-extrações

| Data | Agente | W001 | W002 | W003 | W004 | W005 | Observação |
|------|--------|------|------|------|------|------|------------|
| — | — | — | — | — | — | — | Nenhuma re-extração realizada ainda |

---

## Arquivadas

<!-- Watch items resolvidos e sem risco de regressão futura serão movidos aqui. -->
