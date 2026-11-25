-- =============================================================================
-- Perfil: criar e alterar senha.
--
-- Quem entra por convite só tinha o Google. Agora qualquer pessoa cria/altera a senha em Configurações → Perfil
-- (o front chama auth.updateUser do Supabase) e passa a entrar também com e-mail e senha.
--
-- - api.my_password_status(): a tela sabe se mostra "Criar senha" ou "Alterar senha" (encrypted_password vazio
--   ou null = só Google). Devolve só um boolean, nunca o hash.
-- - Trigger em auth.users: quando a senha muda (por qualquer caminho: Perfil, recuperação), grava
--   'auth.password_changed' em app.audit_log, uma vez por organização em que a pessoa está ativa (igual ao
--   auth.login). metadata.kind = 'created' (antes não tinha) ou 'changed'.
--   O trigger nunca bloqueia a troca: qualquer erro vira só um aviso no log do Postgres.
--
-- Aditiva. Para desfazer:
--   drop trigger if exists audit_password_changed on auth.users;
--   drop function if exists app_private.audit_password_changed();
--   drop function if exists api.my_password_status();
-- Teste: supabase/tests/perfil_senha_test.sql (termina com rollback).
-- =============================================================================

create function api.my_password_status() returns boolean
language sql stable security definer
set search_path = ''
as $$
    select coalesce(u.encrypted_password, '') <> ''
    from auth.users u
    where u.id = auth.uid();
$$;

revoke all on function api.my_password_status() from public, anon;
grant execute on function api.my_password_status() to authenticated;

create function app_private.audit_password_changed() returns trigger
language plpgsql security definer
set search_path = ''
as $$
begin
    begin
        insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
        select m.org_id, new.id, 'auth.password_changed', 'user', new.id::text,
               jsonb_build_object('kind', case when coalesce(old.encrypted_password, '') = '' then 'created' else 'changed' end)
        from app.memberships m
        where m.user_id = new.id and m.status = 'active';
    exception when others then
        raise warning 'audit_password_changed: % (%)', sqlerrm, sqlstate;
    end;
    return new;
end;
$$;

revoke all on function app_private.audit_password_changed() from public, anon, authenticated;

create trigger audit_password_changed
after update of encrypted_password on auth.users
for each row
when (old.encrypted_password is distinct from new.encrypted_password)
execute function app_private.audit_password_changed();
