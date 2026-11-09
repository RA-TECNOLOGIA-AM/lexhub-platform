# Front: estrutura de pastas no estilo do LexHub v1 — design

Data: 09/11/2026 · Escopo: `apps/web/src` · Tipo: refatoração (só mover e renomear) · Branch: `refactor/front-estrutura`

## Objetivo

Hoje fica difícil achar as coisas no front da V2:

- `components/` tem 12 arquivos soltos, misturando layout, peças de dashboard e componentes genéricos.
- O que é de dashboard está espalhado em três lugares: `components/`, `dashboards/` e `pages/`.
- `auth/` e `data/` não seguem o padrão do LexHub v1, que o time já conhece.

A nova organização segue a do v1: **pastas por tipo, e o nome da pasta diz o que tem dentro**. As telas ficam em
`pages/`, divididas como o menu; as peças reaproveitadas, em `components/<tipo>/`; os dados, em `services/` e `types/`.

Considerei organizar por funcionalidade (`features/<item do menu>/`) e cheguei a fazer essa versão, mas ela foi
descartada a favor da versão parecida com o v1, que o time já conhece.

### Sucesso

- A pessoa acha um arquivo pelo tipo, como no v1: tela em `pages/`, peça visual em `components/<tipo>/`, dados em
  `services/`, formato em `types/`.
- O app se comporta exatamente igual: mesmas rotas, telas, dados e testes.
- Typecheck, lint, Prettier, testes e build passam, e o histórico de cada arquivo é mantido (`git mv`).

## Regras de negócio da V2 que não mudam

- **Um módulo por dashboard, com a unidade como parâmetro.** Não volta a pasta por unidade do v1 (`NG/`, `LA/`, `RJ/`).
- **`DataClient` é a única porta de dados**, com troca mock ↔ api por `VITE_DATA_SOURCE`.
- **`navigation.ts` é o mapa do app.** Menu, breadcrumb e rotas leem dele.
- **As regras puras ficam em `*View.ts`, com teste ao lado** (`*.test.ts`).

## Fora do escopo

- **Mudar código por dentro dos arquivos.** Só os caminhos de `import` mudam.
- **Renomear arquivos ou componentes.**
- **Quebrar `types` e o mock por domínio.**
- **`apps/api`, `supabase` e `workers`.**

## Estrutura-alvo

```
src/
  App.tsx · main.tsx · navigation.ts      (ficam onde estão)
  components/
    auth/        RequireAuth
    layout/      AppLayout, PageHeader
    dashboard/   CardSection, DashboardCard, DashboardHeader, Delta, Freshness, Kpi, KpiSection
    ui/          Icon, DataTable, PillGroup
    states/      ErrorState, LoadingState, StateMessage
  contexts/      AuthProvider, auth-context
  hooks/         useAsync, useFavorites
  lib/           format, viewTransition
  services/      client (DataClient), apiClient, mockClient, http, env, errors, supabase
    mock/        catalog, members, billing, protocolo, pendencias…
  types/         index.ts
  pages/
    LoginPage, ComingSoonPage
    dashboards/  HubPage, DashboardPage, DashboardView, registry, types
      protocolo/ · pendencias/
    admin/
      members/
      billing/
  styles/
```

**Regra para achar e criar arquivos:**

- **Tela:** `pages/`. Telas de dashboard ficam em `pages/dashboards/`, e as da seção Administração do menu, em
  `pages/admin/<tela>/`.
- **Peça visual usada por mais de uma tela:** `components/<tipo>/` (`layout`, `dashboard`, `ui`, `auth`, `states`).
- **Contexto React (estado global):** `contexts/`.
- **Porta de dados e mock:** `services/`. **Formato dos dados:** `types/`.

## Mapa de movimentação

Todos os caminhos são relativos a `apps/web/src/`. Arquivos que não aparecem aqui não mudam de lugar:

- `App.tsx`, `main.tsx` e `navigation.ts`;
- `components/states/*`;
- `hooks/*`;
- `lib/*` e `styles/*`;
- `pages/LoginPage.tsx` e `pages/ComingSoonPage.tsx`.

| De                                                                                                      | Para                    |
| ------------------------------------------------------------------------------------------------------- | ----------------------- |
| `auth/RequireAuth.tsx`                                                                                  | `components/auth/`      |
| `auth/AuthProvider.tsx`, `auth/auth-context.ts`                                                         | `contexts/`             |
| `components/AppLayout.tsx`, `PageHeader.tsx`                                                            | `components/layout/`    |
| `components/CardSection`, `DashboardCard`, `DashboardHeader`, `Delta`, `Freshness`, `Kpi`, `KpiSection` | `components/dashboard/` |
| `components/Icon.tsx`, `DataTable.tsx`, `PillGroup.tsx`                                                 | `components/ui/`        |
| `pages/HubPage.tsx`, `pages/DashboardPage.tsx`                                                          | `pages/dashboards/`     |
| `dashboards/*` (DashboardView, registry, types, protocolo/, pendencias/)                                | `pages/dashboards/*`    |
| `pages/members/*`                                                                                       | `pages/admin/members/*` |
| `pages/billing/*`                                                                                       | `pages/admin/billing/*` |
| `data/types.ts`                                                                                         | `types/index.ts`        |
| `data/*` (client, apiClient, mockClient, http + teste, env, errors, supabase, mock/)                    | `services/*`            |

Pastas que ficam vazias e somem: `auth/`, `dashboards/`, `data/`.

## Como executar

1. **Mover com `git mv`** (por script, com o mapa acima), para o Git reconhecer cada arquivo como renomeado.
2. **Corrigir os imports relativos** de cada arquivo movido e de quem importa dele. O typecheck aponta o que faltar.
3. **Rodar o Prettier** (`npm run format`).
4. **Atualizar o `apps/web/README.md`:** a seção de estrutura, a regra acima e os caminhos citados.
5. **Atualizar os caminhos do plano do Protocolo** (ver Riscos).

## Verificação

- `npx tsc -b`, `npm run lint`, `npm run format:check`, `npm test` (37 testes) e `npm run build`.
- **No navegador, em modo mock:** login, hub, Protocolo e Pendências, Membros, Plano e cobrança e uma página "Em
  construção". Também conferir que não há erros no console.
- **O diff só pode ter renomeações (R) e linhas de import.**

## Riscos

- **Plano do Protocolo em andamento.** `docs/superpowers/plans/2026-11-09-protocolo-unificado.md` cita caminhos de
  arquivo e ainda tem tarefas por fazer. Os caminhos foram atualizados para a estrutura nova, sem mudar o conteúdo das
  tarefas. Arquivos novos que o plano cria em pastas que ainda não existem (`components/charts/`,
  `components/filters/`, `lib/csv.ts`…) continuam onde o plano diz, porque já seguem a regra por tipo.
- **Branches de outras pessoas** que mexem em `apps/web/src` vão ter conflitos de caminho. A refatoração é um commit
  isolado, sem mudança de código, e o Git resolve a maioria das renomeações sozinho.
