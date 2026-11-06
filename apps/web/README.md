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

Ainda não existe: `/login` é só uma tela provisória e as páginas abrem sem login.
Próximo passo: login fictício no cliente de dados (qualquer e-mail e senha entram, como no template).
No final, troca pelo Supabase Auth, com usuário de teste no projeto de staging.

## Rotas

| URL | Tela | Moldura |
|---|---|---|
| `/login` | Login | não |
| `/:org/dashboards` | Hub de dashboards (ex.: `/lexgroup/dashboards`) | sim |
| `/:org/:unit/dashboards/:dashboardKey` | Dashboard (ex.: `/lexgroup/NG/dashboards/protocolo-lexpre`) | sim |
| qualquer outra | redireciona para `/lexgroup/dashboards` | — |

As rotas de dashboard seguem a API: `GET /orgs/{org}/units/{unit}/dashboards/{key}`.
A moldura (barra lateral + cabeçalho) é o `<AppLayout>`, uma rota de layout sem `path`; a tela filha entra no `<Outlet />`.

## Estrutura

```
src/
  main.tsx            ponto de entrada: importa o tokens.css e desenha o <App />
  App.tsx             tabela de rotas
  styles/tokens.css   cópia inteira do template (cores, tipografia, componentes)
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
| `client.ts` | Interface `DataClient` e escolha da implementação por `VITE_DATA_SOURCE` |
| `types.ts` | Formato das respostas (campos da v1 + bloco `meta` da V2) |
| `mockClient.ts` | Implementação atual: lê o mock, espera 300 ms e devolve 403 fora das unidades liberadas |
| `mock-data.ts` | Dados fictícios (porte do `template/mock-data.js`) |
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
- [ ] `<AppLayout>` usar `getMe()` (org e usuário ainda fixos no componente)
- [ ] Login fictício e rotas protegidas
- [ ] Telas de verdade (hub, Protocolo, Pendências) e estados (carregando, vazio, atrasado, 403)
- [ ] `apiClient` + Supabase Auth
