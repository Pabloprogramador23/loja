# Plano de Exploração — loja

> Criado pelo Reversa em 2026-05-26
> Marque cada tarefa com ✅ quando concluída.
> Você pode editar este plano antes de iniciar: adicione, remova ou reordene tarefas conforme necessário.

---

## Fase 1: Reconhecimento 🔍

- [x] **Scout** — Mapeamento de estrutura de pastas e tecnologias
- [x] **Scout** — Análise de dependências e gerenciadores de pacotes
- [x] **Scout** — Identificação de entry points, CI/CD e configurações

## Decisão de organização das specs 🗂️

> Entre o Scout e o Arqueólogo, o Reversa pergunta como você quer organizar as specs (por módulo, caso de uso, endpoint, híbrida, por features ou customizada). A escolha fica persistida em `.reversa/config.toml` na seção `[specs]` e não será reperguntada em execuções futuras. Para reapresentar o menu, remova manualmente a seção.

## Fase 2: Escavação 🏗️

- [x] **Arqueólogo** — Análise do módulo `store_saas` (config, ASGI híbrido, Celery)
- [x] **Arqueólogo** — Análise do módulo `core` (modelos, views, cart, checkout, pagamento, API FastAPI, tasks, middleware, multi-tenancy)
- [x] **Arqueólogo** — Análise do módulo `accounts` (autenticação)

## Fase 3: Interpretação 🧠

- [x] **Detetive** — Arqueologia Git e ADRs retroativos
- [x] **Detetive** — Regras de negócio implícitas e máquinas de estado
- [x] **Detetive** — Matriz de permissões (RBAC/ACL)
- [x] **Arquiteto** — Diagramas C4 (Contexto, Containers, Componentes)
- [x] **Arquiteto** — ERD completo e integrações externas
- [x] **Arquiteto** — Spec Impact Matrix

## Fase 4: Geração 📝

- [x] **Redator** — Specs SDD por componente (15 units, 71 arquivos)
- [x] **Redator** — OpenAPI (se aplicável) → openapi/loja-api.yaml
- [x] **Redator** — User Stories (se aplicável) → user-stories/compra-online.md + gestao-loja.md
- [x] **Redator** — Code/Spec Matrix → traceability/code-spec-matrix.md

## Fase 5: Revisão ✅

- [x] **Revisor** — Revisão cruzada de specs (15 units, 8 reclassificações)
- [x] **Revisor** — Resolução de lacunas com o usuário (23/23 perguntas respondidas, 10 decisões)
- [x] **Revisor** — Relatório de confiança final (91% 🟢)

---

## Agentes Independentes

> Execute estes agentes quando os recursos estiverem disponíveis — podem rodar em qualquer fase.

- [ ] **Visor** — Análise de interface via screenshots
- [ ] **Data Master** — Análise completa do banco de dados
- [ ] **Design System** — Extração de tokens de design
- [ ] **Tracer** — Análise dinâmica (requer sistema acessível)

---

## Próximo passo

Após o Time de Descoberta concluir e o `_reversa_sdd/` estar populado, você pode disparar um dos fluxos seguintes:

- `/reversa-migrate`: orquestrador do **Time de Migração** (Paradigm Advisor → Curator → Strategist → Designer → Screen Translator → Inspector). Gera as specs do sistema novo. Saída em `_reversa_sdd/migration/` e `_reversa_sdd/screens/`.
- `/reversa-reconstructor`: gera plano bottom-up para reimplementar o software a partir das specs do legado (uma tarefa por sessão).
