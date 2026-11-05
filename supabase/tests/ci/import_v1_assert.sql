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

    assert (select count(*) from app.members) = 8, 'deveria ter 8 membros';
    assert (select email from app.members where full_name = 'Pendencias NG') = 'pendencias.ng@x.test',
        'e-mail deveria ser normalizado para minúsculas';
    assert (select role from app.members where email = 'dev@x.test') = 'admin', 'Desenvolvedor -> admin';
    assert (select status from app.members where email = 'inativo.ng@x.test') = 'disabled', 'inativo -> disabled';

    assert (select count(*) from app.unit_members um join app.members m on m.id = um.member_id
            where m.email = 'pendencias.ng@x.test') = 2, 'companhia extra (usuario_companhia) não importada';
    assert (select um.role from app.unit_members um join app.members m on m.id = um.member_id
            where m.email = 'gestor.ng@x.test' and um.unit_id = ng) = 'manager', 'Gestor -> manager';

    -- acesso final
    assert app.user_can_view_dashboard('a0000000-0000-0000-0000-000000000001', ng, 'pendencias'),    'dev vê tudo';
    assert app.user_can_view_dashboard('a0000000-0000-0000-0000-000000000002', ng, 'pendencias'),    'gestor NG vê tudo da NG';
    assert app.user_can_view_dashboard('a0000000-0000-0000-0000-000000000003', ng, 'protocolo-lexpre'), 'Protocolo vê protocolo';
    assert not app.user_can_view_dashboard('a0000000-0000-0000-0000-000000000003', ng, 'pendencias'), 'Protocolo não vê pendências';
    assert app.user_can_view_dashboard('a0000000-0000-0000-0000-000000000004', ng, 'pendencias'),    'Pendências (NG extra) vê pendências';
    assert not app.user_can_view_dashboard('a0000000-0000-0000-0000-000000000005', ng, 'protocolo-lexpre'), 'Comercial não vê';
    assert not app.user_can_view_dashboard('a0000000-0000-0000-0000-000000000006', ng, 'protocolo-lexpre'), 'inativo não vê';
    assert not app.user_can_view_dashboard('a0000000-0000-0000-0000-000000000007', la, 'protocolo-lexpre'), 'LA não tem dashboards no MVP';
    assert not app.user_can_view_dashboard('a0000000-0000-0000-0000-000000000008', ng, 'protocolo-lexpre'), 'gestor sem unidade não vê';

    raise notice 'OK: importação V1 -> app';
end $$;
