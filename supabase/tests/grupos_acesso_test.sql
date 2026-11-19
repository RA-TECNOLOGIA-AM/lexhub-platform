-- =============================================================================
-- Teste de 20261119170000_grupos_acesso.sql. Roda numa transação e desfaz no fim (ROLLBACK): não deixa dados.
-- Passou = nenhum ERROR (só o aviso 'OK: ...'). Falhou = ERROR 'FALHOU: ...' (o CI para aí).
--
-- Cenário: org 'org-teste-grupos', unidades U1 e U2.
--   Dashboards: j1, j2 (Jurídico) e f1 (Financeiro) ligados em U1 e U2; j2 desligado em U2.
--   Setores U1: CTRL (grupo juridico), DIR (vê tudo), CEL (regra card a card: j1). Setor U2: CTRL2 (grupo juridico).
--   c1 = colaborador U1 (CTRL) e U2 (CTRL2) · c2 = colaborador U1 (CEL) · d1 = colaborador U1 (DIR)
--   l1 = leitor U1 (CTRL) · p1 = colaborador U1 e U2 sem setor; exceções: grupo financeiro em U1, avulso j1 em U2
--   g1 = Gestor só em U1 · v1 = Desenvolvedor
-- =============================================================================

begin;

insert into auth.users (id, email, raw_user_meta_data, raw_app_meta_data)
values ('00000000-0000-4000-8000-0000000000e1', 'c1.grupos@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000e2', 'c2.grupos@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000e3', 'd1.grupos@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000e4', 'l1.grupos@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000e5', 'p1.grupos@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000e6', 'g1.grupos@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000e7', 'v1.grupos@exemplo.com', '{}', '{}');

insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-0000000000e1', 'org-teste-grupos', 'Org Teste Grupos');
insert into app.units (id, org_id, code, name)
values ('20000000-0000-4000-8000-0000000000e1', '10000000-0000-4000-8000-0000000000e1', 'U1', 'Unidade 1'),
       ('20000000-0000-4000-8000-0000000000e2', '10000000-0000-4000-8000-0000000000e1', 'U2', 'Unidade 2');
insert into app.teams (id, org_id, unit_id, name)
values ('30000000-0000-4000-8000-0000000000e1', '10000000-0000-4000-8000-0000000000e1', '20000000-0000-4000-8000-0000000000e1', 'CTRL'),
       ('30000000-0000-4000-8000-0000000000e2', '10000000-0000-4000-8000-0000000000e1', '20000000-0000-4000-8000-0000000000e1', 'DIR'),
       ('30000000-0000-4000-8000-0000000000e3', '10000000-0000-4000-8000-0000000000e1', '20000000-0000-4000-8000-0000000000e1', 'CEL'),
       ('30000000-0000-4000-8000-0000000000e4', '10000000-0000-4000-8000-0000000000e1', '20000000-0000-4000-8000-0000000000e2', 'CTRL2');
update app.teams set sees_all = true where id = '30000000-0000-4000-8000-0000000000e2';

-- j1 sem group_slug: o gatilho preenche pela área
insert into app.dashboard_catalog (key, name, area, active, sort_order)
values ('t-j1', 'Jur Um', 'Jurídico', true, 1);
insert into app.dashboard_catalog (key, name, area, group_slug, active, sort_order)
values ('t-j2', 'Jur Dois', 'Jurídico', 'juridico', true, 2),
       ('t-f1', 'Fin Um', 'Financeiro', 'financeiro', true, 3);
insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select '10000000-0000-4000-8000-0000000000e1', u, k, not (u = '20000000-0000-4000-8000-0000000000e2' and k = 't-j2')
from unnest(array['20000000-0000-4000-8000-0000000000e1', '20000000-0000-4000-8000-0000000000e2']::uuid[]) u,
     unnest(array['t-j1', 't-j2', 't-f1']) k;

insert into app.team_group_grants (org_id, team_id, group_slug)
values ('10000000-0000-4000-8000-0000000000e1', '30000000-0000-4000-8000-0000000000e1', 'juridico'),
       ('10000000-0000-4000-8000-0000000000e1', '30000000-0000-4000-8000-0000000000e4', 'juridico');
insert into app.access_rules (org_id, team_id, dashboard_key, scope)
values ('10000000-0000-4000-8000-0000000000e1', '30000000-0000-4000-8000-0000000000e3', 't-j1', 'all');

insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
select ('40000000-0000-4000-8000-0000000000' || x.s)::uuid, '10000000-0000-4000-8000-0000000000e1',
       ('00000000-0000-4000-8000-0000000000' || x.s)::uuid, x.n, x.n || '.grupos@exemplo.com', x.r, 'active'
from (values ('e1', 'c1', 'member'), ('e2', 'c2', 'member'), ('e3', 'd1', 'member'), ('e4', 'l1', 'member'),
             ('e5', 'p1', 'member'), ('e6', 'g1', 'member'), ('e7', 'v1', 'admin')) x(s, n, r);
insert into app.membership_units (org_id, unit_id, membership_id, role_key)
select '10000000-0000-4000-8000-0000000000e1', ('20000000-0000-4000-8000-0000000000' || x.u)::uuid,
       ('40000000-0000-4000-8000-0000000000' || x.m)::uuid, x.r
from (values ('e1', 'e1', 'colaborador'), ('e2', 'e1', 'colaborador'), ('e1', 'e2', 'colaborador'),
             ('e1', 'e3', 'colaborador'), ('e1', 'e4', 'leitor'), ('e1', 'e5', 'colaborador'),
             ('e2', 'e5', 'colaborador'), ('e1', 'e6', 'gestor')) x(u, m, r);
insert into app.membership_teams (org_id, team_id, membership_id)
select '10000000-0000-4000-8000-0000000000e1', ('30000000-0000-4000-8000-0000000000' || x.t)::uuid,
       ('40000000-0000-4000-8000-0000000000' || x.m)::uuid
from (values ('e1', 'e1'), ('e4', 'e1'), ('e3', 'e2'), ('e2', 'e3'), ('e1', 'e4')) x(t, m);
insert into app.member_group_grants (membership_id, unit_id, group_slug)
values ('40000000-0000-4000-8000-0000000000e5', '20000000-0000-4000-8000-0000000000e1', 'financeiro');
insert into app.member_dashboard_grants (membership_id, unit_id, dashboard_key)
values ('40000000-0000-4000-8000-0000000000e5', '20000000-0000-4000-8000-0000000000e2', 't-j1');

-- ---------- A regra: (pessoa, unidade, dashboard) -> scope / exporta ----------
do $$
declare
    c record;
    v_scope text;
    v_export boolean;
begin
    if (select group_slug from app.dashboard_catalog where key = 't-j1') <> 'juridico' then
        raise exception 'FALHOU: gatilho não preencheu group_slug pela área';
    end if;

    for c in
        select * from (values
            -- pessoa, unidade, dashboard, scope esperado, exporta esperado
            ('e1', 'e1', 't-j1', 'all', true),    -- grupo do setor
            ('e1', 'e1', 't-j2', 'all', true),
            ('e1', 'e1', 't-f1', null,  false),   -- fora do grupo
            ('e1', 'e2', 't-j1', 'all', true),    -- grupo do setor da outra unidade
            ('e1', 'e2', 't-j2', null,  false),   -- desligado em U2
            ('e2', 'e1', 't-j1', 'all', true),    -- card a card
            ('e2', 'e1', 't-j2', null,  false),
            ('e3', 'e1', 't-f1', 'all', true),    -- setor que vê tudo
            ('e3', 'e2', 't-j1', null,  false),   -- sem cargo em U2
            ('e4', 'e1', 't-j1', 'all', false),   -- leitor: vê pelo setor, não exporta
            ('e5', 'e1', 't-f1', 'all', false),   -- grupo extra: só vê
            ('e5', 'e1', 't-j1', null,  false),
            ('e5', 'e2', 't-j1', 'all', false),   -- avulso: só vê
            ('e5', 'e2', 't-f1', null,  false),   -- grupo extra é de U1, não de U2
            ('e6', 'e1', 't-f1', 'all', true),    -- Gestor: tudo pelo cargo
            ('e6', 'e2', 't-f1', null,  false),
            ('e7', 'e2', 't-j2', 'all', true)     -- Desenvolvedor: até o desligado
        ) v(usr, unit, dash, scope, export)
    loop
        v_scope := app_private.dashboard_scope(('00000000-0000-4000-8000-0000000000' || c.usr)::uuid,
                                               ('20000000-0000-4000-8000-0000000000' || c.unit)::uuid, c.dash);
        v_export := app_private.dashboard_can_export(('00000000-0000-4000-8000-0000000000' || c.usr)::uuid,
                                                     ('20000000-0000-4000-8000-0000000000' || c.unit)::uuid, c.dash);
        if v_scope is distinct from c.scope or v_export is distinct from c.export then
            raise exception 'FALHOU: % em % / %: scope % (esperado %), exporta % (esperado %)',
                c.usr, c.unit, c.dash, v_scope, c.scope, v_export, c.export;
        end if;
    end loop;

    -- Card novo no Jurídico (sem group_slug, como as migrations de card) aparece sozinho para o grupo
    insert into app.dashboard_catalog (key, name, area, active, sort_order) values ('t-j3', 'Jur Três', 'Jurídico', true, 4);
    insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
    values ('10000000-0000-4000-8000-0000000000e1', '20000000-0000-4000-8000-0000000000e1', 't-j3', true);
    if app_private.dashboard_scope('00000000-0000-4000-8000-0000000000e1', '20000000-0000-4000-8000-0000000000e1', 't-j3')
       is distinct from 'all' then
        raise exception 'FALHOU: card novo do Jurídico não apareceu para o grupo do setor';
    end if;
    if app_private.dashboard_scope('00000000-0000-4000-8000-0000000000e2', '20000000-0000-4000-8000-0000000000e1', 't-j3')
       is not null then
        raise exception 'FALHOU: card novo apareceu para setor card a card';
    end if;

    -- Área que não é coluna do hub: recusada
    begin
        insert into app.dashboard_catalog (key, name, area, active, sort_order) values ('t-x', 'X', 'Nada', true, 5);
        raise exception 'FALHOU: card sem grupo foi aceito';
    exception when not_null_violation then null;
    end;
end $$;

set local role authenticated;

-- ---------- Gestor (g1): só U1 ----------
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000e6","role":"authenticated"}';
do $$
declare r jsonb; ok boolean;
begin
    r := api.access_overview('org-teste-grupos', 'U1');
    if jsonb_array_length(r -> 'groups') <> 6 or r -> 'groups' -> 0 ->> 'slug' <> 'comercial' then
        raise exception 'FALHOU: groups: %', r -> 'groups';
    end if;
    if not (r -> 'teams' @> '[{"name":"CTRL","sees_all":false,"groups":["juridico"]},{"name":"DIR","sees_all":true,"groups":[]}]') then
        raise exception 'FALHOU: teams: %', r -> 'teams';
    end if;
    if not (r -> 'dashboards' @> '[{"key":"t-j1","group":"juridico","teams":["CEL","CTRL","DIR"]},{"key":"t-f1","teams":["DIR"]}]') then
        raise exception 'FALHOU: grade com grupos: %', r -> 'dashboards';
    end if;
    if r -> 'group_of' ->> 't-f1' <> 'financeiro' then
        raise exception 'FALHOU: group_of: %', r -> 'group_of';
    end if;

    -- p1: Gestor de U1 troca o grupo extra de U1; a exceção de U2 (fora do escopo) fica
    r := api.update_member_access('org-teste-grupos', '40000000-0000-4000-8000-0000000000e5',
                                  '[{"code":"U1","role":"colaborador"}]', '{}', null,
                                  '[{"unit":"U1","slug":"comercial"}]', '[{"unit":"U1","key":"t-j2"}]');
    if r -> 'extra_groups' <> '[{"unit":"U1","slug":"comercial"}]'::jsonb
       or r -> 'extra_dashboards' <> '[{"unit":"U1","key":"t-j2"}]'::jsonb then
        raise exception 'FALHOU: exceções de p1 depois do Gestor: %', r;
    end if;
    -- (a exceção de U2 continua: conferido no fim, fora do papel authenticated)

    -- null = não muda as exceções
    r := api.update_member_access('org-teste-grupos', '40000000-0000-4000-8000-0000000000e5',
                                  '[{"code":"U1","role":"colaborador"}]', '{}', null);
    if r -> 'extra_groups' <> '[{"unit":"U1","slug":"comercial"}]'::jsonb then
        raise exception 'FALHOU: sem p_extra_groups deveria manter: %', r;
    end if;

    -- exceção em unidade que ele não gere
    ok := false;
    begin perform api.update_member_access('org-teste-grupos', '40000000-0000-4000-8000-0000000000e5',
                                           '[{"code":"U1","role":"colaborador"}]', '{}', null,
                                           '[{"unit":"U2","slug":"juridico"}]', null);
    exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: Gestor deu grupo extra em U2'; end if;

    -- grupo inválido; avulso que não existe na unidade
    ok := false;
    begin perform api.update_member_access('org-teste-grupos', '40000000-0000-4000-8000-0000000000e5',
                                           '[{"code":"U1","role":"colaborador"}]', '{}', null,
                                           '[{"unit":"U1","slug":"nada"}]', null);
    exception when sqlstate 'P0001' then ok := true; end;
    if not ok then raise exception 'FALHOU: grupo inválido aceito'; end if;
    ok := false;
    begin perform api.update_member_access('org-teste-grupos', '40000000-0000-4000-8000-0000000000e5',
                                           '[{"code":"U1","role":"colaborador"}]', '{}', null,
                                           null, '[{"unit":"U1","key":"nao-existe"}]');
    exception when sqlstate 'P0001' then ok := true; end;
    if not ok then raise exception 'FALHOU: avulso inexistente aceito'; end if;

    -- exceção sem cargo na unidade
    ok := false;
    begin perform api.update_member_access('org-teste-grupos', '40000000-0000-4000-8000-0000000000e5',
                                           '[]', '{}', null, '[{"unit":"U1","slug":"comercial"}]', null);
    exception when sqlstate 'P0001' then ok := true; end;
    if not ok then raise exception 'FALHOU: grupo extra sem cargo aceito'; end if;

    -- tirar o cargo de U1 tira as exceções de U1 (mesmo sem mandar as listas)
    r := api.update_member_access('org-teste-grupos', '40000000-0000-4000-8000-0000000000e5', '[]', '{}', null);
    if r -> 'extra_groups' <> '[]'::jsonb or r -> 'extra_dashboards' <> '[]'::jsonb then
        raise exception 'FALHOU: sem cargo, as exceções de U1 deveriam sair: %', r;
    end if;

    -- Grupos do setor: o Gestor muda os de U1
    r := api.set_team_groups('org-teste-grupos', '30000000-0000-4000-8000-0000000000e3', array['juridico', 'financeiro'], null);
    if r -> 'groups' <> '["financeiro","juridico"]'::jsonb or (r ->> 'sees_all')::boolean then
        raise exception 'FALHOU: set_team_groups: %', r;
    end if;

    ok := false;
    begin perform api.set_team_groups('org-teste-grupos', '30000000-0000-4000-8000-0000000000e4', array['juridico'], null);
    exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: Gestor mudou setor de U2'; end if;

    ok := false;
    begin perform api.set_team_groups('org-teste-grupos', '30000000-0000-4000-8000-0000000000e3', array['juridico'], true);
    exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: Gestor ligou "vê tudo"'; end if;

    ok := false;
    begin perform api.set_team_groups('org-teste-grupos', '30000000-0000-4000-8000-0000000000e3', array['nada'], null);
    exception when sqlstate 'P0001' then ok := true; end;
    if not ok then raise exception 'FALHOU: grupo inválido aceito no setor'; end if;
end $$;

-- ---------- Colaborador: não gere ----------
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000e1","role":"authenticated"}';
do $$
declare ok boolean := false;
begin
    begin perform api.set_team_groups('org-teste-grupos', '30000000-0000-4000-8000-0000000000e1', array['financeiro'], null);
    exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: Colaborador mudou grupos do setor'; end if;
    -- tabelas das exceções não são lidas direto
    ok := false;
    begin perform 1 from app.member_group_grants;
    exception when insufficient_privilege then ok := true; end;
    if not ok then raise exception 'FALHOU: authenticated leu member_group_grants'; end if;
end $$;

-- ---------- Desenvolvedor: liga "vê tudo" ----------
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000e7","role":"authenticated"}';
do $$
declare r jsonb;
begin
    r := api.set_team_groups('org-teste-grupos', '30000000-0000-4000-8000-0000000000e4', array[]::text[], true);
    if not (r ->> 'sees_all')::boolean or r -> 'groups' <> '[]'::jsonb then
        raise exception 'FALHOU: Desenvolvedor ligando vê tudo: %', r;
    end if;
end $$;

reset role;

do $$
begin
    if not exists (select 1 from app.member_dashboard_grants
                   where membership_id = '40000000-0000-4000-8000-0000000000e5'
                     and unit_id = '20000000-0000-4000-8000-0000000000e2' and dashboard_key = 't-j1') then
        raise exception 'FALHOU: Gestor de U1 apagou exceção de U2';
    end if;
    if not exists (select 1 from app.audit_log where action = 'team.access_updated'
                   and target_id = '30000000-0000-4000-8000-0000000000e3') then
        raise exception 'FALHOU: set_team_groups não auditou';
    end if;
    -- CTRL2 agora vê tudo: c1 vê f1 em U2
    if app_private.dashboard_scope('00000000-0000-4000-8000-0000000000e1', '20000000-0000-4000-8000-0000000000e2', 't-f1')
       is distinct from 'all' then
        raise exception 'FALHOU: setor que vê tudo não liberou f1';
    end if;
    raise notice 'OK: grupos de acesso';
end $$;

rollback;
