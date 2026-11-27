-- =============================================================================
-- Teste de 20261127110000_fonte_facebook_ads.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...').
-- Roda num banco vazio (CI) ou no staging: garante a organização 'lexgroup' (a casa) se faltar.
-- Cenário: cliente 'org-teste-fb' com MC_01 e MC_02; t1 Dev da LexGroup; t2 Owner do cliente.
-- As funções de escrita são da API (service_role); o teste chama como dono, passando o usuário.
-- =============================================================================

begin;

insert into app.organizations (slug, name) values ('lexgroup', 'LexGroup') on conflict (slug) do nothing;

insert into auth.users (id, email)
values ('00000000-0000-4000-8000-0000000fa001', 'ti.ads@exemplo.com'),
       ('00000000-0000-4000-8000-0000000fa002', 'owner.ads@exemplo.com');
insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-0000000fa001', 'org-teste-fb', 'Cliente Teste Ads');
insert into app.units (id, org_id, code, name, timezone)
values ('20000000-0000-4000-8000-0000000fa001', '10000000-0000-4000-8000-0000000fa001', 'MC_01', 'Manaus Centro', 'America/Manaus'),
       ('20000000-0000-4000-8000-0000000fa002', '10000000-0000-4000-8000-0000000fa001', 'MC_02', 'Manaus Sul', 'America/Manaus');
insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000fa001', app_private.home_org_id(),
        '00000000-0000-4000-8000-0000000fa001', 'TI', 'ti.ads@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-0000000fa002', '10000000-0000-4000-8000-0000000fa001',
        '00000000-0000-4000-8000-0000000fa002', 'Owner Cliente', 'owner.ads@exemplo.com', 'owner', 'active');

do $$
declare
    ti     constant uuid := '00000000-0000-4000-8000-0000000fa001';
    owner  constant uuid := '00000000-0000-4000-8000-0000000fa002';
    unit   constant uuid := '20000000-0000-4000-8000-0000000fa001';
    unit2  constant uuid := '20000000-0000-4000-8000-0000000fa002';
    cfg    constant jsonb := '{"ad_account_id": "act_1234567890", "account_name": "NG Anúncios", "currency": "BRL",
                               "timezone": "America/Manaus", "metrics": ["reach"], "conversions": ["lead"],
                               "campaigns": null, "breakdowns": ["age_gender", "region"], "backfill_days": 1095,
                               "creatives": true, "collect_version": 1}';
    r      jsonb;
    v_src  app.data_sources;
begin
    -- Só a TI da LexGroup conecta
    begin
        perform app_private.connect_source(owner, unit, 'facebook_ads', 'Ads', '', cfg, 'v1:dG9rZW4=', false, null);
        raise exception 'FALHOU: Owner do cliente conectou Facebook Ads';
    exception when insufficient_privilege then null;
    end;

    -- Precisa do token cifrado e da conta no formato act_<dígitos>; token nunca na config
    begin
        perform app_private.connect_source(ti, unit, 'facebook_ads', 'Ads', '', cfg, null, false, null);
        raise exception 'FALHOU: Facebook Ads sem token cifrado';
    exception when check_violation then null;
    end;
    begin
        perform app_private.connect_source(ti, unit, 'facebook_ads', 'Ads', '', '{"ad_account_id": "1234"}',
                                           'v1:dG9rZW4=', false, null);
        raise exception 'FALHOU: conta sem act_';
    exception when check_violation then null;
    end;
    begin
        perform app_private.connect_source(ti, unit, 'facebook_ads', 'Ads', '', cfg || '{"token": "x"}',
                                           'v1:dG9rZW4=', false, null);
        raise exception 'FALHOU: token na config';
    exception when check_violation then null;
    end;

    r := app_private.connect_source(ti, unit, 'facebook_ads', ' Anúncios MC ', 'Facebook Ads · NG Anúncios (act_1234567890)',
                                    cfg, 'v1:dG9rZW4=', false, '{"app.facebook_ads_daily": [["day", "date"]]}');
    if r ->> 'id' !~ '^fb_mc01_[0-9a-f]{6}$' or r ->> 'connector' <> 'facebook_ads' or r ->> 'kind' <> 'ads'
       or r ->> 'group' <> 'connection' or r ->> 'name' <> 'Anúncios MC' or r ->> 'status' <> 'no_dashboards' then
        raise exception 'FALHOU: conectar Facebook Ads: %', r;
    end if;
    select * into v_src from app.data_sources where key = r ->> 'id';
    if not exists (select 1 from app.unit_source_refs where unit_id = unit and source = v_src.key and ref = '*')
       or v_src.owner_unit_id <> unit or v_src.config ->> 'ad_account_id' <> 'act_1234567890' then
        raise exception 'FALHOU: fonte gravada: %', row_to_json(v_src);
    end if;
    if not exists (select 1 from app.audit_log where org_id = '10000000-0000-4000-8000-0000000fa001'
                     and action = 'source.connected' and metadata ->> 'adAccount' = 'act_1234567890') then
        raise exception 'FALHOU: auditoria sem a conta de anúncios';
    end if;

    -- A mesma conta em outra unidade: barrada com a mensagem de quem já tem
    begin
        perform app_private.connect_source(ti, unit2, 'facebook_ads', 'Ads MC2', '', cfg, 'v1:dG9rZW4=', false, null);
        raise exception 'FALHOU: mesma conta de anúncios duas vezes';
    exception when raise_exception then
        if sqlerrm not like 'Esta conta de anúncios já está conectada (Cliente Teste Ads · MC_01)%' then raise; end if;
    end;

    -- Métricas por anúncio e dia; ad_id só dígitos; gasto não negativo
    insert into app.facebook_ads_daily (source_id, day, ad_id, ad_name, campaign_id, campaign_name, account_id,
                                        currency, spend, impressions, reach, clicks, link_clicks,
                                        landing_page_views, leads, conversations, results, actions)
    values (v_src.id, current_date - 1, '120200000000001', 'Anúncio A', '1202', 'Captação', '1234567890', 'BRL',
            150.25, 10000, 8000, 320, 210, 180, 12, 5, 12,
            '[{"action_type": "lead", "value": "12"}, {"action_type": "onsite_conversion.messaging_conversation_started_7d", "value": "5"}]'),
           (v_src.id, current_date - 2, '120200000000002', 'Anúncio B', '1202', 'Captação', '1234567890', 'BRL',
            49.75, 4000, null, 90, 60, 51, 3, 0, 3, '[{"action_type": "lead", "value": "3"}]');
    begin
        insert into app.facebook_ads_daily (source_id, day, ad_id, account_id) values (v_src.id, current_date, 'x1', '1');
        raise exception 'FALHOU: ad_id fora do formato';
    exception when check_violation then null;
    end;
    begin
        insert into app.facebook_ads_daily (source_id, day, ad_id, account_id, spend)
        values (v_src.id, current_date, '1', '1', -1);
        raise exception 'FALHOU: valor gasto negativo';
    exception when check_violation then null;
    end;

    -- Detalhamentos, campanhas e estado da coleta
    insert into app.facebook_ads_breakdowns (source_id, day, breakdown, campaign_id, dim1, dim2, spend, results, actions)
    values (v_src.id, current_date - 1, 'age_gender', '1202', '25-34', 'female', 90, 7, '[{"action_type": "lead", "value": "7"}]'),
           (v_src.id, current_date - 1, 'region', '1202', 'Amazonas', '', 150.25, 12, '[{"action_type": "lead", "value": "12"}]');
    begin
        insert into app.facebook_ads_breakdowns (source_id, day, breakdown, campaign_id) values (v_src.id, current_date, 'hora', '1');
        raise exception 'FALHOU: detalhamento desconhecido';
    exception when check_violation then null;
    end;
    insert into app.facebook_ads_entities (source_id, level, id, name, effective_status, objective, daily_budget, creative)
    values (v_src.id, 'campaign', '1202', 'Captação Manaus', 'ACTIVE', 'OUTCOME_LEADS', 50, null),
           (v_src.id, 'ad', '120200000000001', 'Anúncio A', 'ACTIVE', null, null, '{"title": "Fale conosco"}');
    insert into app.facebook_ads_sync_state (source_id, dataset, collect_version, backfill_done, covered_until)
    values (v_src.id, 'ads', 1, true, current_date), (v_src.id, 'age_gender', 1, true, current_date),
           (v_src.id, 'region', 1, true, current_date);

    -- Coleta no log: com as linhas; falha sem linhas e com o erro; as de mais de 30 dias saem
    insert into app.source_sync_runs (source_id, started_at, finished_at, ok, rows, run_kind)
    values (v_src.id, now() - interval '40 days', now() - interval '40 days', true, 5, 'sync');
    perform app_private.record_source_sync(v_src.id, false, 99, 800, 'Token recusado pela Meta.');
    perform app_private.record_source_sync(v_src.id, true, 2, 1500, null);
    if exists (select 1 from app.source_sync_runs where source_id = v_src.id and started_at < now() - interval '30 days') then
        raise exception 'FALHOU: coleta antiga não saiu do log';
    end if;
    if (select count(*) from app.source_sync_runs where source_id = v_src.id and run_kind = 'sync') <> 2
       or exists (select 1 from app.source_sync_runs where source_id = v_src.id and not ok and rows is not null) then
        raise exception 'FALHOU: log da coleta';
    end if;
    r := app_private.source_item(v_src.id, unit);
    if (r ->> 'rows')::int <> 2 or (r ->> 'failures')::int <> 0 or r ->> 'syncedAt' is null then
        raise exception 'FALHOU: fonte depois da coleta: %', r;
    end if;

    -- Resumo do painel: período, totais dos últimos 30 dias, campanhas e o histórico
    r := app_private.facebook_ads_summary(v_src.id);
    if (r ->> 'rows')::int <> 2 or (r ->> 'firstDay')::date <> current_date - 2
       or (r -> 'last30' ->> 'spend')::numeric <> 200 or (r -> 'last30' ->> 'results')::numeric <> 15
       or (r -> 'last30' ->> 'conversations')::int <> 5
       or (r -> 'breakdownRows' ->> 'region')::int <> 1
       or (r -> 'entities' ->> 'activeCampaigns')::int <> 1 or (r -> 'entities' ->> 'creatives')::int <> 1
       or r -> 'topCampaigns' -> 0 ->> 'name' <> 'Captação Manaus'
       or r -> 'topCampaigns' -> 0 ->> 'objective' <> 'OUTCOME_LEADS'
       or not (r -> 'backfill' ->> 'done')::boolean then
        raise exception 'FALHOU: resumo do Facebook Ads: %', r;
    end if;

    -- Conversões trocadas: "resultados" sai das ações guardadas, sem coletar de novo
    perform app_private.facebook_ads_recompute_results(
        v_src.id, array['onsite_conversion.messaging_conversation_started_7d']);
    if (select sum(results) from app.facebook_ads_daily where source_id = v_src.id) <> 5
       or (select sum(results) from app.facebook_ads_breakdowns where source_id = v_src.id) <> 0 then
        raise exception 'FALHOU: refazer resultados';
    end if;

    -- Personalizar: só a TI; a conta não muda; o detalhamento que saiu leva as linhas e o estado
    begin
        perform app_private.set_source_config(owner, v_src.id, cfg, '');
        raise exception 'FALHOU: Owner do cliente personalizou';
    exception when insufficient_privilege then null;
    end;
    begin
        perform app_private.set_source_config(ti, v_src.id, cfg || '{"ad_account_id": "act_999"}', '');
        raise exception 'FALHOU: trocou a conta pela personalização';
    exception when raise_exception then
        if sqlerrm not like 'A conta de anúncios não muda%' then raise; end if;
    end;
    r := app_private.set_source_config(ti, v_src.id, cfg || '{"breakdowns": ["age_gender"], "collect_version": 2}', '');
    if exists (select 1 from app.facebook_ads_breakdowns where source_id = v_src.id and breakdown = 'region')
       or exists (select 1 from app.facebook_ads_sync_state where source_id = v_src.id and dataset = 'region')
       or not exists (select 1 from app.facebook_ads_breakdowns where source_id = v_src.id and breakdown = 'age_gender')
       or (select config_version from app.data_sources where id = v_src.id) <> 2
       or (select config ->> 'collect_version' from app.data_sources where id = v_src.id) <> '2' then
        raise exception 'FALHOU: personalizar';
    end if;
    if not exists (select 1 from app.audit_log where action = 'source.config_changed' and target_id = v_src.id::text
                     and metadata -> 'changed' = '["breakdowns", "collect_version"]'::jsonb) then
        raise exception 'FALHOU: auditoria da personalização';
    end if;

    -- Desconectar: some a fonte e tudo o que foi guardado
    perform app_private.disconnect_source(ti, v_src.id);
    if exists (select 1 from app.data_sources where id = v_src.id)
       or exists (select 1 from app.facebook_ads_daily where source_id = v_src.id)
       or exists (select 1 from app.facebook_ads_breakdowns where source_id = v_src.id)
       or exists (select 1 from app.facebook_ads_entities where source_id = v_src.id)
       or exists (select 1 from app.facebook_ads_sync_state where source_id = v_src.id) then
        raise exception 'FALHOU: desconectar Facebook Ads';
    end if;

    -- Desconectada, a conta pode ser ligada de novo (em outra unidade)
    r := app_private.connect_source(ti, unit2, 'facebook_ads', 'Ads MC2', '', cfg, 'v1:dG9rZW4=', false, null);
    if r ->> 'id' !~ '^fb_mc02_' then
        raise exception 'FALHOU: religar a conta depois de desconectar: %', r;
    end if;
end $$;

-- Pelo front: authenticated não lê as tabelas nem chama as funções da API; o detalhe traz o resumo
set local role authenticated;
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000fa002","role":"authenticated"}';
do $$
declare
    d jsonb;
    k text;
begin
    begin
        perform 1 from app.facebook_ads_daily limit 1;
        raise exception 'FALHOU: authenticated leu app.facebook_ads_daily';
    exception when insufficient_privilege then null;
    end;
    begin
        perform 1 from app.facebook_ads_entities limit 1;
        raise exception 'FALHOU: authenticated leu app.facebook_ads_entities';
    exception when insufficient_privilege then null;
    end;
    begin
        perform app_private.record_source_sync(gen_random_uuid(), true, 1, 1, null);
        raise exception 'FALHOU: authenticated gravou coleta';
    exception when insufficient_privilege then null;
    end;
    begin
        perform app_private.set_source_config(gen_random_uuid(), gen_random_uuid(), '{}', '');
        raise exception 'FALHOU: authenticated personalizou';
    exception when insufficient_privilege then null;
    end;
    select r.source into k from app.unit_source_refs r
    where r.unit_id = '20000000-0000-4000-8000-0000000fa002' and r.source like 'fb_%';
    d := api.source_detail('org-teste-fb', 'MC_02', k);
    if d -> 'ads' ->> 'rows' <> '0' or d -> 'config' ->> 'ad_account_id' <> 'act_1234567890'
       or (d ->> 'canManage')::boolean or d::text like '%dG9rZW4=%' then
        raise exception 'FALHOU: detalhe do Facebook Ads para o Owner do cliente: %', d;
    end if;
    raise notice 'OK: todos os casos passaram (o rollback abaixo desfaz tudo)';
end $$;

rollback;
