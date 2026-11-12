-- =============================================================================
-- Solicitar acesso: quem entra (ex.: pelo Google) sem associação ativa pede acesso; a equipe RA aprova
-- (numa organização existente ou numa nova) ou recusa.
--
--   app.access_requests  um pedido por linha; cada pessoa lê só o próprio; ninguém grava direto
--   schema api           SÓ funções, expostas na API REST do Supabase (Settings > API > Exposed schemas)
--                        request_access, my_access_request                    (quem pede)
--                        count_pending_access_requests, list_access_requests,
--                        approval_options, approve_access_request,
--                        reject_access_request                                 (equipe RA)
--   Equipe RA = app_metadata.platform_staff no token (mesma regra da API).
--   Tudo auditado em app.audit_log. Spec: docs/superpowers/specs/2026-11-11-acesso-google-design.md
--
-- Rollback (desfaz tudo desta migration):
--   drop schema if exists api cascade;
--   drop function if exists app_private.is_platform_staff();
--   drop table if exists app.access_requests;
-- Teste (desfaz sozinho): supabase/tests/solicitar_acesso_test.sql
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Pedidos
-- ---------------------------------------------------------------------------
create table app.access_requests (
    id            uuid primary key default gen_random_uuid(),
    user_id       uuid not null references auth.users (id) on delete cascade,
    email         text not null,
    full_name     text not null,
    office        text not null check (length(trim(office)) between 2 and 120),
    message       text check (message is null or length(message) <= 500),
    status        text not null default 'pending' check (status in ('pending', 'approved', 'rejected')),
    decided_by    uuid references auth.users (id) on delete set null,
    decided_at    timestamptz,
    decision_note text check (decision_note is null or length(decision_note) <= 500),
    result_org_id uuid references app.organizations (id) on delete set null,
    created_at    timestamptz not null default now(),
    check ((status = 'pending') = (decided_at is null))
);
create unique index access_requests_one_pending_uq on app.access_requests (user_id) where status = 'pending';
create index access_requests_status_created_idx on app.access_requests (status, created_at desc);

alter table app.access_requests enable row level security;
create policy access_requests_select_own on app.access_requests for select to authenticated
    using (user_id = (select auth.uid()));

-- ---------------------------------------------------------------------------
-- 2. Equipe RA
-- ---------------------------------------------------------------------------
create function app_private.is_platform_staff() returns boolean
language sql stable
set search_path = ''
as $$
    select coalesce((auth.jwt() -> 'app_metadata' ->> 'platform_staff')::boolean, false);
$$;
revoke all on function app_private.is_platform_staff() from public, anon;
grant execute on function app_private.is_platform_staff() to authenticated, service_role;

-- O pedido em JSON, como o front recebe.
create function app_private.access_request_json(r app.access_requests) returns jsonb
language sql stable
set search_path = ''
as $$
    select jsonb_build_object(
        'id', r.id, 'email', r.email, 'full_name', r.full_name, 'office', r.office, 'message', r.message,
        'status', r.status, 'created_at', r.created_at, 'decided_at', r.decided_at,
        'decision_note', r.decision_note, 'result_org_id', r.result_org_id
    );
$$;
revoke all on function app_private.access_request_json(app.access_requests) from public, anon;

-- ---------------------------------------------------------------------------
-- 3. Schema api (só funções)
-- ---------------------------------------------------------------------------
create schema api;
revoke all on schema api from public;
grant usage on schema api to authenticated, service_role;

-- Barra quem não é da equipe RA.
create function app_private.require_platform_staff() returns void
language plpgsql stable
set search_path = ''
as $$
begin
    if not app_private.is_platform_staff() then
        raise exception using errcode = '42501', message = 'Só a equipe RA Tecnologia pode fazer isso.';
    end if;
end;
$$;
revoke all on function app_private.require_platform_staff() from public, anon;
grant execute on function app_private.require_platform_staff() to authenticated, service_role;

-- Quem está logado e sem associação ativa pede acesso.
create function api.request_access(p_office text, p_message text default null) returns jsonb
language plpgsql security definer
set search_path = ''
as $$
declare
    v_uid  uuid := auth.uid();
    v_user auth.users;
    v_row  app.access_requests;
begin
    if v_uid is null then
        raise exception using errcode = '42501', message = 'Entre para pedir acesso.';
    end if;
    if exists (select 1 from app.memberships m where m.user_id = v_uid and m.status = 'active') then
        raise exception using errcode = 'P0001', message = 'Você já tem acesso ao LexHub.';
    end if;
    if exists (select 1 from app.access_requests r where r.user_id = v_uid and r.status = 'pending') then
        raise exception using errcode = 'P0001', message = 'Você já tem um pedido aguardando aprovação.';
    end if;
    if length(trim(coalesce(p_office, ''))) not between 2 and 120 then
        raise exception using errcode = 'P0001', message = 'Informe o escritório ou a empresa (2 a 120 caracteres).';
    end if;
    if p_message is not null and length(p_message) > 500 then
        raise exception using errcode = 'P0001', message = 'A mensagem pode ter até 500 caracteres.';
    end if;

    select * into v_user from auth.users u where u.id = v_uid;

    insert into app.access_requests (user_id, email, full_name, office, message)
    values (
        v_uid,
        lower(v_user.email),
        coalesce(nullif(trim(v_user.raw_user_meta_data ->> 'full_name'), ''),
                 nullif(trim(v_user.raw_user_meta_data ->> 'name'), ''),
                 lower(v_user.email)),
        trim(p_office),
        nullif(trim(coalesce(p_message, '')), '')
    )
    returning * into v_row;

    insert into app.audit_log (actor_user_id, action, target_type, target_id, metadata)
    values (v_uid, 'access_request.created', 'access_request', v_row.id::text,
            jsonb_build_object('office', v_row.office));

    return app_private.access_request_json(v_row);
end;
$$;

-- O último pedido de quem chama (null = nunca pediu).
create function api.my_access_request() returns jsonb
language sql stable security definer
set search_path = ''
as $$
    select app_private.access_request_json(r)
    from app.access_requests r
    where r.user_id = auth.uid()
    order by r.created_at desc
    limit 1;
$$;

-- O número do selo.
create function api.count_pending_access_requests() returns integer
language plpgsql stable security definer
set search_path = ''
as $$
begin
    perform app_private.require_platform_staff();
    return (select count(*)::int from app.access_requests where status = 'pending');
end;
$$;

-- p_status: 'pending' ou 'decided' (aprovados e recusados). Mais recentes primeiro.
create function api.list_access_requests(p_status text default 'pending') returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
begin
    perform app_private.require_platform_staff();
    if p_status not in ('pending', 'decided') then
        raise exception using errcode = 'P0001', message = 'Status inválido: use pending ou decided.';
    end if;
    return coalesce((
        select jsonb_agg(app_private.access_request_json(r) order by r.created_at desc)
        from app.access_requests r
        where (p_status = 'pending' and r.status = 'pending')
           or (p_status = 'decided' and r.status <> 'pending')
    ), '[]'::jsonb);
end;
$$;

-- Organizações e unidades ativas, para o formulário de aprovação.
create function api.approval_options() returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
begin
    perform app_private.require_platform_staff();
    return coalesce((
        select jsonb_agg(jsonb_build_object(
                   'id', o.id, 'slug', o.slug, 'name', o.name,
                   'units', coalesce((
                       select jsonb_agg(jsonb_build_object('id', u.id, 'code', u.code, 'name', u.name)
                                        order by u.name)
                       from app.units u where u.org_id = o.id and u.active
                   ), '[]'::jsonb))
               order by o.name)
        from app.organizations o
        where o.active
    ), '[]'::jsonb);
end;
$$;

-- Aprova numa transação. p_target:
--   {"kind":"existing","org_id":"…","org_role":"admin"|"member",
--    "units":[{"unit_id":"…","role_key":"gestor"|"controller"|"colaborador"|"leitor"}]}
--   {"kind":"new","name":"…","slug":"…","org_role":"owner"|"admin",
--    "unit":{"code":"…","name":"…","timezone":"America/Manaus"}}
create function api.approve_access_request(p_id uuid, p_target jsonb) returns jsonb
language plpgsql security definer
set search_path = ''
as $$
declare
    v_req        app.access_requests;
    v_kind       text := p_target ->> 'kind';
    v_org_role   text := p_target ->> 'org_role';
    v_org        uuid;
    v_membership uuid;
    v_unit       jsonb;
    v_new_unit   uuid;
begin
    perform app_private.require_platform_staff();

    select * into v_req from app.access_requests where id = p_id for update;
    if v_req.id is null then
        raise exception using errcode = 'P0001', message = 'Pedido não encontrado.';
    end if;
    if v_req.status <> 'pending' then
        raise exception using errcode = 'P0001', message = 'Este pedido já foi decidido.';
    end if;

    if v_kind = 'existing' then
        v_org := (p_target ->> 'org_id')::uuid;
        if not exists (select 1 from app.organizations o where o.id = v_org and o.active) then
            raise exception using errcode = 'P0001', message = 'Organização não encontrada.';
        end if;
        if v_org_role not in ('admin', 'member') then
            raise exception using errcode = 'P0001', message = 'Papel na organização inválido.';
        end if;
        if v_org_role = 'member' and jsonb_array_length(coalesce(p_target -> 'units', '[]'::jsonb)) = 0 then
            raise exception using errcode = 'P0001', message = 'Escolha pelo menos uma unidade.';
        end if;
    elsif v_kind = 'new' then
        if v_org_role not in ('owner', 'admin') then
            raise exception using errcode = 'P0001', message = 'Papel na organização nova inválido.';
        end if;
        insert into app.organizations (slug, name)
        values (lower(trim(p_target ->> 'slug')), trim(p_target ->> 'name'))
        returning id into v_org;
        insert into app.units (org_id, code, name, timezone)
        values (v_org, upper(trim(p_target -> 'unit' ->> 'code')), trim(p_target -> 'unit' ->> 'name'),
                coalesce(nullif(trim(p_target -> 'unit' ->> 'timezone'), ''), 'America/Manaus'))
        returning id into v_new_unit;
    else
        raise exception using errcode = 'P0001', message = 'Destino da aprovação inválido.';
    end if;

    -- Associação: nova, ou reativa a que já existia nessa organização (ex.: desativada).
    select m.id into v_membership from app.memberships m where m.org_id = v_org and m.user_id = v_req.user_id;
    if v_membership is null then
        insert into app.memberships (org_id, user_id, full_name, email, role_key, status)
        values (v_org, v_req.user_id, v_req.full_name, v_req.email, v_org_role, 'active')
        returning id into v_membership;
    else
        update app.memberships set role_key = v_org_role, status = 'active' where id = v_membership;
        delete from app.membership_units where membership_id = v_membership;
    end if;

    if v_kind = 'existing' then
        for v_unit in select * from jsonb_array_elements(coalesce(p_target -> 'units', '[]'::jsonb)) loop
            if not exists (select 1 from app.units u
                           where u.id = (v_unit ->> 'unit_id')::uuid and u.org_id = v_org and u.active) then
                raise exception using errcode = 'P0001', message = 'Unidade fora da organização escolhida.';
            end if;
            insert into app.membership_units (org_id, unit_id, membership_id, role_key)
            values (v_org, (v_unit ->> 'unit_id')::uuid, v_membership, v_unit ->> 'role_key');
        end loop;
    end if;

    update app.access_requests
       set status = 'approved', decided_by = auth.uid(), decided_at = now(), result_org_id = v_org
     where id = p_id
     returning * into v_req;

    insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
    values (v_org, auth.uid(), 'access_request.approved', 'access_request', p_id::text,
            jsonb_build_object('kind', v_kind, 'org_role', v_org_role, 'membership_id', v_membership,
                               'user_id', v_req.user_id));

    return app_private.access_request_json(v_req);
end;
$$;

create function api.reject_access_request(p_id uuid, p_note text default null) returns jsonb
language plpgsql security definer
set search_path = ''
as $$
declare
    v_req app.access_requests;
begin
    perform app_private.require_platform_staff();
    if p_note is not null and length(p_note) > 500 then
        raise exception using errcode = 'P0001', message = 'A nota pode ter até 500 caracteres.';
    end if;

    update app.access_requests
       set status = 'rejected', decided_by = auth.uid(), decided_at = now(),
           decision_note = nullif(trim(coalesce(p_note, '')), '')
     where id = p_id and status = 'pending'
     returning * into v_req;
    if v_req.id is null then
        raise exception using errcode = 'P0001', message = 'Pedido não encontrado ou já decidido.';
    end if;

    insert into app.audit_log (actor_user_id, action, target_type, target_id, metadata)
    values (auth.uid(), 'access_request.rejected', 'access_request', p_id::text,
            jsonb_build_object('user_id', v_req.user_id));

    return app_private.access_request_json(v_req);
end;
$$;

-- Só quem está logado chama (cada função confere o resto).
revoke all on all functions in schema api from public, anon;
grant execute on all functions in schema api to authenticated;
