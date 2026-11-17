-- =============================================================================
-- Nomes da Execução no catálogo, como na v1: "Execução Condenação" (antes: "Execução") e "Execução Acordos"
-- (antes: "Acordos"). A key (execucao, acordos), as permissões e o resto do cadastro não mudam.
-- =============================================================================

update app.dashboard_catalog
   set name = 'Execução Condenação',
       description = 'Processos em execução da condenação: entradas, saídas, valores e alvarás.'
 where key = 'execucao';

update app.dashboard_catalog
   set name = 'Execução Acordos',
       description = 'Acordos em execução: fechamento, entradas, pagamentos e valores.'
 where key = 'acordos';

-- =============================================================================
-- Rollback:
-- update app.dashboard_catalog set name = 'Execução', description = 'Processos em execução e valores.'
--  where key = 'execucao';
-- update app.dashboard_catalog set name = 'Acordos', description = 'Acordos fechados e valores.'
--  where key = 'acordos';
-- =============================================================================
