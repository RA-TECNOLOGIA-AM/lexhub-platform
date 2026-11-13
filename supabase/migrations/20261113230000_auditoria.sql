-- =============================================================================
-- Auditoria: a tela lê app.audit_log direto no Supabase (sem a API em Python).
--
-- Aditiva: cria api.list_audit; troca api.my_admin_permissions (ganha 'audit', para o menu esconder a aba).
-- Quem vê: audit.view (Owner, Desenvolvedor), a organização inteira. A tabela continua só de inserção
-- (trigger audit_log_no_update); nada aqui apaga ou muda evento.
-- O texto de cada evento ("Exportou dados", detalhe) é montado no front (services/auditEvents.ts):
-- aqui só vêm o evento cru, quem fez e o nome do alvo.
-- Teste: supabase/tests/auditoria_test.sql (termina com rollback).
-- =============================================================================

-- Os últimos eventos da organização, do mais recente para o mais antigo (até 2000; padrão 500).
create function api.list_audit(p_org text, p_limit integer default 500) returns jsonb
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

revoke all on function api.list_audit(text, integer) from public, anon;
grant execute on function api.list_audit(text, integer) to authenticated;

-- Menu: api.my_admin_permissions ganha 'audit' (mesmo corpo de 20261113180000_unidades_fontes.sql)
create or replace function api.my_admin_permissions(p_org text) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org uuid;
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    if v_org is null then
        return jsonb_build_object('access', false, 'members', false, 'sources', false, 'audit', false);
    end if;
    return jsonb_build_object(
        'access', cardinality(app_private.access_scope(v_org)) > 0,
        'members', cardinality(app_private.members_scope(v_org)) > 0,
        'sources', cardinality(app_private.sources_scope(v_org)) > 0,
        'audit', v_org = any (app_private.my_org_ids_with('audit.view'))
    );
end;
$$;

-- =============================================================================
-- Rollback:
-- (recriar api.my_admin_permissions com o corpo de 20261113180000_unidades_fontes.sql)
-- drop function api.list_audit(text, integer);
-- =============================================================================
