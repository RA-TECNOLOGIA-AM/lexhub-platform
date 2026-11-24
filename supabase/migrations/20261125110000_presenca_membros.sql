-- Membros: "Online agora" / "Visto há N min" e a foto de perfil na lista.
--
-- 1) api.touch_presence(): o front chama a cada minuto enquanto a aba está aberta e visível; grava
--    memberships.last_seen_at = now() em todas as organizações ativas de quem chama. Antes, last_seen_at
--    só mudava no login (trigger em auth.sessions), então não dava para saber quem está online.
--    Grava no máximo a cada 30 s por pessoa (não enche o banco se houver várias abas abertas).
-- 2) app_private.member_json passa a devolver avatar_path (app.profiles), para a lista de Membros mostrar a foto.

create or replace function api.touch_presence() returns void
language sql volatile security definer
set search_path = ''
as $$
    update app.memberships
       set last_seen_at = now()
     where user_id = auth.uid()
       and status = 'active'
       and (last_seen_at is null or last_seen_at < now() - interval '30 seconds');
$$;

revoke all on function api.touch_presence() from public, anon;
grant execute on function api.touch_presence() to authenticated;

-- Igual à versão de 20261119170000_grupos_acesso.sql, mais 'avatar_path'.
create or replace function app_private.member_json(p_membership uuid, p_scope uuid[])
returns jsonb
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
        'extra_groups', coalesce((select jsonb_agg(jsonb_build_object('unit', u.code, 'slug', g.group_slug)
                                                   order by u.code, g.group_slug)
                                  from app.member_group_grants g join app.units u on u.id = g.unit_id
                                  where g.membership_id = m.id and g.unit_id = any (p_scope)), '[]'::jsonb),
        'extra_dashboards', coalesce((select jsonb_agg(jsonb_build_object('unit', u.code, 'key', g.dashboard_key)
                                                       order by u.code, g.dashboard_key)
                                      from app.member_dashboard_grants g join app.units u on u.id = g.unit_id
                                      where g.membership_id = m.id and g.unit_id = any (p_scope)), '[]'::jsonb),
        'status', m.status,
        'last_seen_at', m.last_seen_at,
        'avatar_path', p.avatar_path,
        'security', case when au.raw_app_meta_data -> 'providers' ? 'google' then 'Google' end
    )
    from app.memberships m
    left join auth.users au on au.id = m.user_id
    left join app.profiles p on p.user_id = m.user_id
    where m.id = p_membership;
$$;
