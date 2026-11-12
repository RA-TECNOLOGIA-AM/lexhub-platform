-- =============================================================================
-- Abre os dashboards do banco NG que ganharam o cálculo da v1 (branch feat/ativar-cards):
-- Comercial, Comissão Comercial, Marketing, Protocolo, Pendências, Organização de Documentos e
-- Peticionamento (todos com source = 'NG' no catálogo).
--
-- Mesmo molde de 20261111180000_abrir_dashboards_lexpre.sql e 20261112100000_abrir_dashboards_lexflow.sql:
--   * unidade -> banco NG (app.unit_source_refs, source = 'ng'): o ref é o sufixo da unidade na v1
--     ("NG", "RJ"). Na v1 as duas saem do mesmo banco NG (as rotas _RJ ficam só com o RJ). A LA tem as
--     suas rotas no banco LAADV e fica de fora; o Marketing NG só existe para a NG;
--   * status = 'available' (sai de "Chegando na V2");
--   * ligado nas unidades NG e RJ em que o Protocolo (LexPre) está ligado (Marketing: só NG);
--   * mesmas regras de acesso por equipe do Protocolo (LexPre) nessas unidades (hoje: Controladoria e
--     Diretoria). Owner/admin (Desenvolvedor) já veem tudo pela permissão org.dashboards.all.
-- Outras equipes (ex.: Comercial na Comissão) entram depois, quando o analista validar os números e a
-- gestão definir quem vê cada um.
-- =============================================================================

insert into app.unit_source_refs (unit_id, source, ref)
select u.id, 'ng', v.ref
  from app.units u
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
  join (values ('NG', 'NG'), ('RJ', 'RJ')) as v (code, ref) on v.code = u.code
on conflict do nothing;

update app.dashboard_catalog
   set status = 'available'
 where key in ('comercial', 'comissao', 'marketing', 'protocolo', 'pendencias', 'org-documentos', 'peticionamento');

-- Dashboard -> unidades em que abre.
with alvo (dashboard_key, unit_code) as (
    select k.key, u.code
      from (values ('comercial'), ('comissao'), ('protocolo'), ('pendencias'), ('org-documentos'),
                   ('peticionamento')) as k(key)
     cross join (values ('NG'), ('RJ')) as u(code)
    union all
    select 'marketing', 'NG'
)
insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select od.org_id, od.unit_id, a.dashboard_key, od.enabled
  from app.org_dashboards od
  join app.units u on u.id = od.unit_id
  join alvo a on a.unit_code = u.code
 where od.dashboard_key = 'protocolo-lexpre'
on conflict do nothing;

with alvo (dashboard_key, unit_code) as (
    select k.key, u.code
      from (values ('comercial'), ('comissao'), ('protocolo'), ('pendencias'), ('org-documentos'),
                   ('peticionamento')) as k(key)
     cross join (values ('NG'), ('RJ')) as u(code)
    union all
    select 'marketing', 'NG'
)
insert into app.access_rules (org_id, team_id, dashboard_key, scope, created_by)
select r.org_id, r.team_id, a.dashboard_key, r.scope, r.created_by
  from app.access_rules r
  join app.teams t on t.id = r.team_id
  join app.units u on u.id = t.unit_id
  join alvo a on a.unit_code = u.code
 where r.dashboard_key = 'protocolo-lexpre'
on conflict (team_id, dashboard_key) do nothing;
