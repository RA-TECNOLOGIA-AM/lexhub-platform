-- =============================================================================
-- Conectar fonte (PR 2): banco próprio da operação (Postgres, MySQL) e planilha publicada do Google.
--
-- Decisões (Luís, 17/11):
--   * sem o Vault do Supabase: a API cifra a senha do banco (e o link da planilha, que dá acesso aos
--     dados) com AES-256-GCM; a chave de 32 bytes fica só no .env da API (SOURCE_SECRET_KEY). Aqui fica
--     só o texto cifrado ('v1:' + base64), que sem a chave não serve para nada;
--   * NG e LAADV continuam no .env da API (fora do botão); LexPre/LexFlow são o PR 1;
--   * só a TI da LexGroup conecta, troca a senha e desconecta (app_private.is_source_admin).
-- As funções de escrita são da API (ela testa a conexão antes): grant só para service_role; o usuário
-- vem em p_user (na conexão da API não há auth.uid()).
-- Aditiva, exceto: sai a coluna secret_id (do Vault, nunca usada) e a regra data_sources_db_secret.
-- Teste: supabase/tests/conectar_banco_planilha_test.sql (termina com rollback).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. data_sources: o segredo cifrado no lugar do id do Vault
-- ---------------------------------------------------------------------------
alter table app.data_sources
    drop constraint data_sources_db_secret,
    drop constraint data_sources_sheet_config,
    drop column secret_id;

alter table app.data_sources
    add column secret_ciphertext text
        check (secret_ciphertext is null or secret_ciphertext ~ '^v1:[A-Za-z0-9+/]+={0,2}$');

-- Banco: sempre com a senha cifrada. Planilha: as 3 antigas (link no .env da API, config '{}') ou as
-- novas (link cifrado + a aba em config.tab). O resto (produtos, NG/LAADV): nunca guarda segredo aqui.
alter table app.data_sources
    add constraint data_sources_secret check (
        case
            when connector in ('postgres', 'mysql') then secret_ciphertext is not null
            when connector = 'sheets' then (config = '{}'::jsonb and secret_ciphertext is null)
                                        or (config ? 'tab' and secret_ciphertext is not null)
            else secret_ciphertext is null
        end
    );

-- A API acha a fonte conectada só pela key (o "nome do banco" das queries): única no banco todo.
create unique index data_sources_connected_key_uq
    on app.data_sources (key)
    where connector in ('postgres', 'mysql', 'sheets');

-- ---------------------------------------------------------------------------
-- 2. Auxiliar: fonte conectada pela tela, só para quem gerencia fontes
-- ---------------------------------------------------------------------------
create function app_private.require_connected_source(p_user uuid, p_source uuid) returns app.data_sources
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_source app.data_sources;
begin
    if not app_private.is_source_admin(p_user) then
        raise exception using errcode = '42501', message = 'Só a TI da LexGroup gerencia fontes.';
    end if;
    select ds.* into v_source from app.data_sources ds where ds.id = p_source and ds.active;
    if v_source.id is null then
        raise exception using errcode = 'P0001', message = 'Fonte não encontrada.';
    end if;
    if v_source.secret_ciphertext is null then
        raise exception using errcode = 'P0001',
            message = 'Esta fonte não é gerenciada pela tela (produto Lex, banco interno ou planilha antiga).';
    end if;
    return v_source;
end;
$$;

revoke all on function app_private.require_connected_source(uuid, uuid) from public, anon, authenticated;

-- ---------------------------------------------------------------------------
-- 3. Conectar: cria a fonte (dona = a unidade) e liga na unidade
-- ---------------------------------------------------------------------------
create function app_private.connect_source(
    p_user uuid,
    p_unit uuid,
    p_connector text,
    p_name text,
    p_detail text,
    p_config jsonb,
    p_secret_ciphertext text,
    p_writer_ack boolean,
    p_schema_cache jsonb
) returns jsonb
language plpgsql volatile security definer
set search_path = ''
as $$
declare
    v_unit app.units;
    v_key  text;
    v_id   uuid;
begin
    if not app_private.is_source_admin(p_user) then
        raise exception using errcode = '42501', message = 'Só a TI da LexGroup conecta fontes.';
    end if;
    select u.* into v_unit
    from app.units u join app.organizations o on o.id = u.org_id and o.active
    where u.id = p_unit and u.active;
    if v_unit.id is null then
        raise exception using errcode = 'P0001', message = 'Unidade não encontrada.';
    end if;
    if p_connector not in ('postgres', 'mysql', 'sheets') then
        raise exception using errcode = 'P0001', message = 'Tipo de fonte inválido.';
    end if;
    if coalesce(trim(p_name), '') = '' then
        raise exception using errcode = 'P0001', message = 'Dê um nome para a fonte.';
    end if;

    -- 'pg_mco_3fa9c1': tipo + unidade + sufixo aleatório (nunca reaproveitada depois de desconectar).
    v_key := case p_connector when 'postgres' then 'pg' when 'mysql' then 'my' else 'gs' end
             || '_' || left(lower(regexp_replace(v_unit.code, '[^A-Za-z0-9]', '', 'g')), 12)
             || '_' || left(md5(gen_random_uuid()::text), 6);

    insert into app.data_sources (org_id, key, kind, name, detail, owner_unit_id, connector, config,
                                  secret_ciphertext, writer_ack, schema_cache, created_by)
    values (v_unit.org_id, v_key,
            case p_connector when 'sheets' then 'sheet' else 'database' end,
            trim(p_name), coalesce(p_detail, ''), v_unit.id, p_connector, coalesce(p_config, '{}'::jsonb),
            p_secret_ciphertext, coalesce(p_writer_ack, false), p_schema_cache, p_user)
    returning id into v_id;

    insert into app.unit_source_refs (unit_id, source, ref) values (v_unit.id, v_key, '*');

    insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
    values (v_unit.org_id, p_user, 'source.connected', 'source', v_id::text,
            jsonb_build_object('unit', v_unit.code, 'connector', p_connector, 'name', trim(p_name),
                               'host', p_config ->> 'host', 'tab', p_config ->> 'tab',
                               'writerAck', coalesce(p_writer_ack, false)));

    return app_private.source_item(v_id, v_unit.id);
end;
$$;

-- ---------------------------------------------------------------------------
-- 4. Trocar a senha (ou o link da planilha): a API testou com o novo antes
-- ---------------------------------------------------------------------------
create function app_private.set_source_secret(
    p_user uuid,
    p_source uuid,
    p_secret_ciphertext text,
    p_writer_ack boolean,
    p_schema_cache jsonb
) returns jsonb
language plpgsql volatile security definer
set search_path = ''
as $$
declare
    v_source app.data_sources := app_private.require_connected_source(p_user, p_source);
begin
    update app.data_sources
       set secret_ciphertext = p_secret_ciphertext,
           writer_ack = coalesce(p_writer_ack, false),
           schema_cache = coalesce(p_schema_cache, schema_cache),
           config_version = config_version + 1,
           updated_at = now()
     where id = v_source.id;

    insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
    values (v_source.org_id, p_user, 'source.secret_changed', 'source', v_source.id::text,
            jsonb_build_object('name', v_source.name, 'connector', v_source.connector,
                               'writerAck', coalesce(p_writer_ack, false)));

    return app_private.source_item(v_source.id, v_source.owner_unit_id);
end;
$$;

-- ---------------------------------------------------------------------------
-- 5. Desconectar: some a fonte, as ligações e o segredo (a key não volta a ser usada)
-- ---------------------------------------------------------------------------
create function app_private.disconnect_source(p_user uuid, p_source uuid) returns void
language plpgsql volatile security definer
set search_path = ''
as $$
declare
    v_source app.data_sources := app_private.require_connected_source(p_user, p_source);
begin
    delete from app.unit_source_refs r
    using app.units u
    where u.id = r.unit_id and u.org_id = v_source.org_id and r.source = v_source.key;
    delete from app.dashboard_sources where source_key = v_source.key;
    delete from app.data_sources where id = v_source.id; -- leva o log (source_sync_runs) junto

    insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
    values (v_source.org_id, p_user, 'source.disconnected', 'source', v_source.id::text,
            jsonb_build_object('name', v_source.name, 'connector', v_source.connector, 'key', v_source.key));
end;
$$;

-- ---------------------------------------------------------------------------
-- 6. Registrar um teste (ou checagem) no log da fonte
-- ---------------------------------------------------------------------------
create function app_private.record_source_run(
    p_source uuid,
    p_kind text,
    p_ok boolean,
    p_checks jsonb,
    p_ms integer,
    p_error text
) returns void
language sql volatile security definer
set search_path = ''
as $$
    insert into app.source_sync_runs (source_id, started_at, finished_at, ok, error, run_kind, checks, duration_ms)
    values (p_source, now() - make_interval(secs => greatest(p_ms, 0) / 1000.0), now(), p_ok, p_error,
            p_kind, p_checks, greatest(p_ms, 0));
$$;

revoke all on function app_private.connect_source(uuid, uuid, text, text, text, jsonb, text, boolean, jsonb)
    from public, anon, authenticated;
revoke all on function app_private.set_source_secret(uuid, uuid, text, boolean, jsonb) from public, anon, authenticated;
revoke all on function app_private.disconnect_source(uuid, uuid) from public, anon, authenticated;
revoke all on function app_private.record_source_run(uuid, text, boolean, jsonb, integer, text)
    from public, anon, authenticated;
grant execute on function app_private.connect_source(uuid, uuid, text, text, text, jsonb, text, boolean, jsonb)
    to service_role;
grant execute on function app_private.set_source_secret(uuid, uuid, text, boolean, jsonb) to service_role;
grant execute on function app_private.disconnect_source(uuid, uuid) to service_role;
grant execute on function app_private.record_source_run(uuid, text, boolean, jsonb, integer, text) to service_role;

-- ---------------------------------------------------------------------------
-- 7. api.source_detail: + a configuração (sem segredo nenhum) e quem pode gerenciar
--    (mesmo resultado de 20261113200000_detalhe_fonte.sql com 2 campos novos)
-- ---------------------------------------------------------------------------
create or replace function api.source_detail(p_org text, p_unit text, p_source text) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org    uuid;
    v_unit   app.units;
    v_source app.data_sources;
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    select u.* into v_unit from app.units u
    where u.org_id = v_org and u.code = p_unit
      and u.id = any (app_private.sources_scope(v_org));
    if v_unit.id is null then
        raise exception using errcode = '42501', message = 'Você não vê as fontes desta unidade.';
    end if;

    select ds.* into v_source
    from app.unit_source_refs ref
    join app.data_sources ds on ds.org_id = v_org and ds.key = ref.source and ds.active
    where ref.unit_id = v_unit.id and ref.source = p_source;
    if v_source.id is null then
        raise exception using errcode = 'P0001', message = 'Esta unidade não usa essa fonte.';
    end if;

    return jsonb_build_object(
        'unit', jsonb_build_object('code', v_unit.code, 'name', v_unit.name),
        'source', app_private.source_item(v_source.id, v_unit.id),
        'owner', (select jsonb_build_object('code', o.code, 'name', o.name)
                  from app.units o where o.id = v_source.owner_unit_id),
        -- host, porta, banco, usuário, SSL (banco) ou a aba (planilha). A senha e o link nunca saem daqui.
        'config', v_source.config,
        'writerAck', v_source.writer_ack,
        -- A TI da LexGroup pode testar de novo, trocar a senha e desconectar (só fonte conectada pela tela)
        'canManage', app_private.is_source_admin(auth.uid()) and v_source.secret_ciphertext is not null,
        'dashboards', coalesce((
            select jsonb_agg(jsonb_build_object('key', c.key, 'name', c.name) order by c.sort_order, c.name)
            from app.dashboard_sources dsrc
            join app.dashboard_catalog c on c.key = dsrc.dashboard_key and c.active
            join app.org_dashboards od on od.dashboard_key = c.key and od.unit_id = v_unit.id and od.enabled
            where dsrc.source_key = v_source.key
        ), '[]'::jsonb),
        'runs', coalesce((
            select jsonb_agg(jsonb_build_object(
                       'startedAt', r.started_at, 'finishedAt', r.finished_at,
                       'ok', r.ok, 'rows', r.rows, 'error', r.error
                   ) order by r.started_at desc)
            from (select * from app.source_sync_runs
                  where source_id = v_source.id
                  order by started_at desc limit 10) r
        ), '[]'::jsonb)
    );
end;
$$;

-- =============================================================================
-- Rollback:
-- (recriar api.source_detail com o corpo de 20261113200000_detalhe_fonte.sql)
-- drop function app_private.record_source_run(uuid, text, boolean, jsonb, integer, text);
-- drop function app_private.disconnect_source(uuid, uuid);
-- drop function app_private.set_source_secret(uuid, uuid, text, boolean, jsonb);
-- drop function app_private.connect_source(uuid, uuid, text, text, text, jsonb, text, boolean, jsonb);
-- drop function app_private.require_connected_source(uuid, uuid);
-- drop index app.data_sources_connected_key_uq;
-- alter table app.data_sources drop constraint data_sources_secret, drop column secret_ciphertext,
--     add column secret_id uuid;
-- (recriar data_sources_db_secret e data_sources_sheet_config como em 20261117100000_conectar_fonte.sql)
-- =============================================================================
