-- =============================================================================
-- CÓPIA V1 -> STAGING  |  PASSO 2 de 2: DADOS
--
-- Rode na MAIN (produção), DEPOIS de ter rodado no staging o script do passo 1.
-- Não altera nenhum dado: só cria uma função temporária (some sozinha no fim)
-- para ler as tabelas. O resultado é UMA célula com um script SQL: copie e
-- rode na branch STAGING.
--
-- Tabelas que NÃO são copiadas (lista "excluir" abaixo; edite se quiser):
--   segredos:   conta_azul_config, conta_azul_tokens, conta_azul_cron, api_refresh_token
--   financeiro: conta_azul_contas_pagar, conta_azul_contas_receber, conta_azul_sync_runs
--   logs:       usuario_login_historico
-- Elas continuam existindo no staging (passo 1), só que vazias.
--
-- Usuários do login (auth.users): copia só id, e-mail e datas, SEM senha.
-- Ninguém consegue logar no staging com a senha da produção.
-- =============================================================================
create or replace function pg_temp.dados_json(p_tabela text, p_colunas text)
returns text
language plpgsql
as $$
declare
    resultado text;
begin
    execute format(
        'select coalesce(json_agg(x), ''[]'')::text from (select %s from public.%I) x',
        p_colunas, p_tabela
    ) into resultado;
    return resultado;
end;
$$;

with recursive
excluir (tabela) as (
    values
        ('conta_azul_config'),
        ('conta_azul_tokens'),
        ('conta_azul_cron'),
        ('api_refresh_token'),
        ('conta_azul_contas_pagar'),
        ('conta_azul_contas_receber'),
        ('conta_azul_sync_runs'),
        ('usuario_login_historico')
),
tabs as (
    select c.oid, c.relname
    from pg_class c
    join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public'
      and c.relkind in ('r', 'p')
      and c.relname not in (select tabela from excluir)
      and not exists (select 1 from pg_depend d where d.objid = c.oid and d.deptype = 'e')
),
-- ordem de carga: quem é referenciado entra antes de quem referencia
fks as (
    select distinct c.conrelid as filho, c.confrelid as pai
    from pg_constraint c
    join tabs t1 on t1.oid = c.conrelid
    join tabs t2 on t2.oid = c.confrelid
    where c.contype = 'f' and c.conrelid <> c.confrelid
),
nivel (oid, n, caminho) as (
    select t.oid, 0, array[t.oid] from tabs t
    union all
    select f.filho, nv.n + 1, nv.caminho || f.filho
    from nivel nv
    join fks f on f.pai = nv.oid
    where not f.filho = any (nv.caminho)
),
ordem as (
    select oid, max(n) as n from nivel group by oid
),
colunas as (
    select
        t.oid,
        t.relname,
        string_agg(quote_ident(a.attname), ', ' order by a.attnum) as lista
    from tabs t
    join pg_attribute a on a.attrelid = t.oid and a.attnum > 0 and not a.attisdropped and a.attgenerated = ''
    group by t.oid, t.relname
),
inserts as (
    select string_agg(
        format(
            E'insert into public.%I (%s) overriding system value\nselect %s from json_populate_recordset(null::public.%I, %L);',
            c.relname, c.lista, c.lista, c.relname, pg_temp.dados_json(c.relname, c.lista)),
        E'\n\n' order by o.n, c.relname) as sql
    from colunas c
    join ordem o on o.oid = c.oid
),
contadores as (
    select string_agg(
        format('select setval(pg_get_serial_sequence(%L, %L), coalesce((select max(%I) from public.%I), 0) + 1, false);',
            'public.' || quote_ident(t.relname), a.attname, a.attname, t.relname),
        E'\n' order by t.relname, a.attname) as sql
    from tabs t
    join pg_attribute a on a.attrelid = t.oid and a.attnum > 0 and not a.attisdropped
    where pg_get_serial_sequence('public.' || quote_ident(t.relname), a.attname) is not null
),
usuarios as (
    select format(
        E'insert into auth.users (id, email, aud, role, created_at, updated_at)\nselect id, email, aud, role, created_at, updated_at\nfrom json_populate_recordset(null::auth.users, %L)\non conflict (id) do nothing;',
        coalesce(json_agg(json_build_object(
            'id', u.id, 'email', u.email, 'aud', u.aud, 'role', u.role,
            'created_at', u.created_at, 'updated_at', u.updated_at)), '[]')::text) as sql
    from auth.users u
),
relatorio as (
    select string_agg(
        format('select %L as tabela, (select count(*) from public.%I) as linhas', relname, relname),
        E'\nunion all ' order by relname) as sql
    from tabs
)
select concat_ws(E'\n\n',
    '-- ===== Dados da V1 gerados em ' || now()::text || ' =====',
    '-- Rodar SOMENTE na branch STAGING, depois do script de estrutura.',
    '-- Não copiadas: ' || (select string_agg(tabela, ', ' order by tabela) from excluir),
    'begin;',
    $guard$do $trava$
declare
    tem_dados boolean;
begin
    if to_regclass('public.usuario') is null then
        raise exception 'PARADO: public.usuario não existe. Rode antes o script de ESTRUTURA no staging.';
    end if;
    execute 'select exists (select 1 from public.usuario)' into tem_dados;
    if tem_dados then
        raise exception 'PARADO: public.usuario já tem dados. Isto parece a PRODUÇÃO (ou a cópia já foi feita). Para refazer no staging, rode de novo o script de estrutura.';
    end if;
end $trava$;$guard$,
    '-- usuários do login (sem senha)',
    (select sql from usuarios),
    '-- tabelas',
    (select sql from inserts),
    '-- contadores (ids automáticos continuam do maior valor copiado)',
    (select sql from contadores),
    '-- relatório',
    (select sql from relatorio) || E'\norder by 1;',
    'commit;'
) as script;
