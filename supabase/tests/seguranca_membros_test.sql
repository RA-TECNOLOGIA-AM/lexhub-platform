-- =============================================================================
-- Teste de 20261113235950_seguranca_membros.sql. Roda numa transação e desfaz no fim (ROLLBACK): não deixa dados.
-- Passou = nenhum ERROR (só o aviso 'OK: ...'). Falhou = ERROR 'FALHOU: ...' (o CI para aí).
-- Uso: rodar depois da migration (CI, SQL Editor do staging ou psql).
--
-- Cenário: org 'org-teste-seguranca' com unidades U1 e U2.
--   d1 = Desenvolvedor · g1 = Gestor só em U1 · x1 = colaborador em U1 · c1 = Controller em U1 e U2
--   convites: cA em U1+U2, cB só em U1, cC de Desenvolvedor (sem unidade)
-- =============================================================================

begin;

insert into auth.users (id, email, raw_user_meta_data, raw_app_meta_data)
values ('00000000-0000-4000-8000-0000000000a1', 'd1.seg@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000a2', 'g1.seg@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000a3', 'x1.seg@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000a4', 'c1.seg@exemplo.com', '{}', '{}');

insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-0000000000a1', 'org-teste-seguranca', 'Org Teste Segurança');
insert into app.units (id, org_id, code, name)
values ('20000000-0000-4000-8000-0000000000a1', '10000000-0000-4000-8000-0000000000a1', 'U1', 'Unidade 1'),
       ('20000000-0000-4000-8000-0000000000a2', '10000000-0000-4000-8000-0000000000a1', 'U2', 'Unidade 2');

insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000000a1', '10000000-0000-4000-8000-0000000000a1',
        '00000000-0000-4000-8000-0000000000a1', 'Dev', 'd1.seg@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-0000000000a2', '10000000-0000-4000-8000-0000000000a1',
        '00000000-0000-4000-8000-0000000000a2', 'Gestor', 'g1.seg@exemplo.com', 'member', 'active'),
       ('40000000-0000-4000-8000-0000000000a3', '10000000-0000-4000-8000-0000000000a1',
        '00000000-0000-4000-8000-0000000000a3', 'Colab', 'x1.seg@exemplo.com', 'member', 'active'),
       ('40000000-0000-4000-8000-0000000000a4', '10000000-0000-4000-8000-0000000000a1',
        '00000000-0000-4000-8000-0000000000a4', 'Controller', 'c1.seg@exemplo.com', 'member', 'active');
insert into app.membership_units (org_id, unit_id, membership_id, role_key)
values ('10000000-0000-4000-8000-0000000000a1', '20000000-0000-4000-8000-0000000000a1',
        '40000000-0000-4000-8000-0000000000a4', 'controller'),
       ('10000000-0000-4000-8000-0000000000a1', '20000000-0000-4000-8000-0000000000a2',
        '40000000-0000-4000-8000-0000000000a4', 'controller');
insert into app.membership_units (org_id, unit_id, membership_id, role_key)
values ('10000000-0000-4000-8000-0000000000a1', '20000000-0000-4000-8000-0000000000a1',
        '40000000-0000-4000-8000-0000000000a2', 'gestor'),
       ('10000000-0000-4000-8000-0000000000a1', '20000000-0000-4000-8000-0000000000a1',
        '40000000-0000-4000-8000-0000000000a3', 'colaborador');

insert into app.invitations (id, org_id, email, role_key, unit_ids, token_hash, created_at, expires_at)
values ('50000000-0000-4000-8000-0000000000a1', '10000000-0000-4000-8000-0000000000a1', 'ca.seg@exemplo.com',
        'leitor', '{20000000-0000-4000-8000-0000000000a1,20000000-0000-4000-8000-0000000000a2}',
        'teste-seg-a', now(), now() + interval '7 days'),
       ('50000000-0000-4000-8000-0000000000a2', '10000000-0000-4000-8000-0000000000a1', 'cb.seg@exemplo.com',
        'leitor', '{20000000-0000-4000-8000-0000000000a1}', 'teste-seg-b', now(), now() + interval '7 days'),
       ('50000000-0000-4000-8000-0000000000a3', '10000000-0000-4000-8000-0000000000a1', 'cc.seg@exemplo.com',
        'admin', '{}', 'teste-seg-c', now(), now() + interval '7 days');

set local role authenticated;

-- ---------- Gestor (g1) ----------
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000a2","role":"authenticated","app_metadata":{}}';
do $$
declare ok boolean; r jsonb;
begin
    -- 1. não muda o próprio acesso (nem para Gestor numa unidade que já gere)
    ok := false;
    begin perform api.update_member_access('org-teste-seguranca', '40000000-0000-4000-8000-0000000000a2',
                                           '[{"code":"U1","role":"gestor"}]', '{}', null);
    exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: Gestor mudou o próprio acesso'; end if;

    -- mas segue mudando o acesso de quem ele gere
    r := api.update_member_access('org-teste-seguranca', '40000000-0000-4000-8000-0000000000a3',
                                  '[{"code":"U1","role":"leitor"}]', '{}', null);
    if r -> 'units' -> 0 ->> 'role' <> 'leitor' then raise exception 'FALHOU: Gestor deveria mudar o cargo de x1: %', r; end if;

    -- 2. funções internas não são chamáveis direto
    ok := false;
    begin perform app_private.member_json('40000000-0000-4000-8000-0000000000a1', '{}');
    exception when insufficient_privilege then ok := true; end;
    if not ok then raise exception 'FALHOU: member_json executável por authenticated'; end if;
    ok := false;
    begin perform app_private.members_scope('10000000-0000-4000-8000-0000000000a1');
    exception when insufficient_privilege then ok := true; end;
    if not ok then raise exception 'FALHOU: members_scope executável por authenticated'; end if;
    ok := false;
    begin perform app_private.require_members_scope('org-teste-seguranca');
    exception when insufficient_privilege then ok := true; end;
    if not ok then raise exception 'FALHOU: require_members_scope executável por authenticated'; end if;

    -- ...e as funções da api que as usam seguem funcionando
    r := api.list_members('org-teste-seguranca');
    if jsonb_array_length(r -> 'members') < 1 then raise exception 'FALHOU: list_members quebrou: %', r; end if;

    -- 3. convites: só o que está inteiro em U1
    ok := false;
    begin perform api.revoke_invitation('50000000-0000-4000-8000-0000000000a1');
    exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: Gestor cancelou convite que também vale para U2'; end if;

    ok := false;
    begin perform api.revoke_invitation('50000000-0000-4000-8000-0000000000a3');
    exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: Gestor cancelou convite de Desenvolvedor'; end if;

    -- can_revoke na lista segue a mesma regra (antes de cancelar cB)
    r := api.list_members('org-teste-seguranca');
    if jsonb_array_length(r -> 'invitations') <> 2 then raise exception 'FALHOU: Gestor deveria ver cA e cB: %', r; end if;
    if exists (select 1 from jsonb_array_elements(r -> 'invitations') i
               where (i ->> 'can_revoke')::boolean is distinct from (i ->> 'email' = 'cb.seg@exemplo.com')) then
        raise exception 'FALHOU: can_revoke do Gestor deveria ser true só em cB: %', r;
    end if;

    r := api.revoke_invitation('50000000-0000-4000-8000-0000000000a2');
    if r ->> 'revoked_at' is null then raise exception 'FALHOU: Gestor deveria cancelar convite só de U1: %', r; end if;
end $$;

-- ---------- Controller (c1): acompanha, não gere ----------
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000a4","role":"authenticated","app_metadata":{}}';
do $$
declare ok boolean; r jsonb;
begin
    r := api.my_admin_permissions('org-teste-seguranca');
    if (r ->> 'members')::boolean or (r ->> 'access')::boolean then
        raise exception 'FALHOU: Controller não deveria ver Membros nem Acesso no menu: %', r;
    end if;
    if not (r ->> 'sources')::boolean then raise exception 'FALHOU: Controller deveria ver fontes: %', r; end if;

    ok := false;
    begin perform api.list_members('org-teste-seguranca'); exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: Controller listou membros'; end if;

    ok := false;
    begin perform api.update_member_access('org-teste-seguranca', '40000000-0000-4000-8000-0000000000a3',
                                           '[{"code":"U1","role":"gestor"}]', '{}', null);
    exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: Controller mudou o acesso de alguém'; end if;
end $$;

-- Ver e exportar: conferido como dono do banco (as funções de escopo são internas)
reset role;
do $$
begin
    if app_private.dashboard_scope('00000000-0000-4000-8000-0000000000a4', '20000000-0000-4000-8000-0000000000a2', 'pendencias') <> 'all' then
        raise exception 'FALHOU: Controller deveria ver tudo de U2';
    end if;
    if not app_private.has_unit_permission('00000000-0000-4000-8000-0000000000a4', '20000000-0000-4000-8000-0000000000a2', 'dashboards.export') then
        raise exception 'FALHOU: Controller deveria exportar em U2';
    end if;
end $$;
set local role authenticated;

-- ---------- Desenvolvedor (d1) ----------
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000a1","role":"authenticated","app_metadata":{}}';
do $$
declare r jsonb;
begin
    r := api.revoke_invitation('50000000-0000-4000-8000-0000000000a1');
    if r ->> 'revoked_at' is null then raise exception 'FALHOU: Dev deveria cancelar convite de U1+U2: %', r; end if;
    r := api.revoke_invitation('50000000-0000-4000-8000-0000000000a3');
    if r ->> 'revoked_at' is null then raise exception 'FALHOU: Dev deveria cancelar convite de Desenvolvedor: %', r; end if;
end $$;

reset role;
do $$ begin raise notice 'OK: todos os casos passaram (o rollback abaixo desfaz tudo)'; end $$;

rollback;
