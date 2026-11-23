-- =============================================================================
-- Reabrir organização encerrada (30 dias) e apagar de vez depois do prazo
--
-- 1) api.list_clients ganha closed: as organizações encerradas há menos de 30 dias, com quando, quem
--    encerrou e quando somem de vez. Mesmo corpo de 20261123140000_excluir_unidade_organizacao.sql + closed.
-- 2) api.reopen_organization: volta a organização (active = true) com unidades e membros como estavam (os
--    membros voltam a entrar; desativá-los deixaria o cliente sem ninguém para reativar, porque a plataforma
--    não gere membros). As fontes não voltam: foram apagadas com as senhas no encerramento.
--    Só Owner/Desenvolvedor da LexGroup e equipe RA. Passou de 30 dias = recusa. Auditoria: 'org.reopened'
--    na LexGroup (como o 'org.closed').
-- 3) Depois de 30 dias, app_private.purge_closed_orgs (pg_cron, diário) apaga a organização de vez: unidades,
--    membros, convites, notificações, plano e faturas (cascade) e a auditoria dela. Fica só um 'org.purged'
--    na auditoria da LexGroup (nome, slug e quando foi encerrada). As contas de login (auth.users) ficam:
--    a pessoa pode ser de outra organização; sem nenhuma, não entra em nada.
--    A auditoria continua só inserção para todo o resto: a trigger só deixa apagar quando a própria limpeza
--    liga app.audit_purge na transação (set_config local), rodando como dona das tabelas.
-- Teste: supabase/tests/reabrir_organizacao_test.sql (termina com rollback).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Auditoria: só inserção, salvo a limpeza de organização encerrada
-- ---------------------------------------------------------------------------
create or replace function app.audit_log_immutable() returns trigger
language plpgsql
set search_path = ''
as $$
begin
    -- Única exceção: app_private.purge_closed_orgs apagando a auditoria de uma organização encerrada há
    -- mais de 30 dias (ela liga app.audit_purge só dentro da transação dela).
    -- current_user = postgres: a limpeza é security definer da dona; o service_role (que tem DELETE na
    -- tabela) não passa nem ligando a variável.
    if tg_op = 'DELETE' and current_setting('app.audit_purge', true) = 'on' and current_user = 'postgres' then
        return old;
    end if;
    raise exception 'app.audit_log é somente inserção';
end;
$$;

-- ---------------------------------------------------------------------------
-- 2. Clientes: as encerradas que ainda dá para reabrir
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
            end,
            'closed', coalesce((
                select jsonb_agg(jsonb_build_object(
                           'slug', o.slug,
                           'name', o.name,
                           'closedAt', o.closed_at,
                           'purgeAt', o.closed_at + interval '30 days',
                           'closedBy', au.email
                       ) order by o.closed_at desc)
                from app.organizations o
                left join auth.users au on au.id = o.closed_by
                where not o.active and o.closed_at is not null and o.closed_at > now() - interval '30 days'
            ), '[]'::jsonb)
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

-- ---------------------------------------------------------------------------
-- 3. Reabrir
-- ---------------------------------------------------------------------------
create function api.reopen_organization(p_org text) returns void
language plpgsql volatile security definer
set search_path = ''
as $$
declare
    v_org app.organizations;
begin
    if not app_private.can_see_clients() then
        raise exception using errcode = '42501', message = 'Só Owner ou Desenvolvedor da LexGroup reabrem organizações.';
    end if;
    select o.* into v_org from app.organizations o
    where o.slug = lower(trim(p_org)) and not o.active and o.closed_at is not null
    for update;
    if v_org.id is null then
        raise exception using errcode = 'P0001', message = 'Organização encerrada não encontrada.';
    end if;
    if v_org.closed_at <= now() - interval '30 days' then
        raise exception using errcode = 'P0001',
            message = format('O prazo de 30 dias para reabrir %s já passou.', v_org.name);
    end if;

    update app.organizations
    set active = true, closed_at = null, closed_by = null, updated_at = now()
    where id = v_org.id;

    insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
    values (app_private.home_org_id(), auth.uid(), 'org.reopened', 'organization', v_org.id::text,
            jsonb_build_object('slug', v_org.slug, 'name', v_org.name, 'closedAt', v_org.closed_at));
end;
$$;

revoke all on function api.reopen_organization(text) from public, anon;
grant execute on function api.reopen_organization(text) to authenticated;

-- ---------------------------------------------------------------------------
-- 4. Apagar de vez depois de 30 dias
-- ---------------------------------------------------------------------------
create function app_private.purge_closed_orgs() returns integer
language plpgsql volatile security definer
set search_path = ''
as $$
declare
    v_org   record;
    v_count integer := 0;
begin
    for v_org in
        select o.id, o.slug, o.name, o.closed_at from app.organizations o
        where not o.active and not o.platform_owner
          and o.closed_at is not null and o.closed_at < now() - interval '30 days'
        for update
    loop
        insert into app.audit_log (org_id, actor_user_id, action, target_type, target_id, metadata)
        values (app_private.home_org_id(), null, 'org.purged', 'organization', v_org.id::text,
                jsonb_build_object('slug', v_org.slug, 'name', v_org.name, 'closedAt', v_org.closed_at));

        perform set_config('app.audit_purge', 'on', true);
        delete from app.audit_log where org_id = v_org.id;
        perform set_config('app.audit_purge', 'off', true);

        delete from app.organizations where id = v_org.id; -- cascade: unidades, membros, plano, faturas...
        v_count := v_count + 1;
    end loop;
    return v_count;
end;
$$;

revoke all on function app_private.purge_closed_orgs() from public, anon, authenticated;

-- Todo dia às 06:40 UTC (02:40 em Manaus), depois da limpeza de unidades. O Postgres do CI não tem pg_cron.
do $$
begin
    if exists (select 1 from pg_catalog.pg_available_extensions where name = 'pg_cron') then
        create extension if not exists pg_cron with schema pg_catalog;
        perform cron.schedule('lexhub-purge-closed-orgs', '40 6 * * *', 'select app_private.purge_closed_orgs()');
    end if;
end;
$$;

-- =============================================================================
-- Rollback:
-- select cron.unschedule('lexhub-purge-closed-orgs');
-- drop function app_private.purge_closed_orgs();
-- drop function api.reopen_organization(text);
-- (recriar api.list_clients com o corpo de 20261123140000_excluir_unidade_organizacao.sql)
-- (recriar app.audit_log_immutable com o corpo de 20261105120000_app_core.sql)
-- =============================================================================
