-- =============================================================================
-- Login só por convite: nenhum usuário novo nasce no Supabase Auth sem convite pendente.
--
--   app_private.hook_before_user_created(event)   Auth Hook "Before User Created"
--
-- Antes: qualquer conta Google criava usuário; o "Solicitar acesso" virava um membro novo e quem
-- entrava com outro e-mail aparecia duplicado. Agora o usuário só é criado se o e-mail tem convite
-- pendente e não vencido (o mesmo critério do api.accept_my_invitations); senão o login volta com 403.
-- Quem já tem usuário não passa por aqui (o hook só roda na criação; o Google se liga à conta
-- existente do mesmo e-mail).
--
-- LIGAR NO PAINEL depois de aplicar: Authentication -> Hooks -> Before User Created ->
-- Postgres function app_private.hook_before_user_created.
-- Teste: supabase/tests/login_por_convite_test.sql (termina com rollback).
-- =============================================================================

create function app_private.hook_before_user_created(event jsonb) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_email text := lower(trim(event -> 'user' ->> 'email'));
begin
    if v_email is not null and v_email <> ''
       and exists (select 1 from app.invitations i
                   join app.organizations o on o.id = i.org_id and o.active
                   where i.email = v_email
                     and i.accepted_at is null and i.revoked_at is null and i.expires_at > now()) then
        return '{}'::jsonb;
    end if;

    -- O front não mostra este texto (mostra uma mensagem fixa); ele fica nos logs do Auth.
    return jsonb_build_object('error', jsonb_build_object(
        'http_code', 403,
        'message', 'Sem convite para o LexHub.'));
end;
$$;

-- Quem chama o hook é o supabase_auth_admin: precisa do schema e da função, mais ninguém.
grant usage on schema app_private to supabase_auth_admin;
revoke all on function app_private.hook_before_user_created(jsonb) from public, anon, authenticated;
grant execute on function app_private.hook_before_user_created(jsonb) to supabase_auth_admin;

-- =============================================================================
-- Rollback (rodar à mão se precisar desfazer):
-- 1. Desligar o hook no painel (Authentication -> Hooks) ANTES do drop, senão todo cadastro falha.
-- 2. drop function app_private.hook_before_user_created(jsonb);
--    revoke usage on schema app_private from supabase_auth_admin;
-- =============================================================================
