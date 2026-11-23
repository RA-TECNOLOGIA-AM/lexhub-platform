-- =============================================================================
-- Excluir unidade e encerrar organização
--
-- Unidade: arquivada (active = false + deleted_at) e apagada de vez depois de 30 dias (pg_cron).
--   Na hora: as fontes da unidade são desligadas e as senhas cifradas apagadas (mesmo que
--   app_private.disconnect_source faz). Volta em até 30 dias só por SQL: update app.units set active = true,
--   deleted_at = null, deleted_by = null where id = ... (sem as fontes, que já foram apagadas).
--   Travas: unidade com deletion_locked (NG, LA e RJ da LexGroup) e a última unidade ativa da organização.
--   deletion_locked só muda por migration (nenhuma função da api mexe nele).
-- Organização: encerrada (active = false + closed_at). Não dá para apagar de vez: app.audit_log é só
--   inserção e o "on delete set null" dele seria um update. Todas as telas e a API já filtram o.active.
--   Na hora: as fontes da organização são apagadas (com as senhas). A dona da plataforma (LexGroup) nunca.
-- Também: api.list_sources ganha orgName (título da tela) e api.list_clients ganha as unidades de cada
-- organização e se ela pode ser encerrada.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Colunas e travas
-- ---------------------------------------------------------------------------
alter table app.units
    add column deleted_at      timestamptz,
    add column deleted_by      uuid references auth.users (id) on delete set null,
    add column deletion_locked boolean not null default false;

alter table app.organizations
    add column closed_at timestamptz,
    add column closed_by uuid references auth.users (id) on delete set null;

-- As unidades que alimentam a operação da LexGroup: não saem pela tela. Para excluir uma, uma migration
-- faz "update app.units set deletion_locked = false where ..." antes.
update app.units u set deletion_locked = true
from app.organizations o
where o.id = u.org_id and o.platform_owner and u.code in ('NG', 'LA', 'RJ');

-- Nem um delete direto apaga unidade travada (a limpeza de 30 dias e o cascade da organização incluídos).
create function app_private.block_locked_unit_delete() returns trigger
language plpgsql
set search_path = ''
as $$
begin
    if old.deletion_locked then
        raise exception using errcode = 'P0001',
            message = format('A unidade %s não pode ser excluída (trava da plataforma).', old.name);
    end if;
    return old;
end;
$$;

revoke all on function app_private.block_locked_unit_delete() from public, anon, authenticated;

create trigger units_block_locked_delete before delete on app.units
    for each row execute function app_private.block_locked_unit_delete();

-- ---------------------------------------------------------------------------
-- 2. O que vai junto (a tela mostra antes de confirmar)
-- ---------------------------------------------------------------------------
create function app_private.unit_deletion_json(p_unit uuid) returns jsonb
language sql stable security definer
set search_path = ''
as $$
    select jsonb_build_object(
        'code', u.code,
        'name', u.name,
        'sources', jsonb_array_length(coalesce(s.j -> 'sources', '[]'::jsonb)),
        'dashboards', coalesce((s.j ->> 'dashboards')::int, 0),
        'members', (select count(*) from app.membership_units m where m.unit_id = u.id)::int,
        'locked', u.deletion_locked,
        'lastUnit', not exists (
            select 1 from app.units o where o.org_id = u.org_id and o.active and o.id <> u.id
        )
    )
    from app.units u
    cross join lateral (select app_private.unit_sources_json(u.id) as j) s
    where u.id = p_unit;
$$;

revoke all on function app_private.unit_deletion_json(uuid) from public, anon, authenticated;

-- A unidade ativa que Owner/Desenvolvedor da organização pode excluir; senão 42501/P0001.
create function app_private.require_unit_to_delete(p_org text, p_code text) returns app.units
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org  uuid;
    v_unit app.units;
begin
    select o.id into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    if v_org is null or not (v_org = any (app_private.my_org_ids_with('units.manage'))) then
        raise exception using errcode = '42501', message = 'Só Owner ou Desenvolvedor excluem unidades.';
    end if;
    select u.* into v_unit from app.units u
    where u.org_id = v_org and u.code = upper(trim(coalesce(p_code, ''))) and u.active;
    if v_unit.id is null then
        raise exception using errcode = 'P0001', message = 'Unidade não encontrada.';
    end if;
    return v_unit;
end;
$$;

revoke all on function app_private.require_unit_to_delete(text, text) from public, anon, authenticated;

create function api.unit_deletion_impact(p_org text, p_code text) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_unit app.units := app_private.require_unit_to_delete(p_org, p_code);
begin
    return app_private.unit_deletion_json(v_unit.id);
end;
$$;

-- ---------------------------------------------------------------------------
-- 3. api.delete_unit: arquiva, desliga as fontes e apaga as senhas na hora
-- ---------------------------------------------------------------------------
create function api.delete_unit(p_org text, p_code text, p_confirm text) returns void
language plpgsql volatile security definer
set search_path = ''
as $$
declare
    v_unit   app.units := app_private.require_unit_to_delete(p_org, p_code);
    v_impact jsonb;
    v_keys   text[];
begin
    perform 1 from app.units u where u.id = v_unit.id for update;
    v_impact := app_private.unit_deletion_json(v_unit.id);

    if v_unit.deletion_locked then
        raise exception using errcode = 'P0001',
            message = format('A unidade %s não pode ser excluída (trava da plataforma).', v_unit.name);
    end if;
    if (v_impact ->> 'lastUnit')::boolean then
        raise exception using errcode = 'P0001', message = 'A organização precisa de pelo menos uma unidade.';
    end if;
    if lower(trim(coalesce(p_confirm, ''))) <> lower(trim(v_unit.name)) then
        raise exception using errcode = 'P0001', message = 'Digite o nome da unidade para confirmar.';
    end if;

    -- As fontes que são só desta unidade saem inteiras (com a senha e o log), como no Desconectar.
    select coalesce(array_agg(ds.key), '{}') into v_keys
    from app.data_sources ds where ds.owner_unit_id = v_unit.id;
    delete from app.data_sources where owner_unit_id = v_unit.id;
    delete from app.dashboard_sources d where d.source_key = any (v_keys)
        and not exists (select 1 from app.data_sources o where o.key = d.source_key);
    -- As da organização (LexPre, LexFlow, banco interno) só deixam de alimentar esta unidade.
    delete from app.unit_source_refs where unit_id = v_unit.id;

    update app.units
    set active = false, deleted_at = now(), deleted_by = auth.uid(), updated_at = now()
    where id = v_unit.id;

    insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
    values (v_unit.org_id, auth.uid(), 'unit.deleted', 'unit', v_unit.id::text,
            jsonb_build_object('code', v_unit.code, 'name', v_unit.name,
                               'sources', v_impact -> 'sources', 'dashboards', v_impact -> 'dashboards',
                               'members', v_impact -> 'members', 'purgeAfterDays', 30));
end;
$$;

-- Apaga de vez as unidades arquivadas há mais de 30 dias (o cascade leva dashboards, vínculos e grupos).
create function app_private.purge_deleted_units() returns integer
language plpgsql volatile security definer
set search_path = ''
as $$
declare
    v_count integer;
begin
    delete from app.units u
    where not u.active and not u.deletion_locked
      and u.deleted_at is not null and u.deleted_at < now() - interval '30 days';
    get diagnostics v_count = row_count;
    return v_count;
end;
$$;

revoke all on function app_private.purge_deleted_units() from public, anon, authenticated;

-- Todo dia às 06:30 UTC (02:30 em Manaus). O Postgres do CI não tem pg_cron: lá só pula.
do $$
begin
    if exists (select 1 from pg_catalog.pg_available_extensions where name = 'pg_cron') then
        create extension if not exists pg_cron with schema pg_catalog;
        perform cron.schedule('lexhub-purge-deleted-units', '30 6 * * *',
                              'select app_private.purge_deleted_units()');
    end if;
end;
$$;

-- ---------------------------------------------------------------------------
-- 4. Encerrar organização (só Owner/Desenvolvedor da LexGroup e equipe RA)
-- ---------------------------------------------------------------------------
create function app_private.require_org_to_close(p_org text) returns app.organizations
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org app.organizations;
begin
    if not app_private.can_see_clients() then
        raise exception using errcode = '42501', message = 'Só Owner ou Desenvolvedor da LexGroup encerram organizações.';
    end if;
    select o.* into v_org from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    if v_org.id is null then
        raise exception using errcode = 'P0001', message = 'Organização não encontrada.';
    end if;
    return v_org;
end;
$$;

revoke all on function app_private.require_org_to_close(text) from public, anon, authenticated;

create function app_private.org_closure_json(p_org uuid) returns jsonb
language sql stable security definer
set search_path = ''
as $$
    select jsonb_build_object(
        'slug', o.slug,
        'name', o.name,
        'units', (select count(*) from app.units u where u.org_id = o.id and u.active)::int,
        'members', (select count(*) from app.memberships m where m.org_id = o.id)::int,
        'sources', (select count(*) from app.data_sources ds where ds.org_id = o.id)::int,
        'locked', o.platform_owner
    )
    from app.organizations o
    where o.id = p_org;
$$;

revoke all on function app_private.org_closure_json(uuid) from public, anon, authenticated;

create function api.org_closure_impact(p_org text) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org app.organizations := app_private.require_org_to_close(p_org);
begin
    return app_private.org_closure_json(v_org.id);
end;
$$;

create function api.close_organization(p_org text, p_confirm text) returns void
language plpgsql volatile security definer
set search_path = ''
as $$
declare
    v_org    app.organizations := app_private.require_org_to_close(p_org);
    v_impact jsonb := app_private.org_closure_json(v_org.id);
    v_keys   text[];
begin
    if v_org.platform_owner then
        raise exception using errcode = 'P0001', message = 'A organização dona da plataforma não pode ser encerrada.';
    end if;
    if lower(trim(coalesce(p_confirm, ''))) <> lower(trim(v_org.name)) then
        raise exception using errcode = 'P0001', message = 'Digite o nome da organização para confirmar.';
    end if;

    -- As fontes saem inteiras (senhas e log); as unidades ficam, só que a organização some das telas.
    select coalesce(array_agg(ds.key), '{}') into v_keys
    from app.data_sources ds where ds.org_id = v_org.id;
    delete from app.unit_source_refs r using app.units u where u.id = r.unit_id and u.org_id = v_org.id;
    delete from app.data_sources where org_id = v_org.id;
    -- Só as chaves que mais ninguém usa saem do catálogo dashboard -> fonte (lexpre/lexflow ficam).
    delete from app.dashboard_sources d where d.source_key = any (v_keys)
        and not exists (select 1 from app.data_sources o where o.key = d.source_key);

    update app.organizations
    set active = false, closed_at = now(), closed_by = auth.uid(), updated_at = now()
    where id = v_org.id;

    -- Na auditoria da LexGroup (quem encerrou), que é quem ainda vê a tela.
    insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
    values (app_private.home_org_id(), auth.uid(), 'org.closed', 'organization', v_org.id::text,
            jsonb_build_object('slug', v_org.slug, 'name', v_org.name, 'units', v_impact -> 'units',
                               'members', v_impact -> 'members', 'sources', v_impact -> 'sources'));
end;
$$;

revoke all on function api.unit_deletion_impact(text, text) from public, anon;
revoke all on function api.delete_unit(text, text, text) from public, anon;
revoke all on function api.org_closure_impact(text) from public, anon;
revoke all on function api.close_organization(text, text) from public, anon;
grant execute on function api.unit_deletion_impact(text, text) to authenticated;
grant execute on function api.delete_unit(text, text, text) to authenticated;
grant execute on function api.org_closure_impact(text) to authenticated;
grant execute on function api.close_organization(text, text) to authenticated;

-- ---------------------------------------------------------------------------
-- 5. api.list_sources: mesmo corpo de 20261117100000_conectar_fonte.sql + orgName (o título da tela)
-- ---------------------------------------------------------------------------
create or replace function api.list_sources(p_org text) returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
declare
    v_org   uuid;
    v_name  text;
    v_scope uuid[];
begin
    select o.id, o.name into v_org, v_name from app.organizations o where o.slug = lower(trim(p_org)) and o.active;
    v_scope := case when v_org is null then '{}'::uuid[] else app_private.sources_scope(v_org) end;
    if cardinality(v_scope) = 0 then
        raise exception using errcode = '42501', message = 'Você não vê as fontes desta organização.';
    end if;

    return jsonb_build_object(
        'orgName', v_name,
        'syncEveryMin', app_private.sync_every_min(),
        'unitLimit', null, -- o plano ainda não guarda limite de unidades
        'canManageUnits', v_org = any (app_private.my_org_ids_with('units.manage')),
        'canManageSources', app_private.is_source_admin(auth.uid()),
        'units', coalesce((
            select jsonb_agg(app_private.unit_sources_json(u.id) order by u.name)
            from app.units u
            where u.id = any (v_scope)
        ), '[]'::jsonb)
    );
end;
$$;

-- ---------------------------------------------------------------------------
-- 6. api.list_clients: mesmo corpo de 20261116100000_plano_clientes.sql + units e canClose
-- ---------------------------------------------------------------------------
create or replace function api.list_clients() returns jsonb
language plpgsql stable security definer
set search_path = ''
as $$
begin
    if not app_private.can_see_clients() then
        raise exception using errcode = '42501', message = 'Só Owner ou Desenvolvedor da LexGroup veem os clientes.';
    end if;

    return (
        select jsonb_build_object(
            'clients', coalesce(jsonb_agg(c.item order by c.name), '[]'::jsonb),
            -- Receita: soma dos planos ativos com preço. Algum plano ativo sem preço = ainda não dá para somar.
            'monthlyRevenue', case
                when bool_or(c.paying and c.price is null) then null
                when bool_or(c.paying) then sum(c.price) filter (where c.paying)
            end
        )
        from (
            select o.name,
                   s.plan_key is not null and s.status = 'active' as paying,
                   s.monthly_price as price,
                   jsonb_build_object(
                       'slug', o.slug,
                       'name', o.name,
                       'sub', u.units || case when u.units = 1 then ' unidade' else ' unidades' end
                              || ' · cliente desde ' || to_char(o.created_at, 'MM/YYYY'),
                       'plan', coalesce(s.plan_key, 'onboarding'),
                       'seats', jsonb_build_object('used', u.seats, 'total', s.seat_limit),
                       'failingSources', app_private.failing_sources_of(o.id),
                       'billing', case
                           when s.status = 'past_due'
                             or exists (select 1 from app.invoices i where i.org_id = o.id and i.status = 'overdue')
                               then 'overdue'
                           when s.plan_key is null then 'onboarding_paid'
                           else 'ok'
                       end,
                       'units', coalesce((
                           select jsonb_agg(jsonb_build_object('code', un.code, 'name', un.name) order by un.name)
                           from app.units un
                           where un.org_id = o.id and un.active
                       ), '[]'::jsonb),
                       'canClose', not o.platform_owner
                   ) as item
            from app.organizations o
            cross join lateral app_private.subscription_of(o.id) s
            cross join lateral app_private.usage_of(o.id) u
            where o.active
        ) c
    );
end;
$$;

-- =============================================================================
-- Rollback:
-- (recriar api.list_clients com o corpo de 20261116100000_plano_clientes.sql)
-- (recriar api.list_sources com o corpo de 20261117100000_conectar_fonte.sql)
-- select cron.unschedule('lexhub-purge-deleted-units');
-- drop function api.close_organization(text, text);
-- drop function api.org_closure_impact(text);
-- drop function app_private.org_closure_json(uuid);
-- drop function app_private.require_org_to_close(text);
-- drop function app_private.purge_deleted_units();
-- drop function api.delete_unit(text, text, text);
-- drop function api.unit_deletion_impact(text, text);
-- drop function app_private.require_unit_to_delete(text, text);
-- drop function app_private.unit_deletion_json(uuid);
-- drop trigger units_block_locked_delete on app.units;
-- drop function app_private.block_locked_unit_delete();
-- alter table app.organizations drop column closed_by, drop column closed_at;
-- alter table app.units drop column deletion_locked, drop column deleted_by, drop column deleted_at;
-- =============================================================================
