-- =============================================================================
-- Teste de 20261126110000_suporte_explica_acesso.sql. Roda numa transação e desfaz no fim (ROLLBACK): não deixa dados.
-- Passou = nenhum ERROR (só o aviso 'OK: ...'). Falhou = ERROR 'FALHOU: ...' (o CI para aí).
--
-- Cenário: org 'org-teste-suporte' com unidades U1 e U2; setores E1 (U1, regra 'own' para s-um), E2 (U2, sem regra).
--   Dashboards: s-um ligado em U1 e U2; s-off desligado em U1.
--   d1 = Desenvolvedor · x1 = colaborador em U1 (E1) · n1 = colaborador em U1 sem setor e em U2 (E2)
--   z1 = desativado (colaborador em U1, E1) · s1 = só membro da org, sem cargo em unidade nenhuma
-- =============================================================================

begin;

insert into auth.users (id, email, raw_user_meta_data, raw_app_meta_data)
values ('00000000-0000-4000-8000-0000000005d1', 'dev.suporte@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000005d2', 'colab.suporte@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000005d3', 'semsetor.suporte@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000005d4', 'desativado.suporte@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000005d5', 'semcargo.suporte@exemplo.com', '{}', '{}');

insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-0000000005a1', 'org-teste-suporte', 'Org Teste Suporte');
insert into app.units (id, org_id, code, name)
values ('20000000-0000-4000-8000-0000000005a1', '10000000-0000-4000-8000-0000000005a1', 'U1', 'Unidade 1'),
       ('20000000-0000-4000-8000-0000000005a2', '10000000-0000-4000-8000-0000000005a1', 'U2', 'Unidade 2');
insert into app.teams (id, org_id, unit_id, name)
values ('30000000-0000-4000-8000-0000000005a1', '10000000-0000-4000-8000-0000000005a1',
        '20000000-0000-4000-8000-0000000005a1', 'E1'),
       ('30000000-0000-4000-8000-0000000005a2', '10000000-0000-4000-8000-0000000005a1',
        '20000000-0000-4000-8000-0000000005a2', 'E2');

insert into app.dashboard_catalog (key, name, area, group_slug, active, sort_order)
values ('s-um', 'Sup Um', 'Tecnologia', 'tecnologia', true, 1),
       ('s-off', 'Sup Off', 'Tecnologia', 'tecnologia', true, 2);
insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
values ('10000000-0000-4000-8000-0000000005a1', '20000000-0000-4000-8000-0000000005a1', 's-um', true),
       ('10000000-0000-4000-8000-0000000005a1', '20000000-0000-4000-8000-0000000005a1', 's-off', false),
       ('10000000-0000-4000-8000-0000000005a1', '20000000-0000-4000-8000-0000000005a2', 's-um', true);
insert into app.access_rules (org_id, team_id, dashboard_key, scope)
values ('10000000-0000-4000-8000-0000000005a1', '30000000-0000-4000-8000-0000000005a1', 's-um', 'own'),
       ('10000000-0000-4000-8000-0000000005a1', '30000000-0000-4000-8000-0000000005a1', 's-off', 'all');

insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000005c1', '10000000-0000-4000-8000-0000000005a1',
        '00000000-0000-4000-8000-0000000005d1', 'Dev', 'dev.suporte@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-0000000005c2', '10000000-0000-4000-8000-0000000005a1',
        '00000000-0000-4000-8000-0000000005d2', 'Colab', 'colab.suporte@exemplo.com', 'member', 'active'),
       ('40000000-0000-4000-8000-0000000005c3', '10000000-0000-4000-8000-0000000005a1',
        '00000000-0000-4000-8000-0000000005d3', 'Sem Setor', 'semsetor.suporte@exemplo.com', 'member', 'active'),
       ('40000000-0000-4000-8000-0000000005c4', '10000000-0000-4000-8000-0000000005a1',
        '00000000-0000-4000-8000-0000000005d4', 'Desativado', 'desativado.suporte@exemplo.com', 'member', 'disabled'),
       ('40000000-0000-4000-8000-0000000005c5', '10000000-0000-4000-8000-0000000005a1',
        '00000000-0000-4000-8000-0000000005d5', 'Sem Cargo', 'semcargo.suporte@exemplo.com', 'member', 'active');
insert into app.membership_units (org_id, unit_id, membership_id, role_key)
values ('10000000-0000-4000-8000-0000000005a1', '20000000-0000-4000-8000-0000000005a1', '40000000-0000-4000-8000-0000000005c2', 'colaborador'),
       ('10000000-0000-4000-8000-0000000005a1', '20000000-0000-4000-8000-0000000005a1', '40000000-0000-4000-8000-0000000005c3', 'colaborador'),
       ('10000000-0000-4000-8000-0000000005a1', '20000000-0000-4000-8000-0000000005a2', '40000000-0000-4000-8000-0000000005c3', 'colaborador'),
       ('10000000-0000-4000-8000-0000000005a1', '20000000-0000-4000-8000-0000000005a1', '40000000-0000-4000-8000-0000000005c4', 'colaborador');
insert into app.membership_teams (org_id, team_id, membership_id)
values ('10000000-0000-4000-8000-0000000005a1', '30000000-0000-4000-8000-0000000005a1', '40000000-0000-4000-8000-0000000005c2'),
       ('10000000-0000-4000-8000-0000000005a1', '30000000-0000-4000-8000-0000000005a2', '40000000-0000-4000-8000-0000000005c3'),
       ('10000000-0000-4000-8000-0000000005a1', '30000000-0000-4000-8000-0000000005a1', '40000000-0000-4000-8000-0000000005c4');

do $$
declare
    u1 constant uuid := '20000000-0000-4000-8000-0000000005a1';
    u2 constant uuid := '20000000-0000-4000-8000-0000000005a2';
    d1 constant uuid := '00000000-0000-4000-8000-0000000005d1';
    x1 constant uuid := '00000000-0000-4000-8000-0000000005d2';
    n1 constant uuid := '00000000-0000-4000-8000-0000000005d3';
    z1 constant uuid := '00000000-0000-4000-8000-0000000005d4';
    s1 constant uuid := '00000000-0000-4000-8000-0000000005d5';
    e record;
    p uuid;
    un uuid;
    k text;
begin
    -- visível pelo setor, só os próprios
    select * into e from app_private.dashboard_access_explain(x1, u1, 's-um');
    if (e.scope, e.via, e.reason) is distinct from ('own'::text, 'sector'::text, null::text) then
        raise exception 'FALHOU: x1/U1/s-um: % % %', e.scope, e.via, e.reason;
    end if;

    -- desligado na unidade (o setor tem regra, mas não adianta)
    select * into e from app_private.dashboard_access_explain(x1, u1, 's-off');
    if (e.scope, e.via, e.reason) is distinct from (null::text, null::text, 'dashboard_off'::text) then
        raise exception 'FALHOU: x1/U1/s-off: % % %', e.scope, e.via, e.reason;
    end if;

    -- o Dev pode religar: continua vendo
    select * into e from app_private.dashboard_access_explain(d1, u1, 's-off');
    if (e.scope, e.via, e.reason) is distinct from ('all'::text, 'role'::text, null::text) then
        raise exception 'FALHOU: d1/U1/s-off: % % %', e.scope, e.via, e.reason;
    end if;

    -- sem cargo na unidade
    select * into e from app_private.dashboard_access_explain(x1, u2, 's-um');
    if e.reason is distinct from 'no_unit_role' or e.scope is not null then
        raise exception 'FALHOU: x1/U2/s-um: % %', e.scope, e.reason;
    end if;
    select * into e from app_private.dashboard_access_explain(s1, u1, 's-um');
    if e.reason is distinct from 'no_unit_role' then
        raise exception 'FALHOU: s1/U1/s-um: %', e.reason;
    end if;

    -- cargo na unidade, mas nenhum setor com regra (n1 em U1 sem setor; em U2 no E2 sem regra)
    select * into e from app_private.dashboard_access_explain(n1, u1, 's-um');
    if e.reason is distinct from 'no_sector_rule' or e.scope is not null then
        raise exception 'FALHOU: n1/U1/s-um: % %', e.scope, e.reason;
    end if;
    select * into e from app_private.dashboard_access_explain(n1, u2, 's-um');
    if e.reason is distinct from 'no_sector_rule' then
        raise exception 'FALHOU: n1/U2/s-um: %', e.reason;
    end if;

    -- membro desativado
    select * into e from app_private.dashboard_access_explain(z1, u1, 's-um');
    if e.reason is distinct from 'not_member' or e.scope is not null then
        raise exception 'FALHOU: z1/U1/s-um: % %', e.scope, e.reason;
    end if;
    -- desativado vem antes de "desligado": o suporte vê um motivo só para o membro inteiro
    select * into e from app_private.dashboard_access_explain(z1, u1, 's-off');
    if e.reason is distinct from 'not_member' then
        raise exception 'FALHOU: z1/U1/s-off deveria ser not_member: %', e.reason;
    end if;

    -- sempre uma linha, mesmo para dashboard que não existe na unidade
    if (select count(*) from app_private.dashboard_access_explain(x1, u2, 's-off')) <> 1 then
        raise exception 'FALHOU: explain deve devolver sempre uma linha';
    end if;

    -- paridade com a regra (antes da org ficar inativa)
    foreach p in array array[d1, x1, n1, z1, s1] loop
        foreach un in array array[u1, u2] loop
            foreach k in array array['s-um', 's-off', 'nao-existe'] loop
                if (select x.scope from app_private.dashboard_access_explain(p, un, k) x)
                   is distinct from app_private.dashboard_scope(p, un, k) then
                    raise exception 'FALHOU: paridade %/%/%', p, un, k;
                end if;
            end loop;
        end loop;
    end loop;

    -- organização inativa
    update app.organizations set active = false where id = '10000000-0000-4000-8000-0000000005a1';
    select * into e from app_private.dashboard_access_explain(d1, u1, 's-um');
    if e.reason is distinct from 'org_inactive' or e.scope is not null then
        raise exception 'FALHOU: org inativa: % %', e.scope, e.reason;
    end if;
    if app_private.dashboard_scope(d1, u1, 's-um') is not null then
        raise exception 'FALHOU: org inativa ainda dá acesso pela regra';
    end if;

    raise notice 'OK: modo_suporte (o rollback abaixo desfaz tudo)';
end $$;

rollback;
