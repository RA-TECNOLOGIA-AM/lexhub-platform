-- =============================================================================
-- Notificações: o sino da topbar.
--
--   app.notifications            uma notificação por pessoa; cada um lê só as próprias; ninguém grava direto
--   gatilho em access_requests   pedido aprovado -> "Seu acesso foi aprovado" para quem pediu
--   api.list_my_notifications    as últimas da pessoa + quantas não lidas (o número do sino)
--   api.mark_notifications_read  marca como lidas (ids escolhidos ou todas)
--
-- Pedidos de acesso pendentes NÃO viram linha aqui: o sino da equipe RA soma o número que já existe
-- (api.count_pending_access_requests), que some sozinho quando alguém decide.
-- Evento novo = um tipo novo em `kind` + quem insere (gatilho ou função do próprio fluxo).
-- Teste: supabase/tests/notificacoes_test.sql (termina com rollback).
-- =============================================================================

create table app.notifications (
    id         uuid primary key default gen_random_uuid(),
    user_id    uuid not null references auth.users (id) on delete cascade,
    org_id     uuid references app.organizations (id) on delete cascade,
    kind       text not null check (kind in ('access_request.approved')),
    title      text not null check (length(title) between 1 and 120),
    body       text check (body is null or length(body) <= 300),
    link       text check (link is null or link like '/%'), -- caminho dentro do app
    created_at timestamptz not null default now(),
    read_at    timestamptz
);
create index notifications_user_created_idx on app.notifications (user_id, created_at desc);
create index notifications_unread_idx on app.notifications (user_id) where read_at is null;

-- Ler direto só as próprias (RLS); gravar só pelas funções abaixo ou pelo service_role (ex.: worker).
grant select on app.notifications to authenticated;
grant all on app.notifications to service_role;

alter table app.notifications enable row level security;
create policy notifications_select_own on app.notifications for select to authenticated
    using (user_id = (select auth.uid()));

-- ---------------------------------------------------------------------------
-- Pedido aprovado -> avisa quem pediu (entra junto na transação da aprovação).
-- ---------------------------------------------------------------------------
create function app_private.notify_access_request_decided() returns trigger
language plpgsql security definer
set search_path = ''
as $$
declare
    v_org app.organizations;
begin
    if new.status = 'approved' and old.status = 'pending' then
        select * into v_org from app.organizations o where o.id = new.result_org_id;
        insert into app.notifications (user_id, org_id, kind, title, body, link)
        values (
            new.user_id,
            v_org.id,
            'access_request.approved',
            'Seu acesso foi aprovado',
            case when v_org.id is null then 'Você já pode usar o LexHub.'
                 else 'Você agora faz parte de ' || v_org.name || '.' end,
            case when v_org.id is null then null else '/' || v_org.slug || '/dashboards' end
        );
    end if;
    return new;
end;
$$;
revoke all on function app_private.notify_access_request_decided() from public, anon, authenticated;

create trigger access_requests_notify_decided
    after update of status on app.access_requests
    for each row execute function app_private.notify_access_request_decided();

-- ---------------------------------------------------------------------------
-- Schema api
-- ---------------------------------------------------------------------------
-- As últimas notificações de quem chama (mais recentes primeiro; até 50, padrão 20) e o total não lido.
create function api.list_my_notifications(p_limit integer default 20) returns jsonb
language sql stable security definer
set search_path = ''
as $$
    select jsonb_build_object(
        'items', coalesce((
            select jsonb_agg(jsonb_build_object(
                       'id', n.id, 'kind', n.kind, 'title', n.title, 'body', n.body, 'link', n.link,
                       'created_at', n.created_at, 'read_at', n.read_at)
                   order by n.created_at desc, n.id desc)
            from (
                select * from app.notifications
                where user_id = auth.uid()
                order by created_at desc, id desc
                limit greatest(1, least(coalesce(p_limit, 20), 50))
            ) n
        ), '[]'::jsonb),
        'unread', (select count(*)::int from app.notifications where user_id = auth.uid() and read_at is null)
    );
$$;

-- Marca como lidas as notificações de quem chama. p_ids null = todas. Devolve quantas mudaram.
-- Id de outra pessoa é ignorado (o where filtra por auth.uid()).
create function api.mark_notifications_read(p_ids uuid[] default null) returns integer
language plpgsql security definer
set search_path = ''
as $$
declare
    v_count integer;
begin
    if auth.uid() is null then
        raise exception using errcode = '42501', message = 'Entre para ver as notificações.';
    end if;
    update app.notifications
       set read_at = now()
     where user_id = auth.uid()
       and read_at is null
       and (p_ids is null or id = any (p_ids));
    get diagnostics v_count = row_count;
    return v_count;
end;
$$;

revoke all on function api.list_my_notifications(integer) from public, anon;
revoke all on function api.mark_notifications_read(uuid[]) from public, anon;
grant execute on function api.list_my_notifications(integer) to authenticated;
grant execute on function api.mark_notifications_read(uuid[]) to authenticated;

-- =============================================================================
-- Rollback:
-- drop function api.mark_notifications_read(uuid[]);
-- drop function api.list_my_notifications(integer);
-- drop trigger access_requests_notify_decided on app.access_requests;
-- drop function app_private.notify_access_request_decided();
-- drop table app.notifications;
-- =============================================================================
