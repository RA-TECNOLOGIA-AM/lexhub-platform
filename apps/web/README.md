# LexHub V2 — front (`apps/web`)

React 19 + Vite 8 + TypeScript, com React Router para as rotas, Oxlint como linter e Prettier como formatador.
Visual e contrato de dados vêm do template estático em [`template/`](template/README.md).

## Rodar local

Precisa do Node (testado com 26). Tudo é rodado **dentro de `apps/web`** (confira o prompt: `...\apps\web>`):

```powershell
cd apps\web
npm install
npm run dev
```

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
| `npm run build`        | Checa os tipos e gera o `dist/`       |
| `npm run preview`      | Serve o `dist/` gerado pelo build     |

Antes de commitar: `npx tsc -b`, `npm run lint` e `npm run format:check` sem erros.
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

Por enquanto é **fictício**: o `mockClient.ts` confere e-mail e senha contra a lista `testUsers` de
`data/mock/users.ts` (sem banco; esses usuários só existem no navegador).

| Para testar             | E-mail                       | Senha       | Resultado                                     |
| ----------------------- | ---------------------------- | ----------- | --------------------------------------------- |
| Login com sucesso       | `controller@lexgroup.com.br` | `lexhub123` | entra (o e-mail ignora maiúsculas)            |
| Credencial errada (401) | outro e-mail ou outra senha  | —           | "E-mail ou senha incorretos."                 |
| E-mail mal formatado    | ex.: `abc`                   | qualquer    | "Digite um e-mail válido." (validado na tela) |
| Campos vazios           | —                            | —           | "Preencha e-mail e senha."                    |

Para outro usuário de teste, acrescente na lista `testUsers`. O usuário exibido depois de entrar é sempre o `me`
de `data/mock/users.ts`. A sessão fica no `sessionStorage` (chave `lexhub.mock.session`): sobrevive ao F5 e some ao
fechar a aba. Para simular sessão expirada: `sessionStorage.clear()` no console e trocar de unidade.

Estados do login: `/login?convite=abc` e `/login?estado=sessao-expirada`.

No final, troca pelo Supabase Auth, com usuários de teste no projeto de staging
(com vínculo à NG = sucesso; sem vínculo = 403).

### Para onde o login leva

| Situação                                     | Depois de entrar             |
| -------------------------------------------- | ---------------------------- |
| Clicou em **Sair** (de qualquer página)      | hub                          |
| Sessão expirou (401, botão "Entrar de novo") | a mesma página em que estava |
| Abriu um link direto sem estar logado        | a página do link             |

- `auth/AuthProvider.tsx` guarda quem está logado (`me`) e oferece `signIn`/`signOut` via contexto; `useAuth()` lê.
  `signOut()` = Sair; `signOut({ returnHere: true })` = sessão expirada.
- `auth/RequireAuth.tsx` é a rota "porteiro": sem sessão, manda para `/login` levando o endereço de origem (`from`),
  exceto depois de um Sair.

## Rotas

| URL                                    | Tela                                                        | Moldura |
| -------------------------------------- | ----------------------------------------------------------- | ------- |
| `/login`                               | Login (única rota aberta sem sessão)                        | não     |
| `/:org/dashboards`                     | Hub de dashboards (ex.: `/lexgroup/dashboards`)             | sim     |
| `/:org/:unit/dashboards/:dashboardKey` | Dashboard (ex.: `/lexgroup/NG/dashboards/protocolo-lexpre`) | sim     |
| qualquer outra                         | redireciona para o hub da organização de quem está logado   | —       |

As rotas de dashboard seguem a API: `GET /orgs/{org}/units/{unit}/dashboards/{key}`.
A **unidade é a URL**: as pílulas de unidade são links, então F5, voltar e compartilhar o link mantêm a unidade.
A moldura (barra lateral + cabeçalho) é o `<AppLayout>`, uma rota de layout sem `path`; a tela filha entra no `<Outlet />`.

## Módulos

Regra do projeto: **um módulo é um bloco com uma responsabilidade, que esconde como funciona atrás de uma interface
de parâmetros e pode ser reutilizado ou trocado sem afetar o resto.** Código repetido com pequenas variações vira um
módulo, e a variação entra como parâmetro (props, argumentos).

## Estrutura

```
src/
  main.tsx                 ponto de entrada: importa os CSS e desenha o <App />
  App.tsx                  tabela de rotas
  auth/                    sessão: AuthProvider, useAuth() e o porteiro RequireAuth
  components/
    AppLayout.tsx          barra lateral + cabeçalho (vem do template/app.js)
    DashboardCard.tsx      card de um dashboard no hub
    DashboardHeader.tsx    cabeçalho dos dashboards: voltar, título + unidade, selo, pílulas de unidade
    Freshness.tsx          selo "Atualizado há X" / "Fonte atrasada"
    Kpi.tsx, Delta.tsx     indicador (com tone) e comparativo "▲ 8,2% vs. mês anterior"
    KpiSection.tsx         bloco de KPIs com título ("No período", "Situação atual do setor")
    Icon.tsx               ícones de traço do template
    states/                StateMessage (base), ErrorState (por status), LoadingState (texto ou esqueleto)
  dashboards/              cada dashboard como módulo (ver abaixo)
  data/                    camada de dados (ver abaixo)
  hooks/useAsync.ts        busca assíncrona: { data, error, loading }, refaz quando as deps mudam
  lib/format.ts            formatação pt-BR (números, R$, %, dias, "há X min")
  pages/                   telas das rotas (Login, Hub, DashboardPage)
  styles/
    tokens.css             cópia inteira do template (não editar aqui)
    app.css                estilos novos do app React
template/                  HTML estático de referência (não é usado pelo app)
```

## Dashboards

Todo dashboard segue o mesmo roteiro, que fica no `dashboards/DashboardView.tsx`: buscar os dados da unidade e o
catálogo, mostrar carregando/erro, o cabeçalho e o conteúdo. Cada dashboard só informa o que é dele
(contrato `DashboardModule` em `dashboards/types.ts`):

```ts
export const pendencias: DashboardModule<PendenciasResponse> = {
    key: 'pendencias', // o mesmo do catálogo e da API
    fetch: (query) => dataClient.getPendencias(query), // como buscar os dados de uma unidade
    Content: PendenciasContent, // o miolo da página (KPIs, gráficos...)
}
```

**Para criar um dashboard novo:**

1. Pasta `dashboards/<nome>/` com o `<Nome>Content.tsx` (recebe `data`) e o `index.ts` (o módulo acima).
2. Uma linha em `dashboards/registry.tsx`: `[<nome>.key]: toPage(<nome>)`.
3. No mock: o tipo da resposta em `data/types.ts`, o `<nome>For(unit)` em `data/mock/` e o método no `DataClient`.

Dashboard que está no catálogo mas não no registro abre "Em construção".

| Dashboard  | Key                | Página                                 |
| ---------- | ------------------ | -------------------------------------- |
| Protocolo  | `protocolo-lexpre` | KPIs ("No período" e "Situação atual") |
| Pendências | `pendencias`       | KPIs ("No período" e "Situação atual") |

## Camada de dados

As telas **só** importam `dataClient` de `src/data/client.ts` e nunca sabem de onde vêm os dados.

```
telas  →  dataClient (interface DataClient)  →  mockClient  →  data/mock/
                                             →  apiClient   →  FastAPI   (a fazer)
```

| Arquivo         | O que é                                                                                                      |
| --------------- | ------------------------------------------------------------------------------------------------------------ |
| `client.ts`     | Interface `DataClient` (sessão + dados) e escolha da implementação por `VITE_DATA_SOURCE`                    |
| `types.ts`      | Formato das respostas (campos da v1 + bloco `meta` da V2)                                                    |
| `errors.ts`     | `DataError` com o status HTTP (401, 403...) e `toDataError`                                                  |
| `mockClient.ts` | O "servidor" fictício: espera 300 ms, 401 sem sessão, 403 fora das unidades liberadas, aplica o período      |
| `mock/`         | Os dados fictícios: `users`, `catalog`, `protocolo`, `pendencias` e `helpers` (porta de entrada: `index.ts`) |

**Dados por unidade:** NG é a base; LA AM tem 62% e LA RJ 38% do volume (`UNIT_SIZE` em `mock/helpers.ts`).
Contagens, valores e séries escalam (`unitScale`); tempos, taxas e médias por pessoa, não.

Para trocar pela API real: escrever um `apiClient.ts` que implemente `DataClient` e escolhê-lo em `createDataClient()`.
Nenhuma tela muda, e a pasta `mock/` deixa de ser usada.

## Variáveis de ambiente

Opcionais por enquanto. Ficam em `apps/web/.env.local` (não versionado).
Só variáveis com prefixo `VITE_` chegam ao navegador, e qualquer uma delas fica visível para quem abrir o site:
**nunca colocar segredo em `VITE_*`**.

| Variável           | Padrão | Uso                                                 |
| ------------------ | ------ | --------------------------------------------------- |
| `VITE_DATA_SOURCE` | `mock` | `mock` = dados fictícios; outro valor ainda dá erro |

## Estado atual (card #121, até 12/11)

- [x] Base: Vite + React + TS, `tokens.css` inteiro, fonte Inter, Prettier
- [x] Rotas, `<AppLayout>` (inclui menu do celular) e login fictício com rotas protegidas
- [x] Hub: cards por área, selo de atualização, "Chegando na V2"
- [x] Dashboard como módulo (`DashboardView` + registro) e estados reutilizáveis (carregando, erro por status)
- [x] Protocolo e Pendências: cabeçalho, troca de unidade e KPIs, com dados por unidade no mock
- [ ] Gráficos (por dia, por funcionário, por matéria/origem)
- [ ] Filtros (período, matéria, funcionário, UF), comissionamento e Exportar
- [ ] Estados "vazio" e "fonte atrasada"; filtro por unidade no hub
- [ ] Breadcrumb com o título do dashboard (hoje mostra a key)
- [ ] `getDashboard(key, query)` genérico no `DataClient` e testes (Vitest)
- [ ] `apiClient` + Supabase Auth (card #123)
