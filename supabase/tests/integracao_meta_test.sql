-- =============================================================================
-- Teste de 20261127120000_integracao_meta.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...').
-- Roda num banco vazio (CI) ou no staging: garante a organização 'lexgroup' (a casa) se faltar.
-- Cenário: t1 Dev da LexGroup (TI); t2 Owner de um cliente.
-- =============================================================================

begin;

insert into app.organizations (slug, name) values ('lexgroup', 'LexGroup') on conflict (slug) do nothing;

insert into auth.users (id, email)
values ('00000000-0000-4000-8000-0000000fb101', 'ti.meta@exemplo.com'),
       ('00000000-0000-4000-8000-0000000fb102', 'owner.meta@exemplo.com');
insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-0000000fb101', 'org-teste-meta', 'Cliente Teste Meta');
insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000fb101', app_private.home_org_id(),
        '00000000-0000-4000-8000-0000000fb101', 'TI', 'ti.meta@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-0000000fb102', '10000000-0000-4000-8000-0000000fb101',
        '00000000-0000-4000-8000-0000000fb102', 'Owner Cliente', 'owner.meta@exemplo.com', 'owner', 'active');

-- Num banco que já tem a integração configurada (staging), o teste começa do zero.
delete from app.platform_integrations where key = 'meta';

do $$
declare
    ti    constant uuid := '00000000-0000-4000-8000-0000000fb101';
    owner constant uuid := '00000000-0000-4000-8000-0000000fb102';
    cfg   constant jsonb := '{"app_id": "1234567890", "graph_version": "v26.0", "sync_paused": false}';
    v     app.platform_integrations;
begin
    -- Sem nada salvo: atualização automática ligada, a cada 10 min
    if app_private.ads_sync_every_min() <> 10 or app_private.ads_sync_paused() then
        raise exception 'FALHOU: padrão sem integração salva';
    end if;

    -- Só a TI da LexGroup configura
    begin
        perform app_private.set_platform_integration(owner, 'meta', cfg, 'v1:c2VncmVkbw==', 'set');
        raise exception 'FALHOU: Owner de cliente configurou a Meta';
    exception when insufficient_privilege then null;
    end;
    -- Integração desconhecida, ação inválida, set sem segredo, segredo fora do formato e segredo na config
    begin
        perform app_private.set_platform_integration(ti, 'google', cfg, null, 'keep');
        raise exception 'FALHOU: integração desconhecida';
    exception when raise_exception then
        if sqlerrm not like 'Integração desconhecida%' then raise; end if;
    end;
    begin
        perform app_private.set_platform_integration(ti, 'meta', cfg, null, 'trocar');
        raise exception 'FALHOU: ação inválida';
    exception when raise_exception then null;
    end;
    begin
        perform app_private.set_platform_integration(ti, 'meta', cfg, null, 'set');
        raise exception 'FALHOU: set sem segredo';
    exception when raise_exception then null;
    end;
    begin
        perform app_private.set_platform_integration(ti, 'meta', cfg, 'segredo-aberto', 'set');
        raise exception 'FALHOU: segredo sem cifra';
    exception when check_violation then null;
    end;
    begin
        perform app_private.set_platform_integration(ti, 'meta', cfg || '{"app_secret": "x"}', null, 'keep');
        raise exception 'FALHOU: segredo na config';
    exception when check_violation then null;
    end;

    -- Gravar com o segredo; manter (keep) não perde; limpar (clear) apaga
    perform app_private.set_platform_integration(ti, 'meta', cfg, 'v1:c2VncmVkbw==', 'set');
    select * into v from app.platform_integrations where key = 'meta';
    if v.secret_ciphertext <> 'v1:c2VncmVkbw==' or v.config ->> 'app_id' <> '1234567890' or v.updated_by <> ti then
        raise exception 'FALHOU: gravar a Meta: %', row_to_json(v);
    end if;

    perform app_private.set_platform_integration(ti, 'meta', cfg || '{"sync_paused": true}', null, 'keep');
    select * into v from app.platform_integrations where key = 'meta';
    if v.secret_ciphertext <> 'v1:c2VncmVkbw==' or not (v.config ->> 'sync_paused')::boolean then
        raise exception 'FALHOU: keep perdeu o segredo ou não pausou: %', row_to_json(v);
    end if;
    if not exists (select 1 from app.audit_log where action = 'integration.updated' and target_id = 'meta'
                     and org_id = app_private.home_org_id()
                     and metadata -> 'changed' = '["sync_paused"]'::jsonb and metadata ->> 'secret' = 'keep') then
        raise exception 'FALHOU: auditoria da pausa';
    end if;

    -- Atualização automática: sem intervalo salvo, 10 min (a pausa salva acima vale); o intervalo só aceita
    -- os da tela
    if app_private.ads_sync_every_min() <> 10 or not app_private.ads_sync_paused() then
        raise exception 'FALHOU: intervalo padrão ou pausa salva: % %',
            app_private.ads_sync_every_min(), app_private.ads_sync_paused();
    end if;
    perform app_private.set_platform_integration(ti, 'meta', cfg || '{"sync_interval_min": 30}', null, 'keep');
    if app_private.ads_sync_every_min() <> 30 or app_private.ads_sync_paused() then
        raise exception 'FALHOU: intervalo da tela';
    end if;
    begin
        perform app_private.set_platform_integration(ti, 'meta', cfg || '{"sync_interval_min": 7}', null, 'keep');
        raise exception 'FALHOU: intervalo fora da lista';
    exception when check_violation then null;
    end;

    perform app_private.set_platform_integration(ti, 'meta', cfg, null, 'clear');
    if app_private.ads_sync_every_min() <> 10 then
        raise exception 'FALHOU: sem intervalo salvo volta aos 10 min';
    end if;
    if (select secret_ciphertext from app.platform_integrations where key = 'meta') is not null then
        raise exception 'FALHOU: clear não apagou o segredo';
    end if;
    if exists (select 1 from app.audit_log where action = 'integration.updated'
                 and metadata::text like '%c2VncmVkbw==%') then
        raise exception 'FALHOU: segredo na auditoria';
    end if;
end $$;

-- Pelo front: authenticated não lê a tabela nem grava pela função
set local role authenticated;
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000fb101","role":"authenticated"}';
do $$
begin
    begin
        perform 1 from app.platform_integrations limit 1;
        raise exception 'FALHOU: authenticated leu app.platform_integrations';
    exception when insufficient_privilege then null;
    end;
    begin
        perform app_private.set_platform_integration(
            '00000000-0000-4000-8000-0000000fb101', 'meta', '{}', null, 'keep');
        raise exception 'FALHOU: authenticated gravou integração';
    exception when insufficient_privilege then null;
    end;
    begin
        perform app_private.ads_sync_every_min();
        raise exception 'FALHOU: authenticated chamou ads_sync_every_min';
    exception when insufficient_privilege then null;
    end;
    raise notice 'OK: todos os casos passaram (o rollback abaixo desfaz tudo)';
end $$;

rollback;
