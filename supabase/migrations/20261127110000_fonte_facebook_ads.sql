-- =============================================================================
-- Fonte Facebook Ads: ligar uma conta de anúncios da Meta numa unidade, personalizar o que é coletado e
-- guardar as métricas por dia no LexHub.
--
-- Decisões (26/11):
--   * os dados ficam no Supabase do LexHub, não no banco NG: a Meta só mantém 37 meses de totais (13 meses
--     de alguns cortes, desde 12/01/2026), então o histórico tem de ser nosso;
--   * o token do usuário do sistema (Gerenciador de Negócios, permissão ads_read) é segredo: a API cifra
--     com a SOURCE_SECRET_KEY, como a senha do banco. A config guarda o id da conta, o que a Meta devolveu
--     no teste (nome, moeda, fuso) e a personalização:
--       metrics      grupos opcionais: 'reach' (alcance e frequência), 'video', 'quality';
--       conversions  os tipos de ação da Meta que somam em "resultados" (ex.: lead, conversa iniciada);
--       campaigns    ids das campanhas coletadas (null = todas);
--       breakdowns   detalhamentos: 'age_gender', 'platform', 'region', 'device';
--       backfill_days, creatives, collect_version (sobe quando a coleta precisa refazer o histórico);
--   * uma conta de anúncios fica ligada a uma fonte só, no banco todo (senão seria coletada duas vezes);
--   * quem coleta é a API (app/facebook_ads_sync.py, ligada por FACEBOOK_ADS_SYNC_ENABLED). Cada rodada vai
--     para app.source_sync_runs (run_kind 'sync', com as linhas gravadas); as de mais de 30 dias saem;
--   * desconectar apaga tudo o que foi guardado (on delete cascade); desligar guarda tudo.
-- Aditiva: troca 3 checks e 1 índice de data_sources, app_private.connect_source e api.source_detail;
-- 1 índice, 4 tabelas e 4 funções novas.
-- Teste: supabase/tests/fonte_facebook_ads_test.sql (termina com rollback).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. data_sources: o tipo novo (ícone 'ads', conector 'facebook_ads')
-- ---------------------------------------------------------------------------
alter table app.data_sources
    drop constraint data_sources_kind_check,
    add constraint data_sources_kind_check
        check (kind in ('database', 'flow', 'finance', 'sheet', 'ads')),
    drop constraint data_sources_connector_check,
    add constraint data_sources_connector_check
        check (connector in ('lexpre', 'lexflow', 'internal', 'postgres', 'mysql', 'sheets', 'facebook_ads'));

-- Facebook Ads: sempre o token cifrado e o id da conta ('act_' + dígitos) na config.
-- (mesmo check de 20261118100000_fontes_liga_desliga.sql + o caso do Facebook Ads)
alter table app.data_sources
    drop constraint data_sources_secret,
    add constraint data_sources_secret check (
        case
            when connector in ('postgres', 'mysql') then secret_ciphertext is not null
            when connector = 'sheets' then config = '{}'::jsonb
                                        or (config ? 'tab' and secret_ciphertext is not null)
            when connector = 'facebook_ads' then secret_ciphertext is not null
                                              and coalesce(config ->> 'ad_account_id', '') ~ '^act_[0-9]{1,20}$'
            else secret_ciphertext is null
        end
    );

-- A API acha a fonte conectada pela key (única no banco todo), agora também a do Facebook Ads.
drop index app.data_sources_connected_key_uq;
create unique index data_sources_connected_key_uq
    on app.data_sources (key)
    where connector in ('postgres', 'mysql', 'sheets', 'facebook_ads');

-- Uma conta de anúncios numa fonte só, no banco todo.
create unique index data_sources_ad_account_uq
    on app.data_sources ((config ->> 'ad_account_id'))
    where connector = 'facebook_ads';

-- ---------------------------------------------------------------------------
-- 2. Conectar: + Facebook Ads (mesmo corpo de 20261117180000_conectar_banco_planilha.sql, com o tipo
--    novo, a chave 'fb_...', a conta na auditoria e a mensagem da conta já ligada)
-- ---------------------------------------------------------------------------
create or replace function app_private.connect_source(
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
    v_unit  app.units;
    v_key   text;
    v_id    uuid;
    v_taken text;
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
    if p_connector not in ('postgres', 'mysql', 'sheets', 'facebook_ads') then
        raise exception using errcode = 'P0001', message = 'Tipo de fonte inválido.';
    end if;
    if coalesce(trim(p_name), '') = '' then
        raise exception using errcode = 'P0001', message = 'Dê um nome para a fonte.';
    end if;

    -- 'pg_mco_3fa9c1': tipo + unidade + sufixo aleatório (nunca reaproveitada depois de desconectar).
    v_key := case p_connector when 'postgres' then 'pg' when 'mysql' then 'my' when 'facebook_ads' then 'fb'
                              else 'gs' end
             || '_' || left(lower(regexp_replace(v_unit.code, '[^A-Za-z0-9]', '', 'g')), 12)
             || '_' || left(md5(gen_random_uuid()::text), 6);

    begin
        insert into app.data_sources (org_id, key, kind, name, detail, owner_unit_id, connector, config,
                                      secret_ciphertext, writer_ack, schema_cache, created_by)
        values (v_unit.org_id, v_key,
                case p_connector when 'sheets' then 'sheet' when 'facebook_ads' then 'ads' else 'database' end,
                trim(p_name), coalesce(p_detail, ''), v_unit.id, p_connector, coalesce(p_config, '{}'::jsonb),
                p_secret_ciphertext, coalesce(p_writer_ack, false), p_schema_cache, p_user)
        returning id into v_id;
    exception when unique_violation then
        if p_connector <> 'facebook_ads' then
            raise;
        end if;
        select o.name || ' · ' || u.code into v_taken
        from app.data_sources ds
        join app.organizations o on o.id = ds.org_id
        left join app.units u on u.id = ds.owner_unit_id
        where ds.connector = 'facebook_ads' and ds.config ->> 'ad_account_id' = p_config ->> 'ad_account_id';
        raise exception using errcode = 'P0001',
            message = format('Esta conta de anúncios já está conectada (%s).', coalesce(v_taken, 'outra unidade'));
    end;

    insert into app.unit_source_refs (unit_id, source, ref) values (v_unit.id, v_key, '*');

    insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
    values (v_unit.org_id, p_user, 'source.connected', 'source', v_id::text,
            jsonb_build_object('unit', v_unit.code, 'connector', p_connector, 'name', trim(p_name),
                               'host', p_config ->> 'host', 'tab', p_config ->> 'tab',
                               'adAccount', p_config ->> 'ad_account_id',
                               'writerAck', coalesce(p_writer_ack, false)));

    return app_private.source_item(v_id, v_unit.id);
end;
$$;

-- ---------------------------------------------------------------------------
-- 3. Métricas por anúncio e dia (/insights, level=ad). Coluna null = grupo não coletado (config.metrics).
-- ---------------------------------------------------------------------------
create table app.facebook_ads_daily (
    source_id          uuid not null references app.data_sources (id) on delete cascade,
    day                date not null,
    ad_id              text not null check (ad_id ~ '^[0-9]{1,30}$'),
    ad_name            text,
    adset_id           text,
    adset_name         text,
    campaign_id        text,
    campaign_name      text,
    account_id         text not null,
    currency           text,
    -- Sempre
    spend              numeric(14, 2) not null default 0 check (spend >= 0),            -- valor gasto
    impressions        bigint not null default 0 check (impressions >= 0),
    clicks             bigint not null default 0 check (clicks >= 0),                    -- todos os cliques
    link_clicks        bigint not null default 0 check (link_clicks >= 0),              -- cliques no link
    outbound_clicks    bigint not null default 0 check (outbound_clicks >= 0),          -- saíram para o site
    landing_page_views bigint not null default 0 check (landing_page_views >= 0),
    leads              bigint not null default 0 check (leads >= 0),                    -- formulário + pixel
    conversations      bigint not null default 0 check (conversations >= 0),            -- WhatsApp, Messenger, Direct
    results            numeric(14, 2) not null default 0 check (results >= 0),          -- soma de config.conversions
    -- 'reach'
    reach              bigint check (reach >= 0),
    frequency          numeric(10, 4) check (frequency >= 0),
    -- 'video'
    video_plays        bigint check (video_plays >= 0),
    video_thruplays    bigint check (video_thruplays >= 0),                             -- 15 s ou até o fim
    video_p25          bigint check (video_p25 >= 0),
    video_p50          bigint check (video_p50 >= 0),
    video_p75          bigint check (video_p75 >= 0),
    video_p100         bigint check (video_p100 >= 0),
    -- 'quality': ranking da Meta (ABOVE_AVERAGE, AVERAGE, BELOW_AVERAGE_35...)
    quality_ranking    text,
    engagement_ranking text,
    conversion_ranking text,
    actions            jsonb not null default '[]'::jsonb,                              -- "actions" como veio
    action_values      jsonb not null default '[]'::jsonb,
    fetched_at         timestamptz not null default now(),
    primary key (source_id, day, ad_id)
);

create index facebook_ads_daily_campaign on app.facebook_ads_daily (source_id, campaign_id, day);

comment on table app.facebook_ads_daily is
    'Facebook Ads por anúncio e dia, coletado pela API (app/facebook_ads_sync.py). Fonte: data_sources.';

-- ---------------------------------------------------------------------------
-- 4. Detalhamentos por campanha e dia (config.breakdowns). dim1/dim2 por detalhamento:
--    age_gender = faixa etária / gênero; platform = plataforma / posicionamento;
--    region = região (estado) / ''; device = dispositivo / ''.
-- ---------------------------------------------------------------------------
create table app.facebook_ads_breakdowns (
    source_id          uuid not null references app.data_sources (id) on delete cascade,
    day                date not null,
    breakdown          text not null check (breakdown in ('age_gender', 'platform', 'region', 'device')),
    campaign_id        text not null check (campaign_id ~ '^[0-9]{1,30}$'),
    campaign_name      text,
    dim1               text not null default '',
    dim2               text not null default '',
    spend              numeric(14, 2) not null default 0 check (spend >= 0),
    impressions        bigint not null default 0 check (impressions >= 0),
    clicks             bigint not null default 0 check (clicks >= 0),
    link_clicks        bigint not null default 0 check (link_clicks >= 0),
    landing_page_views bigint not null default 0 check (landing_page_views >= 0),
    leads              bigint not null default 0 check (leads >= 0),
    conversations      bigint not null default 0 check (conversations >= 0),
    results            numeric(14, 2) not null default 0 check (results >= 0),
    reach              bigint check (reach >= 0),
    actions            jsonb not null default '[]'::jsonb,
    fetched_at         timestamptz not null default now(),
    primary key (source_id, day, breakdown, campaign_id, dim1, dim2)
);

-- ---------------------------------------------------------------------------
-- 5. Campanhas, conjuntos e anúncios como estão na Meta (objetivo, status, orçamento e o criativo)
-- ---------------------------------------------------------------------------
create table app.facebook_ads_entities (
    source_id         uuid not null references app.data_sources (id) on delete cascade,
    level             text not null check (level in ('campaign', 'adset', 'ad')),
    id                text not null check (id ~ '^[0-9]{1,30}$'),
    name              text,
    campaign_id       text,
    adset_id          text,
    status            text,             -- o que a pessoa ligou (ACTIVE, PAUSED...)
    effective_status  text,             -- o que vale (CAMPAIGN_PAUSED, WITH_ISSUES...)
    objective         text,             -- campanha (OUTCOME_LEADS...)
    optimization_goal text,             -- conjunto (LEAD_GENERATION, CONVERSATIONS...)
    daily_budget      numeric(14, 2),   -- na moeda da conta
    lifetime_budget   numeric(14, 2),
    start_time        timestamptz,
    stop_time         timestamptz,
    created_time      timestamptz,
    creative          jsonb,            -- anúncio (config.creatives): título, texto, imagem, link, chamada
    fetched_at        timestamptz not null default now(),
    primary key (source_id, level, id)
);

-- ---------------------------------------------------------------------------
-- 6. Até onde a coleta chegou em cada conjunto de dados ('ads' ou um detalhamento)
-- ---------------------------------------------------------------------------
create table app.facebook_ads_sync_state (
    source_id       uuid not null references app.data_sources (id) on delete cascade,
    dataset         text not null check (dataset in ('ads', 'age_gender', 'platform', 'region', 'device')),
    collect_version integer not null check (collect_version >= 1), -- config.collect_version do histórico
    backfill_done   boolean not null default false,
    covered_until   date,                                          -- último dia já gravado
    updated_at      timestamptz not null default now(),
    primary key (source_id, dataset)
);

-- Sem policy: só a API (service_role) lê e grava; a tela vê o resumo por api.source_detail.
alter table app.facebook_ads_daily enable row level security;
alter table app.facebook_ads_breakdowns enable row level security;
alter table app.facebook_ads_entities enable row level security;
alter table app.facebook_ads_sync_state enable row level security;
revoke all on app.facebook_ads_daily, app.facebook_ads_breakdowns, app.facebook_ads_entities,
              app.facebook_ads_sync_state from public, anon, authenticated;
grant all on app.facebook_ads_daily, app.facebook_ads_breakdowns, app.facebook_ads_entities,
             app.facebook_ads_sync_state to service_role;

-- ---------------------------------------------------------------------------
-- 7. Registrar uma coleta no log da fonte (com as linhas gravadas). Guarda 30 dias de coletas.
-- ---------------------------------------------------------------------------
create function app_private.record_source_sync(
    p_source uuid,
    p_ok boolean,
    p_rows integer,
    p_ms integer,
    p_error text
) returns void
language sql volatile security definer
set search_path = ''
as $$
    delete from app.source_sync_runs
    where source_id = p_source and run_kind = 'sync' and started_at < now() - interval '30 days';

    insert into app.source_sync_runs (source_id, started_at, finished_at, ok, rows, error, run_kind, duration_ms)
    values (p_source, now() - make_interval(secs => greatest(p_ms, 0) / 1000.0), now(), p_ok,
            case when p_ok then greatest(coalesce(p_rows, 0), 0) end, p_error, 'sync', greatest(p_ms, 0));
$$;

-- ---------------------------------------------------------------------------
-- 8. Personalizar a coleta depois de conectar (a API validou a config antes)
-- ---------------------------------------------------------------------------
create function app_private.set_source_config(p_user uuid, p_source uuid, p_config jsonb, p_detail text)
returns jsonb
language plpgsql volatile security definer
set search_path = ''
as $$
declare
    v_source     app.data_sources := app_private.require_connected_source(p_user, p_source);
    v_breakdowns text[];
    v_changed    jsonb;
begin
    if v_source.connector <> 'facebook_ads' then
        raise exception using errcode = 'P0001', message = 'Só a fonte Facebook Ads tem personalização.';
    end if;
    if p_config ->> 'ad_account_id' is distinct from v_source.config ->> 'ad_account_id' then
        raise exception using errcode = 'P0001',
            message = 'A conta de anúncios não muda: para outra conta, conecte outra fonte.';
    end if;

    select coalesce(jsonb_agg(k order by k), '[]'::jsonb) into v_changed
    from (
        select n.key as k from jsonb_each(p_config) n
        where n.value is distinct from v_source.config -> n.key
        union
        select o.key from jsonb_each(v_source.config) o where not p_config ? o.key
    ) diff;

    update app.data_sources
       set config = p_config,
           detail = coalesce(nullif(trim(p_detail), ''), detail),
           config_version = config_version + 1,
           updated_at = now()
     where id = v_source.id;

    -- Detalhamento que saiu: as linhas e o estado dele saem também (não ficam paradas no tempo).
    select coalesce(array_agg(x.b), '{}') into v_breakdowns
    from jsonb_array_elements_text(coalesce(p_config -> 'breakdowns', '[]'::jsonb)) as x(b);
    delete from app.facebook_ads_breakdowns
    where source_id = v_source.id and breakdown <> all (v_breakdowns);
    delete from app.facebook_ads_sync_state
    where source_id = v_source.id and dataset <> 'ads' and dataset <> all (v_breakdowns);

    insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
    values (v_source.org_id, p_user, 'source.config_changed', 'source', v_source.id::text,
            jsonb_build_object('name', v_source.name, 'connector', v_source.connector, 'changed', v_changed));

    return app_private.source_item(v_source.id, v_source.owner_unit_id);
end;
$$;

-- Trocar só as conversões não pede coletar de novo: "resultados" sai das ações já guardadas.
create function app_private.facebook_ads_recompute_results(p_source uuid, p_types text[]) returns void
language sql volatile security definer
set search_path = ''
as $$
    update app.facebook_ads_daily d
       set results = coalesce((
               select sum((a ->> 'value')::numeric)
               from jsonb_array_elements(d.actions) a
               where a ->> 'action_type' = any (p_types) and a ->> 'value' ~ '^[0-9]+(\.[0-9]+)?$'
           ), 0)
     where d.source_id = p_source;
    update app.facebook_ads_breakdowns b
       set results = coalesce((
               select sum((a ->> 'value')::numeric)
               from jsonb_array_elements(b.actions) a
               where a ->> 'action_type' = any (p_types) and a ->> 'value' ~ '^[0-9]+(\.[0-9]+)?$'
           ), 0)
     where b.source_id = p_source;
$$;

-- ---------------------------------------------------------------------------
-- 9. O resumo do que está guardado (o painel do detalhe da fonte)
-- ---------------------------------------------------------------------------
create function app_private.facebook_ads_summary(p_source uuid) returns jsonb
language sql stable security definer
set search_path = ''
as $$
    with recent as (
        select * from app.facebook_ads_daily
        where source_id = p_source and day > current_date - 30
    ), top as (
        select r.campaign_id, max(r.campaign_name) as name, sum(r.spend) as spend, sum(r.results) as results,
               sum(r.impressions) as impressions, sum(r.link_clicks) as link_clicks
        from recent r
        group by r.campaign_id
        order by sum(r.spend) desc
        limit 8
    )
    select jsonb_build_object(
        'firstDay', (select min(day) from app.facebook_ads_daily where source_id = p_source),
        'lastDay', (select max(day) from app.facebook_ads_daily where source_id = p_source),
        'rows', (select count(*) from app.facebook_ads_daily where source_id = p_source),
        'breakdownRows', coalesce((
            select jsonb_object_agg(b.breakdown, b.n)
            from (select breakdown, count(*) as n from app.facebook_ads_breakdowns
                  where source_id = p_source group by breakdown) b
        ), '{}'::jsonb),
        'entities', (
            select jsonb_build_object(
                'campaigns', count(*) filter (where level = 'campaign'),
                'activeCampaigns', count(*) filter (where level = 'campaign' and effective_status = 'ACTIVE'),
                'adsets', count(*) filter (where level = 'adset'),
                'ads', count(*) filter (where level = 'ad'),
                'creatives', count(*) filter (where level = 'ad' and creative is not null))
            from app.facebook_ads_entities where source_id = p_source
        ),
        'last30', (
            select jsonb_build_object(
                'spend', coalesce(sum(spend), 0), 'impressions', coalesce(sum(impressions), 0),
                'clicks', coalesce(sum(clicks), 0), 'linkClicks', coalesce(sum(link_clicks), 0),
                'landingPageViews', coalesce(sum(landing_page_views), 0), 'leads', coalesce(sum(leads), 0),
                'conversations', coalesce(sum(conversations), 0), 'results', coalesce(sum(results), 0))
            from recent
        ),
        'topCampaigns', coalesce((
            select jsonb_agg(jsonb_build_object(
                       'id', t.campaign_id, 'name', coalesce(e.name, t.name), 'status', e.effective_status,
                       'objective', e.objective, 'spend', t.spend, 'results', t.results,
                       'impressions', t.impressions, 'linkClicks', t.link_clicks
                   ) order by t.spend desc)
            from top t
            left join app.facebook_ads_entities e
                   on e.source_id = p_source and e.level = 'campaign' and e.id = t.campaign_id
        ), '[]'::jsonb),
        'backfill', (
            select jsonb_build_object('done', s.backfill_done, 'coveredUntil', s.covered_until)
            from app.facebook_ads_sync_state s
            where s.source_id = p_source and s.dataset = 'ads'
        )
    );
$$;

revoke all on function app_private.record_source_sync(uuid, boolean, integer, integer, text)
    from public, anon, authenticated;
revoke all on function app_private.set_source_config(uuid, uuid, jsonb, text) from public, anon, authenticated;
revoke all on function app_private.facebook_ads_recompute_results(uuid, text[]) from public, anon, authenticated;
revoke all on function app_private.facebook_ads_summary(uuid) from public, anon, authenticated;
grant execute on function app_private.record_source_sync(uuid, boolean, integer, integer, text) to service_role;
grant execute on function app_private.set_source_config(uuid, uuid, jsonb, text) to service_role;
grant execute on function app_private.facebook_ads_recompute_results(uuid, text[]) to service_role;

-- ---------------------------------------------------------------------------
-- 10. api.source_detail: + o resumo do Facebook Ads (mesmo resultado de
--     20261118100000_fontes_liga_desliga.sql com o campo 'ads')
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
        -- host, porta, banco, usuário, SSL (banco), a aba (planilha) ou a conta e a personalização
        -- (Facebook Ads). A senha, o link e o token nunca saem daqui.
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
        -- Facebook Ads: o que já está guardado (período, totais dos últimos 30 dias, campanhas)
        'ads', case when v_source.connector = 'facebook_ads'
                    then app_private.facebook_ads_summary(v_source.id) end,
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
-- (recriar api.source_detail como em 20261118100000_fontes_liga_desliga.sql)
-- drop function app_private.facebook_ads_summary(uuid);
-- drop function app_private.facebook_ads_recompute_results(uuid, text[]);
-- drop function app_private.set_source_config(uuid, uuid, jsonb, text);
-- drop function app_private.record_source_sync(uuid, boolean, integer, integer, text);
-- drop table app.facebook_ads_sync_state, app.facebook_ads_entities, app.facebook_ads_breakdowns,
--     app.facebook_ads_daily;
-- (recriar app_private.connect_source como em 20261117180000_conectar_banco_planilha.sql)
-- delete from app.unit_source_refs where source in (select key from app.data_sources where connector = 'facebook_ads');
-- delete from app.dashboard_sources where source_key in (select key from app.data_sources where connector = 'facebook_ads');
-- delete from app.data_sources where connector = 'facebook_ads';
-- drop index app.data_sources_ad_account_uq;
-- drop index app.data_sources_connected_key_uq;
-- create unique index data_sources_connected_key_uq on app.data_sources (key)
--     where connector in ('postgres', 'mysql', 'sheets');
-- (recriar data_sources_secret como em 20261118100000_fontes_liga_desliga.sql)
-- alter table app.data_sources
--     drop constraint data_sources_connector_check, add constraint data_sources_connector_check
--         check (connector in ('lexpre', 'lexflow', 'internal', 'postgres', 'mysql', 'sheets')),
--     drop constraint data_sources_kind_check, add constraint data_sources_kind_check
--         check (kind in ('database', 'flow', 'finance', 'sheet'));
-- =============================================================================
