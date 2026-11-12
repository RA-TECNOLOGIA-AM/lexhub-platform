-- =============================================================================
-- Membros: listar, convidar, desativar/reativar, cancelar convite e aceitar convite no login.
-- Spec: docs/superpowers/specs/2026-11-12-membros-design.md
--
-- Aditiva: só cria funções (as tabelas já existem). O front chama pelo schema api (rpc),
-- sem passar pela API em Python. Quem gere:
--   * members.manage (Owner, Desenvolvedor): todas as unidades da organização;
--   * unit.members.manage (Gestor, Controller): só as unidades em que têm esse cargo,
--     e só com cargos de unidade (nunca Owner/Desenvolvedor).
-- O convite é uma pré-autorização: vira associação quando a pessoa entra com o Google
-- (e-mail verificado) e o app chama api.accept_my_invitations(). Não sai e-mail.
-- Teste: supabase/tests/membros_test.sql (termina com rollback).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Auxiliares (app_private)
-- ---------------------------------------------------------------------------
-- Unidades ativas da organização que o usuário logado gere ('{}' = nenhuma).
create function app_private.members_scope(p_org uuid) returns uuid[]
language sql stable security definer
set search_path = ''
as $$
    select coalesce(array_agg(u.id), '{}')
    from app.units u
    where u.org_id = p_org
      and u.active
      and (
          p_org = any (app_private.my_org_ids_with('members.manage'))
          or u.id = any (app_private.my_unit_ids_with('unit.members.manage'))
      );
$$;

-- Organização pelo slug + escopo de quem chama. Sem escopo (ou slug inexistente) = 42501.
create function app_private.require_members_scope(p_org text, out org_id uuid, out scope uuid[], out is_admin boolean)
language plpgsql stable security definer
set search_path = ''
as $$
begin
    select o.id into org_id from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    scope := case when org_id is null then '{}'::uuid[] else app_private.members_scope(org_id) end;
    if cardinality(scope) = 0 then
        raise exception using errcode = '42501', message = 'Você não gere membros nesta organização.';
    end if;
    is_admin := org_id = any (app_private.my_org_ids_with('members.manage'));
end;
$$;

-- Um membro no formato da lista (unidades só as do escopo).
create function app_private.member_json(p_membership uuid, p_scope uuid[]) returns jsonb
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
                           where mt.membership_id = m.id and t.unit_id = any (p_scope)), '[]'::jsonb),
        'status', m.status,
        'last_seen_at', m.last_seen_at,
        'security', case when au.raw_app_meta_data -> 'providers' ? 'google' then 'Google' end
    )
    from app.memberships m
    left join auth.users au on au.id = m.user_id
    where m.id = p_membership;
$$;

revoke all on function app_private.members_scope(uuid) from public, anon;
revoke all on function app_private.require_members_scope(text) from public, anon;
revoke all on function app_private.member_json(uuid, uuid[]) from public, anon;
grant execute on function app_private.members_scope(uuid) to authenticated, service_role;
grant execute on function app_private.require_members_scope(text) to authenticated, service_role;
grant execute on function app_private.member_json(uuid, uuid[]) to authenticated, service_role;

-- ---------------------------------------------------------------------------
-- 2. Lista
-- ---------------------------------------------------------------------------
-- { members, invitations, teams, units, can_invite_admin }
-- Owner/Dev veem todos; Gestor/Controller, quem tem ao menos uma unidade no escopo.
create function api.list_members(p_org text) returns jsonb
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
                       'expires_at', i.expires_at
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

-- ---------------------------------------------------------------------------
-- 3. Convidar
-- ---------------------------------------------------------------------------
-- { invited: [e-mail], skipped: [{ email, reason }] }
create function api.invite_members(p_org text, p_emails text[], p_role text, p_units text[], p_teams uuid[])
returns jsonb
language plpgsql security definer
set search_path = ''
as $$
declare
    s         record;
    v_units   uuid[];
    v_teams   uuid[] := coalesce(p_teams, '{}');
    v_email   text;
    v_status  text;
    v_invited text[] := '{}';
    v_skipped jsonb := '[]'::jsonb;
begin
    select * into s from app_private.require_members_scope(p_org);

    if p_role is null or p_role not in ('admin', 'gestor', 'controller', 'colaborador', 'leitor') then
        raise exception using errcode = 'P0001', message = 'Papel inválido.';
    end if;
    if p_role = 'admin' and not s.is_admin then
        raise exception using errcode = '42501', message = 'Só Owner ou Desenvolvedor convida Desenvolvedor.';
    end if;

    select coalesce(array_agg(u.id), '{}') into v_units
    from app.units u
    where u.org_id = s.org_id and u.active and u.code = any (coalesce(p_units, '{}'));
    if cardinality(v_units) <> cardinality(array(select distinct x from unnest(coalesce(p_units, '{}')) x)) then
        raise exception using errcode = 'P0001', message = 'Unidade não encontrada.';
    end if;
    if p_role <> 'admin' and cardinality(v_units) = 0 then
        raise exception using errcode = 'P0001', message = 'Escolha ao menos uma unidade.';
    end if;
    if not (v_units <@ s.scope) then
        raise exception using errcode = '42501', message = 'Você não gere membros nesta unidade.';
    end if;
    if exists (select 1 from unnest(v_teams) tid
               where not exists (select 1 from app.teams t
                                 where t.id = tid and t.org_id = s.org_id and t.active and t.unit_id = any (v_units))) then
        raise exception using errcode = 'P0001', message = 'Equipe fora das unidades escolhidas.';
    end if;

    for v_email in
        select distinct lower(trim(e)) from unnest(coalesce(p_emails, '{}')) e where trim(e) <> ''
    loop
        if position('@' in v_email) <= 1 then
            raise exception using errcode = 'P0001', message = 'E-mail inválido: ' || v_email;
        end if;

        select m.status::text into v_status from app.memberships m
        where m.org_id = s.org_id and lower(m.email) = v_email;

        if v_status = 'active' then
            v_skipped := v_skipped || jsonb_build_object('email', v_email, 'reason', 'Já faz parte da organização');
        elsif v_status = 'disabled' then
            v_skipped := v_skipped || jsonb_build_object('email', v_email, 'reason', 'Desativado: reative na lista');
        elsif exists (select 1 from app.invitations i
                      where i.org_id = s.org_id and i.email = v_email
                        and i.accepted_at is null and i.revoked_at is null and i.expires_at > now()) then
            v_skipped := v_skipped || jsonb_build_object('email', v_email, 'reason', 'Já tem convite pendente');
        else
            -- Convite vencido ocupa o índice de pendentes (accepted/revoked nulos): encerra antes.
            update app.invitations set revoked_at = now()
             where org_id = s.org_id and email = v_email
               and accepted_at is null and revoked_at is null and expires_at <= now();

            insert into app.invitations (org_id, email, role_key, unit_ids, team_ids, token_hash, invited_by)
            values (s.org_id, v_email, p_role, v_units, v_teams, gen_random_uuid()::text, auth.uid());

            insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
            values (s.org_id, auth.uid(), 'member.invited', 'invitation', v_email,
                    jsonb_build_object('role', p_role, 'units', p_units, 'teams', v_teams));
            v_invited := v_invited || v_email;
        end if;
        v_status := null;
    end loop;

    return jsonb_build_object('invited', to_jsonb(v_invited), 'skipped', v_skipped);
end;
$$;

-- ---------------------------------------------------------------------------
-- 4. Desativar / reativar
-- ---------------------------------------------------------------------------
create function api.set_member_status(p_org text, p_member uuid, p_status text) returns jsonb
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
    -- Associação 'invited' só vira ativa pelo aceite no login (api.accept_my_invitations).
    if v_m.status = 'invited' and p_status = 'active' then
        raise exception using errcode = 'P0001',
            message = 'Esta pessoa ainda não aceitou o convite: ela precisa entrar com o Google.';
    end if;
    if v_m.user_id = auth.uid() then
        raise exception using errcode = 'P0001', message = 'Você não pode desativar a si mesmo.';
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
-- 5. Cancelar convite
-- ---------------------------------------------------------------------------
create function api.revoke_invitation(p_id uuid) returns jsonb
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
       or not (v_inv.org_id = any (app_private.my_org_ids_with('members.manage')) or v_inv.unit_ids && v_scope) then
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

-- ---------------------------------------------------------------------------
-- 6. Aceitar convites (chamada pelo app logo depois do login)
-- ---------------------------------------------------------------------------
-- Só com e-mail verificado pelo Google (auth.identities). Devolve quantos aceitou.
-- Associação desativada não é reativada por convite (o convite fica pendente).
create function api.accept_my_invitations() returns integer
language plpgsql security definer
set search_path = ''
as $$
declare
    v_uid   uuid := auth.uid();
    v_email text := lower(trim(auth.jwt() ->> 'email'));
    v_meta  jsonb := coalesce(auth.jwt() -> 'user_metadata', '{}'::jsonb);
    v_inv   app.invitations;
    v_m     app.memberships;
    v_unit  uuid;
    v_count integer := 0;
begin
    -- E-mail verificado pelo Google, lido de auth.identities: o user_metadata do token a própria
    -- pessoa edita (auth.updateUser), então não serve de prova.
    if v_uid is null or v_email is null or v_email = ''
       or not exists (select 1 from auth.identities i
                      where i.user_id = v_uid
                        and i.provider = 'google'
                        and lower(trim(i.identity_data ->> 'email')) = v_email
                        and coalesce((i.identity_data ->> 'email_verified')::boolean, false)) then
        return 0;
    end if;

    for v_inv in
        select i.* from app.invitations i
        join app.organizations o on o.id = i.org_id and o.active
        where i.email = v_email and i.accepted_at is null and i.revoked_at is null and i.expires_at > now()
        order by i.created_at
        for update of i
    loop
        select * into v_m from app.memberships m where m.org_id = v_inv.org_id and m.user_id = v_uid;
        if v_m.id is null then
            select * into v_m from app.memberships m where m.org_id = v_inv.org_id and lower(m.email) = v_email;
        end if;
        continue when v_m.status = 'disabled';

        if v_m.id is null then
            insert into app.memberships (org_id, user_id, full_name, email, role_key, status)
            values (v_inv.org_id, v_uid,
                    coalesce(nullif(trim(v_meta ->> 'full_name'), ''), nullif(trim(v_meta ->> 'name'), ''), v_email),
                    v_email, case when v_inv.role_key = 'admin' then 'admin' else 'member' end, 'active')
            returning * into v_m;
        else
            update app.memberships
               set status = 'active',
                   role_key = case when v_inv.role_key = 'admin' and role_key = 'member' then 'admin' else role_key end
             where id = v_m.id;
        end if;

        if v_inv.role_key <> 'admin' then
            foreach v_unit in array v_inv.unit_ids loop
                insert into app.membership_units (org_id, unit_id, membership_id, role_key)
                values (v_inv.org_id, v_unit, v_m.id, v_inv.role_key)
                on conflict do nothing;
            end loop;
        end if;
        insert into app.membership_teams (org_id, team_id, membership_id)
        select v_inv.org_id, t, v_m.id from unnest(v_inv.team_ids) t
        on conflict do nothing;

        update app.invitations set accepted_at = now() where id = v_inv.id;
        insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
        values (v_inv.org_id, v_uid, 'invitation.accepted', 'invitation', v_inv.id::text,
                jsonb_build_object('membership_id', v_m.id, 'role', v_inv.role_key));
        v_count := v_count + 1;
        v_m := null;
    end loop;

    return v_count;
end;
$$;

revoke all on function api.list_members(text) from public, anon;
revoke all on function api.invite_members(text, text[], text, text[], uuid[]) from public, anon;
revoke all on function api.set_member_status(text, uuid, text) from public, anon;
revoke all on function api.revoke_invitation(uuid) from public, anon;
revoke all on function api.accept_my_invitations() from public, anon;
grant execute on function api.list_members(text) to authenticated;
grant execute on function api.invite_members(text, text[], text, text[], uuid[]) to authenticated;
grant execute on function api.set_member_status(text, uuid, text) to authenticated;
grant execute on function api.revoke_invitation(uuid) to authenticated;
grant execute on function api.accept_my_invitations() to authenticated;

-- =============================================================================
-- Rollback (rodar à mão se precisar desfazer):
-- drop function api.accept_my_invitations();
-- drop function api.revoke_invitation(uuid);
-- drop function api.set_member_status(text, uuid, text);
-- drop function api.invite_members(text, text[], text, text[], uuid[]);
-- drop function api.list_members(text);
-- drop function app_private.member_json(uuid, uuid[]);
-- drop function app_private.require_members_scope(text);
-- drop function app_private.members_scope(uuid);
-- =============================================================================
