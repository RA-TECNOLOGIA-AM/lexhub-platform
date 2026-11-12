-- =============================================================================
-- Permissões do menu de Administração: o front esconde "Acesso" (e pode esconder "Membros") de quem
-- não gere nada nesta organização. Não protege dado nenhum — as funções de cada aba já recusam (42501);
-- é só para o item não aparecer para Colaborador/Leitor.
-- Aditiva. Teste: supabase/tests/permissoes_menu_test.sql (termina com rollback).
-- =============================================================================

-- { access: gere acesso em alguma unidade, members: gere membros em alguma unidade }.
-- Org que não existe ou de que a pessoa não faz parte: tudo falso (sem erro).
create function api.my_admin_permissions(p_org text) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org uuid;
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    if v_org is null then
        return jsonb_build_object('access', false, 'members', false);
    end if;
    return jsonb_build_object(
        'access', cardinality(app_private.access_scope(v_org)) > 0,
        'members', cardinality(app_private.members_scope(v_org)) > 0
    );
end;
$$;

revoke all on function api.my_admin_permissions(text) from public, anon;
grant execute on function api.my_admin_permissions(text) to authenticated;

-- =============================================================================
-- Rollback: drop function api.my_admin_permissions(text);
-- =============================================================================
