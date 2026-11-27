-- =============================================================================
-- Integrações da plataforma configuradas pela tela (Unidades e fontes > Integração Meta), não pelo .env.
--
-- Decisões (27/11):
--   * a Meta (Facebook Ads) é a primeira: ID do app, chave secreta do app, versão da Graph API e a pausa
--     da coleta. A tela tem prioridade; o .env da API (FACEBOOK_APP_ID, FACEBOOK_APP_SECRET,
--     FACEBOOK_GRAPH_VERSION) só vale quando a tela não definiu;
--   * a chave secreta do app é segredo: a API testa na Meta, cifra com a SOURCE_SECRET_KEY e só o texto
--     cifrado vem para cá (como a senha dos bancos). A config nunca leva segredo;
--   * só a TI da LexGroup (app_private.is_source_admin) configura; cada mudança vai para a auditoria da
--     LexGroup, com os campos que mudaram e o que aconteceu com o segredo (nunca o segredo);
--   * ficam no .env, de propósito: SOURCE_SECRET_KEY e PUBLIC_API_JWT_SECRET (as chaves-mestras não podem
--     morar ao lado do que protegem) e FACEBOOK_ADS_SYNC_ENABLED (a trava da máquina: API local não coleta).
-- Aditiva: 1 tabela e 1 função.
-- Teste: supabase/tests/integracao_meta_test.sql (termina com rollback).
-- =============================================================================

create table app.platform_integrations (
    key               text primary key check (key in ('meta')),
    config            jsonb not null default '{}'::jsonb,
    secret_ciphertext text check (secret_ciphertext is null or secret_ciphertext ~ '^v1:[A-Za-z0-9+/]+={0,2}$'),
    updated_by        uuid references auth.users (id) on delete set null,
    updated_at        timestamptz not null default now(),
    constraint platform_integrations_config_no_secret
        check (not (config ?| array['password', 'pass', 'senha', 'secret', 'token', 'app_secret']))
);

comment on table app.platform_integrations is
    'Integrações da plataforma configuradas pela tela (a Meta: app, versão, pausa). Lida pela API.';

-- Sem policy: só a API (service_role) lê; a tela fala com a API.
alter table app.platform_integrations enable row level security;
revoke all on app.platform_integrations from public, anon, authenticated;
grant all on app.platform_integrations to service_role;

-- Gravar uma integração. p_secret_action: 'keep' (mantém o segredo salvo), 'set' (troca pelo novo,
-- p_secret_ciphertext) ou 'clear' (apaga). A API testou na Meta antes de 'set'.
create function app_private.set_platform_integration(
    p_user uuid,
    p_key text,
    p_config jsonb,
    p_secret_ciphertext text,
    p_secret_action text
) returns void
language plpgsql volatile security definer
set search_path = ''
as $$
declare
    v_old     app.platform_integrations;
    v_config  jsonb := coalesce(p_config, '{}'::jsonb);
    v_changed jsonb;
begin
    if not app_private.is_source_admin(p_user) then
        raise exception using errcode = '42501', message = 'Só a TI da LexGroup configura integrações.';
    end if;
    if p_key is distinct from 'meta' then
        raise exception using errcode = 'P0001', message = 'Integração desconhecida.';
    end if;
    if p_secret_action is null or p_secret_action not in ('keep', 'set', 'clear') then
        raise exception using errcode = 'P0001', message = 'Ação do segredo inválida: keep, set ou clear.';
    end if;
    if p_secret_action = 'set' and p_secret_ciphertext is null then
        raise exception using errcode = 'P0001', message = 'Falta o segredo cifrado.';
    end if;

    select * into v_old from app.platform_integrations where key = p_key;

    select coalesce(jsonb_agg(k order by k), '[]'::jsonb) into v_changed
    from (
        select n.key as k from jsonb_each(v_config) n
        where n.value is distinct from coalesce(v_old.config, '{}'::jsonb) -> n.key
        union
        select o.key from jsonb_each(coalesce(v_old.config, '{}'::jsonb)) o where not v_config ? o.key
    ) diff;

    insert into app.platform_integrations (key, config, secret_ciphertext, updated_by, updated_at)
    values (p_key, v_config, case when p_secret_action = 'set' then p_secret_ciphertext end, p_user, now())
    on conflict (key) do update
       set config = excluded.config,
           secret_ciphertext = case p_secret_action
                                   when 'keep' then app.platform_integrations.secret_ciphertext
                                   when 'set' then excluded.secret_ciphertext
                               end,
           updated_by = excluded.updated_by,
           updated_at = now();

    insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
    values (app_private.home_org_id(), p_user, 'integration.updated', 'integration', p_key,
            jsonb_build_object('integration', p_key, 'changed', v_changed, 'secret', p_secret_action));
end;
$$;

revoke all on function app_private.set_platform_integration(uuid, text, jsonb, text, text)
    from public, anon, authenticated;
grant execute on function app_private.set_platform_integration(uuid, text, jsonb, text, text) to service_role;

-- =============================================================================
-- Rollback:
-- drop function app_private.set_platform_integration(uuid, text, jsonb, text, text);
-- drop table app.platform_integrations;
-- =============================================================================
