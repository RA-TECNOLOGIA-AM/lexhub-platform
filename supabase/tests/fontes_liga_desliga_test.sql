-- =============================================================================
-- Teste de 20261118100000_fontes_liga_desliga.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...').
-- Roda num banco vazio (CI) ou no staging: garante a organização 'lexgroup' (a casa) se faltar.
-- Cenário: cliente 'org-teste-liga' com C1; t1 Dev da LexGroup; t2 Owner do cliente.
-- =============================================================================

begin;

insert into app.organizations (slug, name) values ('lexgroup', 'LexGroup') on conflict (slug) do nothing;

insert into auth.users (id, email)
values ('00000000-0000-4000-8000-0000000fc001', 'ti.liga@exemplo.com'),
       ('00000000-0000-4000-8000-0000000fc002', 'owner.liga@exemplo.com');
insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-0000000fc001', 'org-teste-liga', 'Cliente Teste Liga');
insert into app.units (id, org_id, code, name, timezone)
values ('20000000-0000-4000-8000-0000000fc001', '10000000-0000-4000-8000-0000000fc001', 'LG_01', 'Liga Centro',
        'America/Manaus');
insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000fc001', app_private.home_org_id(),
        '00000000-0000-4000-8000-0000000fc001', 'TI', 'ti.liga@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-0000000fc002', '10000000-0000-4000-8000-0000000fc001',
        '00000000-0000-4000-8000-0000000fc002', 'Owner Cliente', 'owner.liga@exemplo.com', 'owner', 'active'),
       -- a TI também é membro do cliente aqui só para abrir o detalhe (o modo suporte é outro PR)
       ('40000000-0000-4000-8000-0000000fc003', '10000000-0000-4000-8000-0000000fc001',
        '00000000-0000-4000-8000-0000000fc001', 'TI', 'ti.liga@exemplo.com', 'admin', 'active');

do $$
declare
    ti     constant uuid := '00000000-0000-4000-8000-0000000fc001';
    owner  constant uuid := '00000000-0000-4000-8000-0000000fc002';
    unit   constant uuid := '20000000-0000-4000-8000-0000000fc001';
    cfg    constant jsonb := '{"host": "db.operacao.com.br", "port": 5432, "database": "operacao", "user": "lexhub_leitura", "ssl": true}';
    r      jsonb;
    v_id   uuid;
    v_old  uuid;
begin
    -- A planilha de teste saiu e o rótulo errado também
    if exists (select 1 from app.data_sources where key = 'sheets_protocolo_passado_ng')
       or exists (select 1 from app.data_sources where detail like '%conta de serviço%') then
        raise exception 'FALHOU: planilha de teste ou rótulo antigo ainda no banco';
    end if;

    r := app_private.connect_source(ti, unit, 'postgres', 'Banco Liga', 'Postgres · db.operacao.com.br/operacao',
                                    cfg, 'v1:YWJjZA==', false, '{"public.processo": [["id", "integer"]]}');
    select id into v_id from app.data_sources where key = r ->> 'id';
    if not (select enabled from app.data_sources where id = v_id) then
        raise exception 'FALHOU: fonte nova nasce desligada';
    end if;

    -- Só a TI da LexGroup liga e desliga
    begin
        perform app_private.set_source_enabled(owner, v_id, false);
        raise exception 'FALHOU: Owner do cliente desligou a fonte';
    exception when insufficient_privilege then null;
    end;

    -- Desligar: status 'disabled', segredo continua, auditoria com de/para
    r := app_private.set_source_enabled(ti, v_id, false);
    if r ->> 'status' <> 'disabled' or (select enabled from app.data_sources where id = v_id)
       or (select secret_ciphertext from app.data_sources where id = v_id) <> 'v1:YWJjZA==' then
        raise exception 'FALHOU: desligar: %', r;
    end if;
    if not exists (select 1 from app.audit_log
                   where action = 'source.disabled' and target_id = v_id::text and actor_user_id = ti
                     and org_id = '10000000-0000-4000-8000-0000000fc001'
                     and metadata ->> 'from' = 'true' and metadata ->> 'to' = 'false') then
        raise exception 'FALHOU: auditoria de desligar';
    end if;

    -- Desligar de novo não muda nada nem audita de novo
    perform app_private.set_source_enabled(ti, v_id, false);
    if (select count(*) from app.audit_log where action = 'source.disabled' and target_id = v_id::text) <> 1 then
        raise exception 'FALHOU: desligar duas vezes auditou duas vezes';
    end if;

    -- Religar: volta, sem pedir segredo
    r := app_private.set_source_enabled(ti, v_id, true);
    if r ->> 'status' = 'disabled' or not (select enabled from app.data_sources where id = v_id)
       or not exists (select 1 from app.audit_log where action = 'source.enabled' and target_id = v_id::text
                      and metadata ->> 'to' = 'true') then
        raise exception 'FALHOU: religar: %', r;
    end if;

    -- Planilha inteira (como as antigas, link cifrado pelo script): liga/desliga sim, desconectar não
    insert into app.data_sources (org_id, key, kind, name, detail, owner_unit_id, connector, config, secret_ciphertext)
    values ('10000000-0000-4000-8000-0000000fc001', 'sheets_teste_liga', 'sheet', 'Planilha antiga',
            'Google Sheets · link publicado', unit, 'sheets', '{}', 'v1:bGluaw==')
    returning id into v_old;
    insert into app.unit_source_refs (unit_id, source, ref) values (unit, 'sheets_teste_liga', '*');
    perform app_private.set_source_enabled(ti, v_old, false);
    begin
        perform app_private.disconnect_source(ti, v_old);
        raise exception 'FALHOU: desconectou planilha antiga';
    exception when raise_exception then
        if sqlerrm not like 'Esta planilha é usada pelo código%' then raise; end if;
    end;
end $$;

-- Pelo front: authenticated não liga/desliga; o detalhe técnico só para a TI da LexGroup
set local role authenticated;
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000fc002","role":"authenticated"}';
do $$
declare
    d jsonb;
    k text;
begin
    select r.source into k from app.unit_source_refs r
    where r.unit_id = '20000000-0000-4000-8000-0000000fc001' and r.source like 'pg_%';
    begin
        perform app_private.set_source_enabled('00000000-0000-4000-8000-0000000fc001',
            (select id from app.data_sources where key = k), false);
        raise exception 'FALHOU: authenticated chamou set_source_enabled';
    exception when insufficient_privilege then null;
    end;
    d := api.source_detail('org-teste-liga', 'LG_01', k);
    if d ? 'technical' and d -> 'technical' <> 'null'::jsonb or not (d ->> 'enabled')::boolean
       or d::text like '%public.processo%' then
        raise exception 'FALHOU: detalhe para o Owner do cliente: %', d;
    end if;
end $$;

reset role;
set local role authenticated;
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000fc001","role":"authenticated"}';
do $$
declare
    d jsonb;
    k text;
begin
    select r.source into k from app.unit_source_refs r
    where r.unit_id = '20000000-0000-4000-8000-0000000fc001' and r.source like 'pg_%';
    d := api.source_detail('org-teste-liga', 'LG_01', k);
    if d -> 'technical' ->> 'key' <> k or d -> 'technical' -> 'schema' -> 'public.processo' is null
       or not (d ->> 'canManage')::boolean or d::text like '%YWJjZA==%' then
        raise exception 'FALHOU: detalhe para a TI: %', d;
    end if;
    d := api.source_detail('org-teste-liga', 'LG_01', 'sheets_teste_liga');
    if (d ->> 'enabled')::boolean or d -> 'source' ->> 'status' <> 'disabled' then
        raise exception 'FALHOU: planilha antiga desligada no detalhe: %', d;
    end if;
    raise notice 'OK: todos os casos passaram (o rollback abaixo desfaz tudo)';
end $$;

rollback;
