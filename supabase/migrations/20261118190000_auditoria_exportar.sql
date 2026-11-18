-- =============================================================================
-- Auditoria: botão "Exportar CSV".
--
-- O arquivo é montado no front com os eventos que a tela já tem (os mesmos filtros). Antes de baixar,
-- o front chama api.log_audit_export: exportar a auditoria também fica registrado ('audit.export').
-- Se o registro falhar, o arquivo não sai.
--
-- Aditiva: cria api.log_audit_export. Quem pode: audit.view (Owner, Desenvolvedor), como api.list_audit.
-- Teste: supabase/tests/auditoria_exportar_test.sql (termina com rollback).
-- =============================================================================

-- p_kind / p_actor: o filtro da tela ('' ou null = todos); p_rows: quantos eventos foram no arquivo.
create function api.log_audit_export(p_org text, p_kind text, p_actor text, p_rows integer) returns void
language plpgsql security definer
set search_path = ''
as $$
declare
    v_org uuid;
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    if v_org is null or not (v_org = any (app_private.my_org_ids_with('audit.view'))) then
        raise exception using errcode = '42501', message = 'Só Owner ou Desenvolvedor exportam a auditoria.';
    end if;

    insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
    values (v_org, auth.uid(), 'audit.export', 'organization', v_org::text,
            jsonb_strip_nulls(jsonb_build_object(
                'kind', nullif(trim(p_kind), ''),
                'actor', nullif(trim(p_actor), ''),
                'rows', greatest(coalesce(p_rows, 0), 0),
                'format', 'csv'
            )));
end;
$$;

revoke all on function api.log_audit_export(text, text, text, integer) from public, anon;
grant execute on function api.log_audit_export(text, text, text, integer) to authenticated;

-- =============================================================================
-- Rollback:
-- drop function api.log_audit_export(text, text, text, integer);
-- =============================================================================
