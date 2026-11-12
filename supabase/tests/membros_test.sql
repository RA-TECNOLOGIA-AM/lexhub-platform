-- =============================================================================
-- Teste de 20261113090000_membros.sql. Roda numa transação e desfaz no fim (ROLLBACK): não deixa dados.
-- Passou = nenhum ERROR (só o aviso 'OK: ...'). Falhou = ERROR 'FALHOU: ...' (o CI para aí).
-- Uso: rodar depois da migration (CI, SQL Editor do staging ou psql).
-- Simula usuários com set local role + request.jwt.claims (o que o PostgREST faz em cada chamada).
--
-- Cenário: org 'org-teste-membros' com unidades U1 e U2 e a equipe E1 (em U1).
--   o1 = Owner · d1 = Desenvolvedor (admin) · g1 = Gestor só em U1 · x1 = colaborador em U1 e U2
--   n1 = pessoa convidada (ainda não é membro)
-- =============================================================================

begin;

insert into auth.users (id, email, raw_user_meta_data, raw_app_meta_data)
values ('00000000-0000-4000-8000-0000000000b1', 'owner.membros@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000b2', 'dev.membros@exemplo.com', '{}', '{"providers":["google"]}'),
       ('00000000-0000-4000-8000-0000000000b3', 'gestor.membros@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000b4', 'colab.membros@exemplo.com', '{}', '{}'),
       ('00000000-0000-4000-8000-0000000000b5', 'novo.membros@exemplo.com', '{"full_name":"Pessoa Nova"}', '{}'),
       ('00000000-0000-4000-8000-0000000000b6', 'legado.membros@exemplo.com', '{}', '{}');

-- Identidade Google de n1, por enquanto com e-mail NÃO verificado (o user_metadata não vale: a pessoa edita)
insert into auth.identities (provider_id, user_id, identity_data, provider)
values ('google-teste-b5', '00000000-0000-4000-8000-0000000000b5',
        '{"email":"Novo.Membros@Exemplo.com","email_verified":false}', 'google');

insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-0000000000e1', 'org-teste-membros', 'Org Teste Membros');
insert into app.units (id, org_id, code, name)
values ('20000000-0000-4000-8000-0000000000e1', '10000000-0000-4000-8000-0000000000e1', 'U1', 'Unidade 1'),
       ('20000000-0000-4000-8000-0000000000e2', '10000000-0000-4000-8000-0000000000e1', 'U2', 'Unidade 2');
insert into app.teams (id, org_id, unit_id, name)
values ('30000000-0000-4000-8000-0000000000e1', '10000000-0000-4000-8000-0000000000e1',
        '20000000-0000-4000-8000-0000000000e1', 'E1');

insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000000b1', '10000000-0000-4000-8000-0000000000e1',
        '00000000-0000-4000-8000-0000000000b1', 'Owner Teste', 'owner.membros@exemplo.com', 'owner', 'active'),
       ('40000000-0000-4000-8000-0000000000b2', '10000000-0000-4000-8000-0000000000e1',
        '00000000-0000-4000-8000-0000000000b2', 'Dev Teste', 'dev.membros@exemplo.com', 'admin', 'active'),
       ('40000000-0000-4000-8000-0000000000b3', '10000000-0000-4000-8000-0000000000e1',
        '00000000-0000-4000-8000-0000000000b3', 'Gestor Teste', 'gestor.membros@exemplo.com', 'member', 'active'),
       ('40000000-0000-4000-8000-0000000000b4', '10000000-0000-4000-8000-0000000000e1',
        '00000000-0000-4000-8000-0000000000b4', 'Colab Teste', 'colab.membros@exemplo.com', 'member', 'active'),
       ('40000000-0000-4000-8000-0000000000b6', '10000000-0000-4000-8000-0000000000e1',
        '00000000-0000-4000-8000-0000000000b6', 'Legado Teste', 'legado.membros@exemplo.com', 'member', 'invited');
insert into app.membership_units (org_id, unit_id, membership_id, role_key)
values ('10000000-0000-4000-8000-0000000000e1', '20000000-0000-4000-8000-0000000000e1',
        '40000000-0000-4000-8000-0000000000b3', 'gestor'),
       ('10000000-0000-4000-8000-0000000000e1', '20000000-0000-4000-8000-0000000000e1',
        '40000000-0000-4000-8000-0000000000b4', 'colaborador'),
       ('10000000-0000-4000-8000-0000000000e1', '20000000-0000-4000-8000-0000000000e2',
        '40000000-0000-4000-8000-0000000000b4', 'colaborador'),
       ('10000000-0000-4000-8000-0000000000e1', '20000000-0000-4000-8000-0000000000e1',
        '40000000-0000-4000-8000-0000000000b6', 'leitor');

create temp table t_ids (k text primary key, v uuid) on commit drop;
grant all on t_ids to authenticated;

-- Convites que não podem ser aceitos: um revogado e um vencido (direto na tabela, como dono do banco)
insert into app.invitations (org_id, email, role_key, unit_ids, token_hash, created_at, expires_at, revoked_at)
values ('10000000-0000-4000-8000-0000000000e1', 'novo.membros@exemplo.com', 'leitor',
        '{20000000-0000-4000-8000-0000000000e2}', 'teste-revogado', now(), now() + interval '7 days', now()),
       ('10000000-0000-4000-8000-0000000000e1', 'velho.membros@exemplo.com', 'leitor',
        '{20000000-0000-4000-8000-0000000000e2}', 'teste-vencido', now() - interval '10 days', now() - interval '3 days', null);

set local role authenticated;

-- ---------- Desenvolvedor (d1) ----------
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000b2","role":"authenticated"}';
do $$
declare r jsonb;
begin
    r := api.list_members('org-teste-membros');
    if jsonb_array_length(r -> 'members') <> 5 then raise exception 'FALHOU: Dev deveria ver 5 membros: %', r; end if;
    if (r ->> 'can_invite_admin')::boolean is not true then raise exception 'FALHOU: Dev pode convidar Desenvolvedor'; end if;
    if jsonb_array_length(r -> 'units') <> 2 then raise exception 'FALHOU: Dev gere as 2 unidades'; end if;
    if jsonb_array_length(r -> 'invitations') <> 0 then raise exception 'FALHOU: convite revogado/vencido apareceu'; end if;
    if not exists (select 1 from jsonb_array_elements(r -> 'members') m
                   where m ->> 'email' = 'dev.membros@exemplo.com' and m ->> 'security' = 'Google'
                     and m ->> 'org_role' = 'admin') then
        raise exception 'FALHOU: Dev deveria aparecer como admin e Google: %', r;
    end if;
end $$;

-- Slug inexistente: mesmo erro de sem permissão (não revela se a org existe)
do $$
declare ok boolean := false;
begin
    begin perform api.list_members('nao-existe-org'); exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: slug inexistente deveria dar 42501'; end if;
end $$;

-- ---------- Gestor (g1): só U1 ----------
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000b3","role":"authenticated"}';
do $$
declare r jsonb; x jsonb; ok boolean;
begin
    r := api.list_members('org-teste-membros');
    if (r ->> 'can_invite_admin')::boolean then raise exception 'FALHOU: Gestor não convida Desenvolvedor'; end if;
    if jsonb_array_length(r -> 'units') <> 1 or r -> 'units' -> 0 ->> 'code' <> 'U1' then
        raise exception 'FALHOU: Gestor gere só U1: %', r -> 'units';
    end if;
    select m into x from jsonb_array_elements(r -> 'members') m where m ->> 'email' = 'colab.membros@exemplo.com';
    if x is null or jsonb_array_length(x -> 'units') <> 1 or x -> 'units' -> 0 ->> 'code' <> 'U1' then
        raise exception 'FALHOU: Gestor deveria ver o colaborador só com U1: %', x;
    end if;
    if exists (select 1 from jsonb_array_elements(r -> 'members') m where m ->> 'email' = 'dev.membros@exemplo.com') then
        raise exception 'FALHOU: Gestor não deveria ver o Dev (sem unidade no escopo)';
    end if;

    ok := false;
    begin perform api.invite_members('org-teste-membros', array['a@exemplo.com'], 'leitor', array['U2'], '{}');
    exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: Gestor convidou para unidade alheia'; end if;

    ok := false;
    begin perform api.invite_members('org-teste-membros', array['a@exemplo.com'], 'admin', '{}', '{}');
    exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: Gestor convidou Desenvolvedor'; end if;

    ok := false;
    begin perform api.invite_members('org-teste-membros', array['a@exemplo.com'], 'owner', array['U1'], '{}');
    exception when sqlstate 'P0001' then ok := true; end;
    if not ok then raise exception 'FALHOU: convite de owner deveria ser recusado'; end if;

    ok := false;
    begin perform api.invite_members('org-teste-membros', array['a@exemplo.com'], 'leitor', '{}', '{}');
    exception when sqlstate 'P0001' then ok := true; end;
    if not ok then raise exception 'FALHOU: cargo de unidade sem unidade'; end if;

    r := api.invite_members('org-teste-membros', array['  Novo.Membros@Exemplo.com ', 'novo.membros@exemplo.com'],
                            'colaborador', array['U1'], array['30000000-0000-4000-8000-0000000000e1'::uuid]);
    if r -> 'invited' <> '["novo.membros@exemplo.com"]'::jsonb then raise exception 'FALHOU: convite: %', r; end if;

    r := api.invite_members('org-teste-membros', array['novo.membros@exemplo.com', 'colab.membros@exemplo.com'],
                            'leitor', array['U1'], '{}');
    if jsonb_array_length(r -> 'invited') <> 0
       or not (r -> 'skipped' @> '[{"email":"novo.membros@exemplo.com","reason":"Já tem convite pendente"}]')
       or not (r -> 'skipped' @> '[{"email":"colab.membros@exemplo.com","reason":"Já faz parte da organização"}]') then
        raise exception 'FALHOU: pulados: %', r;
    end if;

    r := api.list_members('org-teste-membros');
    if jsonb_array_length(r -> 'invitations') <> 1 or r -> 'invitations' -> 0 ->> 'invited_by' <> 'Gestor Teste'
       or r -> 'invitations' -> 0 -> 'teams' <> '["E1"]'::jsonb then
        raise exception 'FALHOU: convite pendente na lista: %', r -> 'invitations';
    end if;
    insert into t_ids values ('inv', (r -> 'invitations' -> 0 ->> 'id')::uuid);

    ok := false;
    begin perform api.set_member_status('org-teste-membros', '40000000-0000-4000-8000-0000000000b2', 'disabled');
    exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: Gestor desativou o Dev'; end if;

    -- x1 está em U1 e U2; o Gestor só gere U1: desativar cortaria o acesso dele em U2 também
    ok := false;
    begin perform api.set_member_status('org-teste-membros', '40000000-0000-4000-8000-0000000000b4', 'disabled');
    exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: Gestor desativou quem também está em unidade que ele não gere'; end if;
end $$;

-- ---------- Colaborador (x1): não gere ----------
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000b4","role":"authenticated"}';
do $$
declare ok boolean := false;
begin
    begin perform api.list_members('org-teste-membros'); exception when sqlstate '42501' then ok := true; end;
    if not ok then raise exception 'FALHOU: colaborador abriu a lista'; end if;
end $$;

-- ---------- Convidado (n1): aceite ----------
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000b5","role":"authenticated","email":"NOVO.Membros@Exemplo.com","user_metadata":{"email_verified":false,"full_name":"Pessoa Nova"}}';
do $$
begin
    if api.accept_my_invitations() <> 0 then raise exception 'FALHOU: aceitou com e-mail não verificado'; end if;
end $$;

set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000b5","role":"authenticated","email":"NOVO.Membros@Exemplo.com","user_metadata":{"email_verified":true,"full_name":"Pessoa Nova"}}';
do $$
begin
    if api.accept_my_invitations() <> 0 then
        raise exception 'FALHOU: aceitou só porque o user_metadata (editável pela pessoa) diz verificado';
    end if;
end $$;

-- O Google confirma o e-mail (identidade verificada)
reset role;
update auth.identities set identity_data = '{"email":"Novo.Membros@Exemplo.com","email_verified":true}'
 where provider_id = 'google-teste-b5';
set local role authenticated;
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000b5","role":"authenticated","email":"NOVO.Membros@Exemplo.com","user_metadata":{"full_name":"Pessoa Nova"}}';
do $$
declare n int;
begin
    n := api.accept_my_invitations();
    if n <> 1 then raise exception 'FALHOU: deveria aceitar 1 convite (o revogado não), aceitou %', n; end if;
    if api.accept_my_invitations() <> 0 then raise exception 'FALHOU: aceitou duas vezes'; end if;
end $$;

-- ---------- Desenvolvedor: situação ----------
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000b2","role":"authenticated"}';
do $$
declare r jsonb; ok boolean;
begin
    r := api.set_member_status('org-teste-membros', '40000000-0000-4000-8000-0000000000b4', 'disabled');
    if r ->> 'status' <> 'disabled' then raise exception 'FALHOU: desativar: %', r; end if;

    r := api.invite_members('org-teste-membros', array['colab.membros@exemplo.com'], 'leitor', array['U1'], '{}');
    if not (r -> 'skipped' @> '[{"email":"colab.membros@exemplo.com","reason":"Desativado: reative na lista"}]') then
        raise exception 'FALHOU: convite para desativado: %', r;
    end if;

    ok := false;
    begin perform api.set_member_status('org-teste-membros', '40000000-0000-4000-8000-0000000000b2', 'disabled');
    exception when sqlstate 'P0001' then ok := true; end;
    if not ok then raise exception 'FALHOU: desativou a si mesmo'; end if;

    r := api.set_member_status('org-teste-membros', '40000000-0000-4000-8000-0000000000b4', 'active');
    if r ->> 'status' <> 'active' then raise exception 'FALHOU: reativar: %', r; end if;

    -- associação 'invited' (legado) só vira ativa pelo aceite no login, não por aqui
    ok := false;
    begin perform api.set_member_status('org-teste-membros', '40000000-0000-4000-8000-0000000000b6', 'active');
    exception when sqlstate 'P0001' then ok := true; end;
    if not ok then raise exception 'FALHOU: set_member_status ativou uma associação invited'; end if;

    -- convite novo e cancelado
    r := api.invite_members('org-teste-membros', array['outro.membros@exemplo.com'], 'admin', '{}', '{}');
    if r -> 'invited' <> '["outro.membros@exemplo.com"]'::jsonb then raise exception 'FALHOU: convite admin: %', r; end if;
    r := api.list_members('org-teste-membros');
    perform api.revoke_invitation((select (i ->> 'id')::uuid from jsonb_array_elements(r -> 'invitations') i
                                   where i ->> 'email' = 'outro.membros@exemplo.com'));
    r := api.list_members('org-teste-membros');
    if exists (select 1 from jsonb_array_elements(r -> 'invitations') i where i ->> 'email' = 'outro.membros@exemplo.com') then
        raise exception 'FALHOU: convite cancelado ainda aparece';
    end if;

    ok := false;
    begin perform api.revoke_invitation((select v from t_ids where k = 'inv'));
    exception when sqlstate 'P0001' then ok := true; end;
    if not ok then raise exception 'FALHOU: cancelou convite já aceito'; end if;
end $$;

-- ---------- conferências como dono do banco ----------
reset role;
do $$
declare v_m uuid;
begin
    select id into v_m from app.memberships
     where org_id = '10000000-0000-4000-8000-0000000000e1' and user_id = '00000000-0000-4000-8000-0000000000b5'
       and status = 'active' and role_key = 'member' and full_name = 'Pessoa Nova';
    if v_m is null then raise exception 'FALHOU: associação do convidado não foi criada'; end if;
    if not exists (select 1 from app.membership_units where membership_id = v_m
                   and unit_id = '20000000-0000-4000-8000-0000000000e1' and role_key = 'colaborador') then
        raise exception 'FALHOU: cargo do convidado';
    end if;
    if (select count(*) from app.membership_units where membership_id = v_m) <> 1 then
        raise exception 'FALHOU: o convite revogado (U2) foi aplicado';
    end if;
    if not exists (select 1 from app.membership_teams where membership_id = v_m
                   and team_id = '30000000-0000-4000-8000-0000000000e1') then
        raise exception 'FALHOU: equipe do convidado';
    end if;
    if (select accepted_at from app.invitations where token_hash = 'teste-vencido') is not null then
        raise exception 'FALHOU: convite vencido foi aceito';
    end if;
    if (select count(distinct action) from app.audit_log
         where org_id = '10000000-0000-4000-8000-0000000000e1'
           and action in ('member.invited', 'invitation.accepted', 'member.disabled', 'member.enabled',
                          'invitation.revoked')) <> 5 then
        raise exception 'FALHOU: auditoria incompleta';
    end if;
    raise notice 'OK: todos os casos passaram (o rollback abaixo desfaz tudo)';
end $$;

rollback;
