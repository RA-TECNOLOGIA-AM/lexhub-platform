-- =============================================================================
-- Teste de 20261118150100_login_por_convite.sql. Roda numa transação e desfaz no fim (ROLLBACK): não deixa dados.
-- Passou = nenhum ERROR (só o aviso 'OK: ...'). Falhou = ERROR 'FALHOU: ...' (o CI para aí).
-- Uso: rodar depois da migration (CI, SQL Editor do staging ou psql).
--
-- Cenário: org 'org-teste-convite' com convites pendente, vencido, revogado e aceito.
-- =============================================================================

begin;

insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-0000000000c1', 'org-teste-convite', 'Org Teste Convite');

insert into app.invitations (org_id, email, token_hash, created_at, expires_at, accepted_at, revoked_at)
values ('10000000-0000-4000-8000-0000000000c1', 'pendente@exemplo.com', 't-c1', now(), now() + interval '7 days', null, null),
       ('10000000-0000-4000-8000-0000000000c1', 'vencido@exemplo.com', 't-c2', now() - interval '8 days', now() - interval '1 day', null, null),
       ('10000000-0000-4000-8000-0000000000c1', 'revogado@exemplo.com', 't-c3', now(), now() + interval '7 days', null, now()),
       ('10000000-0000-4000-8000-0000000000c1', 'aceito@exemplo.com', 't-c4', now(), now() + interval '7 days', now(), null);

do $$
declare
    function_allows constant text := '{}';
begin
    -- Convite pendente: deixa criar (e-mail com maiúsculas e espaços, como pode vir do provedor)
    if app_private.hook_before_user_created('{"user":{"email":" Pendente@Exemplo.com "}}')::text <> function_allows then
        raise exception 'FALHOU: convite pendente deveria liberar';
    end if;

    -- Sem convite, vencido, revogado, já aceito, sem e-mail: barra com 403
    if (app_private.hook_before_user_created('{"user":{"email":"outro@exemplo.com"}}') #>> '{error,http_code}') <> '403' then
        raise exception 'FALHOU: sem convite deveria barrar';
    end if;
    if (app_private.hook_before_user_created('{"user":{"email":"vencido@exemplo.com"}}') #>> '{error,http_code}') <> '403' then
        raise exception 'FALHOU: convite vencido deveria barrar';
    end if;
    if (app_private.hook_before_user_created('{"user":{"email":"revogado@exemplo.com"}}') #>> '{error,http_code}') <> '403' then
        raise exception 'FALHOU: convite revogado deveria barrar';
    end if;
    if (app_private.hook_before_user_created('{"user":{"email":"aceito@exemplo.com"}}') #>> '{error,http_code}') <> '403' then
        raise exception 'FALHOU: convite já aceito deveria barrar';
    end if;
    if (app_private.hook_before_user_created('{"user":{}}') #>> '{error,http_code}') <> '403' then
        raise exception 'FALHOU: sem e-mail deveria barrar';
    end if;

    -- Organização desativada: convite dela não vale
    update app.organizations set active = false where id = '10000000-0000-4000-8000-0000000000c1';
    if (app_private.hook_before_user_created('{"user":{"email":"pendente@exemplo.com"}}') #>> '{error,http_code}') <> '403' then
        raise exception 'FALHOU: convite de org desativada deveria barrar';
    end if;

    -- Permissões: só o supabase_auth_admin executa
    if not has_function_privilege('supabase_auth_admin', 'app_private.hook_before_user_created(jsonb)', 'execute')
       or not has_schema_privilege('supabase_auth_admin', 'app_private', 'usage') then
        raise exception 'FALHOU: supabase_auth_admin sem acesso ao hook';
    end if;
    if has_function_privilege('authenticated', 'app_private.hook_before_user_created(jsonb)', 'execute')
       or has_function_privilege('anon', 'app_private.hook_before_user_created(jsonb)', 'execute') then
        raise exception 'FALHOU: anon/authenticated não podem chamar o hook';
    end if;

    raise notice 'OK: login_por_convite';
end $$;

rollback;
