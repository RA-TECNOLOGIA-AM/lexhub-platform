-- =============================================================================
-- Teste de 20261119190000_dev_da_owner.sql. Roda numa transação e desfaz no fim (ROLLBACK): não deixa dados.
-- Passou = nenhum ERROR (só o aviso 'OK: ...'). Falhou = ERROR 'FALHOU: ...' (o CI para aí).
--
-- Cenário: org 'org-teste-dao' com a unidade U1.
--   o1 = Owner · d1 = Desenvolvedor · g1 = Gestor da U1 · m1, m2 = membros (leitor na U1)
-- =============================================================================

begin;

insert into auth.users (id, email, raw_user_meta_data, raw_app_meta_data)
values ('00000000-0000-4000-8000-0000000000e1', 'o1.dao@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000e2', 'd1.dao@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000e3', 'g1.dao@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000e4', 'm1.dao@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000e5', 'm2.dao@exemplo.com', '{}', '{}');

insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-0000000000e1', 'org-teste-dao', 'Org Teste Dev dá Owner');
insert into app.units (id, org_id, code, name)
values ('20000000-0000-4000-8000-0000000000e1', '10000000-0000-4000-8000-0000000000e1', 'U1', 'Unidade 1');

insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000000e1', '10000000-0000-4000-8000-0000000000e1',
        '00000000-0000-4000-8000-0000000000e1', 'Owner 1', 'o1.dao@exemplo.com', 'owner', 'active'),
       ('40000000-0000-4000-8000-0000000000e2', '10000000-0000-4000-8000-0000000000e1',
        '00000000-0000-4000-8000-0000000000e2', 'Dev 1', 'd1.dao@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-0000000000e3', '10000000-0000-4000-8000-0000000000e1',
        '00000000-0000-4000-8000-0000000000e3', 'Gestor 1', 'g1.dao@exemplo.com', 'member', 'active'),
       ('40000000-0000-4000-8000-0000000000e4', '10000000-0000-4000-8000-0000000000e1',
        '00000000-0000-4000-8000-0000000000e4', 'Membro 1', 'm1.dao@exemplo.com', 'member', 'active'),
       ('40000000-0000-4000-8000-0000000000e5', '10000000-0000-4000-8000-0000000000e1',
        '00000000-0000-4000-8000-0000000000e5', 'Membro 2', 'm2.dao@exemplo.com', 'member', 'active');
insert into app.membership_units (org_id, unit_id, membership_id, role_key)
values ('10000000-0000-4000-8000-0000000000e1', '20000000-0000-4000-8000-0000000000e1', '40000000-0000-4000-8000-0000000000e3', 'gestor'),
       ('10000000-0000-4000-8000-0000000000e1', '20000000-0000-4000-8000-0000000000e1', '40000000-0000-4000-8000-0000000000e4', 'leitor'),
       ('10000000-0000-4000-8000-0000000000e1', '20000000-0000-4000-8000-0000000000e1', '40000000-0000-4000-8000-0000000000e5', 'leitor');

set local role authenticated;

-- ---------- Gestor (g1): não dá Owner ----------
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000e3","role":"authenticated","app_metadata":{}}';
do $$
declare ok boolean := false;
begin
    begin perform api.update_member_access('org-teste-dao', '40000000-0000-4000-8000-0000000000e4',
                                           '[{"code":"U1","role":"leitor"}]', '{}', 'owner');
    exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: Gestor deu Owner'; end if;
end $$;

-- ---------- Desenvolvedor (d1): dá Owner a m1, não a si mesmo, e depois não desfaz ----------
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000e2","role":"authenticated","app_metadata":{}}';
do $$
declare ok boolean; r jsonb;
begin
    r := api.update_member_access('org-teste-dao', '40000000-0000-4000-8000-0000000000e4',
                                  '[{"code":"U1","role":"leitor"}]', '{}', 'owner');
    if r ->> 'org_role' <> 'owner' then raise exception 'FALHOU: Dev deveria dar Owner: %', r; end if;

    ok := false;
    begin perform api.update_member_access('org-teste-dao', '40000000-0000-4000-8000-0000000000e2',
                                           '[]', '{}', 'owner');
    exception when sqlstate 'P0001' then ok := true; end;
    if not ok then raise exception 'FALHOU: Dev se fez Owner'; end if;

    ok := false;
    begin perform api.update_member_access('org-teste-dao', '40000000-0000-4000-8000-0000000000e4',
                                           '[{"code":"U1","role":"leitor"}]', '{}', 'member');
    exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: Dev rebaixou o Owner que acabou de criar'; end if;

    ok := false;
    begin perform api.update_member_access('org-teste-dao', '40000000-0000-4000-8000-0000000000e5',
                                           '[{"code":"U1","role":"leitor"}]', '{}', 'superuser');
    exception when sqlstate 'P0001' then ok := true; end;
    if not ok then raise exception 'FALHOU: papel inválido passou'; end if;
end $$;

-- ---------- Owner (o1): também dá Owner ----------
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000e1","role":"authenticated","app_metadata":{}}';
do $$
declare r jsonb;
begin
    r := api.update_member_access('org-teste-dao', '40000000-0000-4000-8000-0000000000e5',
                                  '[{"code":"U1","role":"leitor"}]', '{}', 'owner');
    if r ->> 'org_role' <> 'owner' then raise exception 'FALHOU: Owner deveria dar Owner: %', r; end if;
end $$;

reset role;
do $$ begin
    if not exists (select 1 from app.audit_log
                   where target_id = '40000000-0000-4000-8000-0000000000e4' and action = 'member.access_updated'
                     and metadata -> 'after' ->> 'org_role' = 'owner') then
        raise exception 'FALHOU: auditoria não registrou o novo Owner';
    end if;
    raise notice 'OK: dev_da_owner';
end $$;

rollback;
