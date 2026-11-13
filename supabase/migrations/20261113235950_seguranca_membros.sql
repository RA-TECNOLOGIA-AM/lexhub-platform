-- =============================================================================
-- Segurança de Membros e Acesso (revisão de 13/11):
--
--   0. Controller vira cargo de ACOMPANHAMENTO: vê todos os dashboards da unidade, exporta e vê
--      fontes, mas não gere membros nem acesso (antes tinha as mesmas permissões do Gestor).
--      Quem cuida de uma unidade e acompanha outra = Gestor na dele, Controller na outra.
--   1. api.update_member_access  Gestor não muda o próprio acesso (cargo nas unidades e equipes).
--                                Antes só o papel na organização era travado, então quem gere
--                                acesso numa unidade podia se dar cargo em outras do escopo.
--                                Owner/Desenvolvedor seguem podendo (já têm acesso a tudo).
--   2. app_private.members_scope, require_members_scope, member_json
--                                deixam de ser executáveis por `authenticated`. Só as funções
--                                SECURITY DEFINER do schema api as chamam (como dono do banco).
--                                member_json devolvia nome/e-mail/papel de qualquer associação.
--   3. api.revoke_invitation     Gestor só cancela convite que está INTEIRO nas unidades que ele
--                                gere (antes bastava uma unidade em comum, &&). Convite sem unidade
--                                (Desenvolvedor) só quem tem members.manage na org.
--                                api.list_members ganha `can_revoke` por convite (mesma regra), para
--                                a tela só mostrar Cancelar onde a pessoa pode.
--
-- update_member_access é a de 20261113235900_protege_owner.sql com a trava nova ("Próprio acesso:").
-- Teste: supabase/tests/seguranca_membros_test.sql (termina com rollback).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 0. Controller acompanha: sem gerir membros nem acesso
-- ---------------------------------------------------------------------------
delete from app.role_permissions
 where role_key = 'controller' and permission in ('unit.members.manage', 'unit.access.manage');

-- ---------------------------------------------------------------------------
-- 1. Ninguém abaixo de Desenvolvedor muda o próprio acesso
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
    -- Próprio acesso: Gestor/Controller não muda os próprios cargos e equipes.
    if v_m.user_id = auth.uid() and not v_is_admin then
        raise exception using errcode = '42501', message = 'Você não pode mudar o seu próprio acesso.';
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

-- ---------------------------------------------------------------------------
-- 2. Funções internas: só as SECURITY DEFINER do schema api chamam
-- ---------------------------------------------------------------------------
revoke execute on function app_private.members_scope(uuid) from authenticated;
revoke execute on function app_private.require_members_scope(text) from authenticated;
revoke execute on function app_private.member_json(uuid, uuid[]) from authenticated;

-- ---------------------------------------------------------------------------
-- 3. Cancelar convite: só o que está inteiro no escopo de quem chama
-- ---------------------------------------------------------------------------
create or replace function api.revoke_invitation(p_id uuid) returns jsonb
language plpgsql security definer
set search_path = ''
as $$
declare
    v_inv   app.invitations;
    v_scope uuid[];
begin
    select * into v_inv from app.invitations i where i.id = p_id for update;
    v_scope := case when v_inv.id is null then '{}'::uuid[] else app_private.members_scope(v_inv.org_id) end;
    if cardinality(v_scope) = 0
       or not (v_inv.org_id = any (app_private.my_org_ids_with('members.manage'))
               or (cardinality(v_inv.unit_ids) > 0 and v_inv.unit_ids <@ v_scope)) then
        raise exception using errcode = '42501', message = 'Você não gere este convite.';
    end if;
    if v_inv.accepted_at is not null or v_inv.revoked_at is not null then
        raise exception using errcode = 'P0001', message = 'Convite não está mais pendente.';
    end if;

    update app.invitations set revoked_at = now() where id = p_id returning * into v_inv;
    insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
    values (v_inv.org_id, auth.uid(), 'invitation.revoked', 'invitation', p_id::text,
            jsonb_build_object('email', v_inv.email));

    return jsonb_build_object('id', v_inv.id, 'revoked_at', v_inv.revoked_at);
end;
$$;

-- A lista de Membros diz, por convite, se quem chama pode cancelar.
create or replace function api.list_members(p_org text) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    s record;
begin
    select * into s from app_private.require_members_scope(p_org);

    return jsonb_build_object(
        'members', coalesce((
            select jsonb_agg(app_private.member_json(m.id, s.scope)
                             order by array_position(array['active', 'invited', 'disabled'], m.status::text), m.full_name)
            from app.memberships m
            where m.org_id = s.org_id
              and (s.is_admin or exists (select 1 from app.membership_units mu
                                         where mu.membership_id = m.id and mu.unit_id = any (s.scope)))
        ), '[]'::jsonb),
        'invitations', coalesce((
            select jsonb_agg(jsonb_build_object(
                       'id', i.id,
                       'email', i.email,
                       'role', i.role_key,
                       'units', coalesce((select jsonb_agg(u.code order by u.code) from app.units u
                                          where u.id = any (i.unit_ids)), '[]'::jsonb),
                       'teams', coalesce((select jsonb_agg(t.name order by t.name) from app.teams t
                                          where t.id = any (i.team_ids)), '[]'::jsonb),
                       'invited_by', coalesce((select im.full_name from app.memberships im
                                               where im.org_id = i.org_id and im.user_id = i.invited_by),
                                              (select au.email from auth.users au where au.id = i.invited_by)),
                       'created_at', i.created_at,
                       'expires_at', i.expires_at,
                       -- o botão Cancelar: a mesma regra de api.revoke_invitation
                       'can_revoke', s.is_admin or (cardinality(i.unit_ids) > 0 and i.unit_ids <@ s.scope)
                   ) order by i.created_at desc)
            from app.invitations i
            where i.org_id = s.org_id
              and i.accepted_at is null and i.revoked_at is null and i.expires_at > now()
              and (s.is_admin or i.unit_ids && s.scope)
        ), '[]'::jsonb),
        'teams', coalesce((
            select jsonb_agg(jsonb_build_object('id', t.id, 'name', t.name, 'unit', u.code) order by u.code, t.name)
            from app.teams t join app.units u on u.id = t.unit_id
            where t.org_id = s.org_id and t.active and t.unit_id = any (s.scope)
        ), '[]'::jsonb),
        'units', coalesce((
            select jsonb_agg(jsonb_build_object('code', u.code, 'name', u.name) order by u.code)
            from app.units u where u.id = any (s.scope)
        ), '[]'::jsonb),
        'can_invite_admin', s.is_admin
    );
end;
$$;

-- create or replace mantém os grants (authenticated) das funções api.*.

-- =============================================================================
-- Rollback (rodar à mão se precisar desfazer):
-- insert into app.role_permissions (role_key, permission) values
--     ('controller', 'unit.members.manage'), ('controller', 'unit.access.manage');
-- grant execute on function app_private.members_scope(uuid) to authenticated;
-- grant execute on function app_private.require_members_scope(text) to authenticated;
-- grant execute on function app_private.member_json(uuid, uuid[]) to authenticated;
-- recriar api.update_member_access com o corpo de 20261113235900_protege_owner.sql e
-- api.revoke_invitation e api.list_members com o corpo de 20261113090000_membros.sql.
-- =============================================================================
