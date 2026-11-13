-- =============================================================================
-- Teste de 20261113200000_detalhe_fonte.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...').
-- Cenário: org 'org-teste-detalhe' com U1 e U2; fonte 'db1' (banco de U1, também usado por U2).
--   Dashboards: 'dash-teste-1' usa db1 e está ativo em U1 e U2; 'dash-teste-2' usa db1 e só está ativo em U1.
--   Log de db1: 12 sincronizações (o detalhe mostra as 10 últimas), a última com falha.
--   Pessoas: f1 Desenvolvedor; f2 Gestor de U1.
-- =============================================================================

begin;

insert into auth.users (id, email)
values ('00000000-0000-4000-8000-0000000000f1', 'dev.detalhe@exemplo.com'),
       ('00000000-0000-4000-8000-0000000000f2', 'gestor.detalhe@exemplo.com');
insert into app.organizations (id, slug, name) values ('10000000-0000-4000-8000-0000000000f1', 'org-teste-detalhe', 'Org Teste Detalhe');
insert into app.units (id, org_id, code, name)
values ('20000000-0000-4000-8000-0000000000f1', '10000000-0000-4000-8000-0000000000f1', 'U1', 'Unidade 1'),
       ('20000000-0000-4000-8000-0000000000f2', '10000000-0000-4000-8000-0000000000f1', 'U2', 'Unidade 2');
insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000000f1', '10000000-0000-4000-8000-0000000000f1',
        '00000000-0000-4000-8000-0000000000f1', 'Dev', 'dev.detalhe@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-0000000000f2', '10000000-0000-4000-8000-0000000000f1',
        '00000000-0000-4000-8000-0000000000f2', 'Gestor', 'gestor.detalhe@exemplo.com', 'member', 'active');
insert into app.membership_units (org_id, unit_id, membership_id, role_key)
values ('10000000-0000-4000-8000-0000000000f1', '20000000-0000-4000-8000-0000000000f1', '40000000-0000-4000-8000-0000000000f2', 'gestor');

insert into app.data_sources (id, org_id, key, kind, name, detail, owner_unit_id)
values ('50000000-0000-4000-8000-0000000000f1', '10000000-0000-4000-8000-0000000000f1', 'db1', 'database', 'Banco 1',
        'Postgres · somente leitura', '20000000-0000-4000-8000-0000000000f1');
insert into app.unit_source_refs (unit_id, source, ref)
values ('20000000-0000-4000-8000-0000000000f1', 'db1', 'U1'),
       ('20000000-0000-4000-8000-0000000000f2', 'db1', 'U2');

insert into app.dashboard_catalog (key, name, description, area, source, sort_order, status)
values ('dash-teste-1', 'Dashboard Teste 1', '', 'Teste', 'Banco 1', 1, 'available'),
       ('dash-teste-2', 'Dashboard Teste 2', '', 'Teste', 'Banco 1', 2, 'available');
insert into app.dashboard_sources (dashboard_key, source_key)
values ('dash-teste-1', 'db1'), ('dash-teste-2', 'db1');
insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
values ('10000000-0000-4000-8000-0000000000f1', '20000000-0000-4000-8000-0000000000f1', 'dash-teste-1', true),
       ('10000000-0000-4000-8000-0000000000f1', '20000000-0000-4000-8000-0000000000f1', 'dash-teste-2', true),
       ('10000000-0000-4000-8000-0000000000f1', '20000000-0000-4000-8000-0000000000f2', 'dash-teste-1', true);

-- 12 sincronizações de 10 em 10 min; a mais recente (há 1 min) falhou
insert into app.source_sync_runs (source_id, started_at, finished_at, ok, rows, error)
select '50000000-0000-4000-8000-0000000000f1',
       now() - make_interval(mins => 10 * g + 2), now() - make_interval(mins => 10 * g + 1),
       g > 0, case when g > 0 then 1000 + g end, case when g = 0 then 'tempo esgotado (30 s)' end
from generate_series(0, 11) g;

set local role authenticated;

-- Desenvolvedor, de U2: a fonte é de U1 (gerenciada por), só o dashboard ativo em U2, 10 sincronizações
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000f1","role":"authenticated"}';
do $$
declare d jsonb := api.source_detail('org-teste-detalhe', 'U2', 'db1');
begin
    if d -> 'unit' ->> 'code' <> 'U2' or d -> 'owner' ->> 'code' <> 'U1' then
        raise exception 'FALHOU: unidade/dona: %', d;
    end if;
    if d -> 'source' ->> 'managedBy' <> 'Unidade 1' or d -> 'source' ->> 'status' <> 'late' then
        raise exception 'FALHOU: linha da fonte: %', d -> 'source';
    end if;
    if jsonb_array_length(d -> 'dashboards') <> 1 or d -> 'dashboards' -> 0 ->> 'key' <> 'dash-teste-1' then
        raise exception 'FALHOU: U2 deveria ver só dash-teste-1: %', d -> 'dashboards';
    end if;
    if jsonb_array_length(d -> 'runs') <> 10 then
        raise exception 'FALHOU: deveria trazer 10 sincronizações: %', jsonb_array_length(d -> 'runs');
    end if;
    if (d -> 'runs' -> 0 ->> 'ok')::boolean or d -> 'runs' -> 0 ->> 'error' <> 'tempo esgotado (30 s)' then
        raise exception 'FALHOU: a primeira deveria ser a falha mais recente: %', d -> 'runs' -> 0;
    end if;
    -- De U1: os dois dashboards e sem "gerenciada por"
    d := api.source_detail('org-teste-detalhe', 'U1', 'db1');
    if jsonb_array_length(d -> 'dashboards') <> 2 or d -> 'source' -> 'managedBy' <> 'null'::jsonb then
        raise exception 'FALHOU: U1: %', d;
    end if;
    -- A lista continua igual (agora com o auxiliar): a mesma linha da fonte
    if (select s from jsonb_array_elements(api.list_sources('org-teste-detalhe') -> 'units') u,
                     jsonb_array_elements(u -> 'sources') s
        where u -> 'unit' ->> 'code' = 'U2') <> api.source_detail('org-teste-detalhe', 'U2', 'db1') -> 'source' then
        raise exception 'FALHOU: lista e detalhe deveriam montar a mesma linha';
    end if;
    -- Fonte que a unidade não usa: P0001
    begin
        perform api.source_detail('org-teste-detalhe', 'U1', 'nao-existe');
        raise exception 'FALHOU: fonte inexistente deveria dar P0001';
    exception when raise_exception then
        if sqlerrm like 'FALHOU%' then raise; end if;
    end;
end $$;

-- Gestor de U1: vê U1; U2 está fora do escopo (42501)
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000f2","role":"authenticated"}';
do $$
begin
    perform api.source_detail('org-teste-detalhe', 'U1', 'db1');
    begin
        perform api.source_detail('org-teste-detalhe', 'U2', 'db1');
        raise exception 'FALHOU: Gestor de U1 não deveria ver U2';
    exception when insufficient_privilege then null;
    end;
    begin
        perform 1 from app.dashboard_sources limit 1;
        raise exception 'FALHOU: authenticated não deveria ler app.dashboard_sources direto';
    exception when insufficient_privilege then null;
    end;
    raise notice 'OK: todos os casos passaram (o rollback abaixo desfaz tudo)';
end $$;

rollback;
