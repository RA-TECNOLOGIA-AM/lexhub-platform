-- =============================================================================
-- API pública (chave de API) — spec: docs/superpowers/specs/2026-11-26-api-publica-design.md
--
--   * app.api_keys: uma chave por pessoa por org (pedido -> ativa | recusada -> revogada). Pede: Owner da org,
--     ou Gestor/Controller em alguma unidade. Aprova: Desenvolvedor (org role 'admin').
--   * app.api_key_sectors: setores EXTRAS pedidos (justificativa + validade). Os setores base não ficam aqui:
--     são os setores (app.teams) atuais da pessoa, lidos a cada chamada.
--   * app.api_refresh_tokens: refresh tokens da API (só o SHA-256), com rotação; quem emite e troca é a API.
--   * app_private.api_key_scope: o que a chave alcança. Repete as camadas 1 e 2 (setor) de
--     app_private.dashboard_access_explain (20261126110000_suporte_explica_acesso.sql, vigente de novo desde 20261126220000), trocando "setores da pessoa
--     nesta unidade" por "setores desta unidade cujo nome está em api_key_sector_names". A permissão
--     unit.dashboards.all do Gestor NÃO entra. (Sem app.dashboard_catalog.scope: a coluna saiu em
--     20261126220000_excluir_estrategico_geral.sql.)
--   * RPCs api.*: o front pede, consulta, aprova e revoga. Os tokens são gerados pela API em Python.
--
-- Tabelas só do backend: RLS ligado, sem policy, sem grant para anon/authenticated.
-- Versão depois de 20261126220000 (já aplicada no lexhub-v2) para manter a ordem do histórico.
-- Teste: supabase/tests/api_publica_test.sql (termina com rollback).
-- =============================================================================

-- 1. Tabelas ---------------------------------------------------------------------------------------------

create table app.api_keys (
    id                 uuid primary key default gen_random_uuid(),
    org_id             uuid not null references app.organizations (id) on delete cascade,
    user_id            uuid not null references auth.users (id) on delete cascade,
    membership_id      uuid not null references app.memberships (id) on delete cascade,
    status             text not null default 'pending'
                       check (status in ('pending', 'active', 'rejected', 'revoked')),
    note               text,
    decision_note      text,
    requested_at       timestamptz not null default now(),
    decided_by         uuid references auth.users (id) on delete set null,
    decided_at         timestamptz,
    revoked_by         uuid references auth.users (id) on delete set null,
    revoked_at         timestamptz,
    tokens_valid_since timestamptz,
    last_used_at       timestamptz
);
create unique index api_keys_one_open_uq on app.api_keys (org_id, user_id) where status in ('pending', 'active');
create index api_keys_org_status_idx on app.api_keys (org_id, status);
comment on table app.api_keys is
    'Chaves da API pública. Access tokens com iat anterior a tokens_valid_since são recusados.';

create table app.api_key_sectors (
    id            uuid primary key default gen_random_uuid(),
    key_id        uuid not null references app.api_keys (id) on delete cascade,
    sector_name   text not null,
    justification text not null check (length(trim(justification)) >= 10),
    expires_at    timestamptz not null,
    status        text not null default 'pending'
                  check (status in ('pending', 'approved', 'rejected', 'revoked')),
    decided_by    uuid references auth.users (id) on delete set null,
    decided_at    timestamptz,
    unique (key_id, sector_name)
);
comment on table app.api_key_sectors is
    'Setores extras de uma chave (além dos setores da pessoa). Valem só approved e com expires_at > now().';

create table app.api_refresh_tokens (
    id          uuid primary key default gen_random_uuid(),
    key_id      uuid not null references app.api_keys (id) on delete cascade,
    token_hash  text not null unique,
    created_at  timestamptz not null default now(),
    expires_at  timestamptz not null,
    used_at     timestamptz,
    revoked_at  timestamptz,
    replaced_by uuid references app.api_refresh_tokens (id) on delete set null
);
create index api_refresh_tokens_key_idx on app.api_refresh_tokens (key_id);
comment on table app.api_refresh_tokens is
    'Refresh tokens da API pública: só o SHA-256. used_at = já trocado (rotação).';

alter table app.api_keys enable row level security;
alter table app.api_key_sectors enable row level security;
alter table app.api_refresh_tokens enable row level security;
revoke all on app.api_keys, app.api_key_sectors, app.api_refresh_tokens from anon, authenticated;

-- 2. Regra -----------------------------------------------------------------------------------------------

-- Pode pedir chave na org: Owner, ou Gestor/Controller em alguma unidade ativa.
create function app_private.api_key_eligible(p_user uuid, p_org uuid) returns boolean
language sql stable security definer
set search_path = ''
as $$
    select exists (
        select 1 from app.memberships m
        where m.org_id = p_org and m.user_id = p_user and m.status = 'active'
          and (m.role_key = 'owner'
               or exists (select 1 from app.membership_units mu
                          join app.units u on u.id = mu.unit_id and u.active
                          where mu.membership_id = m.id and mu.role_key in ('gestor', 'controller')))
    );
$$;

-- Unidades em que a chave pode valer: todas (Owner) ou as de Gestor/Controller.
create function app_private.api_key_units(p_membership uuid) returns setof uuid
language sql stable security definer
set search_path = ''
as $$
    select u.id
    from app.memberships m
    join app.units u on u.org_id = m.org_id and u.active
    where m.id = p_membership and m.status = 'active'
      and (m.role_key = 'owner'
           or exists (select 1 from app.membership_units mu
                      where mu.membership_id = m.id and mu.unit_id = u.id
                        and mu.role_key in ('gestor', 'controller')));
$$;

create function app_private.api_key_base_sectors(p_membership uuid) returns text[]
language sql stable security definer
set search_path = ''
as $$
    select coalesce(array_agg(distinct t.name order by t.name), '{}')
    from app.membership_teams mt
    join app.teams t on t.id = mt.team_id and t.active
    where mt.membership_id = p_membership;
$$;

-- Setores da chave: base (atuais da pessoa) + extras aprovados e dentro da validade.
create function app_private.api_key_sector_names(p_key uuid) returns text[]
language sql stable security definer
set search_path = ''
as $$
    select coalesce(array_agg(distinct x.name), '{}')
    from (
        select unnest(app_private.api_key_base_sectors(k.membership_id)) as name
        from app.api_keys k where k.id = p_key
        union
        select s.sector_name
        from app.api_key_sectors s
        where s.key_id = p_key and s.status = 'approved' and s.expires_at > now()
    ) x;
$$;

-- O que a chave alcança: 'all', 'own' ou null.
create function app_private.api_key_scope(p_key uuid, p_unit uuid, p_dashboard text) returns text
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_key   app.api_keys;
    v_group text;
    v_names text[];
    v_scope text;
begin
    select * into v_key from app.api_keys where id = p_key and status = 'active';
    if v_key.id is null then
        return null;
    end if;

    -- organização ativa, unidade dela, e cargo que ainda dá direito à chave nesta unidade
    if not exists (select 1 from app.organizations o where o.id = v_key.org_id and o.active)
       or p_unit not in (select app_private.api_key_units(v_key.membership_id)) then
        return null;
    end if;

    -- dashboard ativo e ligado na unidade
    select d.group_slug into v_group
    from app.org_dashboards od
    join app.dashboard_catalog d on d.key = od.dashboard_key and d.active
    where od.org_id = v_key.org_id and od.unit_id = p_unit and od.dashboard_key = p_dashboard and od.enabled;
    if v_group is null then
        return null;
    end if;

    v_names := app_private.api_key_sector_names(p_key);

    -- Camadas 1 e 2 de dashboard_access_explain, pelos setores da chave nesta unidade
    select case
               when bool_or(x.s = 'all') then 'all'
               when count(*) > 0 then 'own'
           end
      into v_scope
    from (
        select r.scope as s
        from app.access_rules r
        join app.teams t on t.id = r.team_id and t.active and t.unit_id = p_unit
        where r.dashboard_key = p_dashboard and t.name = any (v_names)
        union all
        select 'all'
        from app.teams t
        where t.active and t.unit_id = p_unit and t.name = any (v_names)
          and (t.sees_all
               or exists (select 1 from app.team_group_grants g
                          where g.team_id = t.id and g.group_slug = v_group))
    ) x;
    return v_scope;
end;
$$;

create function app_private.api_key_is_dev(p_org uuid) returns boolean
language sql stable security definer
set search_path = ''
as $$
    select exists (select 1 from app.memberships m
                   where m.org_id = p_org and m.user_id = auth.uid()
                     and m.status = 'active' and m.role_key = 'admin');
$$;

create function app_private.api_key_org(p_org text) returns uuid
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org uuid;
begin
    select o.id into v_org from app.organizations o where o.slug = p_org and o.active;
    if v_org is null then
        raise exception using errcode = 'P0001', message = 'Organização não encontrada.';
    end if;
    return v_org;
end;
$$;

create function app_private.api_key_json(p_key uuid) returns jsonb
language sql stable security definer
set search_path = ''
as $$
    select jsonb_build_object(
        'id', k.id,
        'user_name', m.full_name,
        'user_email', m.email,
        'status', k.status,
        'note', k.note,
        'decision_note', k.decision_note,
        'requested_at', k.requested_at,
        'decided_at', k.decided_at,
        'revoked_at', k.revoked_at,
        'last_used_at', k.last_used_at,
        'sectors',
            coalesce((select jsonb_agg(jsonb_build_object('setor', b, 'base', true, 'status', 'approved')
                                       order by b)
                      from unnest(app_private.api_key_base_sectors(k.membership_id)) b), '[]'::jsonb)
            || coalesce((select jsonb_agg(jsonb_build_object(
                                    'setor', s.sector_name, 'base', false, 'status', s.status,
                                    'justificativa', s.justification, 'expires_at', s.expires_at)
                                order by s.sector_name)
                         from app.api_key_sectors s where s.key_id = k.id), '[]'::jsonb)
    )
    from app.api_keys k
    join app.memberships m on m.id = k.membership_id
    where k.id = p_key;
$$;

revoke all on function app_private.api_key_eligible(uuid, uuid), app_private.api_key_units(uuid),
    app_private.api_key_base_sectors(uuid), app_private.api_key_sector_names(uuid),
    app_private.api_key_scope(uuid, uuid, text), app_private.api_key_is_dev(uuid),
    app_private.api_key_org(text), app_private.api_key_json(uuid)
    from public, anon, authenticated;
grant execute on function app_private.api_key_scope(uuid, uuid, text),
    app_private.api_key_sector_names(uuid) to service_role;

-- 3. RPCs do front ---------------------------------------------------------------------------------------

-- Quem chama pode pedir? Setores base e setores que pode pedir como extra (das unidades que a chave alcança).
create function api.api_key_eligibility(p_org text) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org uuid := app_private.api_key_org(p_org);
    v_m   uuid;
begin
    select m.id into v_m from app.memberships m
    where m.org_id = v_org and m.user_id = auth.uid() and m.status = 'active';
    if v_m is null or not app_private.api_key_eligible(auth.uid(), v_org) then
        return jsonb_build_object('eligible', false, 'base_sectors', '[]'::jsonb, 'sectors', '[]'::jsonb);
    end if;
    return jsonb_build_object(
        'eligible', true,
        'base_sectors', to_jsonb(app_private.api_key_base_sectors(v_m)),
        'sectors', coalesce((select jsonb_agg(distinct t.name)
                             from app.teams t
                             where t.active and t.unit_id in (select app_private.api_key_units(v_m))),
                            '[]'::jsonb));
end;
$$;

-- p_extras: [{"setor": text, "justificativa": text, "validade": "AAAA-MM-DD"}]
create function api.request_api_key(p_org text, p_note text, p_extras jsonb) returns uuid
language plpgsql security definer
set search_path = ''
as $$
declare
    v_org     uuid := app_private.api_key_org(p_org);
    v_m       uuid;
    v_key     uuid;
    v_base    text[];
    v_allowed text[];
    e         jsonb;
    v_setor   text;
    v_just    text;
    v_val     date;
begin
    if not app_private.api_key_eligible(auth.uid(), v_org) then
        raise exception using errcode = '42501',
            message = 'Só Owner, Gestor ou Controller podem pedir chave de API.';
    end if;
    select m.id into v_m from app.memberships m
    where m.org_id = v_org and m.user_id = auth.uid() and m.status = 'active';

    if exists (select 1 from app.api_keys k
               where k.org_id = v_org and k.user_id = auth.uid() and k.status in ('pending', 'active')) then
        raise exception using errcode = 'P0001', message = 'Você já tem uma chave pedida ou ativa nesta organização.';
    end if;

    v_base := app_private.api_key_base_sectors(v_m);
    select coalesce(array_agg(distinct t.name), '{}') into v_allowed
    from app.teams t where t.active and t.unit_id in (select app_private.api_key_units(v_m));

    p_extras := coalesce(p_extras, '[]'::jsonb);
    if jsonb_typeof(p_extras) <> 'array' then
        raise exception using errcode = 'P0001', message = 'Setores extras inválidos.';
    end if;
    if cardinality(v_base) = 0 and jsonb_array_length(p_extras) = 0 then
        raise exception using errcode = 'P0001',
            message = 'Você não tem setor cadastrado: peça ao menos um setor extra.';
    end if;

    insert into app.api_keys (org_id, user_id, membership_id, note)
    values (v_org, auth.uid(), v_m, nullif(trim(p_note), ''))
    returning id into v_key;

    for e in select * from jsonb_array_elements(p_extras) loop
        v_setor := trim(e ->> 'setor');
        v_just  := trim(e ->> 'justificativa');
        begin
            v_val := (e ->> 'validade')::date;
        exception when others then
            raise exception using errcode = 'P0001', message = 'Validade inválida.';
        end;
        if v_setor is null or not (v_setor = any (v_allowed)) then
            raise exception using errcode = 'P0001', message = format('Setor "%s" não disponível.', v_setor);
        end if;
        if v_setor = any (v_base) then
            raise exception using errcode = 'P0001', message = format('"%s" já é um setor seu.', v_setor);
        end if;
        if v_just is null or length(v_just) < 10 then
            raise exception using errcode = 'P0001',
                message = 'A justificativa do setor extra precisa de pelo menos 10 caracteres.';
        end if;
        if v_val is null or v_val <= current_date or v_val > current_date + 365 then
            raise exception using errcode = 'P0001',
                message = 'A validade do setor extra deve ser entre amanhã e 365 dias.';
        end if;
        insert into app.api_key_sectors (key_id, sector_name, justification, expires_at)
        values (v_key, v_setor, v_just, (v_val + 1)::timestamp at time zone 'America/Sao_Paulo');
    end loop;

    insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
    values (v_org, auth.uid(), 'api_key.requested', 'api_key', v_key::text,
            jsonb_build_object('extras', p_extras));
    return v_key;
end;
$$;

-- A chave mais recente de quem chama nesta org (ou null).
create function api.my_api_key(p_org text) returns jsonb
language sql stable security definer
set search_path = ''
as $$
    select app_private.api_key_json(k.id)
    from app.api_keys k
    where k.org_id = app_private.api_key_org(p_org) and k.user_id = auth.uid()
    order by k.requested_at desc
    limit 1;
$$;

-- Desenvolvedor: chaves da org. p_status: 'pending' | 'active' | 'closed' (recusadas e revogadas) | 'all'.
create function api.list_api_keys(p_org text, p_status text) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org uuid := app_private.api_key_org(p_org);
begin
    if not app_private.api_key_is_dev(v_org) then
        raise exception using errcode = '42501', message = 'Só Desenvolvedor gerencia chaves de API.';
    end if;
    return coalesce((
        select jsonb_agg(app_private.api_key_json(k.id) order by k.requested_at desc)
        from app.api_keys k
        where k.org_id = v_org
          and (p_status = 'all'
               or k.status = p_status
               or (p_status = 'closed' and k.status in ('rejected', 'revoked')))
    ), '[]'::jsonb);
end;
$$;

create function api.count_pending_api_keys(p_org text) returns integer
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org uuid := app_private.api_key_org(p_org);
begin
    if not app_private.api_key_is_dev(v_org) then
        return 0;
    end if;
    return (select count(*) from app.api_keys k where k.org_id = v_org and k.status = 'pending');
end;
$$;

-- Desenvolvedor aprova (com os extras marcados) ou recusa.
create function api.decide_api_key(p_key uuid, p_approve boolean, p_sectors_approved text[], p_note text)
returns jsonb
language plpgsql security definer
set search_path = ''
as $$
declare
    v_key app.api_keys;
begin
    select * into v_key from app.api_keys where id = p_key for update;
    if v_key.id is null or not app_private.api_key_is_dev(v_key.org_id) then
        raise exception using errcode = '42501', message = 'Só Desenvolvedor decide pedidos de chave de API.';
    end if;
    if v_key.status <> 'pending' then
        raise exception using errcode = 'P0001', message = 'Este pedido já foi decidido.';
    end if;

    update app.api_keys
       set status = case when p_approve then 'active' else 'rejected' end,
           decision_note = nullif(trim(p_note), ''),
           decided_by = auth.uid(), decided_at = now()
     where id = p_key;
    update app.api_key_sectors
       set status = case when p_approve and sector_name = any (coalesce(p_sectors_approved, '{}'))
                         then 'approved' else 'rejected' end,
           decided_by = auth.uid(), decided_at = now()
     where key_id = p_key;

    insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
    values (v_key.org_id, auth.uid(),
            case when p_approve then 'api_key.approved' else 'api_key.rejected' end,
            'api_key', p_key::text,
            jsonb_build_object('sectors_approved', coalesce(p_sectors_approved, '{}'), 'note', p_note));
    return app_private.api_key_json(p_key);
end;
$$;

-- Desenvolvedor ou o dono: encerra a chave e todos os tokens dela.
create function api.revoke_api_key(p_key uuid) returns void
language plpgsql security definer
set search_path = ''
as $$
declare
    v_key app.api_keys;
begin
    select * into v_key from app.api_keys where id = p_key for update;
    if v_key.id is null
       or not (v_key.user_id = auth.uid() or app_private.api_key_is_dev(v_key.org_id)) then
        raise exception using errcode = '42501', message = 'Sem permissão para revogar esta chave.';
    end if;
    if v_key.status not in ('pending', 'active') then
        raise exception using errcode = 'P0001', message = 'Esta chave já está encerrada.';
    end if;
    update app.api_keys
       set status = 'revoked', revoked_by = auth.uid(), revoked_at = now(), tokens_valid_since = now()
     where id = p_key;
    update app.api_refresh_tokens set revoked_at = now() where key_id = p_key and revoked_at is null;
    insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id)
    values (v_key.org_id, auth.uid(), 'api_key.revoked', 'api_key', p_key::text);
end;
$$;

-- Desenvolvedor: tira um setor extra sem derrubar a chave.
create function api.revoke_api_key_sector(p_key uuid, p_sector text) returns void
language plpgsql security definer
set search_path = ''
as $$
declare
    v_key app.api_keys;
begin
    select * into v_key from app.api_keys where id = p_key;
    if v_key.id is null or not app_private.api_key_is_dev(v_key.org_id) then
        raise exception using errcode = '42501', message = 'Só Desenvolvedor revoga setor de chave de API.';
    end if;
    update app.api_key_sectors set status = 'revoked', decided_by = auth.uid(), decided_at = now()
     where key_id = p_key and sector_name = p_sector and status = 'approved';
    if not found then
        raise exception using errcode = 'P0001', message = 'Setor extra não encontrado nesta chave.';
    end if;
    insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
    values (v_key.org_id, auth.uid(), 'api_key.sector_revoked', 'api_key', p_key::text,
            jsonb_build_object('setor', p_sector));
end;
$$;

revoke all on function api.api_key_eligibility(text), api.request_api_key(text, text, jsonb),
    api.my_api_key(text), api.list_api_keys(text, text), api.count_pending_api_keys(text),
    api.decide_api_key(uuid, boolean, text[], text), api.revoke_api_key(uuid),
    api.revoke_api_key_sector(uuid, text)
    from public, anon;
grant execute on function api.api_key_eligibility(text), api.request_api_key(text, text, jsonb),
    api.my_api_key(text), api.list_api_keys(text, text), api.count_pending_api_keys(text),
    api.decide_api_key(uuid, boolean, text[], text), api.revoke_api_key(uuid),
    api.revoke_api_key_sector(uuid, text)
    to authenticated;

-- 4. Menu: api.my_admin_permissions ganha 'api_keys' (Desenvolvedor). Corpo conferido contra
--    20261126100000_modo_suporte_ver_como.sql (definição vigente); a única mudança é a chave nova.
create or replace function api.my_admin_permissions(p_org text) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org uuid;
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    if v_org is null then
        return jsonb_build_object('access', false, 'members', false, 'sources', false, 'audit', false,
                                  'billing', false, 'clients', app_private.can_see_clients(), 'support', false,
                                  'api_keys', false);
    end if;
    return jsonb_build_object(
        'access', cardinality(app_private.access_scope(v_org)) > 0,
        'members', cardinality(app_private.members_scope(v_org)) > 0,
        'sources', cardinality(app_private.sources_scope(v_org)) > 0,
        'audit', v_org = any (app_private.my_org_ids_with('audit.view')),
        'billing', v_org = any (app_private.my_org_ids_with('billing.view')) or app_private.is_platform_staff(),
        'clients', app_private.can_see_clients(),
        'support', v_org = any (app_private.my_org_ids_with('org.dashboards.all')),
        'api_keys', app_private.api_key_is_dev(v_org)
    );
end;
$$;

-- =============================================================================
-- Desfazer:
-- drop function api.revoke_api_key_sector(uuid, text), api.revoke_api_key(uuid),
--     api.decide_api_key(uuid, boolean, text[], text), api.count_pending_api_keys(text),
--     api.list_api_keys(text, text), api.my_api_key(text), api.request_api_key(text, text, jsonb),
--     api.api_key_eligibility(text);
-- drop function app_private.api_key_json(uuid), app_private.api_key_org(text), app_private.api_key_is_dev(uuid),
--     app_private.api_key_scope(uuid, uuid, text), app_private.api_key_sector_names(uuid),
--     app_private.api_key_base_sectors(uuid), app_private.api_key_units(uuid),
--     app_private.api_key_eligible(uuid, uuid);
-- (recriar api.my_admin_permissions com o corpo de 20261126100000_modo_suporte_ver_como.sql)
-- drop table app.api_refresh_tokens, app.api_key_sectors, app.api_keys;
-- =============================================================================
