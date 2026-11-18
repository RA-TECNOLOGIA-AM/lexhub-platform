-- =============================================================================
-- PR 3: ligar/desligar fonte, planilhas do .env para o banco e o detalhe técnico para o analista.
--
-- Decisões (Luís, 18/11):
--   * data_sources.enabled (padrão true): desligar é pausa reversível. O segredo cifrado fica salvo;
--     a API não lê a fonte desligada e o dashboard mostra "Fonte desligada". Só planilha, Postgres e
--     MySQL (LexPre/LexFlow têm o "desvincular escritório"; NG/LAADV ficam no .env, fora da tela);
--   * só a TI da LexGroup (app_private.is_source_admin) liga e desliga; fica na auditoria;
--   * as planilhas antigas (sheets_financeiro_ng/la) passam a ter o link cifrado no banco: o script
--     apps/api/scripts/migrar_planilhas_env.py preenche secret_ciphertext (a migration não lê o .env).
--     Elas leem a planilha inteira (várias abas): config '{}'. Não podem ser desconectadas (as chaves
--     estão no código dos dashboards Financeiro estratégico e Meta anual); podem ser desligadas;
--   * sheets_protocolo_passado_ng era teste: sai;
--   * o rótulo "conta de serviço" estava errado: é link publicado;
--   * api.source_detail mostra a chave da fonte e a estrutura salva (tabelas/colunas ou abas/colunas)
--     só para a TI da LexGroup.
-- Teste: supabase/tests/fontes_liga_desliga_test.sql (termina com rollback).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. data_sources: liga/desliga; planilha inteira pode ter o link cifrado
-- ---------------------------------------------------------------------------
alter table app.data_sources
    add column enabled boolean not null default true;

-- Planilha: inteira (config '{}', link cifrado ou ainda no .env até o script rodar) ou uma aba
-- (config.tab, link cifrado). Banco: sempre a senha cifrada. O resto: nunca guarda segredo aqui.
alter table app.data_sources
    drop constraint data_sources_secret,
    add constraint data_sources_secret check (
        case
            when connector in ('postgres', 'mysql') then secret_ciphertext is not null
            when connector = 'sheets' then config = '{}'::jsonb
                                        or (config ? 'tab' and secret_ciphertext is not null)
            else secret_ciphertext is null
        end
    );

-- ---------------------------------------------------------------------------
-- 2. Dados: a planilha de teste sai; o rótulo certo nas antigas
-- ---------------------------------------------------------------------------
delete from app.unit_source_refs where source = 'sheets_protocolo_passado_ng';
delete from app.dashboard_sources where source_key = 'sheets_protocolo_passado_ng';
delete from app.data_sources where key = 'sheets_protocolo_passado_ng';

update app.data_sources
   set detail = 'Google Sheets · link publicado'
 where detail = 'Google Sheets · conta de serviço';

-- ---------------------------------------------------------------------------
-- 3. Desconectar: a planilha inteira (antiga) não sai pela tela; desliga-se
--    (mesmo corpo de 20261117180000_conectar_banco_planilha.sql + a trava)
-- ---------------------------------------------------------------------------
create or replace function app_private.disconnect_source(p_user uuid, p_source uuid) returns void
language plpgsql volatile security definer
set search_path = ''
as $$
declare
    v_source app.data_sources := app_private.require_connected_source(p_user, p_source);
begin
    if v_source.connector = 'sheets' and v_source.config = '{}'::jsonb then
        raise exception using errcode = 'P0001',
            message = 'Esta planilha é usada pelo código dos dashboards: desligue em vez de desconectar.';
    end if;

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
-- 4. Ligar/desligar (a API chama e limpa o cache dela na hora)
-- ---------------------------------------------------------------------------
create function app_private.set_source_enabled(p_user uuid, p_source uuid, p_enabled boolean) returns jsonb
language plpgsql volatile security definer
set search_path = ''
as $$
declare
    v_source app.data_sources := app_private.require_connected_source(p_user, p_source);
begin
    if p_enabled is null then
        raise exception using errcode = 'P0001', message = 'Informe se a fonte fica ligada ou desligada.';
    end if;
    if v_source.enabled is distinct from p_enabled then
        update app.data_sources set enabled = p_enabled, updated_at = now() where id = v_source.id;

        insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
        values (v_source.org_id, p_user, case when p_enabled then 'source.enabled' else 'source.disabled' end,
                'source', v_source.id::text,
                jsonb_build_object('name', v_source.name, 'connector', v_source.connector, 'key', v_source.key,
                                   'from', v_source.enabled, 'to', p_enabled));
    end if;
    return app_private.source_item(v_source.id, v_source.owner_unit_id);
end;
$$;

revoke all on function app_private.set_source_enabled(uuid, uuid, boolean) from public, anon, authenticated;
grant execute on function app_private.set_source_enabled(uuid, uuid, boolean) to service_role;

-- ---------------------------------------------------------------------------
-- 5. source_item: 'disabled' antes de tudo (mesmo corpo de 20261117100000_conectar_fonte.sql + 1 caso)
-- ---------------------------------------------------------------------------
create or replace function app_private.source_item(p_source uuid, p_unit uuid) returns jsonb
language sql stable security definer
set search_path = ''
as $$
    select jsonb_build_object(
        'id', ds.key,
        'kind', ds.kind,
        'connector', ds.connector,
        'name', ds.name,
        'detail', ds.detail,
        'group', case when ds.owner_unit_id is null then 'product' else 'connection' end,
        'managedBy', case when ds.owner_unit_id <> p_unit then owner.name end,
        'syncedAt', last_ok.finished_at,
        'rows', last_ok.rows,
        'failures', fails.n,
        -- Desligada vem antes de tudo; depois falha; depois "nenhum dashboard ligado na unidade usa a
        -- fonte"; depois o log.
        'status', case
            when not ds.enabled then 'disabled'
            when exists (select 1 from app.source_sync_runs r where r.source_id = ds.id)
             and (fails.n > 0
                  or last_ok.finished_at is null
                  or last_ok.finished_at < now() - make_interval(mins => 2 * app_private.sync_every_min()))
                then 'late'
            when not exists (
                select 1
                from app.dashboard_sources dsrc
                join app.dashboard_catalog c on c.key = dsrc.dashboard_key and c.active
                join app.org_dashboards od on od.dashboard_key = c.key and od.unit_id = p_unit and od.enabled
                where dsrc.source_key = ds.key
            ) then 'no_dashboards'
            when not exists (select 1 from app.source_sync_runs r where r.source_id = ds.id) then 'waiting'
            else 'healthy'
        end
    )
    from app.data_sources ds
    left join app.units owner on owner.id = ds.owner_unit_id
    left join lateral (
        select r.finished_at, r.rows from app.source_sync_runs r
        where r.source_id = ds.id and r.ok
        order by r.finished_at desc limit 1
    ) last_ok on true
    cross join lateral (
        select count(*)::integer as n from app.source_sync_runs r
        where r.source_id = ds.id and r.ok = false
          and (last_ok.finished_at is null or r.finished_at > last_ok.finished_at)
    ) fails
    where ds.id = p_source;
$$;

-- ---------------------------------------------------------------------------
-- 6. api.source_detail: + enabled e a seção técnica (só TI da LexGroup)
--    (mesmo resultado de 20261117180000_conectar_banco_planilha.sql com 2 campos novos)
-- ---------------------------------------------------------------------------
create or replace function api.source_detail(p_org text, p_unit text, p_source text) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org    uuid;
    v_unit   app.units;
    v_source app.data_sources;
    v_admin  boolean := app_private.is_source_admin(auth.uid());
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
        'enabled', v_source.enabled,
        -- A TI da LexGroup pode testar de novo, trocar a senha, ligar/desligar e desconectar
        -- (só fonte conectada pela tela, com o segredo no banco)
        'canManage', v_admin and v_source.secret_ciphertext is not null,
        -- Para o analista escrever as queries: a chave da fonte e a estrutura salva no teste. Só a TI da
        -- LexGroup (a estrutura do banco do cliente não é do Owner do cliente).
        'technical', case when v_admin then jsonb_build_object(
                         'key', v_source.key,
                         'schema', v_source.schema_cache
                     ) end,
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
-- (recriar api.source_detail como em 20261117180000_conectar_banco_planilha.sql)
-- (recriar app_private.source_item como em 20261117100000_conectar_fonte.sql)
-- (recriar app_private.disconnect_source como em 20261117180000_conectar_banco_planilha.sql)
-- drop function app_private.set_source_enabled(uuid, uuid, boolean);
-- update app.data_sources set detail = 'Google Sheets · conta de serviço' where detail = 'Google Sheets · link publicado';
-- (a planilha de teste sheets_protocolo_passado_ng não volta: era teste)
-- update app.data_sources set secret_ciphertext = null where connector = 'sheets' and config = '{}'::jsonb;
-- alter table app.data_sources drop constraint data_sources_secret, add constraint data_sources_secret check (
--     case when connector in ('postgres', 'mysql') then secret_ciphertext is not null
--          when connector = 'sheets' then (config = '{}'::jsonb and secret_ciphertext is null)
--                                      or (config ? 'tab' and secret_ciphertext is not null)
--          else secret_ciphertext is null end);
-- alter table app.data_sources drop column enabled;
-- =============================================================================
