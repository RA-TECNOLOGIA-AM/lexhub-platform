-- =============================================================================
-- Teste de 20261125120000_convite_primeiro_acesso.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...').
-- Cenário: org 'org-teste-convite1' com unidades U1 e U2; d1 Desenvolvedor ativo; n1 convidado para U1.
--   n1 entra pelo Google: a sessão nasce ANTES da associação (o trigger de login não acha membro).
--   Ao aceitar o convite: "Entrou" e last_seen_at gravados, 'invitation.accepted' com units = ["U1"],
--   e os dois aparecem na Auditoria filtrada por U1 (e não por U2) — junto com um aceite antigo sem 'units'.
-- =============================================================================

begin;

insert into auth.users (id, email)
values ('00000000-0000-4000-8000-0000000c1001', 'dev.convite1@exemplo.com'),
       ('00000000-0000-4000-8000-0000000c1002', 'novo.convite1@exemplo.com');
insert into auth.identities (provider_id, user_id, identity_data, provider)
values ('google-teste-c1002', '00000000-0000-4000-8000-0000000c1002',
        '{"email":"novo.convite1@exemplo.com","email_verified":true}', 'google');
insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-0000000c1001', 'org-teste-convite1', 'Org Teste Convite');
insert into app.units (id, org_id, code, name)
values ('20000000-0000-4000-8000-0000000c1001', '10000000-0000-4000-8000-0000000c1001', 'U1', 'Unidade 1'),
       ('20000000-0000-4000-8000-0000000c1002', '10000000-0000-4000-8000-0000000c1001', 'U2', 'Unidade 2');
insert into app.memberships (id, org_id, user_id, full_name, email, role_key, status)
values ('40000000-0000-4000-8000-0000000c1001', '10000000-0000-4000-8000-0000000c1001',
        '00000000-0000-4000-8000-0000000c1001', 'Dev Convite', 'dev.convite1@exemplo.com', 'admin', 'active');
insert into app.invitations (org_id, email, role_key, unit_ids, token_hash, created_at, expires_at)
values ('10000000-0000-4000-8000-0000000c1001', 'novo.convite1@exemplo.com', 'colaborador',
        '{20000000-0000-4000-8000-0000000c1001}', 'teste-convite1', now(), now() + interval '7 days');
-- Um aceite antigo, gravado sem 'units' (antes desta migration): também tem que aparecer no filtro U1.
insert into app.invitations (id, org_id, email, role_key, unit_ids, token_hash, created_at, expires_at, accepted_at)
values ('60000000-0000-4000-8000-0000000c1001', '10000000-0000-4000-8000-0000000c1001', 'antigo.convite1@exemplo.com',
        'colaborador', '{20000000-0000-4000-8000-0000000c1001}', 'teste-convite1-antigo',
        now() - interval '2 days', now() + interval '5 days', now() - interval '1 day');
insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
values ('10000000-0000-4000-8000-0000000c1001', '00000000-0000-4000-8000-0000000c1001', 'invitation.accepted',
        'invitation', '60000000-0000-4000-8000-0000000c1001', '{"role":"colaborador"}');

-- O login: a sessão nasce antes de a pessoa ser membro (o trigger não grava nada).
insert into auth.sessions (id, user_id, created_at, updated_at, ip, user_agent)
values ('50000000-0000-4000-8000-0000000c1002', '00000000-0000-4000-8000-0000000c1002', now(), now(),
        '189.10.20.31', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36');

set local role authenticated;
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000c1002","role":"authenticated","email":"novo.convite1@exemplo.com","session_id":"50000000-0000-4000-8000-0000000c1002","user_metadata":{"full_name":"Pessoa Convite"}}';
do $$
begin
    if api.accept_my_invitations() <> 1 then raise exception 'FALHOU: deveria aceitar 1 convite'; end if;
    -- De novo (o front chama a cada login): nada novo, nem "Entrou" repetido.
    if api.accept_my_invitations() <> 0 then raise exception 'FALHOU: segundo aceite deveria ser 0'; end if;
end $$;

set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000c1001","role":"authenticated"}';
do $$
declare
    all_e jsonb := api.list_audit('org-teste-convite1') -> 'events';
    u1    jsonb := api.list_audit('org-teste-convite1', p_unit => 'U1') -> 'events';
    u2    jsonb := api.list_audit('org-teste-convite1', p_unit => 'U2') -> 'events';
    m     jsonb := (select x from jsonb_array_elements(api.list_members('org-teste-convite1') -> 'members') x
                    where x ->> 'email' = 'novo.convite1@exemplo.com');
begin
    if (select count(*) from jsonb_array_elements(all_e) x where x ->> 'action' = 'auth.login') <> 1 then
        raise exception 'FALHOU: deveria haver 1 "Entrou" (sessão do JWT): %', all_e;
    end if;
    if not exists (select 1 from jsonb_array_elements(all_e) x
                   where x ->> 'action' = 'auth.login' and x -> 'metadata' ->> 'ip' = '189.10.20.31') then
        raise exception 'FALHOU: "Entrou" sem o IP da sessão: %', all_e;
    end if;
    if not exists (select 1 from jsonb_array_elements(all_e) x
                   where x ->> 'action' = 'invitation.accepted' and x -> 'metadata' -> 'units' = '["U1"]') then
        raise exception 'FALHOU: aceite sem units = ["U1"]: %', all_e;
    end if;
    if (select count(*) from jsonb_array_elements(u1) x
        where x ->> 'action' in ('auth.login', 'invitation.accepted')) <> 3 then
        raise exception 'FALHOU: filtro U1 deveria trazer "Entrou", o aceite novo e o antigo: %', u1;
    end if;
    if jsonb_array_length(u2) <> 0 then raise exception 'FALHOU: filtro U2 deveria vir vazio: %', u2; end if;
    if m ->> 'last_seen_at' is null then raise exception 'FALHOU: último acesso vazio depois do aceite: %', m; end if;
    raise warning 'OK: primeiro acesso por convite grava "Entrou", último acesso e unidade do aceite';
end $$;

rollback;
