-- =============================================================================
-- Unidade -> LexFlow (app.unit_source_refs, source = 'lexflow').
--
-- No LexFlow a v1 não filtra por id de escritório: cada unidade tem a sua rota e as suas queries
-- (ex.: Execução /execucao para NG, /execucao_LA, /execucao_RJ). O ref guarda o sufixo da unidade
-- na v1 ("NG", "LA", "RJ"); cada módulo da V2 escolhe o dashboard da v1 por ele
-- (app/dashboards/execucao.py, acordos.py, recursal.py).
-- =============================================================================

insert into app.unit_source_refs (unit_id, source, ref)
select u.id, 'lexflow', v.ref
  from app.units u
  join app.organizations o on o.id = u.org_id and o.slug = 'lexgroup'
  join (values ('NG', 'NG'), ('LA', 'LA'), ('RJ', 'RJ')) as v (code, ref) on v.code = u.code
on conflict do nothing;
