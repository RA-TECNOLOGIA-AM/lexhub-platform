-- =============================================================================
-- Desenvolvedor dá Owner: api.update_member_access aceita p_org_role = 'owner'.
--
--   Quem: Owner ou Desenvolvedor (access.manage), nunca o próprio papel.
--   Continua: só Owner (ou a equipe RA) muda/rebaixa um Owner (can_manage_owners); por isso,
--   depois de salvo, o Desenvolvedor não desfaz — o front avisa antes de salvar.
-- A função é a mesma de 20261119170000_grupos_acesso.sql, só com a lista de papéis aceitos maior.
-- Teste: supabase/tests/dev_da_owner_test.sql (termina com rollback).
-- =============================================================================
create or replace function api.update_member_access(p_org text, p_member uuid, p_units jsonb, p_teams uuid[], p_org_role text,
                                         p_extra_groups jsonb default null, p_extra_dashboards jsonb default null)
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
    -- Owner: só outro Owner (ou a equipe RA) mexe nos cargos e equipes de um Owner.
    if v_m.role_key = 'owner' and not app_private.can_manage_owners(v_org) then
        raise exception using errcode = '42501', message = 'Só um Owner muda o acesso de outro Owner.';
    end if;
    -- Próprio acesso: Gestor/Controller não muda os próprios cargos e equipes.
    if v_m.user_id = auth.uid() and not v_is_admin then
        raise exception using errcode = '42501', message = 'Você não pode mudar o seu próprio acesso.';
    end if;
    if v_m.status = 'disabled' then
        raise exception using errcode = 'P0001', message = 'Reative a pessoa antes de mudar o acesso.';
    end if;

    -- Papel na organização (Membro, Desenvolvedor ou Owner)
    if p_org_role is not null then
        if not v_is_admin then
            raise exception using errcode = '42501', message = 'Só Owner ou Desenvolvedor muda o papel na organização.';
        end if;
        if p_org_role not in ('owner', 'admin', 'member') then
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

    -- Exceções desejadas: unidade do escopo, com cargo nela; grupo e dashboard que existem
    if p_extra_groups is not null then
        if exists (select 1 from jsonb_array_elements(p_extra_groups) e
                   left join app.units u on u.org_id = v_org and u.active and u.code = e ->> 'unit'
                   where u.id is null or not (u.id = any (v_scope))) then
            raise exception using errcode = '42501', message = 'Você não gere acesso nesta unidade.';
        end if;
        if exists (select 1 from jsonb_array_elements(p_extra_groups) e
                   join app.units u on u.org_id = v_org and u.code = e ->> 'unit'
                   where not (u.id = any (v_units))) then
            raise exception using errcode = 'P0001', message = 'Grupo extra sem cargo na unidade.';
        end if;
        if exists (select 1 from jsonb_array_elements(p_extra_groups) e
                   where not exists (select 1 from app.hub_groups g where g.slug = e ->> 'slug')) then
            raise exception using errcode = 'P0001', message = 'Grupo inválido.';
        end if;
    end if;
    if p_extra_dashboards is not null then
        if exists (select 1 from jsonb_array_elements(p_extra_dashboards) e
                   left join app.units u on u.org_id = v_org and u.active and u.code = e ->> 'unit'
                   where u.id is null or not (u.id = any (v_scope))) then
            raise exception using errcode = '42501', message = 'Você não gere acesso nesta unidade.';
        end if;
        if exists (select 1 from jsonb_array_elements(p_extra_dashboards) e
                   join app.units u on u.org_id = v_org and u.code = e ->> 'unit'
                   where not (u.id = any (v_units))) then
            raise exception using errcode = 'P0001', message = 'Dashboard avulso sem cargo na unidade.';
        end if;
        if exists (select 1 from jsonb_array_elements(p_extra_dashboards) e
                   join app.units u on u.org_id = v_org and u.code = e ->> 'unit'
                   where not exists (select 1 from app.org_dashboards od
                                     where od.unit_id = u.id and od.dashboard_key = e ->> 'key')) then
            raise exception using errcode = 'P0001', message = 'Dashboard avulso não existe nesta unidade.';
        end if;
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

    -- Exceções: unidade do escopo sem cargo perde todas; o resto só muda quando veio a lista
    delete from app.member_group_grants g
     where g.membership_id = v_m.id and g.unit_id = any (v_scope) and not (g.unit_id = any (v_units));
    delete from app.member_dashboard_grants g
     where g.membership_id = v_m.id and g.unit_id = any (v_scope) and not (g.unit_id = any (v_units));
    if p_extra_groups is not null then
        delete from app.member_group_grants g
         where g.membership_id = v_m.id and g.unit_id = any (v_scope)
           and not exists (select 1 from jsonb_array_elements(p_extra_groups) e
                           join app.units u on u.org_id = v_org and u.code = e ->> 'unit'
                           where u.id = g.unit_id and e ->> 'slug' = g.group_slug);
        insert into app.member_group_grants (membership_id, unit_id, group_slug, created_by)
        select v_m.id, u.id, e ->> 'slug', auth.uid()
        from jsonb_array_elements(p_extra_groups) e
        join app.units u on u.org_id = v_org and u.code = e ->> 'unit'
        on conflict do nothing;
    end if;
    if p_extra_dashboards is not null then
        delete from app.member_dashboard_grants g
         where g.membership_id = v_m.id and g.unit_id = any (v_scope)
           and not exists (select 1 from jsonb_array_elements(p_extra_dashboards) e
                           join app.units u on u.org_id = v_org and u.code = e ->> 'unit'
                           where u.id = g.unit_id and e ->> 'key' = g.dashboard_key);
        insert into app.member_dashboard_grants (membership_id, unit_id, dashboard_key, created_by)
        select v_m.id, u.id, e ->> 'key', auth.uid()
        from jsonb_array_elements(p_extra_dashboards) e
        join app.units u on u.org_id = v_org and u.code = e ->> 'unit'
        on conflict do nothing;
    end if;

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

revoke all on function api.update_member_access(text, uuid, jsonb, uuid[], text, jsonb, jsonb) from public, anon;
grant execute on function api.update_member_access(text, uuid, jsonb, uuid[], text, jsonb, jsonb) to authenticated;
