-- =============================================================================
-- Importação V1 (schema public) -> V2 (schema app)
--
-- O QUE FAZ (só LÊ o public; só ESCREVE no app):
--   Lexgroup                      -> app.organizations (slug 'lexgroup')
--   public.companhia              -> app.units          (NG, LAADVAM->LA, LAADVRJ->RJ, demais pela sigla)
--   public.usuario + usuario_companhia -> app.membership_units (unidades de cada pessoa)
--   public.setor (por unidade)    -> app.teams
--   public.usuario                -> app.memberships    (mesmo id do login: auth.users)
--   cargo Desenvolvedor           -> papel admin       (vê tudo da organização)
--   cargo Gestor                  -> papel gestor      (vê tudo das SUAS unidades)
--   cargo Colaborador             -> papel colaborador (vê só o liberado para a equipe)
--   Unidade NG                    -> dashboards do MVP: protocolo-lexpre, pendencias
--   Regras de acesso (mesma regra da V1, dashboardAccess.ts, unidade NG), escopo "all":
--       protocolo-lexpre: Protocolo, Controladoria, Tecnologia, Diretoria
--       pendencias:       Pendências Iniciais, Controladoria, Tecnologia, Diretoria
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

-- 4. Associações (memberships) -------------------------------------------------
insert into app.memberships (org_id, user_id, full_name, email, role_key, status)
select
    (select id from v_org),
    u.id,
    coalesce(nullif(trim(u.nome), ''), u.email),
    lower(trim(u.email)),
    case pg_temp.norm(c.nome)
        when 'desenvolvedor' then 'admin'
        when 'gestor' then 'gestor'
        else 'colaborador'
    end,
    case when u.ativo then 'active' else 'disabled' end::app.member_status
from public.usuario u
join public.cargo c on c.id = u.cargo_id
on conflict (org_id, user_id) do update
    set full_name = excluded.full_name,
        email = excluded.email,
        role_key = excluded.role_key,
        status = excluded.status;

-- 5. Associação x unidade --------------------------------------------------------
insert into app.membership_units (org_id, unit_id, membership_id)
select m.org_id, uu.unit_id, m.id
from v_user_units uu
join app.memberships m on m.user_id = uu.user_id and m.org_id = (select id from v_org)
on conflict (unit_id, membership_id) do nothing;

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

-- 7. Associação x equipe ---------------------------------------------------------
insert into app.membership_teams (org_id, team_id, membership_id)
select t.org_id, t.id, m.id
from v_user_units uu
join public.usuario u on u.id = uu.user_id
join app.teams t on t.unit_id = uu.unit_id and t.legacy_setor_id = u.setor_id
join app.memberships m on m.user_id = u.id and m.org_id = t.org_id
on conflict do nothing;

-- 8. Dashboards do MVP ligados na NG --------------------------------------------
insert into app.org_dashboards (org_id, unit_id, dashboard_key)
select un.org_id, un.id, d.key
from app.units un
cross join app.dashboard_catalog d
where un.org_id = (select id from v_org)
  and un.code = 'NG'
  and d.key in ('protocolo-lexpre', 'pendencias')
on conflict do nothing;

-- 9. Regras de acesso por equipe (regra da V1, unidade NG) -------------------------
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
insert into app.access_rules (org_id, team_id, dashboard_key, scope)
select t.org_id, t.id, r.dashboard_key, 'all'
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
        'members', (select count(*) from app.memberships where org_id = (select id from v_org))
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
    from app.memberships where org_id = (select id from o) and status = 'active'
    union all
    select 4, 'membros desativados', count(*), null
    from app.memberships where org_id = (select id from o) and status = 'disabled'
    union all
    select 5, 'admins (Desenvolvedor)', count(*), null
    from app.memberships where org_id = (select id from o) and role_key = 'admin'
    union all
    select 6, 'gestores', count(*), null
    from app.memberships where org_id = (select id from o) and role_key = 'gestor'
    union all
    select 7, 'regras de acesso (NG)', count(*),
           string_agg(distinct r.dashboard_key || ' -> ' || t.name, '; ')
    from app.access_rules r join app.teams t on t.id = r.team_id
    where r.org_id = (select id from o)
    union all
    select 8, 'membros que veem algum dashboard', count(distinct m.id), null
    from app.memberships m
    join app.org_dashboards od on od.org_id = m.org_id and od.unit_id is not null
    where m.org_id = (select id from o)
      and app_private.dashboard_scope(m.user_id, od.unit_id, od.dashboard_key) is not null
    union all
    select 9, 'ATENÇÃO: membros sem nenhuma unidade', count(*),
           string_agg(m.email, ', ' order by m.email)
    from app.memberships m
    where m.org_id = (select id from o)
      and m.role_key not in ('owner', 'admin')
      and not exists (select 1 from app.membership_units mu where mu.membership_id = m.id)
    union all
    select 10, 'ATENÇÃO: equipes da NG sem liberação', count(*),
           string_agg(t.name, ', ' order by t.name)
    from app.teams t
    join app.units un on un.id = t.unit_id and un.code = 'NG'
    where t.org_id = (select id from o)
      and not exists (select 1 from app.access_rules r where r.team_id = t.id)
) r
order by ordem;

rollback;  -- ENSAIO. Para gravar de verdade, troque por: commit;
