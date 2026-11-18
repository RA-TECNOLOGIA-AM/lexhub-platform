-- =============================================================================
-- Auditoria: coluna "E-mail" (a conta usada por quem fez; no login, o e-mail com que a pessoa entrou).
--
-- Troca api.list_audit (mesmo corpo de 20261113230000_auditoria.sql) só para devolver 'actorEmail':
-- o e-mail de auth.users; sem pessoa (evento do sistema), null.
-- Teste: supabase/tests/auditoria_test.sql (confere o actorEmail).
-- =============================================================================

create or replace function api.list_audit(p_org text, p_limit integer default 500) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org uuid;
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    if v_org is null or not (v_org = any (app_private.my_org_ids_with('audit.view'))) then
        raise exception using errcode = '42501', message = 'Só Owner ou Desenvolvedor veem a auditoria.';
    end if;

    return jsonb_build_object('events', coalesce((
        select jsonb_agg(
            jsonb_build_object(
                'id', a.id::text,
                'at', a.created_at,
                'action', a.action,
                -- Quem fez: o nome na organização; sem associação, o e-mail; sem pessoa, o sistema.
                'actor', coalesce(m.full_name, au.email, 'Sistema'),
                -- A conta usada (auth.users); sem pessoa, null.
                'actorEmail', au.email,
                'targetType', a.target_type,
                'targetId', a.target_id,
                -- O nome do alvo, quando dá para achar (o detalhe fica legível sem ids).
                'targetName', case a.target_type
                    when 'dashboard' then (select c.name from app.dashboard_catalog c where c.key = a.target_id)
                    when 'unit' then (select u.name from app.units u where u.id::text = a.target_id)
                    when 'membership' then (select tm.full_name from app.memberships tm where tm.id::text = a.target_id)
                end,
                'metadata', a.metadata
            )
            order by a.created_at desc, a.id desc
        )
        from (
            select * from app.audit_log
            where org_id = v_org
            order by created_at desc, id desc
            limit greatest(1, least(coalesce(p_limit, 500), 2000))
        ) a
        left join app.memberships m on m.org_id = a.org_id and m.user_id = a.actor_user_id
        left join auth.users au on au.id = a.actor_user_id
    ), '[]'::jsonb));
end;
$$;

-- =============================================================================
-- Rollback: recriar api.list_audit com o corpo de 20261113230000_auditoria.sql (sem 'actorEmail').
-- =============================================================================
