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
| `SOURCE_CACHE_*`, `DB_POOL_*`, `DB_CONNECT_TIMEOUT`, `DB_QUERY_CONCURRENCY_*` | Ajustes opcionais do cache, pools, tempo limite de conexão e concorrência; padrões definidos em `app/config.py`. |

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
- **Bancos de origem fora do ar:** a API não espera NG, LAADV, LexFlow nem LexPre para subir. Cada banco conecta numa tarefa de fundo e, sem resposta, fica `down` e é tentado de novo sozinho (1 s, 2 s, 4 s... até 1 min entre as tentativas). Banco que cai durante o uso também é marcado `down` e conferido até voltar. Enquanto isso, só os dashboards daquele banco respondem 503, ou o último dado bom do cache por até 1 h. Cada conexão nova tem tempo limite de `DB_CONNECT_TIMEOUT` (10 s), então o motivo aparece no log em segundos.
- **Banco da plataforma (`DATABASE_URL`):** este sim impede a subida. São 3 tentativas com o mesmo tempo limite; se todas falharem, a API sai com erro, e num deploy o Swarm volta à versão anterior.
- **Atrás do proxy:** defina `FORWARDED_ALLOW_IPS` com o IP ou a rede do proxy reverso. Assim, o IP real do cliente chega à auditoria e ao limite do login por TV.
- **Fuso:** `TZ=America/Manaus` já vem na imagem. `PORT` (padrão 8000) muda a porta interna.
- **Desligamento:** o `tini` é o PID 1. No SIGTERM, o uvicorn espera até 25 s pelas requisições em andamento.
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
