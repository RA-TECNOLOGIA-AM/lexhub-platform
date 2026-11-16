-- Login de dispositivos: códigos curtos aprovados por uma sessão autenticada.
-- A tabela e as funções são acessíveis diretamente apenas ao backend service_role.

create table api.device_auth_sessions (
    id             uuid primary key default gen_random_uuid(),
    device_code    text not null,
    user_code      text not null,
    status         text not null default 'pending'
                   check (status in ('pending', 'approved', 'expired')),
    user_id        uuid references auth.users (id) on delete cascade,
    expires_at     timestamptz not null,
    created_at     timestamptz not null default now(),
    last_polled_at timestamptz,
    claim_id       uuid,
    claimed_at     timestamptz,
    check ((claim_id is null) = (claimed_at is null))
);

create unique index device_auth_sessions_device_code_uq
    on api.device_auth_sessions (device_code);
create unique index device_auth_sessions_user_code_uq
    on api.device_auth_sessions (user_code);
create index device_auth_sessions_expires_at_idx
    on api.device_auth_sessions (expires_at);

alter table api.device_auth_sessions enable row level security;
revoke all on api.device_auth_sessions from public, anon, authenticated;
grant select, insert, update, delete on api.device_auth_sessions to service_role;

create table api.device_auth_rate_limits (
    bucket_key        text primary key,
    window_started_at timestamptz not null,
    attempts          integer not null check (attempts > 0)
);

create index device_auth_rate_limits_window_idx
    on api.device_auth_rate_limits (window_started_at);

alter table api.device_auth_rate_limits enable row level security;
revoke all on api.device_auth_rate_limits from public, anon, authenticated;
grant select, insert, update, delete on api.device_auth_rate_limits to service_role;

create function api.consume_device_auth_rate_limit(
    p_bucket_key text,
    p_limit integer,
    p_window_seconds integer
) returns boolean
language plpgsql
security invoker
set search_path = ''
as $$
declare
    v_now      timestamptz := clock_timestamp();
    v_attempts integer;
begin
    if length(p_bucket_key) <> 64
       or p_limit not between 1 and 1000
       or p_window_seconds not between 1 and 3600 then
        raise exception using errcode = '22023', message = 'Parâmetros de limite inválidos.';
    end if;

    insert into api.device_auth_rate_limits (bucket_key, window_started_at, attempts)
    values (p_bucket_key, v_now, 1)
    on conflict (bucket_key) do update
       set window_started_at = case
               when api.device_auth_rate_limits.window_started_at
                    <= v_now - make_interval(secs => p_window_seconds)
                   then v_now
               else api.device_auth_rate_limits.window_started_at
           end,
           attempts = case
               when api.device_auth_rate_limits.window_started_at
                    <= v_now - make_interval(secs => p_window_seconds)
                   then 1
               else api.device_auth_rate_limits.attempts + 1
           end
    returning attempts into v_attempts;

    delete from api.device_auth_rate_limits
     where bucket_key in (
         select bucket_key
           from api.device_auth_rate_limits
          where window_started_at < v_now - interval '1 day'
          limit 100
     );

    return v_attempts <= p_limit;
end;
$$;

create function api.approve_device_auth_session(p_user_code text, p_user_id uuid)
returns text
language plpgsql
security invoker
set search_path = ''
as $$
declare
    v_session api.device_auth_sessions;
begin
    select * into v_session
      from api.device_auth_sessions s
     where s.user_code = p_user_code
     for update;

    if not found then
        return 'invalid';
    end if;
    if v_session.expires_at <= clock_timestamp() then
        update api.device_auth_sessions set status = 'expired' where id = v_session.id;
        return 'expired';
    end if;
    if v_session.status <> 'pending' then
        return 'invalid';
    end if;

    update api.device_auth_sessions
       set status = 'approved', user_id = p_user_id
     where id = v_session.id;
    return 'approved';
end;
$$;

create function api.claim_device_auth_session(p_device_code text, p_claim_id uuid)
returns table (result text, user_id uuid)
language plpgsql
security invoker
set search_path = ''
as $$
declare
    v_session api.device_auth_sessions;
    v_now     timestamptz := clock_timestamp();
begin
    select * into v_session
      from api.device_auth_sessions s
     where s.device_code = p_device_code
     for update;

    if not found then
        return query select 'invalid'::text, null::uuid;
        return;
    end if;
    if v_session.expires_at <= v_now then
        update api.device_auth_sessions
           set status = 'expired', claim_id = null, claimed_at = null
         where id = v_session.id;
        return query select 'expired'::text, null::uuid;
        return;
    end if;
    if v_session.last_polled_at is not null
       and v_session.last_polled_at > v_now - interval '5 seconds' then
        return query select 'slow_down'::text, null::uuid;
        return;
    end if;

    update api.device_auth_sessions
       set last_polled_at = v_now
     where id = v_session.id;

    if v_session.status = 'pending' then
        return query select 'authorization_pending'::text, null::uuid;
        return;
    end if;
    if v_session.status <> 'approved' or v_session.user_id is null then
        return query select 'invalid'::text, null::uuid;
        return;
    end if;
    if v_session.claim_id is not null and v_session.claimed_at > v_now - interval '90 seconds' then
        return query select 'authorization_pending'::text, null::uuid;
        return;
    end if;

    update api.device_auth_sessions
       set claim_id = p_claim_id, claimed_at = v_now
     where id = v_session.id;
    return query select 'approved'::text, v_session.user_id;
end;
$$;

create function api.finish_device_auth_session(
    p_device_code text,
    p_claim_id uuid,
    p_consume boolean
) returns boolean
language plpgsql
security invoker
set search_path = ''
as $$
declare
    v_rows integer;
begin
    if p_consume then
        delete from api.device_auth_sessions
         where device_code = p_device_code and claim_id = p_claim_id and status = 'approved';
    else
        update api.device_auth_sessions
           set claim_id = null, claimed_at = null
         where device_code = p_device_code and claim_id = p_claim_id and status = 'approved';
    end if;
    get diagnostics v_rows = row_count;
    return v_rows > 0;
end;
$$;

revoke all on function api.consume_device_auth_rate_limit(text, integer, integer)
    from public, anon, authenticated;
revoke all on function api.approve_device_auth_session(text, uuid)
    from public, anon, authenticated;
revoke all on function api.claim_device_auth_session(text, uuid)
    from public, anon, authenticated;
revoke all on function api.finish_device_auth_session(text, uuid, boolean)
    from public, anon, authenticated;

grant execute on function api.consume_device_auth_rate_limit(text, integer, integer) to service_role;
grant execute on function api.approve_device_auth_session(text, uuid) to service_role;
grant execute on function api.claim_device_auth_session(text, uuid) to service_role;
grant execute on function api.finish_device_auth_session(text, uuid, boolean) to service_role;
