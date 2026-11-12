-- =============================================================================
-- Teste de 20261112160000_solicitar_acesso.sql. Roda numa transação e desfaz no fim (ROLLBACK): não deixa dados.
-- Passou = nenhum ERROR (só o aviso 'OK: ...'). Falhou = ERROR 'FALHOU: ...' (o CI para aí).
-- Uso: rodar depois da migration (CI, SQL Editor do staging ou psql).
-- Simula usuários com set local role + request.jwt.claims (o que o PostgREST faz em cada chamada).
-- =============================================================================

begin;

-- Pessoas de teste (só existem nesta transação)
insert into auth.users (id, email, raw_user_meta_data)
values ('00000000-0000-4000-8000-0000000000a1', 'pedido.teste@exemplo.com', '{"full_name":"Pessoa Teste"}'),
       ('00000000-0000-4000-8000-0000000000a2', 'pedido.teste2@exemplo.com', '{}'),
       ('00000000-0000-4000-8000-0000000000a3', 'pedido.teste3@exemplo.com', '{}');

-- Organização e unidade de teste (o banco do CI começa vazio)
insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-0000000000f1', 'org-teste-pedido', 'Org Teste Pedido');
insert into app.units (id, org_id, code, name)
values ('20000000-0000-4000-8000-0000000000f1', '10000000-0000-4000-8000-0000000000f1', 'TP', 'Unidade Teste');

create temp table t_ids (k text primary key, v uuid) on commit drop;
grant all on t_ids to authenticated;

-- ---------- quem pede: a1 ----------
set local role authenticated;
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000a1","role":"authenticated","app_metadata":{}}';

do $$
declare r jsonb; ok boolean;
begin
    r := api.request_access('  Escritório Teste  ', 'sou dev');
    if r ->> 'status' <> 'pending' or r ->> 'office' <> 'Escritório Teste' or r ->> 'full_name' <> 'Pessoa Teste' then
        raise exception 'FALHOU: pedido criado errado: %', r;
    end if;
    insert into t_ids values ('req1', (r ->> 'id')::uuid);

    ok := false;
    begin perform api.request_access('Outro', null); exception when sqlstate 'P0001' then ok := true; end;
    if not ok then raise exception 'FALHOU: segundo pedido pendente foi aceito'; end if;

    ok := false;
    begin perform api.request_access('x', null); exception when sqlstate 'P0001' then ok := true; end;
    if not ok then raise exception 'FALHOU: escritório curto foi aceito'; end if;

    if api.my_access_request() ->> 'id' <> (r ->> 'id') then raise exception 'FALHOU: my_access_request'; end if;

    -- não é equipe RA
    ok := false;
    begin perform api.count_pending_access_requests(); exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: count sem staff'; end if;
    ok := false;
    begin perform api.list_access_requests('pending'); exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: list sem staff'; end if;
    ok := false;
    begin perform api.approve_access_request((r ->> 'id')::uuid, '{}'); exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: approve sem staff'; end if;
    ok := false;
    begin perform api.reject_access_request((r ->> 'id')::uuid, null); exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: reject sem staff'; end if;
end $$;

-- ---------- a2 e a3 pedem ----------
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000a2","role":"authenticated","app_metadata":{}}';
do $$ begin insert into t_ids values ('req2', (api.request_access('Escritório Novo', null) ->> 'id')::uuid); end $$;
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000a3","role":"authenticated","app_metadata":{}}';
do $$ begin insert into t_ids values ('req3', (api.request_access('Alguém', null) ->> 'id')::uuid); end $$;

-- ---------- equipe RA decide ----------
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000a2","role":"authenticated","app_metadata":{"platform_staff":true}}';

do $$
declare
    n int; opts jsonb; v_org uuid; v_unit uuid; r jsonb; ok boolean;
    v_req1 uuid := (select v from t_ids where k = 'req1');
    v_req2 uuid := (select v from t_ids where k = 'req2');
    v_req3 uuid := (select v from t_ids where k = 'req3');
begin
    n := api.count_pending_access_requests();
    if n < 3 then raise exception 'FALHOU: count = %', n; end if;
    if jsonb_array_length(api.list_access_requests('pending')) < 3 then raise exception 'FALHOU: list pending'; end if;

    opts := api.approval_options();
    v_org := '10000000-0000-4000-8000-0000000000f1';
    v_unit := '20000000-0000-4000-8000-0000000000f1';
    if not exists (select 1 from jsonb_array_elements(opts) o
                   where (o ->> 'id')::uuid = v_org and o -> 'units' @> jsonb_build_array(jsonb_build_object('id', v_unit, 'code', 'TP', 'name', 'Unidade Teste'))) then
        raise exception 'FALHOU: approval_options sem a organização de teste: %', opts;
    end if;

    -- member sem unidade: recusado
    ok := false;
    begin
        perform api.approve_access_request(v_req1, jsonb_build_object('kind', 'existing', 'org_id', v_org, 'org_role', 'member'));
    exception when sqlstate 'P0001' then ok := true; end;
    if not ok then raise exception 'FALHOU: member sem unidade foi aceito'; end if;

    -- a1 em organização existente, leitor numa unidade
    r := api.approve_access_request(v_req1, jsonb_build_object(
        'kind', 'existing', 'org_id', v_org, 'org_role', 'member',
        'units', jsonb_build_array(jsonb_build_object('unit_id', v_unit, 'role_key', 'leitor'))));
    if r ->> 'status' <> 'approved' or (r ->> 'result_org_id')::uuid <> v_org then raise exception 'FALHOU: approve existing: %', r; end if;
    insert into t_ids values ('org1', v_org), ('unit1', v_unit);

    -- decidido não se decide de novo
    ok := false;
    begin perform api.reject_access_request(v_req1, null); exception when sqlstate 'P0001' then ok := true; end;
    if not ok then raise exception 'FALHOU: recusou pedido já aprovado'; end if;

    -- a2 em organização nova, owner
    r := api.approve_access_request(v_req2, jsonb_build_object(
        'kind', 'new', 'name', 'Escritório Novo Teste', 'slug', 'escritorio-novo-teste', 'org_role', 'owner',
        'unit', jsonb_build_object('code', 'SEDE', 'name', 'Sede')));
    insert into t_ids values ('org2', (r ->> 'result_org_id')::uuid);

    -- a3 recusado com nota
    r := api.reject_access_request(v_req3, 'não identificado');
    if r ->> 'status' <> 'rejected' or r ->> 'decision_note' <> 'não identificado' then raise exception 'FALHOU: reject: %', r; end if;
end $$;

-- ---------- a3 pode pedir de novo depois da recusa ----------
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000a3","role":"authenticated","app_metadata":{}}';
do $$ begin perform api.request_access('Alguém, de novo', null); end $$;

-- ---------- a1 aprovado não pede de novo ----------
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000a1","role":"authenticated","app_metadata":{}}';
do $$
declare ok boolean := false;
begin
    begin perform api.request_access('De novo', null); exception when sqlstate 'P0001' then ok := true; end;
    if not ok then raise exception 'FALHOU: quem já tem acesso pediu de novo'; end if;
end $$;

-- ---------- conferências como dono do banco ----------
reset role;
do $$
declare v_org2 uuid := (select v from t_ids where k = 'org2');
begin
    if not exists (select 1 from app.memberships m
                   join app.membership_units mu on mu.membership_id = m.id and mu.role_key = 'leitor'
                                               and mu.unit_id = (select v from t_ids where k = 'unit1')
                   where m.user_id = '00000000-0000-4000-8000-0000000000a1' and m.status = 'active'
                     and m.role_key = 'member' and m.org_id = (select v from t_ids where k = 'org1')) then
        raise exception 'FALHOU: associação de a1 não foi criada';
    end if;
    if not exists (select 1 from app.organizations o join app.units u on u.org_id = o.id and u.code = 'SEDE'
                   where o.id = v_org2 and o.slug = 'escritorio-novo-teste') then
        raise exception 'FALHOU: organização nova não foi criada';
    end if;
    if not exists (select 1 from app.memberships m where m.org_id = v_org2
                   and m.user_id = '00000000-0000-4000-8000-0000000000a2' and m.role_key = 'owner' and m.status = 'active') then
        raise exception 'FALHOU: owner da organização nova';
    end if;
    if (select count(*) from app.audit_log where action like 'access_request.%'
          and actor_user_id in ('00000000-0000-4000-8000-0000000000a1', '00000000-0000-4000-8000-0000000000a2',
                                '00000000-0000-4000-8000-0000000000a3')) < 7 then
        raise exception 'FALHOU: auditoria incompleta';
    end if;
    raise notice 'OK: todos os casos passaram (o rollback abaixo desfaz tudo)';
end $$;

rollback;
