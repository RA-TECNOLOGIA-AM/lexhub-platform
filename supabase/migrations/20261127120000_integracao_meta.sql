-- =============================================================================
-- Integrações da plataforma configuradas pela tela (Unidades e fontes > Integração Meta), não pelo .env.
--
-- Decisões (27/11):
--   * a Meta (Facebook Ads) é a primeira: ID do app, chave secreta do app, versão da Graph API e a
--     atualização automática (ligada ou pausada e o intervalo: 5, 10, 15, 30 ou 60 min). A tela tem
--     prioridade; o .env da API (FACEBOOK_APP_ID, FACEBOOK_APP_SECRET, FACEBOOK_GRAPH_VERSION) só vale
--     quando a tela não definiu;
--   * a fonte do Facebook Ads fica "atrasada" depois de 2 intervalos da tela sem coletar (não mais os
--     10 min fixos de app_private.sync_every_min) e não fica atrasada enquanto a atualização está pausada;
--   * a chave secreta do app é segredo: a API testa na Meta, cifra com a SOURCE_SECRET_KEY e só o texto
--     cifrado vem para cá (como a senha dos bancos). A config nunca leva segredo;
--   * só a TI da LexGroup (app_private.is_source_admin) configura; cada mudança vai para a auditoria da
--     LexGroup, com os campos que mudaram e o que aconteceu com o segredo (nunca o segredo);
--   * ficam no .env, de propósito: SOURCE_SECRET_KEY e PUBLIC_API_JWT_SECRET (as chaves-mestras não podem
--     morar ao lado do que protegem) e FACEBOOK_ADS_SYNC_ENABLED (a trava da máquina: API local não coleta).
-- 1 tabela e 3 funções novas; source_item e facebook_ads_summary recriadas (mesmo resultado + o intervalo).
-- Teste: supabase/tests/integracao_meta_test.sql (termina com rollback).
-- =============================================================================

create table app.platform_integrations (
    key               text primary key check (key in ('meta')),
    config            jsonb not null default '{}'::jsonb,
    secret_ciphertext text check (secret_ciphertext is null or secret_ciphertext ~ '^v1:[A-Za-z0-9+/]+={0,2}$'),
    updated_by        uuid references auth.users (id) on delete set null,
    updated_at        timestamptz not null default now(),
    constraint platform_integrations_config_no_secret
        check (not (config ?| array['password', 'pass', 'senha', 'secret', 'token', 'app_secret'])),
    -- Os intervalos que a tela oferece (minutos); a coleta e a regra de "atrasada" usam o mesmo número.
    constraint platform_integrations_sync_interval
        check (config ->> 'sync_interval_min' is null or config ->> 'sync_interval_min' in ('5', '10', '15', '30', '60'))
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

-- ---------------------------------------------------------------------------
-- Atualização automática do Facebook Ads: o intervalo e a pausa da tela, para a regra de "atrasada" e o
-- painel do detalhe. Sem nada salvo: 10 minutos e ligada (o mesmo padrão da API).
-- ---------------------------------------------------------------------------
create function app_private.ads_sync_every_min() returns integer
language sql stable security definer
set search_path = ''
as $$
    select coalesce((select (i.config ->> 'sync_interval_min')::integer
                       from app.platform_integrations i where i.key = 'meta'), 10)
$$;

create function app_private.ads_sync_paused() returns boolean
language sql stable security definer
set search_path = ''
as $$
    select coalesce((select (i.config ->> 'sync_paused')::boolean
                       from app.platform_integrations i where i.key = 'meta'), false)
$$;

revoke all on function app_private.ads_sync_every_min() from public, anon, authenticated;
revoke all on function app_private.ads_sync_paused() from public, anon, authenticated;

-- source_item: no Facebook Ads, "atrasada" usa o intervalo da tela (2 rodadas sem coletar) e não conta o
-- tempo parado enquanto a atualização automática está pausada. O resto igual a
-- 20261118100000_fontes_liga_desliga.sql.
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
                  or (last_ok.finished_at < now() - make_interval(mins => 2 * (
                          case when ds.connector = 'facebook_ads' then app_private.ads_sync_every_min()
                               else app_private.sync_every_min() end))
                      and not (ds.connector = 'facebook_ads' and app_private.ads_sync_paused())))
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

-- facebook_ads_summary: + syncEveryMin e syncPaused (o painel diz "a cada N minutos" ou "pausada").
-- O resto igual a 20261127110000_fonte_facebook_ads.sql.
create or replace function app_private.facebook_ads_summary(p_source uuid) returns jsonb
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
        ),
        'syncEveryMin', app_private.ads_sync_every_min(),
        'syncPaused', app_private.ads_sync_paused()
    );
$$;

-- =============================================================================
-- Rollback:
-- (source_item e facebook_ads_summary: recriar com o corpo de 20261118100000_fontes_liga_desliga.sql e de
--  20261127110000_fonte_facebook_ads.sql)
-- drop function app_private.ads_sync_paused();
-- drop function app_private.ads_sync_every_min();
-- drop function app_private.set_platform_integration(uuid, text, jsonb, text, text);
-- drop table app.platform_integrations;
-- =============================================================================
