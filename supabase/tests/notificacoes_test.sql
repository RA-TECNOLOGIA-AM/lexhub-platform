-- =============================================================================
-- Teste de 20261113235000_notificacoes.sql. Roda numa transação e desfaz no fim (ROLLBACK).
-- Passou = nenhum ERROR (só o aviso 'OK: ...').
-- Cenário: p1 e p2 pediram acesso; s1 é da equipe RA. s1 aprova p1 (org existente) e recusa p2.
--   p1 recebe "Seu acesso foi aprovado" com link da org; p2 e s1 não recebem nada.
-- =============================================================================

begin;

insert into auth.users (id, email)
values ('00000000-0000-4000-8000-0000000000b1', 'p1.notif@exemplo.com'),
       ('00000000-0000-4000-8000-0000000000b2', 'p2.notif@exemplo.com'),
       ('00000000-0000-4000-8000-0000000000b3', 'staff.notif@exemplo.com');
insert into app.organizations (id, slug, name)
values ('10000000-0000-4000-8000-0000000000b1', 'org-teste-notif', 'Org Teste Notif');
insert into app.access_requests (id, user_id, email, full_name, office)
values ('50000000-0000-4000-8000-0000000000b1', '00000000-0000-4000-8000-0000000000b1',
        'p1.notif@exemplo.com', 'Pessoa Um', 'Escritório Um'),
       ('50000000-0000-4000-8000-0000000000b2', '00000000-0000-4000-8000-0000000000b2',
        'p2.notif@exemplo.com', 'Pessoa Dois', 'Escritório Dois');

set local role authenticated;

-- Equipe RA decide
set local request.jwt.claims =
    '{"sub":"00000000-0000-4000-8000-0000000000b3","role":"authenticated","app_metadata":{"platform_staff":true}}';
select api.approve_access_request('50000000-0000-4000-8000-0000000000b1',
    '{"kind":"existing","org_id":"10000000-0000-4000-8000-0000000000b1","org_role":"admin"}');
select api.reject_access_request('50000000-0000-4000-8000-0000000000b2', null);
do $$
begin
    if (api.list_my_notifications() ->> 'unread')::int <> 0 then
        raise exception 'FALHOU: quem aprovou não deveria receber notificação';
    end if;
end $$;

-- p1: uma notificação não lida, com link para a org
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000b1","role":"authenticated"}';
do $$
declare r jsonb := api.list_my_notifications();
begin
    if (r ->> 'unread')::int <> 1 or jsonb_array_length(r -> 'items') <> 1 then
        raise exception 'FALHOU: p1 deveria ter 1 notificação não lida: %', r;
    end if;
    if r -> 'items' -> 0 ->> 'kind' <> 'access_request.approved'
       or r -> 'items' -> 0 ->> 'link' <> '/org-teste-notif/dashboards'
       or r -> 'items' -> 0 ->> 'body' not like '%Org Teste Notif%' then
        raise exception 'FALHOU: conteúdo: %', r -> 'items' -> 0;
    end if;
    -- Leitura direta: a RLS mostra só as próprias; gravar direto é proibido
    if (select count(*) from app.notifications) <> 1 then raise exception 'FALHOU: RLS de leitura'; end if;
    begin
        update app.notifications set read_at = now();
        raise exception 'FALHOU: não deveria gravar direto';
    exception when insufficient_privilege then null;
    end;
    if api.mark_notifications_read() <> 1 then raise exception 'FALHOU: marcar todas como lidas'; end if;
    if (api.list_my_notifications() ->> 'unread')::int <> 0 then raise exception 'FALHOU: ainda não lida'; end if;
    if api.mark_notifications_read() <> 0 then raise exception 'FALHOU: marcar de novo não muda nada'; end if;
end $$;

-- p2 (recusado): nada; e não consegue marcar a de p1
set local request.jwt.claims = '{"sub":"00000000-0000-4000-8000-0000000000b2","role":"authenticated"}';
do $$
declare v_id uuid;
begin
    if jsonb_array_length(api.list_my_notifications() -> 'items') <> 0 then
        raise exception 'FALHOU: recusado não recebe notificação';
    end if;
    reset role;
    update app.notifications set read_at = null;
    select id into v_id from app.notifications limit 1;
    set local role authenticated;
    if api.mark_notifications_read(array[v_id]) <> 0 then
        raise exception 'FALHOU: marcou notificação de outra pessoa';
    end if;
    raise notice 'OK: todos os casos passaram (o rollback abaixo desfaz tudo)';
end $$;

rollback;
