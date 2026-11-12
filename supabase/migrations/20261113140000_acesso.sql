-- =============================================================================
-- Acesso: o que cada cargo vê por unidade e edição de cargo por unidade, equipes e papel de Desenvolvedor.
-- Spec: docs/superpowers/specs/2026-11-13-acesso-design.md
--
-- Aditiva: só cria funções. O front chama pelo schema api (rpc), sem a API em Python. Quem gere:
--   * access.manage (Owner, Desenvolvedor): todas as unidades + papel de Desenvolvedor;
--   * unit.access.manage (Gestor, Controller): só as unidades em que têm esse cargo; nunca editam
--     Owner/Desenvolvedor nem o papel na organização.
-- A regra de quem vê o quê continua em app_private.dashboard_scope (não muda aqui).
-- Teste: supabase/tests/acesso_test.sql (termina com rollback).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Auxiliar: unidades ativas da organização em que quem chama gere acesso ('{}' = nenhuma)
-- ---------------------------------------------------------------------------
create function app_private.access_scope(p_org uuid) returns uuid[]
language sql stable security definer
set search_path = ''
as $$
    select coalesce(array_agg(u.id), '{}')
    from app.units u
    where u.org_id = p_org
      and u.active
      and (
          p_org = any (app_private.my_org_ids_with('access.manage'))
          or u.id = any (app_private.my_unit_ids_with('unit.access.manage'))
      );
$$;

-- Só as funções do schema api (que rodam como dono) chamam o auxiliar.
revoke all on function app_private.access_scope(uuid) from public, anon, authenticated;

-- O membro no formato da lista ganha team_ids: o nome da equipe se repete entre unidades
-- (ex.: Diretoria em cada uma), e o editor precisa saber qual marcar. Mesmo corpo da versão de
-- 20261113090000_membros.sql + team_ids, e só equipes ativas (as que a tela mostra e edita).
create or replace function app_private.member_json(p_membership uuid, p_scope uuid[]) returns jsonb
language sql stable security definer
set search_path = ''
as $$
    select jsonb_build_object(
        'id', m.id,
        'name', m.full_name,
        'email', m.email,
        'org_role', m.role_key,
        'units', coalesce((select jsonb_agg(jsonb_build_object('code', u.code, 'role', mu.role_key) order by u.code)
                           from app.membership_units mu join app.units u on u.id = mu.unit_id
                           where mu.membership_id = m.id and mu.unit_id = any (p_scope)), '[]'::jsonb),
        'teams', coalesce((select jsonb_agg(t.name order by t.name)
                           from app.membership_teams mt join app.teams t on t.id = mt.team_id
                           where mt.membership_id = m.id and t.active and t.unit_id = any (p_scope)), '[]'::jsonb),
        'team_ids', coalesce((select jsonb_agg(t.id order by t.name, t.id)
                              from app.membership_teams mt join app.teams t on t.id = mt.team_id
                              where mt.membership_id = m.id and t.active and t.unit_id = any (p_scope)), '[]'::jsonb),
        'status', m.status,
        'last_seen_at', m.last_seen_at,
        'security', case when au.raw_app_meta_data -> 'providers' ? 'google' then 'Google' end
    )
    from app.memberships m
    left join auth.users au on au.id = m.user_id
    where m.id = p_membership;
$$;

-- ---------------------------------------------------------------------------
-- 2. Visão da unidade: a grade "o que cada cargo vê" + o que o editor precisa
-- ---------------------------------------------------------------------------
create function api.access_overview(p_org text, p_unit text) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org   uuid;
    v_scope uuid[];
    v_unit  app.units;
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    v_scope := case when v_org is null then '{}'::uuid[] else app_private.access_scope(v_org) end;
    if cardinality(v_scope) = 0 then
        raise exception using errcode = '42501', message = 'Você não gere acesso nesta organização.';
    end if;

    -- Unidade pedida (?unidade=); se não for uma que quem chama gere (link salvo, ou acabou de tirar
    -- o próprio cargo nela), cai na primeira gerida em vez de esconder a página inteira.
    select * into v_unit from app.units u
    where u.id = any (v_scope)
    order by (u.code = p_unit) desc nulls last, u.code
    limit 1;

    return jsonb_build_object(
        'units', (select jsonb_agg(jsonb_build_object('code', u.code, 'name', u.name) order by u.code)
                  from app.units u where u.id = any (v_scope)),
        'unit', v_unit.code,
        'dashboards', coalesce((
            select jsonb_agg(jsonb_build_object(
                       'key', d.key,
                       'title', d.name,
                       'area', d.area,
                       'teams', coalesce((select jsonb_agg(t.name order by t.name)
                                          from app.access_rules r
                                          join app.teams t on t.id = r.team_id and t.active and t.unit_id = v_unit.id
                                          where r.dashboard_key = d.key), '[]'::jsonb)
                   ) order by d.sort_order, d.name)
            from app.org_dashboards od
            join app.dashboard_catalog d on d.key = od.dashboard_key and d.active
            where od.unit_id = v_unit.id and od.enabled
        ), '[]'::jsonb),
        'teams', coalesce((
            select jsonb_agg(jsonb_build_object('id', t.id, 'name', t.name, 'unit', u.code) order by u.code, t.name)
            from app.teams t join app.units u on u.id = t.unit_id
            where t.active and t.unit_id = any (v_scope)
        ), '[]'::jsonb),
        'roles', (
            select jsonb_agg(jsonb_build_object(
                       'key', ro.key,
                       'sees_all', exists (select 1 from app.role_permissions rp
                                           where rp.role_key = ro.key and rp.permission = 'unit.dashboards.all'),
                       'exports', exists (select 1 from app.role_permissions rp
                                          where rp.role_key = ro.key and rp.permission = 'dashboards.export')
                   ) order by ro.sort_order)
            from app.roles ro where ro.level = 'unit'
        ),
        'rules', coalesce((
            select jsonb_agg(jsonb_build_object('team_id', r.team_id, 'dashboard_key', r.dashboard_key))
            from app.access_rules r
            join app.teams t on t.id = r.team_id and t.active and t.unit_id = any (v_scope)
        ), '[]'::jsonb),
        'dashboards_by_unit', (
            select jsonb_object_agg(u.code, coalesce((
                       select jsonb_agg(d.key order by d.sort_order, d.name)
                       from app.org_dashboards od
                       join app.dashboard_catalog d on d.key = od.dashboard_key and d.active
                       where od.unit_id = u.id and od.enabled), '[]'::jsonb))
            from app.units u where u.id = any (v_scope)
        ),
        'titles', coalesce((
            select jsonb_object_agg(x.key, x.name)
            from (select distinct d.key, d.name
                  from app.org_dashboards od
                  join app.dashboard_catalog d on d.key = od.dashboard_key and d.active
                  where od.unit_id = any (v_scope) and od.enabled) x
        ), '{}'::jsonb),
        'can_set_org_role', v_org = any (app_private.my_org_ids_with('access.manage'))
    );
end;
$$;

-- ---------------------------------------------------------------------------
-- 3. Editar cargo por unidade, equipes e papel de Desenvolvedor
-- ---------------------------------------------------------------------------
-- p_units: estado desejado NAS unidades que quem chama gere ([{ code, role }]; unidade ausente = sai).
-- p_teams: estado desejado das equipes NESSAS unidades. p_org_role: null = não muda; 'admin' | 'member'.
-- Unidades e equipes fora do escopo de quem chama ficam intactas.
create function api.update_member_access(p_org text, p_member uuid, p_units jsonb, p_teams uuid[], p_org_role text)
returns jsonb
language plpgsql security definer
set search_path = ''
as $$
declare
    v_org      uuid;
    v_scope    uuid[];
    v_is_admin boolean;
    v_m        app.memberships;
    v_item     jsonb;
    v_unit     uuid;
    v_role     text;
    v_units    uuid[] := '{}';
    v_roles    text[] := '{}';
    v_teams    uuid[] := coalesce(p_teams, '{}');
    v_before   jsonb;
    v_after    jsonb;
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    v_scope := case when v_org is null then '{}'::uuid[] else app_private.access_scope(v_org) end;
    if cardinality(v_scope) = 0 then
        raise exception using errcode = '42501', message = 'Você não gere acesso nesta organização.';
    end if;
    v_is_admin := v_org = any (app_private.my_org_ids_with('access.manage'));

    select * into v_m from app.memberships m where m.id = p_member and m.org_id = v_org for update;
    if v_m.id is null or (not v_is_admin and v_m.role_key in ('owner', 'admin')) then
        raise exception using errcode = '42501', message = 'Você não gere o acesso desta pessoa.';
    end if;
    if v_m.status = 'disabled' then
        raise exception using errcode = 'P0001', message = 'Reative a pessoa antes de mudar o acesso.';
    end if;

    -- Papel na organização (Desenvolvedor <-> Membro)
    if p_org_role is not null then
        if not v_is_admin then
            raise exception using errcode = '42501', message = 'Só Owner ou Desenvolvedor muda o papel na organização.';
        end if;
        if p_org_role not in ('admin', 'member') then
            raise exception using errcode = 'P0001', message = 'Papel na organização inválido.';
        end if;
        if v_m.role_key = 'owner' and p_org_role <> 'owner' then
            raise exception using errcode = 'P0001', message = 'O Owner não muda de papel por aqui.';
        end if;
        if v_m.user_id = auth.uid() and p_org_role <> v_m.role_key then
            raise exception using errcode = 'P0001', message = 'Você não pode mudar o seu próprio papel.';
        end if;
        if v_m.role_key = 'admin' and p_org_role = 'member' and v_m.status = 'active'
           and not exists (select 1 from app.memberships o
                           where o.org_id = v_org and o.id <> v_m.id
                             and o.role_key in ('owner', 'admin') and o.status = 'active') then
            raise exception using errcode = 'P0001',
                message = 'A organização precisa de ao menos um Owner ou Desenvolvedor ativo.';
        end if;
    end if;

    -- Cargos desejados (só unidades do escopo)
    for v_item in select * from jsonb_array_elements(coalesce(p_units, '[]'::jsonb)) loop
        select u.id into v_unit from app.units u
        where u.org_id = v_org and u.active and u.code = v_item ->> 'code';
        if v_unit is null or not (v_unit = any (v_scope)) then
            raise exception using errcode = '42501', message = 'Você não gere acesso nesta unidade.';
        end if;
        v_role := v_item ->> 'role';
        if v_role is null or v_role not in (select ro.key from app.roles ro where ro.level = 'unit') then
            raise exception using errcode = 'P0001', message = 'Cargo inválido.';
        end if;
        if v_unit = any (v_units) then
            raise exception using errcode = 'P0001', message = 'Unidade repetida.';
        end if;
        v_units := v_units || v_unit;
        v_roles := v_roles || v_role;
        v_unit := null;
    end loop;

    -- Equipes desejadas: de unidade do escopo e com cargo nela
    if exists (select 1 from unnest(v_teams) tid
               where not exists (select 1 from app.teams t
                                 where t.id = tid and t.org_id = v_org and t.active and t.unit_id = any (v_scope))) then
        raise exception using errcode = '42501', message = 'Você não gere esta equipe.';
    end if;
    if exists (select 1 from app.teams t where t.id = any (v_teams) and not (t.unit_id = any (v_units))) then
        raise exception using errcode = 'P0001', message = 'Equipe sem cargo na unidade.';
    end if;

    v_before := app_private.member_json(v_m.id, v_scope);

    -- Cargos: tira das unidades do escopo que não estão na lista; grava os desejados
    delete from app.membership_units mu
     where mu.membership_id = v_m.id and mu.unit_id = any (v_scope) and not (mu.unit_id = any (v_units));
    for i in 1 .. cardinality(v_units) loop
        insert into app.membership_units (org_id, unit_id, membership_id, role_key)
        values (v_org, v_units[i], v_m.id, v_roles[i])
        on conflict (unit_id, membership_id) do update set role_key = excluded.role_key;
    end loop;

    -- Equipes: só as das unidades do escopo
    delete from app.membership_teams mt
     using app.teams t
     where mt.membership_id = v_m.id and t.id = mt.team_id and t.unit_id = any (v_scope)
       and t.active  -- só as equipes que a tela mostra; equipe inativa fica como está
       and not (mt.team_id = any (v_teams));
    insert into app.membership_teams (org_id, team_id, membership_id)
    select v_org, tid, v_m.id from unnest(v_teams) tid
    on conflict do nothing;

    if p_org_role is not null and p_org_role <> v_m.role_key then
        update app.memberships set role_key = p_org_role where id = v_m.id;
    end if;

    v_after := app_private.member_json(v_m.id, v_scope);
    if v_after <> v_before then
        insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
        values (v_org, auth.uid(), 'member.access_updated', 'membership', v_m.id::text,
                jsonb_build_object('before', v_before, 'after', v_after));
    end if;

    return v_after;
end;
$$;

revoke all on function api.access_overview(text, text) from public, anon;
revoke all on function api.update_member_access(text, uuid, jsonb, uuid[], text) from public, anon;
grant execute on function api.access_overview(text, text) to authenticated;
grant execute on function api.update_member_access(text, uuid, jsonb, uuid[], text) to authenticated;

-- =============================================================================
-- Rollback (rodar à mão se precisar desfazer):
-- drop function api.update_member_access(text, uuid, jsonb, uuid[], text);
-- drop function api.access_overview(text, text);
-- drop function app_private.access_scope(uuid);
-- (member_json: recriar com o corpo de 20261113090000_membros.sql, sem team_ids)
-- =============================================================================
