# LexHub V2 — front (`apps/web`)

React 19 + Vite 8 + TypeScript, com React Router para as rotas e Oxlint como linter.
Visual e contrato de dados vêm do template estático em [`template/`](template/README.md).

## Rodar local

Precisa do Node (testado com 26). Tudo é rodado **dentro de `apps/web`**:

```powershell
cd apps\web
npm install
npm run dev
```

Abre em http://localhost:5173 (porta fixa: é a que a API libera em `CORS_ORIGINS`).
O navegador atualiza sozinho a cada arquivo salvo. `Ctrl+C` no terminal para parar.

| Comando | O que faz |
|---|---|
| `npm run dev` | Servidor de desenvolvimento |
| `npx tsc -b` | Checa os tipos (sem saída = sem erro) |
| `npm run lint` | Oxlint |
| `npm run build` | Checa os tipos e gera o `dist/` |
| `npm run preview` | Serve o `dist/` gerado pelo build |

Se o editor acusar erro que o `npx tsc -b` não acusa: `Ctrl+Shift+P` → **TypeScript: Restart TS Server**.

## Login

Por enquanto é **fictício**: o `mockClient.ts` confere e-mail e senha contra a lista `testUsers` do `mock-data.ts`
(sem banco; esses usuários só existem no navegador).

| Para testar | E-mail | Senha | Resultado |
|---|---|---|---|
| Login com sucesso | `controller@lexgroup.com.br` | `lexhub123` | entra (o e-mail ignora maiúsculas) |
| Credencial errada (401) | outro e-mail ou outra senha | — | "E-mail ou senha incorretos." |
| E-mail mal formatado | ex.: `abc` | qualquer | "Digite um e-mail válido." (validado na tela) |
| Campos vazios | — | — | "Preencha e-mail e senha." |

Para outro usuário de teste, acrescente na lista `testUsers`. O usuário exibido depois de entrar é sempre o `me` do `mock-data.ts`. A sessão fica no `sessionStorage` (chave `lexhub.mock.session`):
sobrevive ao F5 e some ao fechar a aba. Para deslogar pelo console: `sessionStorage.clear()` + F5.

Estados do login: `/login?convite=abc` e `/login?estado=sessao-expirada`.

No final, troca pelo Supabase Auth, com usuários de teste no projeto de staging
(com vínculo à NG = sucesso; sem vínculo = 403).

### Como funciona

- `auth/AuthProvider.tsx` guarda quem está logado (`me`) e oferece `signIn`/`signOut` via contexto; `useAuth()` lê.
- `auth/RequireAuth.tsx` é a rota "porteiro": sem sessão, manda para `/login` levando o endereço de origem (`from`).
- Depois de entrar, o login volta para o `from` (ou para o hub). Sair só apaga a sessão; o porteiro redireciona.

## Rotas

| URL | Tela | Moldura |
|---|---|---|
| `/login` | Login (única rota aberta sem sessão) | não |
| `/:org/dashboards` | Hub de dashboards (ex.: `/lexgroup/dashboards`) | sim |
| `/:org/:unit/dashboards/:dashboardKey` | Dashboard (ex.: `/lexgroup/NG/dashboards/protocolo-lexpre`) | sim |
| qualquer outra | redireciona para o hub da organização de quem está logado | — |

As rotas de dashboard seguem a API: `GET /orgs/{org}/units/{unit}/dashboards/{key}`.
A moldura (barra lateral + cabeçalho) é o `<AppLayout>`, uma rota de layout sem `path`; a tela filha entra no `<Outlet />`.

## Estrutura

```
src/
  main.tsx            ponto de entrada: importa o tokens.css e desenha o <App />
  App.tsx             tabela de rotas
  styles/tokens.css   cópia inteira do template (cores, tipografia, componentes)
  auth/               sessão: AuthProvider, useAuth() e o porteiro RequireAuth
  components/
    AppLayout.tsx     barra lateral + cabeçalho (vem do template/app.js)
    Icon.tsx          ícones de traço do template
  pages/              uma tela por rota (Login, Hub, Dashboard)
  data/               camada de dados (ver abaixo)
template/             HTML estático de referência (não é usado pelo app)
```

## Camada de dados

As telas **só** importam `dataClient` de `src/data/client.ts` e nunca sabem de onde vêm os dados.

```
telas  →  dataClient (interface DataClient)  →  mockClient  →  mock-data.ts
                                             →  apiClient   →  FastAPI   (a fazer)
```

| Arquivo | O que é |
|---|---|
| `client.ts` | Interface `DataClient` (sessão + dados) e escolha da implementação por `VITE_DATA_SOURCE` |
| `types.ts` | Formato das respostas (campos da v1 + bloco `meta` da V2) |
| `mockClient.ts` | Implementação atual: lê o mock, espera 300 ms, devolve 401 sem sessão e 403 fora das unidades liberadas |
| `mock-data.ts` | Dados fictícios (porte do `template/mock-data.js`) e usuários de teste (`testUsers`) |
| `errors.ts` | `DataError` com o status HTTP (401, 403...) |

Para trocar pela API real: escrever um `apiClient.ts` que implemente `DataClient` e escolhê-lo em `createDataClient()`.
Nenhuma tela muda.

## Variáveis de ambiente

Opcionais por enquanto. Ficam em `apps/web/.env.local` (não versionado).
Só variáveis com prefixo `VITE_` chegam ao navegador, e qualquer uma delas fica visível para quem abrir o site:
**nunca colocar segredo em `VITE_*`**.

| Variável | Padrão | Uso |
|---|---|---|
| `VITE_DATA_SOURCE` | `mock` | `mock` = dados fictícios; outro valor ainda dá erro |

## Estado atual

- [x] Base: Vite + React + TS, `tokens.css` inteiro, fonte Inter
- [x] Rotas e `<AppLayout>` (inclui menu do celular)
- [x] Cliente de dados com mock; o hub já lista os dashboards por ele
- [x] `<AppLayout>` com org e usuário do `getMe()`
- [x] Login fictício, rotas protegidas e botão Sair
- [ ] Telas de verdade (hub, Protocolo, Pendências) e estados (carregando, vazio, atrasado, 403)
- [ ] `apiClient` + Supabase Auth
