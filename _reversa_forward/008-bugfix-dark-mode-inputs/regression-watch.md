# Regression Watch: 008-bugfix-dark-mode-inputs

> Gerado em: 2026-05-30
> Feature: Bugfix — Inputs invisíveis no modo escuro (Configurações)

## Itens monitorados

| ID | O que verificar | Arquivo | Sinal de regressão |
|----|----------------|---------|-------------------|
| W001 | Widgets `delivery_fee` e `free_delivery_threshold` do `StoreSettingsForm` têm `dark:bg-gray-700 dark:border-gray-600 dark:text-white` | `core/forms.py` | Classes `dark:` ausentes ou removidas |
| W002 | Widgets `name` e `mercadopago_access_token` do `StoreSettingsForm` têm `dark:bg-gray-700 dark:border-gray-600 dark:text-white` | `core/forms.py` | Classes `dark:` ausentes ou removidas |
| W003 | Novos campos adicionados ao `StoreSettingsForm` futuramente recebem variantes `dark:` nos seus widgets | `core/forms.py` | Campo novo sem classes dark mode |

## Histórico de re-extrações

| Data | Veredito W001 | Veredito W002 | Veredito W003 | Observações |
|------|--------------|--------------|--------------|-------------|
| 2026-05-30 | 🟢 Corrigido | 🟢 Corrigido | 🟢 OK | Bugfix aplicado nesta data |
