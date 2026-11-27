-- Owner e Desenvolvedor da LexGroup (a organização com platform_owner) entram em toda organização cliente
-- com o mesmo papel: hub, dashboards e administração funcionam como na LexGroup, porque todo o resto
-- (banco e API) já libera pela associação. São eles que conectam as fontes e criam os dashboards.
--
-- * app.memberships.via_lexgroup: a associação automática. O cliente não vê (Membros), não conta
--   assento e não edita (gatilho trava update/delete fora da sincronização).
-- * app_private.sync_lexgroup_access(): cria, ajusta o papel ou remove as automáticas. Roda ao criar
--   organização e quando muda uma associação da LexGroup (entrou, virou Owner/Dev, saiu, foi desativado).
-- * Owner de cliente continua vendo só a própria organização: nada muda para quem não é da LexGroup.
-- * Quem já é membro de verdade do cliente fica como está (a automática não é criada por cima).

alter table app.memberships add column via_lexgroup boolean not null default false;

comment on column app.memberships.via_lexgroup is
    'Associação automática de Owner/Dev da LexGroup (app_private.sync_lexgroup_access). Escondida do cliente.';

-- ---------------------------------------------------------------------------
-- 1. Sincronização
-- ---------------------------------------------------------------------------
-- Quem deve ter: Owner/Dev ativos da LexGroup x organizações clientes ativas.
create function app_private.lexgroup_wanted()
returns table (org_id uuid, user_id uuid, full_name text, email text, role_key text)
language sql stable security definer
set search_path = ''
as $$
    select o.id, m.user_id, m.full_name, m.email, m.role_key
    from app.memberships m
    join app.organizations lg on lg.id = m.org_id and lg.platform_owner
    cross join app.organizations o
    where m.status = 'active'
      and m.role_key in ('owner', 'admin')
      and not m.via_lexgroup
      and o.active
      and not o.platform_owner;
$$;
revoke all on function app_private.lexgroup_wanted() from public, anon, authenticated;

create function app_private.sync_lexgroup_access() returns void
language plpgsql security definer
set search_path = ''
as $$
begin
    -- Libera a trava abaixo só durante esta transação.
    perform set_config('app.lexgroup_sync', 'on', true);

    -- Sai: automática que não deve mais existir.
    delete from app.memberships m
    where m.via_lexgroup
      and not exists (select 1 from app_private.lexgroup_wanted() w
                      where w.org_id = m.org_id and w.user_id = m.user_id);

    -- Ajusta: papel, nome ou e-mail mudaram na LexGroup.
    update app.memberships m
       set role_key = w.role_key, full_name = w.full_name, email = w.email, status = 'active'
      from app_private.lexgroup_wanted() w
     where m.via_lexgroup and w.org_id = m.org_id and w.user_id = m.user_id
       and (m.role_key, m.full_name, m.email, m.status::text)
           is distinct from (w.role_key, w.full_name, w.email, 'active');

    -- Entra: quem ainda não tem associação nenhuma no cliente (membro de verdade fica como está).
    insert into app.memberships (org_id, user_id, full_name, email, status, role_key, via_lexgroup)
    select w.org_id, w.user_id, w.full_name, w.email, 'active', w.role_key, true
    from app_private.lexgroup_wanted() w
    where not exists (select 1 from app.memberships m where m.org_id = w.org_id and m.user_id = w.user_id);

    perform set_config('app.lexgroup_sync', 'off', true);
end;
$$;
revoke all on function app_private.sync_lexgroup_access() from public, anon, authenticated;

-- ---------------------------------------------------------------------------
-- 2. Gatilhos que chamam a sincronização
-- ---------------------------------------------------------------------------
create function app_private.lexgroup_sync_trigger() returns trigger
language plpgsql security definer
set search_path = ''
as $$
begin
    perform app_private.sync_lexgroup_access();
    return null;
end;
$$;
revoke all on function app_private.lexgroup_sync_trigger() from public, anon, authenticated;

-- Organização criada, reaberta ou encerrada.
create trigger lexgroup_sync_orgs
after insert or update of active on app.organizations
for each statement execute function app_private.lexgroup_sync_trigger();

-- Associação da LexGroup mudou. A condição evita rodar de novo pelas próprias automáticas
-- (que são de outras organizações) e por mudanças que não importam (ex.: last_seen_at).
create function app_private.lexgroup_membership_changed() returns trigger
language plpgsql security definer
set search_path = ''
as $$
declare
    v_row app.memberships := coalesce(new, old);
begin
    if v_row.via_lexgroup then
        return null;
    end if;
    if tg_op = 'UPDATE'
       and (new.role_key, new.status, new.full_name, new.email)
           is not distinct from (old.role_key, old.status, old.full_name, old.email) then
        return null;
    end if;
    if exists (select 1 from app.organizations o where o.id = v_row.org_id and o.platform_owner) then
        perform app_private.sync_lexgroup_access();
    end if;
    return null;
end;
$$;
revoke all on function app_private.lexgroup_membership_changed() from public, anon, authenticated;

create trigger lexgroup_sync_memberships
after insert or update or delete on app.memberships
for each row execute function app_private.lexgroup_membership_changed();

-- ---------------------------------------------------------------------------
-- 3. Trava: o cliente não edita nem remove a automática (só a sincronização mexe)
-- ---------------------------------------------------------------------------
create function app_private.guard_lexgroup_membership() returns trigger
language plpgsql security definer
set search_path = ''
as $$
begin
    if coalesce(current_setting('app.lexgroup_sync', true), 'off') = 'on' then
        return coalesce(new, old);
    end if;
    -- Apagar em cascata (organização ou usuário apagados de vez): liberado.
    if tg_op = 'DELETE'
       and (not exists (select 1 from app.organizations o where o.id = old.org_id)
            or not exists (select 1 from auth.users u where u.id = old.user_id)) then
        return old;
    end if;
    -- last_seen_at (presença) e updated_at mudam sozinhos: liberados.
    if tg_op = 'UPDATE'
       and (new.role_key, new.status, new.org_id, new.user_id, new.via_lexgroup)
           is not distinct from (old.role_key, old.status, old.org_id, old.user_id, old.via_lexgroup) then
        return new;
    end if;
    raise exception using errcode = '42501', message = 'O acesso da equipe LexGroup não muda por aqui.';
end;
$$;
revoke all on function app_private.guard_lexgroup_membership() from public, anon, authenticated;

create trigger guard_lexgroup_membership
before update or delete on app.memberships
for each row when (old.via_lexgroup)
execute function app_private.guard_lexgroup_membership();

-- ---------------------------------------------------------------------------
-- 4. Escondida do cliente: assentos e Membros
-- ---------------------------------------------------------------------------
create or replace function app_private.usage_of(p_org uuid)
returns table(seats integer, units integer, sources integer)
language sql stable security definer
set search_path = ''
as $$
    select (select count(*)::integer from app.memberships m
             where m.org_id = p_org and m.status = 'active' and not m.via_lexgroup),
           (select count(*)::integer from app.units u where u.org_id = p_org and u.active),
           (select count(*)::integer from app.data_sources d where d.org_id = p_org and d.active);
$$;

-- Mesmo corpo da versão no banco em 27/11 + "and not m.via_lexgroup" na lista de membros.
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
              and not m.via_lexgroup
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

-- ---------------------------------------------------------------------------
-- 5. Primeira carga
-- ---------------------------------------------------------------------------
select app_private.sync_lexgroup_access();

-- Desfazer:
-- drop trigger guard_lexgroup_membership on app.memberships;
-- drop trigger lexgroup_sync_memberships on app.memberships;
-- drop trigger lexgroup_sync_orgs on app.organizations;
-- delete from app.memberships where via_lexgroup;   -- (com a trava já removida)
-- drop function app_private.guard_lexgroup_membership();
-- drop function app_private.lexgroup_membership_changed();
-- drop function app_private.lexgroup_sync_trigger();
-- drop function app_private.sync_lexgroup_access();
-- drop function app_private.lexgroup_wanted();
-- (voltar app_private.usage_of e api.list_members para a versão anterior)
-- alter table app.memberships drop column via_lexgroup;
