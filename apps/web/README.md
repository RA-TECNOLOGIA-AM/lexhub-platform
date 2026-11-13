# LexHub V2 — front (`apps/web`)

React 19 + Vite 8 + TypeScript, com React Router, Oxlint e Prettier. A aplicação oferece login, hub, dashboards,
documentação, administração da organização e ferramentas da equipe RA. O protótipo estático em
[`template/`](template/README.md) é uma referência visual e de dados, não é executado pelo React.

## Rodar local

Precisa do **Node 22.12+, 24 ou 26** (testado com 26; o Vitest não aceita o 25) e do npm que vem junto.
Tudo é rodado **dentro de `apps/web`** (confira o prompt: `...\apps\web>`):

```powershell
cd apps\web
npm ci                              # instala exatamente as versões do package-lock.json
Copy-Item .env.example .env.local   # opcional no modo mock; configure para usar a API
npm run dev
```

Login de teste: `controller@lexgroup.com.br` / `lexhub123` (ver [Login](#login)).
Não precisa da API nem do banco: `VITE_DATA_SOURCE=mock` (o padrão) usa `src/services/mock/`.

Abre em http://localhost:5173. É a porta que a API libera em `CORS_ORIGINS`; se ela estiver ocupada, o Vite usa a
próxima (5174...) e as chamadas à API passam a ser recusadas por CORS.
O navegador atualiza sozinho a cada arquivo salvo. `Ctrl+C` no terminal para parar.

| Comando                | O que faz                             |
| ---------------------- | ------------------------------------- |
| `npm run dev`          | Servidor de desenvolvimento           |
| `npx tsc -b`           | Checa os tipos (sem saída = sem erro) |
| `npm run lint`         | Oxlint                                |
| `npm run format`       | Prettier: formata todos os arquivos   |
| `npm run format:check` | Prettier: só confere (para o CI)      |
| `npm test`             | Testes (Vitest), uma vez              |
| `npm run test:watch`   | Testes refazendo a cada arquivo salvo |
| `npm run build`        | Checa os tipos e gera o `dist/`       |
| `npm run preview`      | Serve o `dist/` gerado pelo build     |

Antes de commitar: `npx tsc -b`, `npm run lint`, `npm run format:check` e `npm test` sem erros (o CI roda os mesmos).
Rodou um comando fora de `apps\web` e o npx ofereceu instalar um pacote `tsc`? Responda `n`: não é o TypeScript.
Se o editor acusar erro que o `npx tsc -b` não acusa: `Ctrl+Shift+P` → **TypeScript: Restart TS Server**.

## Formatação

Regras em [`.prettierrc.json`](.prettierrc.json): 4 espaços, sem `;`, aspas simples, até 120 colunas, CRLF.
O `tokens.css` não é formatado (fica idêntico ao do template; ver [`.prettierignore`](.prettierignore)).

Para formatar ao salvar no VS Code: extensão **Prettier - Code formatter** (`esbenp.prettier-vscode`) e, nas
configurações do usuário (`Preferences: Open User Settings (JSON)`):

```json
"editor.formatOnSave": true,
"[typescript]": { "editor.defaultFormatter": "esbenp.prettier-vscode" },
"[typescriptreact]": { "editor.defaultFormatter": "esbenp.prettier-vscode" },
"[json]": { "editor.defaultFormatter": "esbenp.prettier-vscode" },
"[css]": { "editor.defaultFormatter": "esbenp.prettier-vscode" }
```

## Login

Em modo `mock`, o `mockClient.ts` confere e-mail e senha contra a lista `testUsers` de `services/mock/users.ts`
(sem banco; esses usuários só existem no navegador). Em modo `api`, a autenticação usa Supabase Auth.

| Para testar             | E-mail                               | Senha       | Resultado                                     |
| ----------------------- | ------------------------------------ | ----------- | --------------------------------------------- |
| Login com sucesso       | `controller@lexgroup.com.br`         | `lexhub123` | entra (o e-mail ignora maiúsculas)            |
| Credencial errada (401) | outro e-mail ou outra senha          | —           | "E-mail ou senha incorretos."                 |
| E-mail mal formatado    | ex.: `abc`                           | qualquer    | "Digite um e-mail válido." (validado na tela) |
| Campos vazios           | —                                    | —           | "Preencha e-mail e senha."                    |
| Sem organização (403)   | `sem.acesso@exemplo.com`             | `lexhub123` | tela "Você ainda não tem acesso"              |
| Google                  | botão "Entrar com conta corporativa" | —           | no mock, entra direto (sem sair do app)       |

Com `VITE_DATA_SOURCE=api`, o botão do Google redireciona para o Google via Supabase Auth (PKCE) e retorna a
`<origem do app>/login`. Cadastre essa URL em **Redirect URLs** no Supabase (ex.: `http://localhost:5173/login`), e o
callback do Supabase (`https://<projeto>.supabase.co/auth/v1/callback`) no client OAuth do Google Cloud.
Quem entra, mas não faz parte de nenhuma organização (403 no `/me`), vê a tela "sem acesso" e pode **solicitar acesso**
(escritório + mensagem). A equipe RA aprova ou recusa em **Plataforma → Pedidos de acesso** (selo com o número de
pendentes no menu). Esses pedidos vão direto ao Supabase, nas funções do schema `api`
(`services/accessRequests.ts`; migration `supabase/migrations/20261112160000_solicitar_acesso.sql`), e não pela API em
Python. O schema `api` precisa estar em Settings → API → Exposed schemas.

No mock: entre com `sem.acesso@exemplo.com`, peça acesso, saia, entre com `controller@lexgroup.com.br` (equipe RA),
aprove em Pedidos de acesso e entre de novo com `sem.acesso@exemplo.com`: vai para o hub. Os pedidos ficam em memória
(voltam ao exemplo no F5).

No mock, para outro usuário de teste, acrescente na lista `testUsers`; o usuário exibido vem do `me` em
`services/mock/users.ts`. A sessão fica no `sessionStorage` (chave `lexhub.mock.session`): sobrevive ao F5 e some ao
fechar a aba. Para simular sessão expirada: `sessionStorage.clear()` no console e trocar de unidade.

Estados do login: `/login?convite=abc` e `/login?estado=sessao-expirada`.

### Para onde o login leva

| Situação                                     | Depois de entrar             |
| -------------------------------------------- | ---------------------------- |
| Clicou em **Sair** (de qualquer página)      | hub                          |
| Sessão expirou (401, botão "Entrar de novo") | a mesma página em que estava |
| Abriu um link direto sem estar logado        | a página do link             |

- `contexts/AuthProvider.tsx` guarda quem está logado (`me`) e oferece `signIn`/`signOut` via contexto; `useAuth()` lê.
  `signOut()` = Sair; `signOut({ returnHere: true })` = sessão expirada.
- `components/auth/RequireAuth.tsx` é a rota "porteiro": sem sessão, manda para `/login` levando o endereço de origem (`from`),
  exceto depois de um Sair.

## Rotas

| URL | Tela |
|---|---|
| `/login` | Login, sem a moldura do app. |
| `/:org/dashboards` | Hub da organização, por exemplo `/lexgroup/dashboards`. |
| `/:org/:unit/dashboards/:dashboardKey` | Dashboard de uma unidade. A unidade está na URL, então recarregar ou compartilhar o link mantém a seleção. |
| `/:org/documentacao/:slug` | Guia de um dashboard. |
| `/:org/admin/membros`, `/:org/admin/acesso`, `/:org/admin/unidades`, `/:org/admin/auditoria`, `/:org/admin/plano` | Administração da organização. |
| `/plataforma/clientes`, `/plataforma/pedidos` | Ferramentas da equipe RA. |

As páginas protegidas ficam sob `RequireAuth`; `OrgScope` valida a organização da URL. A moldura compartilhada é
`AppLayout`. Rotas desconhecidas redirecionam para o hub da organização ativa.

## Módulos

Regra do projeto: **um módulo é um bloco com uma responsabilidade, que esconde como funciona atrás de uma interface
de parâmetros e pode ser reutilizado ou trocado sem afetar o resto.** Código repetido com pequenas variações vira um
módulo, e a variação entra como parâmetro (props, argumentos).

## Estrutura

Pastas por tipo, como no LexHub v1: o nome da pasta diz o que tem dentro.

- **Tela:** `pages/`. Dashboards em `pages/dashboards/`; telas da seção Administração do menu em `pages/admin/<tela>/`;
  telas da seção Plataforma (equipe RA) em `pages/platform/<tela>/`.
- **Peça visual reaproveitada:** `components/<tipo>/` (`layout`, `dashboard`, `ui`, `auth`, `states`, `page_transition`).
- **Contexto React:** `contexts/`. **Porta de dados, clientes e mocks:** `services/`. **Formato dos dados:** `types/`.

```
src/
  main.tsx                 ponto de entrada: importa os CSS e desenha o <App />
  App.tsx                  tabela de rotas
  navigation.ts            mapa do app: menu, breadcrumb e rotas leem daqui
  components/
    auth/RequireAuth.tsx   porteiro das rotas: sem sessão, manda para /login
    layout/                AppLayout (barra lateral + cabeçalho), PageHeader (topo das páginas do menu)
    dashboard/
      CardSection.tsx      bloco do hub: título + grade de cards (Favoritos e cada área)
      DashboardCard.tsx    card de um dashboard no hub (link no título + estrela de favorito)
      DashboardHeader.tsx  cabeçalho dos dashboards: voltar, título + unidade, selo, pílulas de unidade
      Freshness.tsx        selo "Atualizado há X" / "Fonte atrasada"
      Kpi.tsx, Delta.tsx   indicador (com tone) e comparativo "▲ 8,2% vs. mês anterior"
      KpiSection.tsx       bloco de KPIs com título ("No período", "Situação atual do setor")
    ui/                    Icon (ícones do template), DataTable (tabela por colunas), PillGroup (pílulas-link)
    states/                StateMessage (base), ErrorState (por status), LoadingState (texto ou esqueleto)
  contexts/                sessão: AuthProvider e useAuth() (auth-context.ts)
  hooks/useAsync.ts        busca assíncrona: { data, error, loading }, refaz quando as deps mudam
  hooks/useFavorites.ts    favoritos do usuário: ready, isFavorite(key), toggle(key) (troca otimista)
  lib/format.ts            formatação pt-BR (números, R$, %, dias, "há X min")
  lib/viewTransition.ts    anima uma mudança de estado (View Transitions); sem suporte ou "reduzir movimento", só aplica
  services/                camada de dados (ver abaixo)
  types/index.ts           formato das respostas (campos da v1 + bloco `meta` da V2)
  pages/
    LoginPage.tsx, ComingSoonPage.tsx ("Em construção")
    dashboards/            HubPage, DashboardPage e cada dashboard como módulo (ver abaixo)
    admin/members/         Membros: tabela, filtros na URL e painel de convite
    admin/billing/         Plano e cobrança: plano atual com uso, planos e faturas
    admin/access/          Acesso: matriz de papéis, regras por equipe e simulador
    admin/audit/           Auditoria: eventos com filtros de tipo e pessoa na URL
    admin/sources/         Unidades, fontes e detalhes da fonte
    documentacao/          Catálogo e guias de dashboards
    platform/              Clientes e pedidos de acesso (equipe RA)
  styles/
    tokens.css             tokens visuais baseados no template
    app.css                estilos do app React
template/                  protótipo HTML estático, separado do app
```

Testes ficam ao lado do arquivo testado, com o mesmo nome + `.test.ts` (ex.: `services/mock/protocolo.test.ts`).
Por enquanto só funções puras (sem React), em ambiente Node.

## Hub

`/:org/dashboards` mostra os dashboards do catálogo agrupados por área.

- **Filtro por unidade:** as pílulas viram `?unidade=NG` na URL (F5, voltar e compartilhar mantêm). Com filtro, o card
  abre o dashboard nessa unidade.
- **Favoritos:** a estrela sobe o card para a seção "Favoritos" no topo, com animação. No mock ficam no `localStorage`
  (`lexhub.mock.favorites`; padrão: Comercial (LexPre) e Protocolo (LexPre)). Para voltar ao padrão:
  `localStorage.removeItem('lexhub.mock.favorites')` no console.

## Dashboards

Todo dashboard usa `pages/dashboards/DashboardView.tsx` para buscar dados, apresentar carregamento/erro, cabeçalho,
filtros, exportação e conteúdo. Cada módulo declara a key, a função de busca e seu conteúdo em
`pages/dashboards/<key>/index.ts`; `pages/dashboards/registry.tsx` associa a key à página.

O registro do front contém módulos para Comercial e Comissão (`comercial`, `comercial-lexpre`, `comissao`,
`comissao-lexpre`); Marketing (`marketing`, `marketing-lexpre`); NPS (`nps`); Protocolo, Pendências, Organização de
Documentos e Peticionamento nas variantes NG/LexPre; Pré-protocolo; Execução, Acordos e Recursal; Estratégico,
Despesas e Meta anual.

O registro de cálculos da API tem 18 keys: `comercial`, `comercial-lexpre`, `comissao`, `comissao-lexpre`,
`marketing`, `nps`, `protocolo`, `protocolo-lexpre`, `pendencias`, `pendencias-lexpre`, `org-documentos`,
`org-documentos-lexpre`, `peticionamento`, `peticionamento-lexpre`, `pre-protocolo`, `execucao`, `acordos` e
`recursal`. `marketing-lexpre`, `estrategico`, `despesas` e `meta-anual` ainda não estão nesse registro; uma página no
front não significa que a API já forneça seus dados.

Para criar um dashboard, adicione o tipo de resposta, o módulo e conteúdo, registre a página e implemente o cálculo e
as regras do catálogo na API/banco. Os dados fictícios completos estão disponíveis para Protocolo (LexPre) e
Pendências (LexPre); os demais módulos do mock recebem uma resposta estrutural vazia, não métricas reais.

## Camada de dados

As telas usam a interface `DataClient` de `src/services/client.ts`; `VITE_DATA_SOURCE` seleciona `mockClient` ou
`apiClient`.

```
telas → dataClient → mockClient → services/mock/
                    apiClient  → Supabase Auth + FastAPI + funções RPC do schema `api` no Supabase
```

No modo `api`, login é via Supabase Auth. `/me`, catálogo, favoritos, ordem do hub, dados e exportação de dashboards
passam pela FastAPI. Membros/convites, permissões, unidades/fontes, auditoria, notificações e pedidos de acesso usam
funções RPC autenticadas do schema `api` no Supabase; esse schema precisa estar exposto nas configurações de API do
projeto Supabase.

Plano/cobrança e clientes da plataforma são chamados pelo cliente web como rotas da API, mas não há rotas
correspondentes no backend Python atual. Erros de API são convertidos em `DataError`, mantendo o status HTTP (por
exemplo, 401, 403 ou 404).

`services/mock/` mantém a sessão e vários dados de demonstração no navegador; alguns são mantidos em memória e voltam
ao estado inicial ao recarregar. Os detalhes de persistência estão em `mockClient.ts`. Respostas sem implementação na
API retornam 404; cálculos registrados mas ainda não habilitados podem retornar 501.

## Variáveis de ambiente

Configure em `apps/web/.env.local` (não versionado). Todo valor `VITE_*` fica visível no navegador; nunca inclua
senhas, chaves secretas ou `service_role`.

| Variável | Uso |
|---|---|
| `VITE_DATA_SOURCE` | `mock` (padrão) ou `api`. |
| `VITE_BASE_API_URL` | URL base da API FastAPI, por exemplo `http://localhost:8000`. |
| `VITE_SUPABASE_URL` | URL pública do projeto Supabase. |
| `VITE_SUPABASE_ANON_KEY` | Chave pública/anon para Supabase Auth e RPC autorizadas. |

Use [`.env.example`](.env.example) como modelo. Em modo `api`, configure também `CORS_ORIGINS` na API e as URLs de
redirecionamento do login no Supabase.

## Testes

Os testes Vitest ficam próximos ao código testado:

```powershell
npx tsc -b
npm run lint
npm run format:check
npm test
npm run build
```

O workflow de CI executa essas verificações. Referência do contrato inicial e das decisões visuais:
[`docs/superpowers/specs/2026-11-09-protocolo-unificado-design.md`](../../docs/superpowers/specs/2026-11-09-protocolo-unificado-design.md).
