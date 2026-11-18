-- =============================================================================
-- Cada setor (equipe) vê os dashboards do seu trabalho: os Colaboradores passam a ver os dashboards
-- de acordo com o setor em que estão (app.membership_teams), pela regra do app_private.dashboard_scope.
--
-- Antes só Diretoria, Controladoria e o Comercial da LAAM tinham regras. Mapa combinado em 18/11/2026:
--   Comercial                        -> comercial, comercial-lexpre, comissao, comissao-lexpre, marketing, nps
--   Protocolo                        -> protocolo, protocolo-lexpre, pre-protocolo
--   Pendências Iniciais/Intermediárias -> pendencias, pendencias-lexpre
--   Organização de Documentos        -> org-documentos, org-documentos-lexpre
--   Peticionamento                   -> peticionamento, peticionamento-lexpre
--   Execução                         -> execucao, acordos, execucao-estrategico
--   Análise de Recurso               -> recursal, julgados-acordaos
--   Financeiro                       -> financeiro-estrategico, meta-anual
--   Tecnologia                       -> tickets
-- Sem dashboard por enquanto: Acompanhamento Processual, Publicações, Réplicas, Emendas e Manifestações, RH.
--
-- Só cria a regra onde o dashboard está ligado na unidade do setor (app.org_dashboards) e com escopo 'all',
-- como as regras que já existem. Regras já existentes ficam como estão (on conflict do nothing).
-- Gestor/Controller/Desenvolvedor não mudam: já veem tudo pelas permissões do cargo.
-- =============================================================================

with mapa (setor, dashboard_key) as (
    values
        ('Comercial', 'comercial'),
        ('Comercial', 'comercial-lexpre'),
        ('Comercial', 'comissao'),
        ('Comercial', 'comissao-lexpre'),
        ('Comercial', 'marketing'),
        ('Comercial', 'nps'),
        ('Protocolo', 'protocolo'),
        ('Protocolo', 'protocolo-lexpre'),
        ('Protocolo', 'pre-protocolo'),
        ('Pendências Iniciais', 'pendencias'),
        ('Pendências Iniciais', 'pendencias-lexpre'),
        ('Pendências Intermediárias', 'pendencias'),
        ('Pendências Intermediárias', 'pendencias-lexpre'),
        ('Organização de Documentos', 'org-documentos'),
        ('Organização de Documentos', 'org-documentos-lexpre'),
        ('Peticionamento', 'peticionamento'),
        ('Peticionamento', 'peticionamento-lexpre'),
        ('Execução', 'execucao'),
        ('Execução', 'acordos'),
        ('Execução', 'execucao-estrategico'),
        ('Análise de Recurso', 'recursal'),
        ('Análise de Recurso', 'julgados-acordaos'),
        ('Financeiro', 'financeiro-estrategico'),
        ('Financeiro', 'meta-anual'),
        ('Tecnologia', 'tickets')
)
insert into app.access_rules (org_id, team_id, dashboard_key, scope)
select t.org_id, t.id, m.dashboard_key, 'all'
  from app.teams t
  join app.organizations o on o.id = t.org_id and o.slug = 'lexgroup'
  join mapa m on m.setor = t.name
  join app.org_dashboards od on od.unit_id = t.unit_id
                            and od.dashboard_key = m.dashboard_key
                            and od.enabled
 where t.active
on conflict (team_id, dashboard_key) do nothing;

-- Desfazer (só as regras criadas aqui; as da Diretoria/Controladoria e do Comercial LAAM já existiam):
-- delete from app.access_rules r using app.teams t
--  where t.id = r.team_id and r.created_at::date = '2026-11-18'
--    and t.name in ('Comercial', 'Protocolo', 'Pendências Iniciais', 'Pendências Intermediárias',
--                   'Organização de Documentos', 'Peticionamento', 'Execução', 'Análise de Recurso',
--                   'Financeiro', 'Tecnologia');
