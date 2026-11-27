from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Bancos de origem, com os mesmos nomes de variáveis da v1 (api_dashboards):
# DB_<NOME>_URL (tem prioridade) ou DB_<NOME>_NAME/USER/PASSWORD/HOST/PORT.
SOURCE_DATABASES = ("ng", "laadv", "lexflow", "lexpre")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    SUPABASE_URL: str
    SUPABASE_PUBLISHABLE_KEY: str
    # Chave secreta server-side (ignora RLS). Opcional; nunca expor ao frontend.
    SUPABASE_SECRET_KEY: str = ""
    # Nome usado na v1 para a mesma chave (service_role). Vale quando SUPABASE_SECRET_KEY está vazia.
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    # Origem do frontend, usada para montar a URL de ativação exibida no QR Code.
    WEB_BASE_URL: str = ""
    # Só para projetos com o segredo JWT legado (HS256). Projetos novos usam
    # chaves assimétricas publicadas no JWKS e não precisam disto.
    SUPABASE_JWT_SECRET: str = ""
    JWT_AUDIENCE: str = "authenticated"
    # Conexão direta ao Postgres (pooler do Supabase). Usada para a checagem de
    # acesso (app_private) e a auditoria. Vazio = rotas protegidas respondem 503.
    DATABASE_URL: str = ""
    # Pool do banco da plataforma (ver app/platform_db.py). Abrir conexão com o pooler do Supabase
    # (TLS + autenticação, em outra região) leva de 1 a 10 s: o tempo limite é maior que o dos
    # bancos de origem, e as conexões mínimas ficam abertas e testadas a cada
    # PLATFORM_DB_KEEPALIVE_INTERVAL s, para a requisição do usuário não pagar esse tempo.
    PLATFORM_DB_CONNECT_TIMEOUT: float = Field(default=30.0, ge=1.0, le=120.0)
    PLATFORM_DB_POOL_MIN_SIZE: int = Field(default=2, ge=1, le=20)
    PLATFORM_DB_POOL_MAX_SIZE: int = Field(default=10, ge=1, le=50)
    # Menor que os 5 min em que o pool fecha conexão parada e que os 350 s em que o balanceador
    # da AWS na frente do pooler corta conexão TCP ociosa.
    PLATFORM_DB_KEEPALIVE_INTERVAL: float = Field(default=60.0, ge=5.0, le=280.0)
    CORS_ORIGINS: str = Field(default="", description="Origens separadas por vírgula")
    # Logs do terminal: DEBUG mostra também health checks, preflight e o motivo de token recusado.
    LOG_LEVEL: str = Field(default="INFO", pattern=r"(?i)^(DEBUG|INFO|WARNING|ERROR)$")

    # --- Planilhas do Google publicadas como XLSX (iguais à v1; app/sheets.py). O link fica cifrado no
    # banco (desde o PR 3 também o das planilhas antigas; scripts/migrar_planilhas_env.py). ---
    SHEETS_HTTP_TIMEOUT: float = 15.0  # conexão (s)
    SHEETS_HTTP_READ_TIMEOUT: float = 60.0  # download (s)
    SHEETS_HTTP_MAX_RETRIES: int = 3

    # --- Fontes conectadas pela tela (Conectar fonte: banco próprio e planilha). Ver app/secret_box.py. ---
    # Chave AES-256 (base64 de 32 bytes) que cifra a senha do banco e o link da planilha no Supabase.
    # Vazia = conectar banco/planilha pela tela fica desligado (LexPre/LexFlow continuam).
    SOURCE_SECRET_KEY: str = ""
    # IP de saída da API, que a tela pede para a operação liberar no firewall do banco ("" = não mostra).
    SOURCE_EGRESS_IP: str = ""
    # Tempo limite de cada etapa do teste de conexão (s).
    SOURCE_TEST_TIMEOUT: float = Field(default=8.0, ge=1.0, le=60.0)

    # --- API pública /v1 (chave de API). Ver app/public_api. ---
    # Segredo HS256 dos access tokens. Vazio = /v1 responde 503 e "Gerar tokens" fica indisponível.
    PUBLIC_API_JWT_SECRET: str = ""
    PUBLIC_API_ACCESS_TOKEN_TTL_SECONDS: int = Field(default=604800, ge=60)  # 1 semana
    PUBLIC_API_REFRESH_TOKEN_TTL_DAYS: int = Field(default=30, ge=1)
    # Só desenvolvimento: deixa conectar em banco de rede interna (localhost, 10.x...). Em produção, False.
    SOURCE_ALLOW_PRIVATE_HOSTS: bool = False

    # --- Facebook Ads (Marketing API da Meta; app/facebook_ads.py e app/facebook_ads_sync.py). O token do
    # usuário do sistema fica cifrado no banco com a SOURCE_SECRET_KEY, como a senha do banco. ---
    # Versão da Graph API (a Meta mantém cada uma por uns 2 anos; v26.0 é de 29/07/2026).
    FACEBOOK_GRAPH_VERSION: str = Field(default="v26.0", pattern=r"^v\d{2}\.0$")
    # Chave secreta do app da Meta: com ela cada chamada leva o appsecret_proof (obrigatório se o app
    # tiver "Require App Secret" ligado). Vazia = sem appsecret_proof.
    FACEBOOK_APP_SECRET: str = ""
    # ID do app da Meta: com ele e a chave, a tela mostra o tipo e a validade do token (/debug_token).
    FACEBOOK_APP_ID: str = ""
    FACEBOOK_HTTP_TIMEOUT: float = Field(default=30.0, ge=5.0, le=120.0)
    # A coleta que grava as métricas em app.facebook_ads_daily. Desligada por padrão: uma API local com o
    # banco de produção não coleta sozinha. Em produção, ligar em UMA réplica só.
    FACEBOOK_ADS_SYNC_ENABLED: bool = False
    FACEBOOK_ADS_SYNC_INTERVAL: int = Field(default=600, ge=60, le=3600)

    # --- Bancos de origem (iguais à v1). Banco sem variáveis = desligado. ---
    DB_NG_URL: str = ""
    DB_NG_NAME: str = ""
    DB_NG_USER: str = ""
    DB_NG_PASSWORD: str = ""
    DB_NG_HOST: str = ""
    DB_NG_PORT: int = 5432

    DB_LAADV_URL: str = ""
    DB_LAADV_NAME: str = ""
    DB_LAADV_USER: str = ""
    DB_LAADV_PASSWORD: str = ""
    DB_LAADV_HOST: str = ""
    DB_LAADV_PORT: int = 5432

    DB_LEXFLOW_URL: str = ""
    DB_LEXFLOW_NAME: str = ""
    DB_LEXFLOW_USER: str = ""
    DB_LEXFLOW_PASSWORD: str = ""
    DB_LEXFLOW_HOST: str = ""
    DB_LEXFLOW_PORT: int = 5432

    DB_LEXPRE_URL: str = ""
    DB_LEXPRE_NAME: str = ""
    DB_LEXPRE_USER: str = ""
    DB_LEXPRE_PASSWORD: str = ""
    DB_LEXPRE_HOST: str = ""
    DB_LEXPRE_PORT: int = 5432

    # Pool asyncpg (mesmos padrões da v1)
    DB_POOL_MIN_SIZE: int = Field(default=2, ge=1, le=64)
    DB_POOL_MAX_SIZE: int = Field(default=10, ge=1, le=128)
    DB_POOL_MAX_INACTIVE_CONNECTION_LIFETIME: float = Field(default=90.0, ge=5.0, le=3600.0)
    # Tempo limite de uma consulta (s). Passou disso: 503 (ou o último dado bom), banco segue no ar.
    DB_POOL_COMMAND_TIMEOUT: float = Field(default=300.0, ge=1.0)
    # Espera máxima por uma conexão livre do pool (s), incluindo abrir uma nova.
    DB_POOL_ACQUIRE_TIMEOUT: float = Field(default=120.0, ge=1.0)
    DB_POOL_MAX_QUERIES: int = Field(default=10_000, ge=100)
    # Tempo limite para abrir cada conexão com um banco de origem (s). Curto de propósito: banco
    # que não responde aparece no log em segundos, e a reconexão segue em segundo plano. O banco
    # da plataforma tem o próprio (PLATFORM_DB_CONNECT_TIMEOUT).
    DB_CONNECT_TIMEOUT: float = Field(default=10.0, ge=1.0, le=120.0)

    # Consultas simultâneas por banco (mesmos padrões da v1): protege a origem.
    DB_QUERY_CONCURRENCY_NG: int = Field(default=2, ge=1, le=16)
    DB_QUERY_CONCURRENCY_LAADV: int = Field(default=2, ge=1, le=16)
    DB_QUERY_CONCURRENCY_LEXFLOW: int = Field(default=4, ge=1, le=16)
    DB_QUERY_CONCURRENCY_LEXPRE: int = Field(default=4, ge=1, le=16)

    # Cache das queries dos bancos de origem (mesmos padrões da v1: 5 min, reserva de 1 h,
    # aquecedor um pouco antes de vencer). Ver app/source_cache.py e app/cache_warmer.py.
    SOURCE_CACHE_TTL: int = Field(default=300, ge=0)
    # Validade própria do LexFlow (s). O banco é do Supabase, que cobra cada GB que sai (egress), e as
    # queries trazem dezenas de milhares de processos: 15 min em vez de 5 corta as renovações a um terço.
    SOURCE_CACHE_TTL_LEXFLOW: int = Field(default=900, ge=0)
    # Bancos com "só baixa se mudou" (separados por vírgula): na renovação, o banco devolve antes uma
    # impressão digital do resultado (uma linha) e as linhas só vêm se ela mudou. A query roda no banco
    # do mesmo jeito; o que se economiza é a transferência. Vazio = desligado. LexFlow e LexPre estão no
    # Supabase (egress cobrado); as 52 queries do LexFlow e as 5 do LexPre foram conferidas no banco real.
    SOURCE_CACHE_PROBE: str = "lexflow,lexpre"
    # Recorte por unidade (app/unit_scope.py): as queries do LexFlow que trazem todos os escritórios vêm só
    # com as linhas da unidade da tela, nos dashboards que declaram `unit_scoped`. Ligado depois que o
    # scripts/comparar_v1/conferir_recorte_unidade.py deu 189 de 189 casos idênticos com os dados reais
    # (21/11/2026, já com a ordem fixa das linhas). False = como antes, sem deploy (variável na stack).
    SOURCE_UNIT_SCOPE: bool = True
    SOURCE_CACHE_STALE_MAX_AGE: int = Field(default=3600, ge=0)
    # Vencido há até isto (s): a tela recebe o dado atual na hora e ele é renovado em segundo
    # plano. 0 = desligado (quem pedir depois de vencer espera a query no banco).
    SOURCE_CACHE_STALE_WHILE_REVALIDATE: int = Field(default=600, ge=0)
    SOURCE_CACHE_MAX_ENTRIES: int = Field(default=64, ge=1)
    SOURCE_CACHE_WARM_ENABLED: bool = True
    # De quanto em quanto tempo (s) começa um ciclo do aquecedor, contado do início do anterior.
    SOURCE_CACHE_WARM_INTERVAL: int = Field(default=240, ge=30)
    # O aquecedor só renova a query que algum pedido leu nos últimos N s: dashboard que ninguém olha
    # não vai ao banco a cada ciclo. A tela à vista busca de novo a cada 5 min (useAutoRefresh), então
    # o dashboard aberto segue quente; fechado, para de ser renovado depois deste prazo.
    SOURCE_CACHE_WARM_IDLE: int = Field(default=1800, ge=60)
    # Bancos que o aquecedor não renova (separados por vírgula). LexFlow (~1 s) e LexPre (60 a 224 ms no
    # banco, medido em 21/11/2026) respondem rápido: o aquecedor não poupa espera e cada renovação dele era
    # egress cobrado pelo Supabase (até 15 por hora por query em uso, mais 30 min depois de fechar). Lá o
    # dado vencido vai para a tela na hora e é renovado em segundo plano quando alguém lê.
    SOURCE_CACHE_WARM_SKIP: str = "lexflow,lexpre"
    # Memória dos cálculos dos dashboards (app/result_memo.py): quantos resultados guarda (cada um é uma
    # resposta inteira; sai o usado há mais tempo). Vale até o dado ser renovado ou SOURCE_CACHE_TTL.
    # 0 = desligada (todo pedido calcula).
    DASHBOARD_MEMO_MAX_ENTRIES: int = Field(default=64, ge=0)

    # Redis: cache compartilhado (L2) atrás do cache em memória (L1). Mesmos nomes e padrões da v1
    # (api_dashboards). Desligado = só memória. Ver app/cache.py.
    CACHE_ENABLED: bool = False
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    # TTL no Redis: queries pesadas (HEAVY_QUERIES em app/source_cache.py) e as demais chaves.
    CACHE_TTL_HEAVY: int = Field(default=600, ge=60)
    CACHE_TTL_DEFAULT: int = Field(default=300, ge=30)
    # Prefixo das chaves (na v1: "api_dashboards:"), para dividir o mesmo Redis com outras apps.
    CACHE_KEY_PREFIX: str = "lexhub_platform:"
    # Timeout de conexão/comando (v1: 2 s) e espera antes de tentar de novo após uma falha.
    REDIS_SOCKET_TIMEOUT: float = Field(default=2.0, gt=0, le=30)
    REDIS_RETRY_AFTER: float = Field(default=30.0, ge=1)

    @model_validator(mode="after")
    def _pool_da_plataforma(self) -> "Settings":
        if self.PLATFORM_DB_POOL_MIN_SIZE > self.PLATFORM_DB_POOL_MAX_SIZE:
            raise ValueError(
                "PLATFORM_DB_POOL_MIN_SIZE não pode ser maior que PLATFORM_DB_POOL_MAX_SIZE"
            )
        return self

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def jwt_issuer(self) -> str:
        return f"{self.SUPABASE_URL.rstrip('/')}/auth/v1"

    @property
    def jwks_url(self) -> str:
        return f"{self.jwt_issuer}/.well-known/jwks.json"

    @property
    def supabase_secret_key(self) -> str:
        return self.SUPABASE_SECRET_KEY or self.SUPABASE_SERVICE_ROLE_KEY

    def source_dsn(self, name: str) -> dict | None:
        """Como conectar num banco de origem: {'dsn': ...} ou {'host': ..., ...}; None = desligado."""
        prefix = f"DB_{name.upper()}_"
        url = getattr(self, prefix + "URL")
        if url:
            return {"dsn": url}
        host = getattr(self, prefix + "HOST")
        if not host:
            return None
        return {
            "host": host,
            "port": getattr(self, prefix + "PORT"),
            "user": getattr(self, prefix + "USER"),
            "password": getattr(self, prefix + "PASSWORD"),
            "database": getattr(self, prefix + "NAME"),
        }

    def source_concurrency(self, name: str) -> int:
        return getattr(self, f"DB_QUERY_CONCURRENCY_{name.upper()}")

    @property
    def source_cache_ttl_by_db(self) -> dict[str, int]:
        """Validade do cache por banco, quando difere de SOURCE_CACHE_TTL."""
        return {"lexflow": self.SOURCE_CACHE_TTL_LEXFLOW}

    @property
    def source_cache_probe_dbs(self) -> frozenset[str]:
        return _names(self.SOURCE_CACHE_PROBE)

    @property
    def source_cache_warm_skip(self) -> frozenset[str]:
        return _names(self.SOURCE_CACHE_WARM_SKIP)


def _names(value: str) -> frozenset[str]:
    """'lexflow, ng' -> {'lexflow', 'ng'} (vazio = nenhum)."""
    return frozenset(n.strip().lower() for n in value.split(",") if n.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
