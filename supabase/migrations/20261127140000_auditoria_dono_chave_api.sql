-- Auditoria: eventos da chave de API (target_type 'api_key') mostram o dono da chave em targetName.
-- Ex.: "Nicolas aprovou chave de API" passa a dizer de quem é a chave.
-- Mesmo corpo de 20261125120000_convite_primeiro_acesso.sql + o caso 'api_key'; create or replace mantém os grants.

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
                       -- Chave de API: o dono da chave (quem pediu), não quem aprovou/revogou.
                       when 'api_key' then (select km.full_name from app.api_keys k
                                              join app.memberships km on km.id = k.membership_id
                                             where k.id::text = a.target_id)
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
