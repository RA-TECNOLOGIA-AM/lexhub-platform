-- =============================================================================
-- Abre os dashboards LexPre que ganharam o cálculo da v1 (branch feat/dashboards-lexpre-v1):
-- Comercial, Comissão Comercial, Organização de Documentos e Peticionamento (LexPre).
--
-- Mesmo molde de "pendencias-lexpre" (20261111130000_catalogo_pares_ng_lexpre.sql):
--   * status = 'available' (sai de "Chegando na V2");
--   * ligado nas mesmas unidades em que o Protocolo (LexPre) está ligado (hoje: NG, o piloto);
--   * mesmas regras de acesso por equipe do Protocolo (LexPre) (hoje: Controladoria e Diretoria).
-- Owner/admin (Desenvolvedor) já veem tudo pela permissão org.dashboards.all.
-- Outras equipes (ex.: Comercial na Comissão, Organização de Documentos no Org. Doc) entram
-- depois, quando o analista validar os números e a gestão definir quem vê cada um.
-- Marketing (LexPre) continua "Em breve": usa também o banco NG (facebook_ads).
-- =============================================================================

update app.dashboard_catalog
   set status = 'available'
 where key in ('comercial-lexpre', 'comissao-lexpre', 'org-documentos-lexpre', 'peticionamento-lexpre');

insert into app.org_dashboards (org_id, unit_id, dashboard_key, enabled)
select od.org_id, od.unit_id, k.key, od.enabled
  from app.org_dashboards od
 cross join (values ('comercial-lexpre'), ('comissao-lexpre'), ('org-documentos-lexpre'), ('peticionamento-lexpre')) as k(key)
 where od.dashboard_key = 'protocolo-lexpre'
on conflict do nothing;

insert into app.access_rules (org_id, team_id, dashboard_key, scope, created_by)
select r.org_id, r.team_id, k.key, r.scope, r.created_by
  from app.access_rules r
 cross join (values ('comercial-lexpre'), ('comissao-lexpre'), ('org-documentos-lexpre'), ('peticionamento-lexpre')) as k(key)
 where r.dashboard_key = 'protocolo-lexpre'
on conflict (team_id, dashboard_key) do nothing;
