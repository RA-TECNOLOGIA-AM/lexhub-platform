-- =============================================================================
-- Teste de 20261113180000_unidades_fontes.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...').
-- Cenário: org 'org-teste-fontes' com U1 e U2.
--   Fontes: 'prod1' (produto, sem dona), 'db1' (banco de U1, também usado por U2), 'sh1' (planilha de U1).
--   Log: db1 sincronizou há 5 min (saudável); prod1 falhou depois do último sucesso (atrasada);
--        sh1 nunca rodou (aguardando).
--   Pessoas: e1 Desenvolvedor; e2 Gestor de U1; e3 Controller de U2; e4 Colaborador de U1.
-- =============================================================================

begin;

insert into auth.users (id, email)
values ('00000000-0000-4000-8000-0000000000e1', 'dev.fontes@exemplo.com'),
       ('00000000-0000-4000-8000-0000000000e2', 'gestor.fontes@exemplo.com'),
       ('00000000-0000-4000-8000-0000000000e3', 'controller.fontes@exemplo.com'),
       ('00000000-0000-4000-8000-0000000000e4', 'colab.fontes@exemplo.com');
insert into app.organizations (id, slug, name) values ('10000000-0000-4000-8000-0000000000e1', 'org-teste-fontes', 'Org Teste Fontes');
insert into app.units (id, org_id, code, name, timezone)
values ('20000000-0000-4000-8000-0000000000e1', '10000000-0000-4000-8000-0000000000e1', 'U1', 'Unidade 1', 'America/Manaus'),
       ('20000000-0000-4000-8000-0000000000e2', '10000000-0000-4000-8000-0000000000e1', 'U2', 'Unidade 2', 'America/Sao_Paulo');
insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000000e1', '10000000-0000-4000-8000-0000000000e1',
        '00000000-0000-4000-8000-0000000000e1', 'Dev', 'dev.fontes@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-0000000000e2', '10000000-0000-4000-8000-0000000000e1',
        '00000000-0000-4000-8000-0000000000e2', 'Gestor', 'gestor.fontes@exemplo.com', 'member', 'active'),
       ('40000000-0000-4000-8000-0000000000e3', '10000000-0000-4000-8000-0000000000e1',
        '00000000-0000-4000-8000-0000000000e3', 'Controller', 'controller.fontes@exemplo.com', 'member', 'active'),
       ('40000000-0000-4000-8000-0000000000e4', '10000000-0000-4000-8000-0000000000e1',
        '00000000-0000-4000-8000-0000000000e4', 'Colab', 'colab.fontes@exemplo.com', 'member', 'active');
insert into app.membership_units (org_id, unit_id, membership_id, role_key)
values ('10000000-0000-4000-8000-0000000000e1', '20000000-0000-4000-8000-0000000000e1', '40000000-0000-4000-8000-0000000000e2', 'gestor'),
       ('10000000-0000-4000-8000-0000000000e1', '20000000-0000-4000-8000-0000000000e2', '40000000-0000-4000-8000-0000000000e3', 'controller'),
       ('10000000-0000-4000-8000-0000000000e1', '20000000-0000-4000-8000-0000000000e1', '40000000-0000-4000-8000-0000000000e4', 'colaborador');

insert into app.data_sources (id, org_id, key, kind, name, detail, owner_unit_id)
values ('50000000-0000-4000-8000-0000000000e1', '10000000-0000-4000-8000-0000000000e1', 'prod1', 'flow', 'Produto 1', 'Contratado', null),
       ('50000000-0000-4000-8000-0000000000e2', '10000000-0000-4000-8000-0000000000e1', 'db1', 'database', 'Banco 1', 'Postgres', '20000000-0000-4000-8000-0000000000e1'),
       ('50000000-0000-4000-8000-0000000000e3', '10000000-0000-4000-8000-0000000000e1', 'sh1', 'sheet', 'Planilha 1', 'Sheets', '20000000-0000-4000-8000-0000000000e1');
insert into app.unit_source_refs (unit_id, source, ref)
values ('20000000-0000-4000-8000-0000000000e1', 'prod1', '1'),
       ('20000000-0000-4000-8000-0000000000e1', 'db1', 'U1'),
       ('20000000-0000-4000-8000-0000000000e1', 'sh1', 'U1'),
       ('20000000-0000-4000-8000-0000000000e2', 'prod1', '2'),
       ('20000000-0000-4000-8000-0000000000e2', 'db1', 'U2');
insert into app.source_sync_runs (source_id, started_at, finished_at, ok, rows, error)
values ('50000000-0000-4000-8000-0000000000e2', now() - interval '6 min', now() - interval '5 min', true, 1200, null),
       ('50000000-0000-4000-8000-0000000000e1', now() - interval '61 min', now() - interval '60 min', true, 300, null),
       ('50000000-0000-4000-8000-0000000000e1', now() - interval '31 min', now() - interval '30 min', false, null, 'tempo esgotado (30 s)');

set local role authenticated;

-- Desenvolvedor: as duas unidades, produto antes de conexão, status pelo log
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000e1","role":"authenticated"}';
do $$
declare
    r  jsonb := api.list_sources('org-teste-fontes');
    u1 jsonb;
    u2 jsonb;
begin
    if jsonb_array_length(r -> 'units') <> 2 then raise exception 'FALHOU: Dev deveria ver 2 unidades: %', r; end if;
    select x into u1 from jsonb_array_elements(r -> 'units') x where x -> 'unit' ->> 'code' = 'U1';
    select x into u2 from jsonb_array_elements(r -> 'units') x where x -> 'unit' ->> 'code' = 'U2';
    if (r ->> 'syncEveryMin')::int <> 10 then raise exception 'FALHOU: syncEveryMin'; end if;
    if u1 -> 'sources' -> 0 ->> 'id' <> 'prod1' or u1 -> 'sources' -> 0 ->> 'group' <> 'product' then
        raise exception 'FALHOU: produto deveria vir primeiro: %', u1 -> 'sources';
    end if;
    if (select s ->> 'status' from jsonb_array_elements(u1 -> 'sources') s where s ->> 'id' = 'db1') <> 'healthy' then
        raise exception 'FALHOU: db1 deveria estar saudável: %', u1 -> 'sources';
    end if;
    if (select s ->> 'status' from jsonb_array_elements(u1 -> 'sources') s where s ->> 'id' = 'prod1') <> 'late'
       or (select (s ->> 'failures')::int from jsonb_array_elements(u1 -> 'sources') s where s ->> 'id' = 'prod1') <> 1 then
        raise exception 'FALHOU: prod1 deveria estar atrasada com 1 falha: %', u1 -> 'sources';
    end if;
    if (select s ->> 'status' from jsonb_array_elements(u1 -> 'sources') s where s ->> 'id' = 'sh1') <> 'waiting' then
        raise exception 'FALHOU: sh1 deveria estar aguardando: %', u1 -> 'sources';
    end if;
    if u1 -> 'lastFailure' ->> 'source' <> 'Produto 1' or u1 -> 'lastFailure' ->> 'message' <> 'tempo esgotado (30 s)' then
        raise exception 'FALHOU: última falha de U1: %', u1 -> 'lastFailure';
    end if;
    -- Banco de U1 usado por U2: "gerenciada por" a dona; na própria U1, não
    if (select s ->> 'managedBy' from jsonb_array_elements(u2 -> 'sources') s where s ->> 'id' = 'db1') <> 'Unidade 1' then
        raise exception 'FALHOU: db1 em U2 deveria ser gerenciada por Unidade 1: %', u2 -> 'sources';
    end if;
    if (select s -> 'managedBy' from jsonb_array_elements(u1 -> 'sources') s where s ->> 'id' = 'db1') <> 'null'::jsonb then
        raise exception 'FALHOU: db1 em U1 não tem "gerenciada por": %', u1 -> 'sources';
    end if;
    if jsonb_array_length(u2 -> 'sources') <> 2 or u2 ->> 'timezone' <> 'America/Sao_Paulo' then
        raise exception 'FALHOU: U2 deveria ter 2 fontes e fuso de SP: %', u2;
    end if;
end $$;

-- Gestor de U1: só U1
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000e2","role":"authenticated"}';
do $$
declare r jsonb := api.list_sources('org-teste-fontes');
begin
    if jsonb_array_length(r -> 'units') <> 1 or r -> 'units' -> 0 -> 'unit' ->> 'code' <> 'U1' then
        raise exception 'FALHOU: Gestor deveria ver só U1: %', r -> 'units';
    end if;
end $$;

-- Controller de U2: só U2 (as unidades a que tem acesso)
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000e3","role":"authenticated"}';
do $$
declare r jsonb := api.list_sources('org-teste-fontes');
begin
    if jsonb_array_length(r -> 'units') <> 1 or r -> 'units' -> 0 -> 'unit' ->> 'code' <> 'U2' then
        raise exception 'FALHOU: Controller deveria ver só U2: %', r -> 'units';
    end if;
    if (api.my_admin_permissions('org-teste-fontes') ->> 'sources')::boolean is not true then
        raise exception 'FALHOU: menu do Controller deveria mostrar fontes';
    end if;
end $$;

-- Colaborador: recusado (42501) e sem o item no menu; tabelas fechadas para leitura direta
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000e4","role":"authenticated"}';
do $$
begin
    begin
        perform api.list_sources('org-teste-fontes');
        raise exception 'FALHOU: Colaborador não deveria ver as fontes';
    exception when insufficient_privilege then null;
    end;
    begin
        perform api.list_sources('nao-existe');
        raise exception 'FALHOU: org inexistente deveria dar 42501';
    exception when insufficient_privilege then null;
    end;
    if (api.my_admin_permissions('org-teste-fontes') ->> 'sources')::boolean then
        raise exception 'FALHOU: menu do Colaborador não deveria mostrar fontes';
    end if;
    begin
        perform 1 from app.data_sources limit 1;
        raise exception 'FALHOU: authenticated não deveria ler app.data_sources direto';
    exception when insufficient_privilege then null;
    end;
    raise notice 'OK: todos os casos passaram (o rollback abaixo desfaz tudo)';
end $$;

rollback;
