-- =============================================================================
-- Teste de 20261119210000_auditoria_dashboards_abertos.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...').
-- Cenário: org 'org-teste-dabert' (unidades NG e LA); h1 Desenvolvedor (vê a auditoria); h2 colaborador;
-- org 'org-teste-dabert-b' (unidade XX), da qual h2 não é membro.
-- =============================================================================

begin;

insert into auth.users (id, email)
values ('00000000-0000-4000-8000-0000000da001', 'dev.dabert@exemplo.com'),
       ('00000000-0000-4000-8000-0000000da002', 'colab.dabert@exemplo.com');
insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-0000000da001', 'org-teste-dabert', 'Org Teste Dashboards Abertos'),
       ('10000000-0000-4000-8000-0000000da002', 'org-teste-dabert-b', 'Org Teste B');
insert into app.units (id, org_id, code, name, timezone)
values ('20000000-0000-4000-8000-0000000da001', '10000000-0000-4000-8000-0000000da001', 'NG', 'Nova', 'America/Manaus'),
       ('20000000-0000-4000-8000-0000000da002', '10000000-0000-4000-8000-0000000da001', 'LA', 'Lá', 'America/Manaus'),
       ('20000000-0000-4000-8000-0000000da003', '10000000-0000-4000-8000-0000000da002', 'XX', 'Outra', 'America/Manaus');
insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000da001', '10000000-0000-4000-8000-0000000da001',
        '00000000-0000-4000-8000-0000000da001', 'Dev Abertos', 'dev.dabert@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-0000000da002', '10000000-0000-4000-8000-0000000da001',
        '00000000-0000-4000-8000-0000000da002', 'Colab Abertos', 'colab.dabert@exemplo.com', 'member', 'active');
-- Dashboards ligados nas duas unidades; o colaborador vê só julgados-acordaos (exceção pessoal), não julgados-sentencas.
insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select '10000000-0000-4000-8000-0000000da001', u, k, true
from unnest(array['20000000-0000-4000-8000-0000000da001', '20000000-0000-4000-8000-0000000da002']::uuid[]) u,
     unnest(array['julgados-acordaos', 'julgados-sentencas']) k;
insert into app.membership_units (org_id, unit_id, membership_id, role_key)
select '10000000-0000-4000-8000-0000000da001', u, '40000000-0000-4000-8000-0000000da002', 'colaborador'
from unnest(array['20000000-0000-4000-8000-0000000da001', '20000000-0000-4000-8000-0000000da002']::uuid[]) u;
insert into app.member_dashboard_grants (membership_id, unit_id, dashboard_key)
select '40000000-0000-4000-8000-0000000da002', u, 'julgados-acordaos'
from unnest(array['20000000-0000-4000-8000-0000000da001', '20000000-0000-4000-8000-0000000da002']::uuid[]) u;

set local role authenticated;

-- Colaborador abre dashboards: repetição em < 5 min não grava; outra unidade grava.
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000da002","role":"authenticated"}';
do $$
begin
    if not api.log_dashboard_view('org-teste-dabert', 'ng', 'julgados-acordaos') then
        raise exception 'FALHOU: 1ª abertura deveria gravar';
    end if;
    if api.log_dashboard_view('org-teste-dabert', 'NG', 'julgados-acordaos') then
        raise exception 'FALHOU: repetição em menos de 5 min não deveria gravar';
    end if;
    if not api.log_dashboard_view('org-teste-dabert', 'LA', 'julgados-acordaos') then
        raise exception 'FALHOU: outra unidade deveria gravar';
    end if;

    -- Recusas: dashboard sem acesso, unidade de outra org, chave inexistente, org da qual não é membro.
    begin
        perform api.log_dashboard_view('org-teste-dabert', 'NG', 'julgados-sentencas');
        raise exception 'FALHOU: dashboard sem acesso deveria ser recusado';
    exception when insufficient_privilege then null;
    end;
    begin
        perform api.log_dashboard_view('org-teste-dabert', 'XX', 'julgados-acordaos');
        raise exception 'FALHOU: unidade de outra org deveria ser recusada';
    exception when invalid_parameter_value then null;
    end;
    begin
        perform api.log_dashboard_view('org-teste-dabert', 'NG', 'nao-existe');
        raise exception 'FALHOU: dashboard inexistente deveria ser recusado';
    exception when invalid_parameter_value then null;
    end;
    begin
        perform api.log_dashboard_view('org-teste-dabert-b', 'XX', 'julgados-acordaos');
        raise exception 'FALHOU: não-membro deveria ser recusado';
    exception when insufficient_privilege then null;
    end;

    -- Colaborador não vê a auditoria.
    begin
        perform api.list_audit('org-teste-dabert');
        raise exception 'FALHOU: colaborador não deveria ver a auditoria';
    exception when insufficient_privilege then null;
    end;
end $$;

-- Desenvolvedor: filtros de período e tipo no banco, e o aviso de limite.
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000da001","role":"authenticated"}';
do $$
declare r jsonb;
begin
    perform api.log_audit_export('org-teste-dabert', '', '', 3); -- um evento de outro tipo

    r := api.list_audit('org-teste-dabert', p_actions => '{dashboard.view}');
    if jsonb_array_length(r -> 'events') <> 2 or (r ->> 'truncated')::boolean then
        raise exception 'FALHOU: filtro por tipo: %', r;
    end if;
    if r -> 'events' -> 0 ->> 'actor' <> 'Colab Abertos'
       or r -> 'events' -> 0 ->> 'targetName' is null
       or r -> 'events' -> 0 -> 'metadata' <> '{"org": "org-teste-dabert", "unit": "LA"}'::jsonb then
        raise exception 'FALHOU: formato do evento: %', r -> 'events' -> 0;
    end if;

    -- Pessoa filtrada no banco; a lista de pessoas vem do período inteiro (sem o filtro de pessoa).
    r := api.list_audit('org-teste-dabert', p_actor => 'Dev Abertos');
    if jsonb_array_length(r -> 'events') <> 1 or r -> 'events' -> 0 ->> 'action' <> 'audit.export'
       or r -> 'actors' <> '["Colab Abertos", "Dev Abertos"]'::jsonb then
        raise exception 'FALHOU: filtro por pessoa / lista de pessoas: %', r;
    end if;

    -- "Outros": tudo menos os tipos conhecidos (p_exclude_actions).
    r := api.list_audit('org-teste-dabert', p_exclude_actions => '{dashboard.view}');
    if jsonb_array_length(r -> 'events') <> 1 or r -> 'events' -> 0 ->> 'action' <> 'audit.export' then
        raise exception 'FALHOU: exclusão de tipos: %', r;
    end if;

    r := api.list_audit('org-teste-dabert', p_from => now() + interval '1 day');
    if jsonb_array_length(r -> 'events') <> 0 then
        raise exception 'FALHOU: período no futuro deveria vir vazio: %', r;
    end if;

    r := api.list_audit('org-teste-dabert', p_to => now() - interval '1 day');
    if jsonb_array_length(r -> 'events') <> 0 then
        raise exception 'FALHOU: período no passado deveria vir vazio: %', r;
    end if;

    r := api.list_audit('org-teste-dabert', p_limit => 1);
    if jsonb_array_length(r -> 'events') <> 1 or not (r ->> 'truncated')::boolean then
        raise exception 'FALHOU: limite deveria cortar e avisar: %', r;
    end if;

    r := api.list_audit('org-teste-dabert');
    if jsonb_array_length(r -> 'events') <> 3 or (r ->> 'truncated')::boolean then
        raise exception 'FALHOU: sem filtros deveria trazer tudo: %', r;
    end if;

    raise notice 'OK: todos os casos passaram (o rollback abaixo desfaz tudo)';
end $$;

rollback;
