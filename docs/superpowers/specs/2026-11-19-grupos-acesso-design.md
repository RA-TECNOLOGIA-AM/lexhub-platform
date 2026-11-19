# Grupos de acesso e dashboards avulsos — design

Data: 19/11/2026 · Branch: `feat/grupos-acesso` · Status: **para revisão do Luís**

## 1. Problema

Hoje um Colaborador/Leitor vê um dashboard só se algum setor dele (equipe, `app.teams`) tem uma
regra card a card em `app.access_rules`. Todo card novo precisa ser incluído à mão no mapa.

Caso real (lexhub-v2, 19/11): a Controladoria (LA, NG, RJ) trabalha com os cards do Jurídico e
tem regras para Execução, Acordos, Recursal, Julgados… mas **não** para os cards que surgiram
depois: `publicacoes`, `emendas-manifestacoes`, `replicas`, `pendencias-intermediarias`.
O Emerson (Controladoria) não os vê.

## 2. Modelo: 4 camadas que somam

Acesso de um Colaborador/Leitor a um dashboard numa unidade = **união** de:

| Camada | Vem de | Libera | Exporta? |
|---|---|---|---|
| 1. Dashboards do setor | `app.access_rules` (já existe) | cards específicos | sim (se o cargo exporta) |
| 2. Grupos do setor | `app.team_group_grants` (novo) | coluna inteira | sim (se o cargo exporta) |
| 3. Grupos extras da pessoa | `app.member_group_grants` (novo) | coluna inteira | **não** |
| 4. Dashboards avulsos da pessoa | `app.member_dashboard_grants` (novo) | cards específicos | **não** |

- **Só libera, nunca nega**, então não existe conflito para resolver.
- Vale **todos** os setores marcados da pessoa naquela unidade.
- Sempre **por unidade**: cada camada só conta na unidade em que foi dada, a pessoa precisa ter
  cargo nessa unidade (`app.membership_units`) e o dashboard precisa estar ligado nela
  (`app.org_dashboards.enabled`), como já é hoje.
- Owner/Desenvolvedor e Gestor/Controller continuam vendo e exportando tudo pelo cargo. As camadas
  não mudam nada para eles.
- "Exporta" nas camadas 1–2 continua dependendo do cargo: Leitor não exporta nem pelo setor
  (`dashboards.export` não está no cargo Leitor).
- Escopo de linhas: as camadas 2–4 dão `scope = 'all'`. A comissão continua filtrada à parte
  (`can_see_commission` + `member_source_refs`), sem mudança.

## 3. Banco (migration `20261119130000_grupos_acesso.sql`)

### 3.1 Grupos com slug fixo

```sql
create table app.hub_groups (
    slug       text primary key check (slug ~ '^[a-z_]+$'),
    name       text not null,          -- rótulo da coluna no hub (pode mudar)
    sort_order int  not null
);
insert into app.hub_groups values
    ('comercial',     'Comercial',     10),
    ('pre_protocolo', 'Pré-protocolo', 20),
    ('tecnologia',    'Tecnologia',    30),
    ('juridico',      'Jurídico',      40),
    ('financeiro',    'Financeiro',    50),
    ('estrategico',   'Estratégico',   60);

alter table app.dashboard_catalog add column group_slug text references app.hub_groups (slug) on update cascade;
update app.dashboard_catalog d set group_slug = g.slug from app.hub_groups g where g.name = d.area;
alter table app.dashboard_catalog alter column group_slug set not null;
```

- `area` continua sendo o rótulo visual (o hub agrupa por ele). Permissão usa só `group_slug`.
  Renomear ou dividir uma coluna muda `area`/`hub_groups.name`, e as permissões continuam iguais.
- `not null` obriga todo card novo a declarar o grupo, e assim ele entra sozinho para quem tem o grupo.

### 3.2 Tabelas das camadas 2–4

```sql
-- Camada 2: setor herda a coluna inteira (setor já é por unidade)
create table app.team_group_grants (
    org_id     uuid not null,
    team_id    uuid not null,
    group_slug text not null references app.hub_groups (slug) on update cascade,
    created_by uuid references auth.users (id) on delete set null,
    created_at timestamptz not null default now(),
    primary key (team_id, group_slug),
    foreign key (org_id, team_id) references app.teams (org_id, id) on delete cascade
);

-- Camada 3: grupo extra da pessoa, por unidade
create table app.member_group_grants (
    membership_id uuid not null references app.memberships (id) on delete cascade,
    unit_id       uuid not null references app.units (id) on delete cascade,
    group_slug    text not null references app.hub_groups (slug) on update cascade,
    created_by    uuid references auth.users (id) on delete set null,
    created_at    timestamptz not null default now(),
    primary key (membership_id, unit_id, group_slug)
);

-- Camada 4: dashboard avulso da pessoa, por unidade
create table app.member_dashboard_grants (
    membership_id uuid not null references app.memberships (id) on delete cascade,
    unit_id       uuid not null references app.units (id) on delete cascade,
    dashboard_key text not null references app.dashboard_catalog (key) on update cascade on delete cascade,
    created_by    uuid references auth.users (id) on delete set null,
    created_at    timestamptz not null default now(),
    primary key (membership_id, unit_id, dashboard_key)
);
```

RLS ligada nas três tabelas, sem policies: só as funções `security definer` leem e escrevem,
como em `access_rules`.

Por que as camadas 3 e 4 são **por unidade**: um Gestor só gere as unidades dele. Uma exceção
sem unidade dada por um Gestor da NG abriria o acesso também na LA.

### 3.3 Regra única: `app_private.dashboard_access`

Uma função interna decide **de onde** vem o acesso. As outras só a usam (uma responsabilidade só):

```
app_private.dashboard_access(p_user uuid, p_unit uuid, p_dashboard text)
    returns table (scope text, via text)   -- via: 'role' | 'sector' | 'personal'; sem linha = sem acesso
```

Ordem (o primeiro que der acesso vence, porque `via` só serve para exportação):
1. Mesmas checagens de hoje (unidade/org/dashboard ativos e ligados; membro ativo).
2. `org.dashboards.all` ou `unit.dashboards.all` → `('all', 'role')`.
3. Sem cargo na unidade → sem linha.
4. Camada 1 (`access_rules` dos setores da pessoa na unidade) **ou** camada 2 (grupo do card em
   `team_group_grants` de algum desses setores) → `('all'|'own', 'sector')`. Com camada 2, o escopo é `'all'`.
5. Camada 3 ou 4 na unidade → `('all', 'personal')`.

Funções públicas (internas a `app_private`):
- `dashboard_scope(user, unit, key)` **mantém a assinatura** e passa a retornar `scope` de
  `dashboard_access`. Assim nada que chama ela hoje quebra (API, catálogo, RLS).
- **nova** `dashboard_can_export(user, unit, key) returns boolean`
  = `has_unit_permission(user, unit, 'dashboards.export') and via in ('role', 'sector')`.

### 3.4 API (FastAPI)

A exportação passa a ser decidida **por dashboard**, não só por unidade:
- `apps/api/src/app/access.py` `_RESOLVE_SQL`: `can_export` = `app_private.dashboard_can_export($1, u.id, $4)`.
- `apps/api/src/app/catalog.py` `_AVAILABLE_SQL`: idem, por card e unidade. A regra "vale se valer em
  todas as unidades do card" continua.
- `routes/dashboards.py` já bloqueia com 403 quando `can_export` é falso, então não muda.
- `me.py` (`can_export` geral do perfil) não muda: diz se o cargo exporta, não um card.

### 3.5 RPCs da aba Acesso

- `api.access_overview` ganha:
  - `groups`: `[{slug, name}]` em ordem;
  - `dashboards[].group_slug` e `dashboards_by_unit` continuam;
  - `group_of`: `{dashboard_key: group_slug}`;
  - `team_groups`: `[{team_id, group_slug}]` das unidades geridas.
- `member_json` (Membros/Acesso) ganha `extra_groups: [{unit, slug}]` e `extra_dashboards: [{unit, key}]`,
  só das unidades que quem chama gere.
- `api.update_member_access` ganha `p_extra_groups jsonb` e `p_extra_dashboards jsonb`. É o estado
  desejado **nas unidades geridas**, como já é com `p_teams`. Nova assinatura com `drop` + `create`
  (o front é o único que chama). Ao tirar o cargo de uma unidade, as exceções dela saem junto,
  como acontece com as equipes.
- **nova** `api.set_team_groups(p_org text, p_team uuid, p_groups text[])`: estado desejado dos grupos
  de um setor. Pode quem gere a unidade do setor (`app_private.access_scope`).
- Tudo grava em `app.audit_log` (`access.update` já existe; novo `access.team_groups`).
- Mesmas travas de hoje: ninguém mexe no próprio acesso nem em Owner/Desenvolvedor, a não ser Owner/Dev.

## 4. Front (aba Acesso)

### 4.1 Modal da pessoa (`AccessDialog.tsx`)

Em cada coluna de unidade, abaixo dos setores:

- **Grupos extras**: 6 caixas (as colunas do hub). Um grupo já coberto por um setor marcado
  aparece **marcado e travado**, com "pelo setor Controladoria", e não é salvo como exceção.
- **Dashboards avulsos**: lista com busca, só dos dashboards ligados na unidade, agrupados por
  coluna. Os já cobertos (pelo setor ou por grupo extra) ficam **ocultos** e há um contador
  "N já cobertos". Os escolhidos aparecem como chips removíveis.
- Gestor/Controller na unidade: as duas seções ficam desabilitadas com "Já vê tudo pelo cargo".
- Sem cargo na unidade: seções escondidas, como os setores.

**"O que passa a ver"** em tempo real, por unidade, separando a origem:

> NG: 14 de 29 — **pelo setor (exporta):** Execução, Acordos, … · **exceção (só visualiza):** Meta anual

`accessEditor.ts`:
- `AccessDraft` ganha `extraGroups: Record<unit, slug[]>` e `extraDashboards: Record<unit, key[]>`;
- `previewDashboards` aplica as 4 camadas (mesma ordem da §3.3) e devolve `{ sector: [], personal: [] }`;
- `toggleExtraGroup`, `toggleExtraDashboard`, `coveredBySector(unit)`;
- `setUnitRole('')` limpa as exceções da unidade;
- `isDirty`/`toUpdate` incluem os campos novos.

### 4.2 Grupos dos setores (página Acesso)

Uma seção nova "Grupos dos setores" ao lado da grade, para a unidade selecionada: uma linha por
setor e 6 caixas (colunas do hub). Salvar chama `api.set_team_groups`. A grade "o que cada cargo
vê" (`RoleGrid`) passa a mostrar também os setores que liberam o card pelo grupo.

### 4.3 Mock

`mockClient.ts` e `mock/*` ganham as mesmas tabelas e regras (`can_export` por card), para o modo mock
continuar valendo como referência.

## 5. Carga inicial (na mesma migration)

Decidido em 19/11 (respostas da §8). Dados do lexhub-v2 em 19/11; entre parênteses, pessoas no setor.

**Setor que vê tudo — Diretoria.** Nova coluna `app.teams.sees_all boolean not null default false`.
No `dashboard_access`, ter um setor com `sees_all` na unidade vale como "tudo da unidade", via `'sector'`.
Inclui grupos e cards que vierem depois. A carga marca `sees_all = true` nos setores `Diretoria`
(LA, MT, NG, RJ). Só Owner/Desenvolvedor liga/desliga essa marca (em `api.set_team_groups`). A
exportação continua dependendo do cargo (um Leitor na Diretoria vê tudo, mas não exporta).

**Grupo inteiro — só Controladoria.** `team_group_grants`: Controladoria (LA 2, NG 4, RJ 1) → `juridico`.
Ganha Publicações, Emendas, Réplicas e Pendências intermediárias, que ficaram de fora do mapa card a card.

**Card a card (camada 1, `access_rules`) — sem os cards de Execução** (`execucao`, `acordos`):

| Setor | Unidades | Cards |
|---|---|---|
| Publicações | LA (1), RJ (1) | `publicacoes` |
| Emendas e Manifestações | NG (1) | `emendas-manifestacoes` |
| Réplicas | LA (1), NG (1) | `replicas` |
| Acompanhamento Processual | LA (2), NG (2), RJ (1), MT (1) | `publicacoes`, `pendencias-intermediarias`, `emendas-manifestacoes`, `replicas`, `recursal`, `julgados-sentencas`, `julgados-acordaos` |

Como em `20261118110000`, a regra só é criada onde o dashboard está ligado na unidade do setor.

As regras card a card que a Controladoria já tem (`access_rules`) ficam como estão: não atrapalham e
continuam valendo para os cards de outras colunas (Comercial, Pré-protocolo). Limpar as do Jurídico
fica para depois.

Desfazer (comentado no fim da migration): `drop` das três tabelas, de `dashboard_can_export` e da
coluna `group_slug`, e recriar `dashboard_scope` como em `20261118130000_dashboards_liga_desliga.sql`.

## 6. Testes

- `supabase/tests/grupos_acesso_test.sql` (termina em `rollback`): cada camada sozinha; união de
  dois setores; grupo só na unidade dada; dashboard desligado não aparece; Leitor pelo setor não
  exporta; exceção pessoal não exporta; Gestor exporta tudo; tirar cargo limpa exceções;
  `set_team_groups` recusado fora das unidades geridas; card novo com `group_slug` aparece para o grupo.
- API: `can_export` por card em `access` e `catalog` (pytest com repo fake, como os de hoje).
- Front: `accessEditor.test.ts` (prévia em 4 camadas, coberto pelo setor, limpeza ao tirar cargo).

## 7. Fora do escopo

- Negar acesso (só soma).
- Exportação liberada por exceção (se precisar no futuro: uma coluna `can_export` nas tabelas 3–4).
- Migrar o mapa da camada 1 para grupos.
- Equipe Diretoria com nível de Owner/Dev (ideia antiga, separada).

## 8. Decisões (19/11)

1. **Diretoria** vê tudo por regra (`teams.sees_all`), não por grupo, para continuar valendo quando surgirem colunas novas.
2. **Acompanhamento Processual, Publicações, Emendas, Réplicas**: card a card (camada 1), sem Execução.
   O grupo `juridico` inteiro fica só com a Controladoria.
3. **Grupos dos setores** é editado na aba Acesso. As exceções da pessoa (grupos extras e avulsos) ficam
   no modal da pessoa, que também está na aba Acesso.

## 9. Ajustes de implementação

- `dashboard_catalog.group_slug`: um gatilho preenche a partir de `area` quando vier vazio. Assim as
  migrations de card novo que já escrevem `area = 'Jurídico'` continuam funcionando. Área sem grupo
  bate no `not null` e falha.
- `access_overview.teams[]` ganha `sees_all` e `groups`. `dashboards[].teams` (a grade por cargo) passa a
  contar também os setores que liberam pelo grupo ou pelo `sees_all`.
- `update_member_access`: `p_extra_groups`/`p_extra_dashboards` com `default null` (null = não muda).
  Ao tirar o cargo de uma unidade, as exceções dela saem sempre.
