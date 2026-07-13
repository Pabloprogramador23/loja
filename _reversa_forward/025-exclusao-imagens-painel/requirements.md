# Requirements: Exclusão de Imagens no Painel

> Identificador: `025-exclusao-imagens-painel`
> Data: `2026-07-13`
> Pasta da extração reversa: `_reversa_sdd/`
> Confidência: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

Esta feature entrega aos gerentes de loja a capacidade de excluir/apagar as imagens cadastradas para o logotipo da loja, a imagem de capa (marca) e as imagens dos produtos do cardápio através do painel de administração. Atualmente, o sistema só permite a substituição desses arquivos por novos uploads, sem suporte a remoção completa. Essa funcionalidade resolve o problema de lojas que desejam retirar imagens desatualizadas ou manter campos vazios nos produtos ou na identidade visual.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confidência |
|-------|------------------|-------------|
| `_reversa_sdd/inventory.md#Estrutura-de-Diretórios` | Modelos definidos em `core/models.py`, formulários em `core/forms.py` e templates sob `templates/core/manager/` | 🟢 |
| `_reversa_sdd/domain.md#Glossário-de-Domínio` | Store (Tenant) e Product são TenantAwareModels administrados pelo Manager | 🟢 |
| `_reversa_sdd/domain.md#RN-12-Acesso-ao-Dashboard-Manager-Controle-Binário` | O acesso à configuração da loja e edição de produtos é restrito a gerentes com `is_staff=True` | 🟢 |
| `core/models.py#L23-L24` | Os campos `Store.logo` e `Store.cover_image` possuem `null=True, blank=True` | 🟢 |
| `core/models.py#L101` | O campo `Product.image` possui `null=True, blank=True` | 🟢 |
| `core/forms.py#L59` | O campo `ProductForm.image` utiliza widget `forms.FileInput` em vez de `forms.ClearableFileInput` | 🟢 |
| `core/forms.py#L87-L88` | Os campos `StoreSettingsForm.logo` e `StoreSettingsForm.cover_image` utilizam widget `forms.FileInput` em vez de `forms.ClearableFileInput` | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Gerente da Loja (Staff) | Remover a imagem de capa da loja temporariamente | Acessa as configurações da loja, clica em "Remover capa" e salva a alteração. |
| Gerente da Loja (Staff) | Remover a imagem de um produto do cardápio | Edita um produto, clica em "Remover imagem do produto" e salva para que ele seja exibido sem imagem no catálogo do cliente. |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** O gerente da loja (usuário staff) deve poder remover a imagem de logotipo ou de capa da loja sem precisar substituí-la. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#RN-12-Acesso-ao-Dashboard-Manager-Controle-Binário`
   - Tipo: nova
2. **RN-02:** O gerente da loja deve poder remover a imagem de qualquer produto do cardápio. 🟢
   - Origem no legado: `_reversa_sdd/domain.md#RN-12-Acesso-ao-Dashboard-Manager-Controle-Binário`
   - Tipo: nova
3. **RN-03:** A remoção das imagens deve atualizar os campos correspondentes no banco de dados para `None` (ou vazio) mantendo a integridade dos modelos. 🟢
   - Origem no legado: `core/models.py` (definição de `null=True, blank=True`)
   - Tipo: nova
4. **RN-04:** Quando uma imagem for removida de um produto, o catálogo do cliente deve renderizar uma imagem padrão de placeholder (ilustração genérica de talheres). 🟢
   - Origem no legado: n/a
   - Tipo: nova
5. **RN-05:** Ao excluir uma imagem no painel, o arquivo físico correspondente no diretório `media/` deve ser removido do servidor/storage para evitar arquivos órfãos. 🟢
   - Origem no legado: n/a
   - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confidência |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Opção de exclusão do Logotipo da Loja | Must | No painel de configurações da loja, caso haja um logotipo cadastrado, deve existir um botão ou checkbox para marcar sua exclusão. Ao salvar, a imagem do logotipo deve ser desassociada e o arquivo correspondente excluído do servidor. | 🟢 |
| RF-02 | Opção de exclusão da Imagem de Capa da Loja | Must | No painel de configurações da loja, caso haja imagem de capa cadastrada, deve existir um botão ou checkbox para marcar sua exclusão. Ao salvar, a imagem deve ser desassociada e o arquivo correspondente excluído do servidor. | 🟢 |
| RF-03 | Opção de exclusão da Imagem de Produto | Must | No formulário de edição do produto, caso haja imagem cadastrada, deve existir um botão ou checkbox para marcar sua exclusão. Ao salvar, a imagem deve ser desassociada do produto e o arquivo correspondente excluído do servidor. | 🟢 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confidência |
|------|-----------|----------------------------|-------------|
| Segurança | Controle de acesso staff | Apenas usuários staff podem acessar os formulários de configurações e produtos, garantindo que clientes normais não possam apagar imagens. | 🟢 |
| Usabilidade | Feedback visual claro | A interface deve apresentar uma indicação visual explícita de que a imagem foi marcada para remoção ou que não há mais imagem associada. | 🟡 |
| Desempenho | Armazenamento limpo no servidor | A exclusão de imagens deve remover fisicamente os arquivos do servidor/storage para evitar acúmulo de arquivos órfãos em produção. | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Excluir logotipo da loja com sucesso
  Dado que o usuário é um gerente autenticado acessando as configurações da loja
  E a loja possui um logotipo atualmente cadastrado
  Quando o usuário marcar a opção de remover o logotipo, aceitar o popup de confirmação e clicar em "Salvar Configurações"
  Então as configurações são salvas com sucesso
  E o logotipo é removido do banco de dados e do disco do servidor.

Cenário: Excluir imagem de capa da loja com sucesso
  Dado que o usuário é um gerente autenticado acessando as configurações da loja
  E a loja possui uma imagem de capa atualmente cadastrada
  Quando o usuário marcar a opção de remover a capa, aceitar o popup de confirmação e clicar em "Salvar Configurações"
  Então as configurações são salvas com sucesso
  E a capa é removida do banco de dados e do disco do servidor.

Cenário: Excluir imagem de produto com sucesso
  Dado que o usuário é um gerente autenticado acessando a tela de edição de um produto
  E o produto possui uma imagem cadastrada
  Quando o usuário marcar a opção de remover a imagem, aceitar o popup de confirmação e clicar em "Salvar"
  Então o produto é editado com sucesso
  E a imagem é removida do banco de dados e do disco do servidor, exibindo o placeholder no catálogo do cliente.
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 | Must | Essencial para permitir a redefinição de logotipo da loja. |
| RF-02 | Must | Essencial para permitir a redefinição de capa da loja. |
| RF-03 | Must | Essencial para remover fotos antigas de produtos no cardápio. |

## 9. Esclarecimentos

### Sessão 2026-07-13

- **Q:** Ao excluir uma imagem (logo, capa ou produto), como o sistema deve tratar o arquivo físico armazenado no servidor?
  **R:** Excluir fisicamente o arquivo do servidor/storage (media/) para economizar espaço.
- **Q:** Quando um produto do cardápio não possuir imagem (ou tiver sua imagem excluída), como o catálogo público de clientes deve se comportar?
  **R:** Excluir a imagem e exibir uma imagem padrão de placeholder (ex: ilustração genérica de talheres).
- **Q:** Que tipo de proteção contra exclusão acidental você deseja implementar para as imagens?
  **R:** Um popup/modal de confirmação (via alert/confirm de browser) antes de salvar o formulário caso a exclusão seja marcada.

## 10. Lacunas

Nenhuma lacuna pendente.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-07-13 | Versão inicial gerada por `/reversa-requirements` | reversa |
| 2026-07-13 | Dúvidas resolvidas e integradas em sessão clarify | reversa |
