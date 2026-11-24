-- Auditoria e Membros: o primeiro acesso de quem entra por convite.
--
-- O login cria a sessão (auth.sessions) ANTES de api.accept_my_invitations criar a associação. Então o
-- trigger app_private.audit_login não achava membro: não gravava "Entrou" nem memberships.last_seen_at,
-- e Membros mostrava "Nunca acessou" para quem já tinha entrado. Além disso, 'invitation.accepted' era
-- gravado sem unidade, então sumia da Auditoria com o filtro de unidade.
--
-- 1) accept_my_invitations: grava as unidades do convite no evento; nas organizações em que a associação
--    acabou de nascer, grava o "Entrou" que o trigger perdeu (mesma sessão do JWT) e o last_seen_at.
-- 2) list_audit: "Entrou" (sem unidade) aparece na unidade de quem entrou; "Aceitou convite" na unidade do
--    convite (lida do convite, então vale também para os eventos antigos — app.audit_log é só inserção).
-- 3) Backfill: o "Entrou" perdido e o last_seen_at de quem ficou sem.

-- Igual à versão de 20261113090000_membros.sql, mais 'units' no evento e o "Entrou" do primeiro acesso.
create or replace function api.accept_my_invitations() returns integer
language plpgsql security definer
set search_path = ''
as $$
declare
    v_uid     uuid := auth.uid();
    v_email   text := lower(trim(auth.jwt() ->> 'email'));
    v_meta    jsonb := coalesce(auth.jwt() -> 'user_metadata', '{}'::jsonb);
    v_session text := auth.jwt() ->> 'session_id';
    v_inv     app.invitations;
    v_m       app.memberships;
    v_unit    uuid;
    v_count   integer := 0;
    v_new     uuid[] := '{}'; -- organizações em que a associação nasceu agora
begin
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
            v_new := v_new || v_inv.org_id;
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
                jsonb_build_object('membership_id', v_m.id, 'role', v_inv.role_key,
                                   'units', coalesce((select jsonb_agg(u.code order by u.code) from app.units u
                                                      where u.id = any (v_inv.unit_ids)), '[]'::jsonb)));
        v_count := v_count + 1;
        v_m := null;
    end loop;

    -- O "Entrou" que o trigger de login não gravou (a associação ainda não existia na hora da sessão).
    if cardinality(v_new) > 0 then
        insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata, ip, user_agent, created_at)
        select o, v_uid, 'auth.login', 'session', coalesce(s.id::text, v_session),
               jsonb_strip_nulls(jsonb_build_object('ip', host(s.ip), 'userAgent', s.user_agent)),
               s.ip, s.user_agent, coalesce(s.created_at, now())
        from unnest(v_new) o
        left join auth.sessions s on s.id::text = v_session
        where not exists (select 1 from app.audit_log a
                          where a.org_id = o and a.action = 'auth.login' and a.actor_user_id = v_uid
                            and a.target_id = coalesce(s.id::text, v_session));

        update app.memberships set last_seen_at = now()
        where user_id = v_uid and org_id = any (v_new) and status = 'active';
    end if;

    return v_count;
end;
$$;

-- Mesmo corpo de 20261123150000_plataforma_unidades_auditoria.sql + "Entrou" na unidade de quem entrou.
create or replace function api.list_audit(
    p_org text,
    p_from timestamptz default null,
    p_to timestamptz default null,
    p_actions text[] default null,
    p_exclude_actions text[] default null,
    p_actor text default null,
    p_unit text default null,
    p_limit integer default 2000
) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org     uuid := app_private.audit_org(p_org);
    v_limit   integer := greatest(1, least(coalesce(p_limit, 2000), 2000));
    v_unit    text := nullif(upper(trim(coalesce(p_unit, ''))), '');
    v_unit_id text;
    v_events  jsonb;
    v_count   integer;
    v_actors  jsonb;
begin
    if v_unit is not null then
        select u.id::text into v_unit_id from app.units u where u.org_id = v_org and u.code = v_unit;
    end if;

    with base as (
        select l.*,
               coalesce(m.full_name, au.email, 'Sistema') as actor_name,
               au.email as actor_email
        from app.audit_log l
        left join app.memberships m on m.org_id = l.org_id and m.user_id = l.actor_user_id
        left join auth.users au on au.id = l.actor_user_id
        where l.org_id = v_org
          and (p_from is null or l.created_at >= p_from)
          and (p_to is null or l.created_at < p_to)
          and (p_actions is null or l.action = any (p_actions))
          and (p_exclude_actions is null or not (l.action = any (p_exclude_actions)))
          and (v_unit is null
               or l.metadata ->> 'unit' = v_unit
               or (l.target_type = 'unit' and (l.target_id = v_unit_id or l.metadata ->> 'code' = v_unit))
               or (jsonb_typeof(l.metadata -> 'units') = 'array' and l.metadata -> 'units' ? v_unit)
               -- Entrada não tem unidade: aparece na unidade de quem entrou.
               or (l.action = 'auth.login' and exists (
                       select 1 from app.memberships am
                       join app.membership_units amu on amu.membership_id = am.id
                       where am.org_id = l.org_id and am.user_id = l.actor_user_id
                         and amu.unit_id::text = v_unit_id))
               -- Aceite de convite: a unidade vem do convite (os antigos não têm 'units' e a auditoria é imutável).
               or (l.action = 'invitation.accepted' and exists (
                       select 1 from app.invitations ai
                       where ai.id::text = l.target_id and ai.unit_ids @> array[v_unit_id::uuid])))
    ),
    page as (
        select b.*, row_number() over (order by b.created_at desc, b.id desc) as rn
        from base b
        where p_actor is null or b.actor_name = p_actor
        order by b.created_at desc, b.id desc
        limit v_limit + 1
    )
    select coalesce(jsonb_agg(
               jsonb_build_object(
                   'id', a.id::text,
                   'at', a.created_at,
                   'action', a.action,
                   'actor', a.actor_name,
                   'actorEmail', a.actor_email,
                   'targetType', a.target_type,
                   'targetId', a.target_id,
                   'targetName', case a.target_type
                       when 'dashboard' then (select c.name from app.dashboard_catalog c where c.key = a.target_id)
                       when 'unit' then (select u.name from app.units u where u.id::text = a.target_id)
                       when 'membership' then (select tm.full_name from app.memberships tm where tm.id::text = a.target_id)
                   end,
                   'metadata', a.metadata
               )
               order by a.created_at desc, a.id desc
           ) filter (where a.rn <= v_limit), '[]'::jsonb),
           count(*),
           (select coalesce(jsonb_agg(x.actor_name order by x.actor_name), '[]'::jsonb)
              from (select distinct b.actor_name from base b) x)
      into v_events, v_count, v_actors
    from page a;

    return jsonb_build_object(
        'events', v_events,
        'truncated', v_count > v_limit,
        'actors', v_actors,
        -- Todas as unidades, excluídas também (a auditoria delas continua consultável).
        'units', coalesce((
            select jsonb_agg(jsonb_build_object('code', u.code, 'name', u.name, 'deleted', not u.active)
                             order by not u.active, u.name)
            from app.units u where u.org_id = v_org
        ), '[]'::jsonb),
        -- Só a plataforma troca de organização (encerradas também).
        'orgs', case when app_private.can_see_clients() then coalesce((
            select jsonb_agg(jsonb_build_object('slug', o.slug, 'name', o.name, 'closed', not o.active)
                             order by not o.active, o.name)
            from app.organizations o
        ), '[]'::jsonb) end
    );
end;
$$;

-- --- Backfill ---

-- "Entrou" perdido: sessão aberta até 5 min antes de a associação nascer, sem "Entrou" daquela sessão.
insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata, ip, user_agent, created_at)
select m.org_id, s.user_id, 'auth.login', 'session', s.id::text,
       jsonb_strip_nulls(jsonb_build_object('ip', host(s.ip), 'userAgent', s.user_agent)),
       s.ip, s.user_agent, s.created_at
from auth.sessions s
join app.memberships m on m.user_id = s.user_id and m.status = 'active'
where s.created_at <= m.created_at and s.created_at > m.created_at - interval '5 minutes'
  and not exists (select 1 from app.audit_log a
                  where a.org_id = m.org_id and a.action = 'auth.login' and a.target_id = s.id::text);

-- last_seen_at de quem ficou sem: o evento mais recente da pessoa na organização.
update app.memberships m
   set last_seen_at = x.last_at
  from (select a.org_id, a.actor_user_id, max(a.created_at) as last_at
          from app.audit_log a group by a.org_id, a.actor_user_id) x
 where x.org_id = m.org_id and x.actor_user_id = m.user_id
   and m.status = 'active' and m.last_seen_at is null;
