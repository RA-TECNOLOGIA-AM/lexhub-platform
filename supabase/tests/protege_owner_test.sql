-- =============================================================================
-- Teste de 20261113235900_protege_owner.sql. Roda numa transação e desfaz no fim (ROLLBACK): não deixa dados.
-- Passou = nenhum ERROR (só o aviso 'OK: ...'). Falhou = ERROR 'FALHOU: ...' (o CI para aí).
-- Uso: rodar depois da migration (CI, SQL Editor do staging ou psql).
--
-- Cenário: org 'org-teste-owner' com a unidade U1.
--   o1, o2 = Owners · d1, d2 = Desenvolvedores · rs = equipe RA (platform_staff, Desenvolvedor)
-- =============================================================================

begin;

insert into auth.users (id, email, raw_user_meta_data, raw_app_meta_data)
values ('00000000-0000-4000-8000-0000000000f1', 'o1.owner@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000f2', 'o2.owner@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000f3', 'd1.owner@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000f4', 'd2.owner@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000f5', 'rs.owner@exemplo.com', '{}', '{"platform_staff":true}');

insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-0000000000f1', 'org-teste-owner', 'Org Teste Owner');
insert into app.units (id, org_id, code, name)
values ('20000000-0000-4000-8000-0000000000f1', '10000000-0000-4000-8000-0000000000f1', 'U1', 'Unidade 1');

insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000000f1', '10000000-0000-4000-8000-0000000000f1',
        '00000000-0000-4000-8000-0000000000f1', 'Owner 1', 'o1.owner@exemplo.com', 'owner', 'active'),
       ('40000000-0000-4000-8000-0000000000f2', '10000000-0000-4000-8000-0000000000f1',
        '00000000-0000-4000-8000-0000000000f2', 'Owner 2', 'o2.owner@exemplo.com', 'owner', 'active'),
       ('40000000-0000-4000-8000-0000000000f3', '10000000-0000-4000-8000-0000000000f1',
        '00000000-0000-4000-8000-0000000000f3', 'Dev 1', 'd1.owner@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-0000000000f4', '10000000-0000-4000-8000-0000000000f1',
        '00000000-0000-4000-8000-0000000000f4', 'Dev 2', 'd2.owner@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-0000000000f5', '10000000-0000-4000-8000-0000000000f1',
        '00000000-0000-4000-8000-0000000000f5', 'Equipe RA', 'rs.owner@exemplo.com', 'admin', 'active');

set local role authenticated;

-- ---------- Desenvolvedor (d1): não mexe em Owner, mexe em outro Dev ----------
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000f3","role":"authenticated","app_metadata":{}}';
do $$
declare ok boolean; r jsonb;
begin
    ok := false;
    begin perform api.set_member_status('org-teste-owner', '40000000-0000-4000-8000-0000000000f1', 'disabled');
    exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: Dev desativou o Owner'; end if;

    ok := false;
    begin perform api.update_member_access('org-teste-owner', '40000000-0000-4000-8000-0000000000f1',
                                           '[{"code":"U1","role":"leitor"}]', '{}', null);
    exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: Dev mudou o cargo do Owner'; end if;

    r := api.set_member_status('org-teste-owner', '40000000-0000-4000-8000-0000000000f4', 'disabled');
    if r ->> 'status' <> 'disabled' then raise exception 'FALHOU: Dev deveria desativar outro Dev: %', r; end if;
    r := api.set_member_status('org-teste-owner', '40000000-0000-4000-8000-0000000000f4', 'active');
    if r ->> 'status' <> 'active' then raise exception 'FALHOU: Dev deveria reativar outro Dev: %', r; end if;
end $$;

-- ---------- Owner (o1): mexe em outro Owner, mas não deixa a org sem Owner ----------
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000f1","role":"authenticated","app_metadata":{}}';
do $$
declare ok boolean; r jsonb;
begin
    r := api.update_member_access('org-teste-owner', '40000000-0000-4000-8000-0000000000f2',
                                  '[{"code":"U1","role":"leitor"}]', '{}', null);
    if jsonb_array_length(r -> 'units') <> 1 then raise exception 'FALHOU: Owner deveria mudar o cargo de outro Owner: %', r; end if;

    r := api.set_member_status('org-teste-owner', '40000000-0000-4000-8000-0000000000f2', 'disabled');
    if r ->> 'status' <> 'disabled' then raise exception 'FALHOU: Owner deveria desativar outro Owner: %', r; end if;
end $$;

-- o2 desativado; o1 é o único Owner ativo. Equipe RA tenta desativá-lo: barra pela trava do último Owner.
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000f5","role":"authenticated","app_metadata":{"platform_staff":true}}';
do $$
declare ok boolean; r jsonb;
begin
    ok := false;
    begin perform api.set_member_status('org-teste-owner', '40000000-0000-4000-8000-0000000000f1', 'disabled');
    exception when sqlstate 'P0001' then ok := true; end;
    if not ok then raise exception 'FALHOU: desativou o último Owner ativo'; end if;

    -- a equipe RA pode reativar um Owner
    r := api.set_member_status('org-teste-owner', '40000000-0000-4000-8000-0000000000f2', 'active');
    if r ->> 'status' <> 'active' then raise exception 'FALHOU: equipe RA deveria reativar o Owner: %', r; end if;
end $$;

-- ---------- conferências como dono do banco ----------
reset role;
do $$
begin
    if exists (select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace
               where n.nspname = 'app_private' and p.proname = 'can_manage_owners'
                 and has_function_privilege('authenticated', p.oid, 'execute')) then
        raise exception 'FALHOU: app_private.can_manage_owners não deveria ser executável por authenticated';
    end if;
    if (select status from app.memberships where id = '40000000-0000-4000-8000-0000000000f1') <> 'active' then
        raise exception 'FALHOU: o1 deveria seguir ativo';
    end if;
    raise notice 'OK: todos os casos passaram (o rollback abaixo desfaz tudo)';
end $$;

rollback;
