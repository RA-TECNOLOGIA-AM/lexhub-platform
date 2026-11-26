-- =============================================================================
-- Teste de 20261118130000_dashboards_liga_desliga.sql (+ 20261126210000: o Owner também liga/desliga). Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...'). Falhou = ERROR 'FALHOU: ...'.
--
-- Cenário: org 'org-teste-liga' com U1 e U2; d-um ligado nas duas; equipe E1 (U1) com regra E1 -> d-um.
--   o1 = Owner · d1 = Desenvolvedor · x1 = colaborador em U1 (E1)
-- =============================================================================

begin;

insert into auth.users (id, email, raw_user_meta_data, raw_app_meta_data)
values ('00000000-0000-4000-8000-0000000000e1', 'owner.liga@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000e2', 'dev.liga@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000e3', 'colab.liga@exemplo.com', '{}', '{}');

insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-0000000000e1', 'org-teste-liga', 'Org Teste Liga');
insert into app.units (id, org_id, code, name)
values ('20000000-0000-4000-8000-0000000000e1', '10000000-0000-4000-8000-0000000000e1', 'U1', 'Unidade 1'),
       ('20000000-0000-4000-8000-0000000000e2', '10000000-0000-4000-8000-0000000000e1', 'U2', 'Unidade 2');
insert into app.teams (id, org_id, unit_id, name)
values ('30000000-0000-4000-8000-0000000000e1', '10000000-0000-4000-8000-0000000000e1',
        '20000000-0000-4000-8000-0000000000e1', 'E1');

insert into app.dashboard_catalog (key, name, area, active, sort_order)
values ('d-liga', 'Dash Liga', 'Tecnologia', true, 1);
insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
values ('10000000-0000-4000-8000-0000000000e1', '20000000-0000-4000-8000-0000000000e1', 'd-liga', true),
       ('10000000-0000-4000-8000-0000000000e1', '20000000-0000-4000-8000-0000000000e2', 'd-liga', true);
insert into app.access_rules (org_id, team_id, dashboard_key, scope)
values ('10000000-0000-4000-8000-0000000000e1', '30000000-0000-4000-8000-0000000000e1', 'd-liga', 'all');

insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000000e1', '10000000-0000-4000-8000-0000000000e1',
        '00000000-0000-4000-8000-0000000000e1', 'Owner Liga', 'owner.liga@exemplo.com', 'owner', 'active'),
       ('40000000-0000-4000-8000-0000000000e2', '10000000-0000-4000-8000-0000000000e1',
        '00000000-0000-4000-8000-0000000000e2', 'Dev Liga', 'dev.liga@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-0000000000e3', '10000000-0000-4000-8000-0000000000e1',
        '00000000-0000-4000-8000-0000000000e3', 'Colab Liga', 'colab.liga@exemplo.com', 'member', 'active');
insert into app.membership_units (org_id, unit_id, membership_id, role_key)
values ('10000000-0000-4000-8000-0000000000e1', '20000000-0000-4000-8000-0000000000e1',
        '40000000-0000-4000-8000-0000000000e3', 'colaborador');
insert into app.membership_teams (org_id, team_id, membership_id)
values ('10000000-0000-4000-8000-0000000000e1', '30000000-0000-4000-8000-0000000000e1',
        '40000000-0000-4000-8000-0000000000e3');

do $$
declare
    owner uuid := '00000000-0000-4000-8000-0000000000e1';
    dev   uuid := '00000000-0000-4000-8000-0000000000e2';
    colab uuid := '00000000-0000-4000-8000-0000000000e3';
    u1    uuid := '20000000-0000-4000-8000-0000000000e1';
    u2    uuid := '20000000-0000-4000-8000-0000000000e2';
    n     integer;
begin
    -- Ligado: todos veem
    if app_private.dashboard_scope(colab, u1, 'd-liga') is distinct from 'all' then
        raise exception 'FALHOU: colaborador deveria ver o ligado';
    end if;

    -- Owner e Desenvolvedor desligam; o colaborador não
    begin
        perform app_private.set_dashboard_enabled(colab, 'org-teste-liga', 'U1', 'd-liga', false);
        raise exception 'FALHOU: colaborador não deveria desligar';
    exception when insufficient_privilege then null;
    end;

    -- Dev desliga em U1
    if app_private.set_dashboard_enabled(dev, 'org-teste-liga', 'U1', 'd-liga', false) is distinct from false then
        raise exception 'FALHOU: deveria devolver false';
    end if;
    if (select enabled from app.org_dashboards where unit_id = u1 and dashboard_key = 'd-liga') then
        raise exception 'FALHOU: org_dashboards continua ligado';
    end if;

    -- Some para o colaborador; Dev e Owner continuam abrindo (podem religar); U2 não muda
    if app_private.dashboard_scope(colab, u1, 'd-liga') is not null then
        raise exception 'FALHOU: colaborador ainda vê o desligado';
    end if;
    if app_private.dashboard_scope(owner, u1, 'd-liga') is distinct from 'all' then
        raise exception 'FALHOU: Owner deveria abrir o desligado';
    end if;
    if app_private.dashboard_scope(dev, u1, 'd-liga') is distinct from 'all' then
        raise exception 'FALHOU: Dev deveria abrir o desligado';
    end if;
    if app_private.dashboard_scope(owner, u2, 'd-liga') is distinct from 'all' then
        raise exception 'FALHOU: U2 não deveria mudar';
    end if;

    -- Auditoria: uma linha; repetir o mesmo valor não audita de novo
    perform app_private.set_dashboard_enabled(dev, 'org-teste-liga', 'U1', 'd-liga', false);
    select count(*) into n from app.audit_log
    where actor_user_id = dev and action = 'dashboard.disabled' and target_id = 'd-liga'
      and metadata ->> 'unit' = 'U1';
    if n <> 1 then raise exception 'FALHOU: esperava 1 auditoria de desligar, veio %', n; end if;

    -- Dashboard que não existe na unidade
    begin
        perform app_private.set_dashboard_enabled(dev, 'org-teste-liga', 'U1', 'nao-existe', false);
        raise exception 'FALHOU: dashboard inexistente deveria dar erro';
    exception when raise_exception then
        if sqlerrm like 'FALHOU%' then raise; end if;
    end;

    -- Religa: volta para todos
    perform app_private.set_dashboard_enabled(dev, 'org-teste-liga', 'U1', 'd-liga', true);
    if app_private.dashboard_scope(colab, u1, 'd-liga') is distinct from 'all' then
        raise exception 'FALHOU: religado, o colaborador deveria ver';
    end if;
    select count(*) into n from app.audit_log where actor_user_id = dev and action = 'dashboard.enabled';
    if n <> 1 then raise exception 'FALHOU: esperava 1 auditoria de religar, veio %', n; end if;

    -- Owner desliga e religa (U2), com auditoria em nome dele
    if app_private.set_dashboard_enabled(owner, 'org-teste-liga', 'U2', 'd-liga', false) is distinct from false then
        raise exception 'FALHOU: Owner deveria desligar';
    end if;
    if (select enabled from app.org_dashboards where unit_id = u2 and dashboard_key = 'd-liga') then
        raise exception 'FALHOU: org_dashboards de U2 continua ligado';
    end if;
    perform app_private.set_dashboard_enabled(owner, 'org-teste-liga', 'U2', 'd-liga', true);
    select count(*) into n from app.audit_log
    where actor_user_id = owner and action in ('dashboard.disabled', 'dashboard.enabled');
    if n <> 2 then raise exception 'FALHOU: esperava 2 auditorias do Owner, veio %', n; end if;

    raise notice 'OK: dashboards_liga_desliga';
end;
$$;

rollback;
