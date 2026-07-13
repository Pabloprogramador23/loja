# Onboarding: Testando Exclusão de Imagens no Painel

Este guia descreve os passos necessários para testar e validar a funcionalidade de exclusão de mídias no painel e no cardápio de clientes.

## Pré-requisitos

1. O servidor local Django deve estar rodando (normalmente em `http://localhost:8000` ou pelo domínio do tenant).
2. Estar autenticado como usuário de gerenciamento (Manager / Staff). Se necessário, utilize o superusuário de testes.
3. Ter pelo menos um produto cadastrado com imagem e a loja possuir logotipo e imagem de capa definidos.

---

## Roteiro de Testes

### Caso de Teste 1: Exclusão de Logotipo e Imagem de Capa da Loja

1. Acesse o painel de administração da loja.
2. Navegue até a tela **Configurações da Loja** (`/dashboard/settings/`).
3. Verifique que o logotipo e a imagem de capa atuais estão sendo exibidos nas respectivas miniaturas de preview.
4. Identifique o novo botão **Excluir** ou **Remover** ao lado de cada uma das imagens.
5. Clique no botão de exclusão do Logotipo. Verifique se o preview do logotipo desaparece ou fica semitransparente indicando a marcação de exclusão.
6. Clique no botão de exclusão da Imagem de Capa. Verifique o mesmo feedback visual.
7. Clique no botão **Salvar Configurações** no rodapé da página.
8. **Verificação de Confirmação**: O navegador deve exibir uma caixa de diálogo `confirm()` informando que você marcou imagens para exclusão e pedindo para confirmar a operação.
9. Clique em **Cancelar**. Verifique se o formulário não é enviado e os estados permanecem como estavam.
10. Clique em **Salvar Configurações** novamente e, desta vez, clique em **OK** na caixa de confirmação.
11. Após o recarregamento da página, verifique que:
    - Os previews do logotipo e imagem de capa não aparecem mais nas configurações.
    - O banco de dados foi atualizado (`logo = None` e `cover_image = None`).
    - Os arquivos físicos correspondentes foram apagados da pasta local de mídia (`media/store_logos/` e `media/store_covers/`).
12. Acesse o catálogo público da loja e valide se o logotipo e a imagem de capa sumiram da visualização do cliente final.

---

### Caso de Teste 2: Exclusão de Imagem de um Produto

1. Navegue até a tela de **Produtos** (`/dashboard/products/`) no painel.
2. Clique para editar um produto que possua imagem associada.
3. Na seção de imagem, localize o botão **Remover Imagem**.
4. Clique no botão, confirme a marcação visual de remoção.
5. Clique em **Salvar** para submeter o formulário de produto.
6. Aceite o popup de confirmação do navegador.
7. Verifique que:
    - O produto foi salvo e o preview da imagem sumiu do formulário.
    - O arquivo físico foi removido de `media/products/`.
8. Acesse a página do cardápio público (`/catalog/` ou a página inicial do tenant).
9. Encontre o produto editado e certifique-se de que ele exibe agora o placeholder de talheres genérico em SVG no lugar da foto ausente.
