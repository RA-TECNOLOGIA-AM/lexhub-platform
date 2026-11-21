-- Usuário só de leitura do LexHub no banco do LexFlow (Supabase "lexflow").
--
-- Por quê: hoje a API do LexHub entra no banco de produção do LexFlow com o usuário `postgres`, que pode
-- alterar e apagar qualquer coisa, e o tráfego dela se mistura com o de qualquer outro cliente `postgres`
-- (SQL Editor, dumps, scripts) no pg_stat_statements, o que atrapalha medir o egress de cada um.
-- Com um usuário próprio: só SELECT, limite de tempo por consulta e o consumo do LexHub separado.
--
-- NÃO é aplicado por deploy. Quem cuida do banco do LexFlow roda no SQL Editor do Supabase, como postgres,
-- depois troca DB_LEXFLOW_USER / DB_LEXFLOW_PASSWORD no secret da stack do LexHub e acompanha um deploy.
--
-- Atenção, RLS: todas as tabelas do public têm RLS ligado. O LexHub lê os processos de todos os escritórios,
-- então o usuário precisa de BYPASSRLS (como o postgres tem hoje). Se o Supabase recusar o BYPASSRLS no
-- passo 1, NÃO siga: o usuário veria zero linhas e os dashboards zerariam. Nesse caso, fale com o suporte
-- do Supabase ou mantenha o postgres por enquanto.

-- 1. O usuário (troque a senha; ela vai só para o secret da stack).
create role lexhub_leitor login password 'TROQUE-ESTA-SENHA' bypassrls;

-- 2. Só leitura e com limites, valendo para toda sessão dele.
alter role lexhub_leitor set default_transaction_read_only = on;
alter role lexhub_leitor set statement_timeout = '120s';
alter role lexhub_leitor set idle_in_transaction_session_timeout = '60s';

-- 3. SELECT no que existe e no que for criado pelo postgres daqui em diante.
grant usage on schema public to lexhub_leitor;
grant select on all tables in schema public to lexhub_leitor;
alter default privileges for role postgres in schema public grant select on tables to lexhub_leitor;

-- 4. Conferir antes de trocar o secret (cada linha deve ser > 0, igual ao que o postgres vê):
--    set role lexhub_leitor;
--    select count(*) from public.processo;
--    select count(*) from public.agendamento;
--    select count(*) from public.log_fase_processual;
--    reset role;
--
-- 5. Na stack do LexHub, pelo pooler (Supavisor), o usuário leva o ref do projeto:
--    DB_LEXFLOW_USER=lexhub_leitor.<ref do projeto lexflow>
--    Depois do deploy, o log da API deve mostrar "lexflow conectado" e os dashboards do LexFlow com números.
--
-- Desfazer: voltar DB_LEXFLOW_USER/PASSWORD para os do postgres e, se quiser, `drop role lexhub_leitor;`.
