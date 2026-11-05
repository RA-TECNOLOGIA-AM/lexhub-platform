-- =============================================================================
-- SÓ PARA O CI: confere o resultado de supabase/scripts/import_v1.sql sobre v1_fixture.sql
-- =============================================================================
do $$
declare
    org uuid := (select id from app.organizations where slug = 'lexgroup');
    ng  uuid := (select id from app.units where org_id = org and code = 'NG');
    la  uuid := (select id from app.units where org_id = org and code = 'LA');
begin
    assert org is not null, 'organização lexgroup não criada';
    assert (select count(*) from app.organizations) = 1, 'importação duplicou organização';

    assert (select string_agg(code, ',' order by code) from app.units) = 'C5,LA,MT,NG,RJ',
        'códigos de unidade errados: ' || (select string_agg(code, ',' order by code) from app.units);
    assert not (select active from app.units where code = 'MT'), 'MT deveria estar inativa';

    assert (select count(*) from app.memberships) = 8, 'deveria ter 8 membros';
    assert (select email from app.memberships where full_name = 'Pendencias NG') = 'pendencias.ng@x.test',
        'e-mail deveria ser normalizado para minúsculas';
    assert (select role_key from app.memberships where email = 'dev@x.test') = 'admin', 'Desenvolvedor -> admin';
    assert (select role_key from app.memberships where email = 'gestor.ng@x.test') = 'gestor', 'Gestor -> gestor';
    assert (select role_key from app.memberships where email = 'protocolo.ng@x.test') = 'colaborador', 'Colaborador -> colaborador';
    assert (select status from app.memberships where email = 'inativo.ng@x.test') = 'disabled', 'inativo -> disabled';

    assert (select count(*) from app.membership_units mu join app.memberships m on m.id = mu.membership_id
            where m.email = 'pendencias.ng@x.test') = 2, 'companhia extra (usuario_companhia) não importada';
    assert (select count(*) from app.access_rules) = 2, 'deveria ter 2 regras de acesso na NG';

    -- acesso final
    assert app_private.dashboard_scope('a0000000-0000-0000-0000-000000000001', ng, 'pendencias') is not null,    'dev vê tudo';
    assert app_private.dashboard_scope('a0000000-0000-0000-0000-000000000002', ng, 'pendencias') is not null,    'gestor NG vê tudo da NG';
    assert app_private.dashboard_scope('a0000000-0000-0000-0000-000000000003', ng, 'protocolo-lexpre') is not null, 'Protocolo vê protocolo';
    assert app_private.dashboard_scope('a0000000-0000-0000-0000-000000000003', ng, 'pendencias') is null, 'Protocolo não vê pendências';
    assert app_private.dashboard_scope('a0000000-0000-0000-0000-000000000004', ng, 'pendencias') is not null,    'Pendências (NG extra) vê pendências';
    assert app_private.dashboard_scope('a0000000-0000-0000-0000-000000000005', ng, 'protocolo-lexpre') is null, 'Comercial não vê';
    assert app_private.dashboard_scope('a0000000-0000-0000-0000-000000000006', ng, 'protocolo-lexpre') is null, 'inativo não vê';
    assert app_private.dashboard_scope('a0000000-0000-0000-0000-000000000007', la, 'protocolo-lexpre') is null, 'LA não tem dashboards no MVP';
    assert app_private.dashboard_scope('a0000000-0000-0000-0000-000000000008', ng, 'protocolo-lexpre') is null, 'gestor sem unidade não vê';

    raise notice 'OK: importação V1 -> app';
end $$;
