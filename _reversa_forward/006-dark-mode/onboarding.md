# Onboarding — Testar o Modo Escuro (Dark Mode)

> Identificador: `006-dark-mode`
> Data: `2026-05-29`
> Para: quem vai testar a feature pela primeira vez (após o `/reversa-coding`)

## Pré-requisitos

1. Aplicar a migração nova:
   ```powershell
   python manage.py migrate
   ```
2. Subir o servidor (conforme padrão do projeto — uvicorn com `--reload`, porta 8000):
   ```powershell
   uvicorn store_saas.asgi:application --host 127.0.0.1 --port 8000 --reload
   ```
3. Garantir dados de seed (lojas e usuários):
   ```powershell
   python manage.py seed_loja
   ```

> Lembrete de tenant em dev: em `127.0.0.1:8000` o middleware serve a **primeira loja ativa** (`loja1`). Para ver outra loja, logue como o dono ou use o header `X-Tenant-Subdomain`. (Ver `_reversa_sdd/deployment.md` → "Multi-Tenancy — Resolução de Tenant por Host".)

## Roteiro de teste

### 1. Toggle na vitrine (anônimo)
1. Abra `http://127.0.0.1:8000/` (não logado).
2. Localize o **controle de tema** no header.
3. Clique nele → a página deve ficar **escura imediatamente**, sem recarregar.
4. Verifique header, fundo, cards de produto, footer e o **drawer do carrinho** (abra o carrinho) — nenhuma área deve permanecer clara contrastante.

### 2. Persistência anônima (localStorage)
1. Ainda anônimo e no tema escuro, **feche e reabra** o navegador em `http://127.0.0.1:8000/`.
2. A loja deve **reabrir escura**.
3. (Opcional) Console: `localStorage.getItem('theme')` deve refletir a escolha.

### 3. Default pelo SO (prefers-color-scheme)
1. Limpe a preferência: console → `localStorage.removeItem('theme')`; se estiver logado, deixe `theme = system`.
2. Mude o tema do **sistema operacional** para escuro.
3. Recarregue a loja → deve abrir **escura** seguindo o SO.

### 4. Persistência por perfil (usuário logado)
1. Logue como um usuário (ex.: `cliente1`, ou o dono `pizzapablo` para testar o painel).
2. Ative o modo escuro. Confirme no DevTools (aba Network) que houve um `POST /set-theme/` com resposta **204**.
3. Faça logout, logue **em outro navegador** (ou janela anônima logada) com o mesmo usuário.
4. A loja deve abrir no tema salvo no perfil (segue entre navegadores).

### 5. Painel do gestor
1. Logado como gestor, acesse **Painel**, **Pedidos**, **Comandas**, **Catálogo**, **Configurações**.
2. Cada tela deve respeitar o tema escuro (escopo confirmado: painel do gestor incluído).
3. O **admin do Django** (`/admin/`) **não** está no escopo — pode permanecer claro.

### 6. Anti-FOUC
1. Com tema escuro ativo, recarregue qualquer página algumas vezes.
2. Não deve haver **lampejo claro** perceptível antes de o escuro aparecer.

### 7. Voltar ao claro
1. Clique no toggle novamente → volta ao claro e a escolha passa a ser a preferência salva.

## Sinais de problema (o que reportar)

- Áreas que ficam claras no escuro (especialmente **parciais trocadas via HTMX**: lista de produtos, drawer do carrinho, linhas de pedido).
- Flash claro ao recarregar (FOUC).
- `POST /set-theme/` retornando erro (403 CSRF, 401/302 de login, 500).
- Texto ilegível por baixo contraste no escuro.
