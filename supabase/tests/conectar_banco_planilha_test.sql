-- =============================================================================
-- Teste de 20261117180000_conectar_banco_planilha.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...').
-- Roda num banco vazio (CI) ou no staging: garante a organização 'lexgroup' (a casa) se faltar.
-- Cenário: cliente 'org-teste-banco' com C1; t1 Dev da LexGroup; t2 Owner do cliente (Gestor da C1).
-- As funções de escrita são da API (service_role); o teste chama como dono, passando o usuário.
-- =============================================================================

begin;

insert into app.organizations (slug, name) values ('lexgroup', 'LexGroup') on conflict (slug) do nothing;

insert into auth.users (id, email)
values ('00000000-0000-4000-8000-0000000fb001', 'ti.banco@exemplo.com'),
       ('00000000-0000-4000-8000-0000000fb002', 'owner.banco@exemplo.com');
insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-0000000fb001', 'org-teste-banco', 'Cliente Teste Banco');
insert into app.units (id, org_id, code, name, timezone)
values ('20000000-0000-4000-8000-0000000fb001', '10000000-0000-4000-8000-0000000fb001', 'MC_01', 'Manaus Centro', 'America/Manaus');
insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000fb001', app_private.home_org_id(),
        '00000000-0000-4000-8000-0000000fb001', 'TI', 'ti.banco@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-0000000fb002', '10000000-0000-4000-8000-0000000fb001',
        '00000000-0000-4000-8000-0000000fb002', 'Owner Cliente', 'owner.banco@exemplo.com', 'owner', 'active');

do $$
declare
    ti     constant uuid := '00000000-0000-4000-8000-0000000fb001';
    owner  constant uuid := '00000000-0000-4000-8000-0000000fb002';
    unit   constant uuid := '20000000-0000-4000-8000-0000000fb001';
    cfg    constant jsonb := '{"host": "db.operacao.com.br", "port": 5432, "database": "operacao", "user": "lexhub_leitura", "ssl": true}';
    r      jsonb;
    v_src  app.data_sources;
    v_sh   app.data_sources;
begin
    -- Só a TI da LexGroup conecta
    begin
        perform app_private.connect_source(owner, unit, 'postgres', 'Banco', '', cfg, 'v1:YWJj', false, null);
        raise exception 'FALHOU: Owner do cliente conectou banco';
    exception when insufficient_privilege then null;
    end;

    -- Banco: precisa da senha cifrada; config nunca com senha
    begin
        perform app_private.connect_source(ti, unit, 'postgres', 'Banco', '', cfg, null, false, null);
        raise exception 'FALHOU: banco sem senha cifrada';
    exception when check_violation then null;
    end;
    begin
        perform app_private.connect_source(ti, unit, 'postgres', 'Banco', '', cfg || '{"password": "x"}', 'v1:YWJj', false, null);
        raise exception 'FALHOU: senha no config';
    exception when check_violation then null;
    end;
    begin
        perform app_private.connect_source(ti, unit, 'postgres', 'Banco', '', cfg, 'senha-aberta', false, null);
        raise exception 'FALHOU: segredo fora do formato cifrado';
    exception when check_violation then null;
    end;
    begin
        perform app_private.connect_source(ti, unit, 'internal', 'NG', '', '{}', null, false, null);
        raise exception 'FALHOU: banco interno pela tela';
    exception when raise_exception then
        if sqlerrm not like 'Tipo de fonte inválido%' then raise; end if;
    end;

    r := app_private.connect_source(ti, unit, 'postgres', ' Banco Manaus ', 'Postgres · db.operacao.com.br/operacao',
                                    cfg, 'v1:YWJjZA==', true, '{"public.processo": [["id", "integer"]]}');
    if r ->> 'id' !~ '^pg_mc01_[0-9a-f]{6}$' or r ->> 'connector' <> 'postgres' or r ->> 'group' <> 'connection'
       or r ->> 'name' <> 'Banco Manaus' or r ->> 'status' <> 'no_dashboards' then
        raise exception 'FALHOU: conectar banco: %', r;
    end if;
    select * into v_src from app.data_sources where key = r ->> 'id';
    if not exists (select 1 from app.unit_source_refs where unit_id = unit and source = v_src.key and ref = '*')
       or not v_src.writer_ack or v_src.schema_cache is null or v_src.owner_unit_id <> unit then
        raise exception 'FALHOU: fonte gravada: %', row_to_json(v_src);
    end if;

    -- Planilha nova: link cifrado + aba
    r := app_private.connect_source(ti, unit, 'sheets', 'Financeiro MC', 'Google Planilhas · aba FINANCEIRO',
                                    '{"tab": "FINANCEIRO"}', 'v1:bGluaw==', false, null);
    select * into v_sh from app.data_sources where key = r ->> 'id';
    if r ->> 'id' !~ '^gs_mc01_' or v_sh.kind <> 'sheet' then
        raise exception 'FALHOU: conectar planilha: %', r;
    end if;

    -- Trocar senha: versão sobe, auditoria; fonte antiga/produto não
    r := app_private.set_source_secret(ti, v_src.id, 'v1:bm92YQ==', false, null);
    if (select config_version from app.data_sources where id = v_src.id) <> 2
       or (select writer_ack from app.data_sources where id = v_src.id) then
        raise exception 'FALHOU: trocar senha';
    end if;
    begin
        perform app_private.set_source_secret(owner, v_src.id, 'v1:eA==', false, null);
        raise exception 'FALHOU: Owner do cliente trocou senha';
    exception when insufficient_privilege then null;
    end;

    -- Registrar teste no log
    perform app_private.record_source_run(v_src.id, 'test', true, '[{"key": "network", "ok": true}]', 120, null);
    if (select count(*) from app.source_sync_runs where source_id = v_src.id and run_kind = 'test' and ok) <> 1 then
        raise exception 'FALHOU: log do teste';
    end if;

    -- Desconectar: some a fonte, a ligação e o log
    perform app_private.disconnect_source(ti, v_src.id);
    if exists (select 1 from app.data_sources where id = v_src.id)
       or exists (select 1 from app.unit_source_refs where source = v_src.key) then
        raise exception 'FALHOU: desconectar';
    end if;

    if (select count(*) from app.audit_log where org_id = '10000000-0000-4000-8000-0000000fb001'
          and action in ('source.connected', 'source.secret_changed', 'source.disconnected')) <> 4 then
        raise exception 'FALHOU: auditoria (2 conexões + 1 troca + 1 desconexão)';
    end if;
end $$;

-- Produto Lex (sem segredo) não é gerenciado por essas funções
do $$
declare
    v_id uuid;
begin
    insert into app.data_sources (org_id, key, kind, name, connector)
    values ('10000000-0000-4000-8000-0000000fb001', 'lexpre', 'database', 'LexPre', 'lexpre')
    returning id into v_id;
    begin
        perform app_private.disconnect_source('00000000-0000-4000-8000-0000000fb001', v_id);
        raise exception 'FALHOU: desconectou produto';
    exception when raise_exception then
        if sqlerrm not like 'Esta fonte não é gerenciada pela tela%' then raise; end if;
    end;
end $$;

-- Pelo front: authenticated não chama as funções da API; o detalhe mostra config e canManage
set local role authenticated;
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000fb002","role":"authenticated"}';
do $$
declare
    d jsonb;
    k text;
begin
    begin
        perform app_private.connect_source('00000000-0000-4000-8000-0000000fb001',
            '20000000-0000-4000-8000-0000000fb001', 'sheets', 'X', '', '{"tab": "A"}', 'v1:YQ==', false, null);
        raise exception 'FALHOU: authenticated chamou connect_source';
    exception when insufficient_privilege then null;
    end;
    select r.source into k from app.unit_source_refs r
    where r.unit_id = '20000000-0000-4000-8000-0000000fb001' and r.source like 'gs_%';
    d := api.source_detail('org-teste-banco', 'MC_01', k);
    if d -> 'config' ->> 'tab' <> 'FINANCEIRO' or (d ->> 'canManage')::boolean or d ? 'secret_ciphertext'
       or d::text like '%bGluaw==%' then
        raise exception 'FALHOU: detalhe da planilha para o Owner do cliente: %', d;
    end if;
    raise notice 'OK: todos os casos passaram (o rollback abaixo desfaz tudo)';
end $$;

rollback;
