# Acesso — editar cargo por unidade e equipes, e ver o que cada cargo vê

Data: 13/11/2026 · Branch: `feat/acesso` · Status: design aprovado em conversa, aguardando revisão do spec

## Objetivo

Ligar a aba **Administração → Acesso** ao Supabase (staging vvhg), sem a API em Python (pausada), e
entregar duas coisas:

1. **Grade "O que cada cargo vê"**: para uma unidade, cada dashboard e o acesso de cada cargo.
2. **Editor da pessoa**: escolher alguém e mudar o cargo em cada unidade, as equipes e — só para
   Owner/Desenvolvedor — o papel de Desenvolvedor, com uma prévia ao vivo dos dashboards que ela passa a ver.

Hoje a aba busca `GET /orgs/{org}/access` na API em Python e quebra em modo api.

## Decisões (Luís, 12–13/11)

- Escopo: só a edição de cargos e equipes + o visual por cargo. Criar/editar regras de equipe
  ("Nova regra") fica fora.
- Visual: **os dois** — a grade por cargo e a prévia por pessoa no editor.
- Papel de Desenvolvedor: só **Owner e Desenvolvedor** promovem/rebaixam. Gestor/Controller não veem
  essa opção.
- **Diretoria com nível de Owner/Desenvolvedor**: ideia do Luís para depois (decisão de modelo de
  permissões). Fora desta entrega.

## Como o acesso funciona hoje (banco, não muda)

`app_private.dashboard_scope(user, unit, dashboard)` decide, para um dashboard **ligado na unidade**
(`app.org_dashboards.enabled` + `app.dashboard_catalog.active`):

1. Owner/Desenvolvedor (`org.dashboards.all` no papel da org) → vê tudo, em todas as unidades.
2. Cargo na unidade com `unit.dashboards.all` (Gestor, Controller) → vê tudo da unidade.
3. Senão (Colaborador, Leitor) → vê o dashboard se alguma **equipe da pessoa naquela unidade** tem
   regra para ele (`app.access_rules`; hoje todas com `scope = 'all'`).

Exportar: `dashboards.export` (Owner, Desenvolvedor, Gestor, Controller, Colaborador; Leitor não).

## Quem gere acesso

- `access.manage` (Owner, Desenvolvedor): todas as unidades da organização + papel de Desenvolvedor.
- `unit.access.manage` (Gestor, Controller): só as unidades em que têm esse cargo; nunca editam
  Owner/Desenvolvedor nem o papel na organização.
- Os demais: a aba mostra só a matriz de papéis e o estado "Você não gere acesso nesta organização"
  no lugar da grade e do editor.

## Fora do escopo

- Criar/editar regras de equipe, criar equipes.
- Diretoria com poder de organização.
- Esconder o item do menu (o `/me` vem da API pausada; mesma situação de Membros).

## Banco — migration `20261113140000_acesso.sql`

Aditiva, com rollback comentado. Validada no vvhg dentro de `begin … rollback` e aplicada só depois
do "Aplica". Funções: schema `api`, `security definer`, `set search_path = ''`, `revoke` de
`public`/`anon`, `grant execute` a `authenticated`. Erros: regra → `P0001` (pt-BR); sem permissão →
`42501`. Auditoria em `app.audit_log`.

Helper `app_private.access_scope(p_org uuid) returns uuid[]` — unidades ativas da org que quem chama
gere: todas com `access.manage`; senão `my_unit_ids_with('unit.access.manage')` da org. Grants só ao
dono (os `api.*` rodam como dono; não dar a `authenticated`).

### `api.access_overview(p_org text, p_unit text) returns jsonb`

`p_unit` = código; `null` → a primeira unidade do escopo (por código). Unidade fora do escopo → 42501.

```json
{
  "units": [{ "code": "NG", "name": "Nicolas Gomes" }],
  "unit": "NG",
  "dashboards": [{ "key": "protocolo-lexpre", "title": "Protocolo", "area": "Operação", "teams": ["Protocolo", "Diretoria"] }],
  "teams": [{ "id": "…", "name": "Protocolo", "unit": "NG" }],
  "roles": [
    { "key": "gestor", "sees_all": true, "exports": true },
    { "key": "controller", "sees_all": true, "exports": true },
    { "key": "colaborador", "sees_all": false, "exports": true },
    { "key": "leitor", "sees_all": false, "exports": false }
  ],
  "rules": [{ "team_id": "…", "dashboard_key": "protocolo-lexpre" }],
  "dashboards_by_unit": { "NG": ["protocolo-lexpre"], "LA": ["protocolo-lexpre"] },
  "titles": { "protocolo-lexpre": "Protocolo" },
  "can_set_org_role": true
}
```

- `units`: unidades do escopo (ordem por código).
- `dashboards`: os ligados na unidade, ordem `sort_order`, `name`; `teams` = nomes das equipes
  ativas da unidade com regra para ele.
- `teams`: equipes ativas de **todas as unidades do escopo** (o editor precisa de todas).
- `rules`: regras das equipes de todas as unidades do escopo (a prévia do editor usa).
- `roles`: tirado de `app.role_permissions` (`unit.dashboards.all`, `dashboards.export`), cargos de
  nível unidade na ordem de `sort_order`.
- `can_set_org_role`: quem chama tem `access.manage`.

- `dashboards_by_unit` / `titles`: keys ligadas em cada unidade do escopo e o título de cada uma —
  a prévia do editor calcula todas as unidades da pessoa sem nova chamada.

### `api.update_member_access(p_org text, p_member uuid, p_units jsonb, p_teams uuid[], p_org_role text) returns jsonb`

- `p_units`: `[{ "code": "NG", "role": "gestor" }, …]` — o estado desejado **nas unidades do escopo**
  de quem chama. Unidade do escopo ausente da lista = a pessoa sai dela (sem cargo). Unidade fora do
  escopo na lista → 42501. Cargo fora de `gestor|controller|colaborador|leitor` → P0001.
- `p_teams`: estado desejado das equipes **nas unidades do escopo**. Equipe de unidade fora do escopo
  → 42501; equipe de unidade em que a pessoa ficará sem cargo → P0001 `'Equipe sem cargo na unidade.'`.
- `p_org_role`: `null` = não mexe; `'admin'` ou `'member'` = muda (só com `access.manage`, senão 42501).
  `owner` nunca muda por aqui (P0001).
- Recusas: membro de outra org / inexistente → 42501; Gestor/Controller editando Owner/Desenvolvedor
  → 42501; mudar o **próprio** papel na org → P0001 `'Você não pode mudar o seu próprio papel.'`;
  rebaixar o último Owner/Desenvolvedor ativo → P0001; membro `disabled` → P0001 `'Reative a pessoa
  antes de mudar o acesso.'`.
- Unidades e equipes **fora** do escopo de quem chama ficam intactas.
- Devolve o membro no formato de `api.list_members` (`app_private.member_json`, com o escopo de acesso).
- Auditoria `member.access_updated` com antes/depois (unidades, equipes, papel).

## Front

### Contrato (`types/index.ts`)

```ts
export type AccessOverview = {
    units: Unit[]
    unit: string
    dashboards: { key: string; title: string; area: string; teams: string[] }[]
    teams: MemberTeam[]
    roles: { key: UnitRoleKey; sees_all: boolean; exports: boolean }[]
    rules: { team_id: string; dashboard_key: string }[]
    dashboards_by_unit: Record<string, string[]>
    titles: Record<string, string>
    can_set_org_role: boolean
}

export type MemberAccessUpdate = {
    units: { code: string; role: UnitRoleKey }[]
    teams: string[] // ids
    org_role: 'admin' | 'member' | null // null = não muda
}
```

`AccessResponse`, `TeamRule` e `getAccess` saem. A matriz de papéis (`Permission[]`) vira constante do
front (`pages/admin/access/permissions.ts`), com a coluna **Controller** nova (igual em toda org).

### DataClient

`getAccessOverview(org: string, unit: string | null): Promise<AccessOverview>` e
`updateMemberAccess(org: string, memberId: string, update: MemberAccessUpdate): Promise<Member>`.
Módulo `services/accessClient.ts` (rpc no schema `api`, `toRpcError`). Mock em
`services/mock/access.ts` com as mesmas regras (`createAccessStore`), ligado ao mesmo
`createMembersStore` (editar acesso muda a lista de Membros).

### Tela (`pages/admin/access/`)

- **Cabeçalho**: título e texto atuais + seletor **Unidade** (as do escopo), na URL `?unidade=`.
- **Matriz de papéis**: como hoje, com Controller.
- **Grade "O que cada cargo vê"** (`RoleGrid.tsx`): linhas = dashboards da unidade (título + área);
  colunas = Gestor, Controller, Colaborador, Leitor. Célula: cargo com `sees_all` → "Vê"; senão chips
  das equipes que liberam (ou "—" = nenhuma equipe libera). Linha de rodapé por coluna: "Exporta" /
  "Não exporta". Nota acima: "Owner e Desenvolvedor veem todos os dashboards de todas as unidades.
  Colaborador e Leitor veem o que as equipes deles liberam."
- **Pessoas** (`PeopleEditor.tsx`, no lugar do simulador): busca + lista (nome, cargo resumido) dos
  membros ativos de `listMembers`; ao escolher, o editor:
  - por unidade do escopo: seletor de cargo (— / Gestor / Controller / Colaborador / Leitor);
  - por unidade com cargo: as equipes dela (caixas);
  - "Desenvolvedor (todas as unidades)" — só com `can_set_org_role`, nunca para si mesmo;
  - **prévia ao vivo** (`previewDashboards`): por unidade, "vê N dashboards" + os títulos;
    Desenvolvedor → "vê todos os dashboards de todas as unidades";
  - Salvar (desabilitado sem mudança), Descartar; erro do servidor aparece no painel; sucesso
    recarrega a lista.
  - Owner/Desenvolvedor aparecem para Gestor/Controller só para leitura ("Owner/Desenvolvedor: só
    Owner ou Desenvolvedor muda").
- **Sem permissão** (403 de `access_overview`): matriz de papéis + estado "Você não gere acesso nesta
  organização."
- Saem `TeamRules.tsx`, `AccessSimulator.tsx`, `accessView.ts`, `accessMember.ts` (e testes).

### Regras puras (`accessEditor.ts`, testadas)

- `previewDashboards(overview, draft): { unit: string; all: boolean; titles: string[] }[]` — mesma
  regra do `dashboard_scope`: Desenvolvedor → `all`; cargo com `sees_all` → todos de
  `dashboards_by_unit[unit]`; senão os dashboards da unidade com regra de alguma equipe escolhida
  daquela unidade.
- `draftFromMember(member)`, `isDirty(member, draft)`, `toUpdate(draft, canSetOrgRole)`,
  `teamsWithoutRole(draft, teams)` (equipes de unidade sem cargo saem ao tirar o cargo).
- `gridCell(overview, dashboard, role)` → `{ kind: 'all' } | { kind: 'teams'; teams: string[] } | { kind: 'none' }`.

## Testes

- `supabase/tests/acesso_test.sql` (rollback): Gestor de U1 muda cargo/equipe de X só em U1 (U2
  intacta); Gestor não edita Desenvolvedor; Gestor não muda papel na org; equipe sem cargo recusada;
  Dev promove X a Desenvolvedor e volta; ninguém muda o próprio papel; último Owner/Dev não é
  rebaixado; colaborador recebe 42501; `access_overview` traz as equipes certas por dashboard e só as
  unidades do escopo; auditoria gravada.
- Vitest: `accessEditor` (prévia igual à regra do banco, Controller/Gestor veem tudo, equipe de outra
  unidade não libera, Desenvolvedor = tudo), `gridCell`, `accessClient` (parâmetros e 42501→403), mock.
- Navegador no mock: grade por unidade, editar cargo/equipe com prévia, salvar, Desenvolvedor.
- Modo api no vvhg: o Luís testa.

## Ordem de entrega

1. Migration + teste SQL (vvhg com rollback → "Aplica").
2. Contrato, `accessClient`, mock.
3. Regras puras (`accessEditor.ts`, `permissions.ts`).
4. Tela (grade, editor, sem permissão).
5. Verificação no navegador.
