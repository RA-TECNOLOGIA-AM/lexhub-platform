-- =============================================================================
-- Teste de 20261116100000_plano_clientes.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...').
-- Cenário: org 'org-teste-plano' (Pro, 2 unidades, 1 fonte atrasada, 1 fatura vencida) e
--   'org-teste-plano-2' (sem assinatura = em implantação).
--   'org-teste-dona' = dona da plataforma (como a LexGroup): Pro sem teto.
--   p1 Desenvolvedor da 1ª (operação cliente); p2 Gestor da 1ª; p3 equipe RA (platform_staff), sem associação;
--   p4 Desenvolvedor da dona.
-- =============================================================================

begin;

insert into auth.users (id, email)
values ('00000000-0000-4000-8000-0000000000b1', 'dev.plano@exemplo.com'),
       ('00000000-0000-4000-8000-0000000000b2', 'gestor.plano@exemplo.com'),
       ('00000000-0000-4000-8000-0000000000b3', 'ra.plano@exemplo.com'),
       ('00000000-0000-4000-8000-0000000000b4', 'dev.dona@exemplo.com');
insert into app.organizations (id, slug, name, platform_owner)
values ('10000000-0000-4000-8000-0000000000b1', 'org-teste-plano', 'Org Teste Plano', false),
       ('10000000-0000-4000-8000-0000000000b2', 'org-teste-plano-2', 'Org Implantação', false),
       ('10000000-0000-4000-8000-0000000000b3', 'org-teste-dona', 'Org Dona', true);
insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000000b4', '10000000-0000-4000-8000-0000000000b3',
        '00000000-0000-4000-8000-0000000000b4', 'Dev Dona', 'dev.dona@exemplo.com', 'admin', 'active');
insert into app.subscriptions (org_id, plan_key) values ('10000000-0000-4000-8000-0000000000b3', 'pro');
insert into app.units (id, org_id, code, name)
values ('20000000-0000-4000-8000-0000000000b1', '10000000-0000-4000-8000-0000000000b1', 'U1', 'Unidade 1'),
       ('20000000-0000-4000-8000-0000000000b2', '10000000-0000-4000-8000-0000000000b1', 'U2', 'Unidade 2');
insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000000b1', '10000000-0000-4000-8000-0000000000b1',
        '00000000-0000-4000-8000-0000000000b1', 'Dev Plano', 'dev.plano@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-0000000000b2', '10000000-0000-4000-8000-0000000000b1',
        '00000000-0000-4000-8000-0000000000b2', 'Gestor Plano', 'gestor.plano@exemplo.com', 'member', 'active');
insert into app.membership_units (org_id, unit_id, membership_id, role_key)
values ('10000000-0000-4000-8000-0000000000b1', '20000000-0000-4000-8000-0000000000b1',
        '40000000-0000-4000-8000-0000000000b2', 'gestor');

insert into app.subscriptions (org_id, plan_key, seat_limit, unit_limit, source_limit, history_months)
values ('10000000-0000-4000-8000-0000000000b1', 'pro', 60, 5, 15, 24);
insert into app.invoices (org_id, month, status)
values ('10000000-0000-4000-8000-0000000000b1', '2026-09-01', 'paid'),
       ('10000000-0000-4000-8000-0000000000b1', '2026-10-01', 'overdue');

-- Duas fontes: uma saudável (sucesso agora) e uma atrasada (falhou depois do último sucesso).
insert into app.data_sources (id, org_id, key, kind, name)
values ('30000000-0000-4000-8000-0000000000b1', '10000000-0000-4000-8000-0000000000b1', 'fonte_ok', 'database', 'Fonte OK'),
       ('30000000-0000-4000-8000-0000000000b2', '10000000-0000-4000-8000-0000000000b1', 'fonte_ruim', 'database', 'Fonte ruim');
insert into app.source_sync_runs (source_id, started_at, finished_at, ok)
values ('30000000-0000-4000-8000-0000000000b1', now(), now(), true),
       ('30000000-0000-4000-8000-0000000000b2', now() - interval '5 min', now() - interval '5 min', true),
       ('30000000-0000-4000-8000-0000000000b2', now(), now(), false);

set local role authenticated;

-- Desenvolvedor: vê a cobrança, com uso contado ao vivo e faturas mais recentes primeiro
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000b1","role":"authenticated"}';
do $$
declare b jsonb := api.get_billing('org-teste-plano');
begin
    if b -> 'current' ->> 'plan' <> 'pro' then raise exception 'FALHOU: plano: %', b -> 'current'; end if;
    if b -> 'usage' -> 0 ->> 'used' <> '2' or b -> 'usage' -> 0 ->> 'total' <> '60' then
        raise exception 'FALHOU: assentos: %', b -> 'usage' -> 0;
    end if;
    if b -> 'usage' -> 1 ->> 'used' <> '2' or b -> 'usage' -> 2 ->> 'used' <> '2' then
        raise exception 'FALHOU: unidades/fontes: %', b -> 'usage';
    end if;
    if jsonb_array_length(b -> 'plans') <> 3 or b -> 'plans' -> 0 ->> 'key' <> 'starter' then
        raise exception 'FALHOU: planos: %', b -> 'plans';
    end if;
    if b -> 'invoices' -> 0 ->> 'month' <> '2026-10' or jsonb_array_length(b -> 'invoices') <> 2 then
        raise exception 'FALHOU: faturas: %', b -> 'invoices';
    end if;
    if (api.my_admin_permissions('org-teste-plano') ->> 'billing')::boolean is not true then
        raise exception 'FALHOU: menu do Dev deveria mostrar cobrança';
    end if;
end $$;

-- Desenvolvedor de uma operação cliente: não vê os outros clientes, nem no menu
do $$
begin
    if (api.my_admin_permissions('org-teste-plano') ->> 'clients')::boolean then
        raise exception 'FALHOU: menu do Dev cliente não deveria mostrar Clientes';
    end if;
    perform api.list_clients();
    raise exception 'FALHOU: Dev de operação cliente não deveria ver clientes';
exception when insufficient_privilege then null;
end $$;

-- Desenvolvedor da dona da plataforma: vê Clientes e a própria cobrança, sem teto
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000b4","role":"authenticated"}';
do $$
declare
    b jsonb := api.get_billing('org-teste-dona');
    c jsonb;
begin
    if (api.my_admin_permissions('org-teste-dona') ->> 'clients')::boolean is not true then
        raise exception 'FALHOU: menu do Dev da dona deveria mostrar Clientes';
    end if;
    if b -> 'current' ->> 'plan' <> 'pro' or b -> 'usage' -> 0 -> 'total' <> 'null'::jsonb
       or b -> 'usage' -> 0 ->> 'used' <> '1' then
        raise exception 'FALHOU: dona sem teto: %', b -> 'usage';
    end if;
    if jsonb_array_length(b -> 'usage') <> 3 then raise exception 'FALHOU: sem teto, sem linha de histórico: %', b -> 'usage'; end if;
    select e into c from jsonb_array_elements(api.list_clients() -> 'clients') e where e ->> 'slug' = 'org-teste-dona';
    if c -> 'seats' -> 'total' <> 'null'::jsonb then raise exception 'FALHOU: assentos sem teto em Clientes: %', c; end if;
end $$;

-- Desde 20261127150000_lexgroup_em_todo_cliente: Owner/Dev da dona é membro automático de todo cliente
-- (via_lexgroup) e vê tudo dele, inclusive a cobrança; o assento dele não conta para o cliente.
do $$
declare b jsonb := api.get_billing('org-teste-plano');
begin
    if b -> 'current' ->> 'plan' <> 'pro' then
        raise exception 'FALHOU: Dev da dona deveria ver a cobrança do cliente: %', b -> 'current';
    end if;
    if b -> 'usage' -> 0 ->> 'used' <> '2' then
        raise exception 'FALHOU: o Dev da dona não conta assento no cliente: %', b -> 'usage' -> 0;
    end if;
end $$;

-- Gestor: não vê a cobrança, nem no menu
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000b2","role":"authenticated"}';
do $$
begin
    if (api.my_admin_permissions('org-teste-plano') ->> 'billing')::boolean then
        raise exception 'FALHOU: menu do Gestor não deveria mostrar cobrança';
    end if;
    perform api.get_billing('org-teste-plano');
    raise exception 'FALHOU: Gestor não deveria ver cobrança';
exception when insufficient_privilege then null;
end $$;

-- Equipe RA: vê os clientes e a cobrança de qualquer organização
set local request.jwt.claims =
    '{"sub":"00000000-0000-4000-8000-0000000000b3","role":"authenticated","app_metadata":{"platform_staff":true}}';
do $$
declare
    r  jsonb := api.list_clients();
    c1 jsonb;
    c2 jsonb;
begin
    select e into c1 from jsonb_array_elements(r -> 'clients') e where e ->> 'slug' = 'org-teste-plano';
    select e into c2 from jsonb_array_elements(r -> 'clients') e where e ->> 'slug' = 'org-teste-plano-2';
    if c1 ->> 'plan' <> 'pro' or c1 ->> 'billing' <> 'overdue' or (c1 ->> 'failingSources')::int <> 1
       or c1 -> 'seats' ->> 'used' <> '2' or c1 ->> 'sub' not like '2 unidades · cliente desde %' then
        raise exception 'FALHOU: cliente Pro: %', c1;
    end if;
    if c2 ->> 'plan' <> 'onboarding' or c2 ->> 'billing' <> 'onboarding_paid' or c2 -> 'seats' ->> 'total' <> '10'
       or c2 ->> 'sub' not like '0 unidades%' then
        raise exception 'FALHOU: cliente em implantação: %', c2;
    end if;
    if r -> 'monthlyRevenue' <> 'null'::jsonb then raise exception 'FALHOU: receita sem preço deveria ser null'; end if;
    if api.get_billing('org-teste-plano-2') -> 'current' ->> 'plan' <> 'onboarding' then
        raise exception 'FALHOU: equipe RA deveria ver a cobrança de qualquer org';
    end if;
end $$;

do $$ begin raise notice 'OK: plano_clientes'; end $$;

rollback;
