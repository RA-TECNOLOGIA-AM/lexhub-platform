-- =============================================================================
-- Importação V1 (schema public) -> V2 (schema app)
--
-- O QUE FAZ (só LÊ o public; só ESCREVE no app):
--   Lexgroup                      -> app.organizations (slug 'lexgroup')
--   public.companhia              -> app.units          (NG, LAADVAM->LA, LAADVRJ->RJ, demais pela sigla)
--   public.usuario + usuario_companhia -> app.unit_members (unidades de cada pessoa)
--   public.setor (por unidade)    -> app.teams
--   public.usuario                -> app.members        (mesmo id do login: auth.users)
--   cargo Desenvolvedor           -> members.role = admin  (vê tudo da organização)
--   cargo Gestor                  -> unit_members.role = manager (vê tudo das SUAS unidades)
--   cargo Colaborador             -> member (vê só o liberado para a equipe)
--   Unidade NG                    -> dashboards do MVP: protocolo-lexpre, pendencias-ng
--   Liberações (mesma regra da V1, dashboardAccess.ts, unidade NG):
--       protocolo-lexpre: Protocolo, Controladoria, Tecnologia, Diretoria
--       pendencias-ng:    Pendências Iniciais, Controladoria, Tecnologia, Diretoria
--
-- COMO USAR:
--   1. Rode como está: é um ENSAIO. Mostra o relatório e desfaz tudo (rollback na última linha).
--   2. Se o relatório estiver certo, troque a última linha "rollback;" por "commit;" e rode de novo.
--   Pode rodar mais de uma vez: atualiza o que já existe, não duplica.
--   Atenção: rodar de novo sobrescreve papel/status com os valores atuais da V1.
-- =============================================================================
begin;

create function pg_temp.norm(t text) returns text
language sql immutable
as $$
    select lower(trim(translate(
        coalesce(t, ''),
        'áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ',
        'aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC'
    )))
$$;

-- 1. Organização -------------------------------------------------------------
insert into app.organizations (slug, name)
values ('lexgroup', 'Lexgroup')
on conflict (slug) do update set name = excluded.name;

create temp table v_org on commit drop as
    select id from app.organizations where slug = 'lexgroup';

-- 2. Unidades (companhia) ----------------------------------------------------
with src as (
    select
        c.id,
        c.nome,
        c.ativo,
        regexp_replace(upper(coalesce(c.sigla, '')), '[^A-Z0-9_]', '', 'g') as sigla
    from public.companhia c
)
insert into app.units (org_id, code, name, active, legacy_companhia_id)
select
    (select id from v_org),
    case
        when s.sigla = 'LAADVAM' then 'LA'
        when s.sigla = 'LAADVRJ' then 'RJ'
        when length(s.sigla) between 2 and 16 then s.sigla
        else 'C' || s.id
    end,
    s.nome,
    s.ativo,
    s.id
from src s
on conflict (org_id, code) do update
    set name = excluded.name,
        active = excluded.active,
        legacy_companhia_id = excluded.legacy_companhia_id;

-- 3. Unidades de cada usuário (companhia principal + extras) -----------------
create temp table v_user_units on commit drop as
    select u.id as user_id, un.id as unit_id
    from public.usuario u
    join app.units un on un.legacy_companhia_id = u.companhia_id
                     and un.org_id = (select id from v_org)
    union
    select uc.usuario_id, un.id
    from public.usuario_companhia uc
    join app.units un on un.legacy_companhia_id = uc.companhia_id
                     and un.org_id = (select id from v_org);

-- 4. Membros -----------------------------------------------------------------
insert into app.members (org_id, user_id, full_name, email, role, status)
select
    (select id from v_org),
    u.id,
    coalesce(nullif(trim(u.nome), ''), u.email),
    lower(trim(u.email)),
    case when pg_temp.norm(c.nome) = 'desenvolvedor' then 'admin' else 'member' end::app.org_role,
    case when u.ativo then 'active' else 'disabled' end::app.member_status
from public.usuario u
join public.cargo c on c.id = u.cargo_id
on conflict (org_id, user_id) do update
    set full_name = excluded.full_name,
        email = excluded.email,
        role = excluded.role,
        status = excluded.status;

-- 5. Membro x unidade (Gestor = manager) --------------------------------------
insert into app.unit_members (org_id, unit_id, member_id, role)
select
    m.org_id,
    uu.unit_id,
    m.id,
    case when pg_temp.norm(c.nome) = 'gestor' then 'manager' else 'member' end::app.unit_role
from v_user_units uu
join app.members m on m.user_id = uu.user_id and m.org_id = (select id from v_org)
join public.usuario u on u.id = uu.user_id
join public.cargo c on c.id = u.cargo_id
on conflict (unit_id, member_id) do update set role = excluded.role;

-- 6. Equipes (setor dentro de cada unidade onde há gente dele) -----------------
insert into app.teams (org_id, unit_id, name, active, legacy_setor_id)
select distinct
    (select id from v_org),
    uu.unit_id,
    s.nome,
    s.ativo,
    s.id
from v_user_units uu
join public.usuario u on u.id = uu.user_id
join public.setor s on s.id = u.setor_id
on conflict (unit_id, name) do update
    set active = excluded.active,
        legacy_setor_id = excluded.legacy_setor_id;

-- 7. Membro x equipe ------------------------------------------------------------
insert into app.team_members (org_id, team_id, member_id)
select t.org_id, t.id, m.id
from v_user_units uu
join public.usuario u on u.id = uu.user_id
join app.teams t on t.unit_id = uu.unit_id and t.legacy_setor_id = u.setor_id
join app.members m on m.user_id = u.id and m.org_id = t.org_id
on conflict do nothing;

-- 8. Dashboards do MVP ligados na NG --------------------------------------------
insert into app.unit_dashboards (org_id, unit_id, dashboard_key)
select un.org_id, un.id, d.key
from app.units un
cross join app.dashboards d
where un.org_id = (select id from v_org)
  and un.code = 'NG'
  and d.key in ('protocolo-lexpre', 'pendencias')
on conflict do nothing;

-- 9. Liberações por equipe (regra da V1, unidade NG) -----------------------------
with regra (setor, dashboard_key) as (
    values
        ('protocolo',           'protocolo-lexpre'),
        ('controladoria',       'protocolo-lexpre'),
        ('tecnologia',          'protocolo-lexpre'),
        ('diretoria',           'protocolo-lexpre'),
        ('pendencias iniciais', 'pendencias'),
        ('controladoria',       'pendencias'),
        ('tecnologia',          'pendencias'),
        ('diretoria',           'pendencias')
)
insert into app.dashboard_grants (org_id, unit_id, dashboard_key, team_id)
select t.org_id, t.unit_id, r.dashboard_key, t.id
from app.teams t
join app.units un on un.id = t.unit_id and un.code = 'NG'
join regra r on pg_temp.norm(t.name) = r.setor
where t.org_id = (select id from v_org)
on conflict do nothing;

-- 10. Auditoria -------------------------------------------------------------------
insert into app.audit_log (org_id, action, target_type, metadata)
select
    (select id from v_org),
    'import.v1',
    'organization',
    jsonb_build_object(
        'units',   (select count(*) from app.units   where org_id = (select id from v_org)),
        'members', (select count(*) from app.members where org_id = (select id from v_org))
    );

-- 11. Relatório (é o resultado que aparece no SQL Editor) -------------------------
with o as (select id from v_org)
select item, quantidade, detalhe from (
    select 1 as ordem, 'unidades' as item, count(*) as quantidade,
           string_agg(code || case when active then '' else ' (inativa)' end, ', ' order by code) as detalhe
    from app.units where org_id = (select id from o)
    union all
    select 2, 'equipes', count(*), null
    from app.teams where org_id = (select id from o)
    union all
    select 3, 'membros ativos', count(*), null
    from app.members where org_id = (select id from o) and status = 'active'
    union all
    select 4, 'membros desativados', count(*), null
    from app.members where org_id = (select id from o) and status = 'disabled'
    union all
    select 5, 'admins (Desenvolvedor)', count(*), null
    from app.members where org_id = (select id from o) and role = 'admin'
    union all
    select 6, 'gestores (manager de unidade)', count(distinct member_id), null
    from app.unit_members where org_id = (select id from o) and role = 'manager'
    union all
    select 7, 'liberações de dashboard (NG)', count(*),
           string_agg(distinct g.dashboard_key || ' -> ' || t.name, '; ')
    from app.dashboard_grants g join app.teams t on t.id = g.team_id
    where g.org_id = (select id from o)
    union all
    select 8, 'membros que veem algum dashboard', count(distinct m.id), null
    from app.members m
    join app.unit_dashboards ud on ud.org_id = m.org_id
    where m.org_id = (select id from o)
      and app.user_can_view_dashboard(m.user_id, ud.unit_id, ud.dashboard_key)
    union all
    select 9, 'ATENÇÃO: membros sem nenhuma unidade', count(*),
           string_agg(m.email, ', ' order by m.email)
    from app.members m
    where m.org_id = (select id from o)
      and m.role <> 'admin'
      and not exists (select 1 from app.unit_members um where um.member_id = m.id)
    union all
    select 10, 'ATENÇÃO: equipes da NG sem liberação', count(*),
           string_agg(t.name, ', ' order by t.name)
    from app.teams t
    join app.units un on un.id = t.unit_id and un.code = 'NG'
    where t.org_id = (select id from o)
      and not exists (select 1 from app.dashboard_grants g where g.team_id = t.id)
) r
order by ordem;

rollback;  -- ENSAIO. Para gravar de verdade, troque por: commit;
