-- =============================================================================
-- Protege o Owner: Desenvolvedor (admin) não mexe mais no Owner.
--
--   app_private.can_manage_owners(org)  quem chama é Owner ativo da org ou da equipe RA (platform_staff)
--   api.set_member_status                desativar/reativar um Owner só com can_manage_owners;
--                                        a org nunca fica sem Owner ativo (se tiver algum)
--   api.update_member_access             mudar cargos/equipes de um Owner só com can_manage_owners
--
-- Antes: o Desenvolvedor pulava a checagem de hierarquia e a trava de "último" contava Owner e
-- Desenvolvedor juntos, então um Dev conseguia desativar o único Owner.
-- As funções são as mesmas de 20261113090000_membros.sql e 20261113140000_acesso.sql, só com as
-- travas novas (marcadas com "Owner:").
-- Teste: supabase/tests/protege_owner_test.sql (termina com rollback).
-- =============================================================================

create function app_private.can_manage_owners(p_org uuid) returns boolean
language sql stable security definer
set search_path = ''
as $$
    select app_private.is_platform_staff()
        or exists (select 1 from app.memberships me
                   where me.org_id = p_org and me.user_id = auth.uid()
                     and me.role_key = 'owner' and me.status = 'active');
$$;
revoke all on function app_private.can_manage_owners(uuid) from public, anon, authenticated;
grant execute on function app_private.can_manage_owners(uuid) to service_role;

-- ---------------------------------------------------------------------------
-- 1. Desativar / reativar
-- ---------------------------------------------------------------------------
create or replace function api.set_member_status(p_org text, p_member uuid, p_status text) returns jsonb
language plpgsql security definer
set search_path = ''
as $$
declare
    s   record;
    v_m app.memberships;
begin
    select * into s from app_private.require_members_scope(p_org);

    if p_status is null or p_status not in ('active', 'disabled') then
        raise exception using errcode = 'P0001', message = 'Situação inválida.';
    end if;

    select * into v_m from app.memberships m where m.id = p_member and m.org_id = s.org_id for update;
    -- Gestor/Controller: só quem está INTEIRO nas unidades que ele gere (desativar vale para a
    -- organização toda; não pode cortar o acesso da pessoa em unidade alheia). Nunca Owner/Dev.
    if v_m.id is null
       or (not s.is_admin and (v_m.role_key in ('owner', 'admin')
                               or not exists (select 1 from app.membership_units mu
                                              where mu.membership_id = v_m.id and mu.unit_id = any (s.scope))
                               or exists (select 1 from app.membership_units mu
                                          where mu.membership_id = v_m.id and mu.unit_id <> all (s.scope)))) then
        raise exception using errcode = '42501', message = 'Você não gere este membro.';
    end if;
    -- Owner: só outro Owner (ou a equipe RA) desativa ou reativa um Owner.
    if v_m.role_key = 'owner' and not app_private.can_manage_owners(s.org_id) then
        raise exception using errcode = '42501', message = 'Só um Owner desativa ou reativa outro Owner.';
    end if;
    -- Associação 'invited' só vira ativa pelo aceite no login (api.accept_my_invitations).
    if v_m.status = 'invited' and p_status = 'active' then
        raise exception using errcode = 'P0001',
            message = 'Esta pessoa ainda não aceitou o convite: ela precisa entrar com o Google.';
    end if;
    if v_m.user_id = auth.uid() then
        raise exception using errcode = 'P0001', message = 'Você não pode desativar a si mesmo.';
    end if;
    -- Owner: a organização que tem Owner nunca fica sem Owner ativo.
    if p_status = 'disabled' and v_m.role_key = 'owner' and v_m.status = 'active'
       and not exists (select 1 from app.memberships o
                       where o.org_id = s.org_id and o.id <> v_m.id
                         and o.role_key = 'owner' and o.status = 'active') then
        raise exception using errcode = 'P0001', message = 'A organização precisa de ao menos um Owner ativo.';
    end if;
    if p_status = 'disabled' and v_m.role_key in ('owner', 'admin') and v_m.status = 'active'
       and not exists (select 1 from app.memberships o
                       where o.org_id = s.org_id and o.id <> v_m.id
                         and o.role_key in ('owner', 'admin') and o.status = 'active') then
        raise exception using errcode = 'P0001',
            message = 'A organização precisa de ao menos um Owner ou Desenvolvedor ativo.';
    end if;

    if v_m.status::text <> p_status then
        update app.memberships set status = p_status::app.member_status where id = v_m.id;
        insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
        values (s.org_id, auth.uid(),
                case when p_status = 'disabled' then 'member.disabled' else 'member.enabled' end,
                'membership', v_m.id::text, jsonb_build_object('email', v_m.email));
    end if;

    return app_private.member_json(v_m.id, s.scope);
end;
$$;

-- ---------------------------------------------------------------------------
-- 2. Editar cargo por unidade, equipes e papel de Desenvolvedor
-- ---------------------------------------------------------------------------
create or replace function api.update_member_access(p_org text, p_member uuid, p_units jsonb, p_teams uuid[], p_org_role text)
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

-- create or replace mantém os grants (authenticated) de membros.sql e acesso.sql.

-- =============================================================================
-- Rollback (rodar à mão se precisar desfazer):
-- recriar api.set_member_status com o corpo de 20261113090000_membros.sql e
-- api.update_member_access com o corpo de 20261113140000_acesso.sql; depois
-- drop function app_private.can_manage_owners(uuid);
-- =============================================================================
