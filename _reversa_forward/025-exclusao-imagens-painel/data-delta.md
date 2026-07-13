# Data Delta: Exclusão de Imagens no Painel

Este documento apresenta a análise de impacto estrutural no banco de dados para a feature de exclusão de mídias.

## 1. Diff Conceitual do Modelo de Dados

Não há alterações na estrutura (schema) do banco de dados. Os modelos existentes já foram mapeados na extração reversa ([_reversa_sdd/data-dictionary.md](file:///c:/Users/Pablo/Desktop/loja/_reversa_sdd/data-dictionary.md)) e comportam valores nulos e vazios (`null=True, blank=True`).

### Entidades Afetadas

#### `Store` (Modelo correspondente ao Tenant)
* Campos afetados:
  * `logo` (`ImageField`, `null=True, blank=True`): passa de um caminho de arquivo existente para `None`.
  * `cover_image` (`ImageField`, `null=True, blank=True`): passa de um caminho de arquivo existente para `None`.

#### `Product` (Modelo correspondente ao Produto)
* Campos afetados:
  * `image` (`ImageField`, `null=True, blank=True`): passa de um caminho de arquivo existente para `None`.

---

## 2. Migrações Necessárias

* **Migrações de Schema**: **Nenhuma**. Não é necessário rodar `makemigrations` ou `migrate` no banco de dados, pois nenhuma coluna foi adicionada, alterada ou removida dos modelos.
* **Migrações de Dados**: **Nenhuma**. As alterações ocorrem em tempo de execução via formulários de administração quando solicitadas pelo usuário.

---

## 3. Comportamento do Banco de Dados em Deleção Física

O Django gerencia os campos de arquivo (`FileField` e `ImageField`) associados a uma classe de storage. 
Ao chamar o método `image.delete(save=False)` no campo de arquivo de uma instância de modelo:
1. O Django solicita à classe de armazenamento (no caso local, o filesystem) que delete fisicamente o arquivo correspondente no disco (em `media/store_logos/`, `media/store_covers/` ou `media/products/`).
2. O campo é esvaziado internamente (referência limpa no objeto).
3. Ao salvar a instância (`instance.save()`), o registro correspondente na tabela é atualizado para `NULL` no banco de dados (SQLite ou PostgreSQL).
