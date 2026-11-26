# API Dashboard V2

API assíncrona em FastAPI/Python 3.12. Ela valida os tokens do Supabase, aplica as regras de acesso da V2 e consulta os bancos operacionais em modo somente leitura. Rode os comandos a partir de `apps/api`.

## Configuração

```powershell
cd apps\api
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt
Copy-Item .env.example .env
```

Preencha o `.env` com valores de desenvolvimento/staging fornecidos pela equipe. Ele não deve ser versionado. Sem `SUPABASE_URL` e `SUPABASE_PUBLISHABLE_KEY`, a aplicação não inicia. Sem `DATABASE_URL`, a aplicação pode iniciar e responder em `/health`, mas os endpoints protegidos que consultam o banco da plataforma ficam indisponíveis.

| Variável | Uso |
|---|---|
| `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY` | Validar tokens via JWKS e consultar o health check do Supabase. |
| `DATABASE_URL` | Banco da plataforma: usuário, organizações, permissões, catálogo e auditoria. |
| `SUPABASE_SECRET_KEY` ou `SUPABASE_SERVICE_ROLE_KEY` | Obrigatória para login por dispositivo e operações administrativas; nunca expor no front. |
| `WEB_BASE_URL` | URL pública do front, usada para montar o QR Code (`/ativar?code=...`). |
| `SUPABASE_JWT_SECRET` | Opcional; somente para projetos que ainda assinam JWT legado com HS256. |
| `CORS_ORIGINS` | Origens web permitidas, separadas por vírgula. Vazio significa nenhuma origem. |
| `DB_<FONTE>_URL` ou `DB_<FONTE>_NAME/USER/PASSWORD/HOST/PORT` | Conexões das fontes `NG`, `LAADV`, `LEXFLOW` e `LEXPRE`. URL tem prioridade; fonte sem configuração fica desligada. |
| `SOURCE_CACHE_*`, `DASHBOARD_MEMO_MAX_ENTRIES`, `DB_POOL_*`, `DB_CONNECT_TIMEOUT`, `DB_QUERY_CONCURRENCY_*`, `PLATFORM_DB_*` | Ajustes opcionais do cache das fontes, da memória dos cálculos, pools, tempo limite de conexão e concorrência; padrões definidos em `app/config.py`. |

As conexões dos bancos de origem são somente leitura. O `.env.example` documenta as variáveis e seus valores padrão. Para desenvolvimento local do front, libere `http://localhost:5173` em `CORS_ORIGINS`.

## Iniciar

```powershell
python -m uvicorn app.main:app --reload --app-dir src --port 8000
```

Documentação OpenAPI: http://localhost:8000/docs.

Com `make` instalado, o [`Makefile`](Makefile) oferece `make setup`, `make run`, `make dev-test`, `make test`, `make lint`, `make fmt` e `make check`. `PORT=8001` altera a porta de `run` e `dev-test`. `make dev-test` falha se a porta já estiver ocupada, para não testar outro servidor por engano.

## Docker

A imagem de produção é definida em [`Dockerfile`](Dockerfile) e roda num nó do Docker Swarm, com **1 réplica**. Ela leva só `requirements.txt` e `src/` (ver [`.dockerignore`](.dockerignore)), roda com usuário sem privilégios e tem healthcheck em `/health`. Os segredos não entram na imagem: vêm do ambiente ou dos secrets da stack, com as mesmas variáveis do `.env`.

```powershell
docker build -t lexhub-api:dev .
docker run --rm --env-file .env -p 8001:8000 lexhub-api:dev
```

- **Uma réplica e um worker do uvicorn:** o cache das fontes e o aquecedor ficam em memória. Mais processos multiplicam as consultas nos bancos de origem.
- **Aquecedor só do que está em uso:** a cada `SOURCE_CACHE_WARM_INTERVAL` (4 min) ele renova só as queries que algum pedido leu nos últimos `SOURCE_CACHE_WARM_IDLE` (30 min). Dashboard que ninguém abre não vai ao banco; o aberto à vista segue quente, porque a tela busca de novo a cada 5 min.
- **LexFlow, LexPre e o egress do Supabase:** os dois bancos estão no Supabase, que cobra cada GB que sai, e as queries trazem de milhares a dezenas de milhares de linhas. Por isso:
  - o aquecedor não renova o LexFlow nem o LexPre (`SOURCE_CACHE_WARM_SKIP=lexflow,lexpre`). As queries levam ~1 s no LexFlow e de 60 a 224 ms no LexPre (medido em 21/11/2026); o dado vencido vai para a tela na hora e é renovado em segundo plano só quando alguém lê;
  - o dado do LexFlow vale 15 min (`SOURCE_CACHE_TTL_LEXFLOW=900`), e não 5;
  - recorte por unidade (`SOURCE_UNIT_SCOPE=true`, `app/unit_scope.py`; ligado depois que `scripts/comparar_v1/conferir_recorte_unidade.py` deu 189 de 189 casos idênticos com os dados reais, em 21/11/2026): onze queries da v1 trazem os processos de NG, LA e RJ e o cálculo descarta as outras unidades em Python. Nos dashboards que declaram `unit_scoped` (Execução, Acordos, Execução Estratégico, Recursal, Julgados Acórdãos e Sentenças, Controle de Processos), a mesma query vem só com as linhas da unidade da tela (`select * from (<query>) q where q."ID_ESCRITORIO" = N`), guardada no cache como `query@N`. Antes de ligar o recorte, ou de pôr um dashboard novo nele, rode o conferidor (ver o README de lá). `SOURCE_UNIT_SCOPE=false` volta ao comportamento anterior. O aquecedor conhece as chaves recortadas, caso o LexFlow volte para ele;
  - "só baixa se mudou" (`SOURCE_CACHE_PROBE=lexflow,lexpre`): na renovação, o banco devolve primeiro uma linha com a impressão digital do resultado (quantidade de linhas e soma dos hashes delas). Igual à guardada, nada é baixado e a tela mostra a hora da conferência. A query roda no banco do mesmo jeito; o que se economiza é a transferência. Quando o dado mudou, ou na primeira leitura, ela roda duas vezes (impressão digital e linhas), o que dobra a espera de quem abre o dashboard frio. Mesmo assim, o banco roda menos queries que antes, sem o aquecedor. O log diz quanto a conferência poupa ("sem mudança, nada baixado" ou "N linhas"). Impressão digital e linhas saem da mesma foto do banco (`REPEATABLE READ`), e a impressão leva o hash do SQL, a versão do asyncpg e `FINGERPRINT_FORMAT` (`app/database.py`): mude este ao alterar como as linhas viram o que o cache guarda.
- **Bancos de origem fora do ar:** a API não espera NG, LAADV, LexFlow nem LexPre para subir. Cada banco conecta numa tarefa de fundo e, sem resposta, fica `down` e é tentado de novo sozinho (1 s, 2 s, 4 s... até 1 min entre as tentativas). Banco que cai durante o uso também é marcado `down` e conferido até voltar. Enquanto isso, só os dashboards daquele banco respondem 503, ou o último dado bom do cache por até 1 h. Cada conexão nova tem tempo limite de `DB_CONNECT_TIMEOUT` (10 s), então o motivo aparece no log em segundos.
- **Banco da plataforma (`DATABASE_URL`):** este sim impede a subida. São 3 tentativas; se todas falharem, a API sai com erro, e num deploy o Swarm volta à versão anterior. O pooler do Supabase fica em São Paulo e abrir conexão leva de 1 a 10 s, então:
  - o tempo limite para abrir conexão é próprio, `PLATFORM_DB_CONNECT_TIMEOUT` (30 s);
  - as conexões mínimas (`PLATFORM_DB_POOL_MIN_SIZE`, 2) ficam abertas, com um `select 1` a cada `PLATFORM_DB_KEEPALIVE_INTERVAL` (1 min). Assim nem o pool (5 min parada) nem o balanceador da AWS na frente do pooler (350 s ociosa) as fecham, e a requisição do usuário não paga a abertura;
  - sem conexão com o banco, qualquer rota responde 503 ("Banco de dados indisponível no momento"), não 500. Ver `app/platform_db.py`.
- **Atrás do proxy:** defina `FORWARDED_ALLOW_IPS` com o IP ou a rede do proxy reverso. Assim, o IP real do cliente chega à auditoria e ao limite do login por TV.
- **Fuso:** `TZ=America/Manaus` já vem na imagem. `PORT` (padrão 8000) muda a porta interna.
- **Desligamento:** o `tini` é o PID 1. No SIGTERM, o uvicorn espera até 25 s pelas requisições em andamento.
  - **ordem fixa** das linhas nas onze queries do recorte (`unit_scope.ordem_canonica`: id do processo e parte adversa), na query inteira e no recorte. Sem ORDER BY, o banco devolvia as linhas na ordem do plano, e o cálculo da v1 tem listas sem desempate e, no Recursal e no Controle, um processo numa linha por parte adversa (vale a primeira);
  - **resumo no log**, a cada hora, do que saiu de cada banco: `Bancos de origem nos últimos 60min: lexflow: 3 baixadas (61.240 linhas), 12 conferidas sem mudança; ...`. É por ele que se acompanha o egress sem o painel do Supabase;
  - **card do hub**: mostra quando veio do banco o dado mais antigo que o dashboard tem no cache; sem nenhum, "Atualiza ao abrir" (neutro). Antes exigia todas as queries de todas as unidades, e sem o aquecedor os cards do LexFlow ficavam em "Aguardando sincronização", em âmbar.
- **Memória:** com o cache cheio (37 consultas), a API usa cerca de 1,8 GB.
- **Stack do Portainer:** [`deploy/stack.yml`](deploy/stack.yml), no padrão da Lex (Traefik, GHCR, webhook). Para validar: `docker stack config -c deploy/stack.yml`, com as variáveis do cabeçalho definidas.

## Endpoints implementados

Rotas de usuário exigem `Authorization: Bearer <token>`. O código e o polling do login por dispositivo são públicos; a aprovação exige a sessão Supabase do celular:

| Método e caminho | Finalidade |
|---|---|
| `GET /health` | Liveness da API. |
| `GET /health/supabase` | Verifica conectividade com o Supabase. |
| `GET /health/sources` | Estado `connecting`, `up`, `down` ou `off` de cada banco de origem; responde 503 se algum configurado não estiver no ar. Não entra no healthcheck: banco de origem fora não derruba a API. |
| `POST /auth/device/code` | Inicia sessão da TV e retorna códigos com validade de 10 minutos. |
| `GET /auth/device/token?device_code=...` | Polling da TV; retorna `authorization_pending`, `slow_down`, `expired_token` ou a sessão Supabase de uso único. |
| `POST /auth/device/authorize` | Aprova o código curto com um access token Supabase válido. |
| `GET /me?org=<slug>` | Identidade, organizações, unidade e permissões do usuário atual. |
| `GET /orgs/{org_slug}/dashboards` | Catálogo de dashboards que o usuário pode abrir. |
| `GET/POST/DELETE /orgs/{org_slug}/favorites[/{dashboard_key}]` | Preferências de favoritos. |
| `GET/PUT /orgs/{org_slug}/hub-order` | Ordem personalizada dos cards. |
| `GET /orgs/{org_slug}/units/{unit_code}/dashboards/{dashboard_key}/access` | Confere acesso e escopo (`all` ou `own`). |
| `GET /orgs/{org_slug}/units/{unit_code}/dashboards/{dashboard_key}` | Dados do dashboard; aceita período `from`/`to` e filtros do módulo. |
| `GET /orgs/{org_slug}/units/{unit_code}/dashboards/{dashboard_key}/export` | Exportação CSV/XLSX, com campos e filtros selecionáveis. |
| `GET /orgs/{org_slug}/geral/dashboards/{dashboard_key}/access` | Confere acesso a um dashboard da organização inteira (`scope = 'org'`, ex.: Estratégico Geral); só Owner/Dev. |
| `GET /orgs/{org_slug}/geral/dashboards/{dashboard_key}` | Dados do dashboard da organização, uma parte por unidade (NG, LAAM, LARJ) em `units[]`. |

O registro de cálculos está em `app/dashboards/`. Uma key no catálogo ou no front não garante que o cálculo já esteja registrado na API; dashboard sem cálculo retorna 404. Módulo registrado mas ainda não habilitado retorna 501. Fonte ou banco da plataforma indisponível retorna 503.

## Autenticação e autorização

- O JWT é validado localmente com o JWKS do projeto Supabase (`/auth/v1/.well-known/jwks.json`), com cache e renovação para `kid` desconhecido.
- `/me` e o escopo do dashboard são determinados pelo banco da plataforma; as rotas de dashboard usam `require_dashboard` em `app/access.py`.
- Token ausente, inválido, expirado ou de outro projeto: 401. Organização/unidade/dashboard sem permissão: 403; tentativas negadas são auditadas.
- `DATABASE_URL` vazio ou dependência indisponível: 503.
- Login por dispositivo exige `SUPABASE_SECRET_KEY` ou `SUPABASE_SERVICE_ROLE_KEY` e `WEB_BASE_URL`. Códigos são armazenados como HMAC, tentativas são limitadas por IP no banco e a sessão aprovada é reivindicada e consumida atomicamente.
- O front também chama funções de administração e notificações no schema `api` do Supabase diretamente. Essas funções não são rotas desta API; veja [README do front](../web/README.md) e [README do banco](../../supabase/README.md).

## Testes e lint

```powershell
python -m pytest -q
python -m ruff check src tests
```

`tests/test_pg_repo.py` executa consultas reais contra PostgreSQL e fica desativado sem `TEST_DATABASE_URL`. Para executá-lo, aplique `supabase/tests/ci/supabase_stub.sql` e todas as migrations em um banco de teste, configure a variável e rode:

```powershell
$env:TEST_DATABASE_URL = "postgresql://postgres@localhost:54329/postgres"
python -m pytest tests/test_pg_repo.py -v
```

O workflow de CI configura o Postgres e as migrations automaticamente. Os testes unitários não precisam de `.env`.
