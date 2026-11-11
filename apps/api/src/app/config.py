from functools import lru_cache

from pydantic import Field
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
    # Só para projetos com o segredo JWT legado (HS256). Projetos novos usam
    # chaves assimétricas publicadas no JWKS e não precisam disto.
    SUPABASE_JWT_SECRET: str = ""
    JWT_AUDIENCE: str = "authenticated"
    # Conexão direta ao Postgres (pooler do Supabase). Usada para a checagem de
    # acesso (app_private) e a auditoria. Vazio = rotas protegidas respondem 503.
    DATABASE_URL: str = ""
    CORS_ORIGINS: str = Field(default="", description="Origens separadas por vírgula")

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
    DB_POOL_COMMAND_TIMEOUT: float = Field(default=300.0, ge=1.0)
    DB_POOL_ACQUIRE_TIMEOUT: float = Field(default=120.0, ge=1.0)
    DB_POOL_MAX_QUERIES: int = Field(default=10_000, ge=100)

    # Consultas simultâneas por banco (mesmos padrões da v1): protege a origem.
    DB_QUERY_CONCURRENCY_NG: int = Field(default=2, ge=1, le=16)
    DB_QUERY_CONCURRENCY_LAADV: int = Field(default=2, ge=1, le=16)
    DB_QUERY_CONCURRENCY_LEXFLOW: int = Field(default=4, ge=1, le=16)
    DB_QUERY_CONCURRENCY_LEXPRE: int = Field(default=4, ge=1, le=16)

    # Cache das queries dos bancos de origem (mesmos padrões da v1: 5 min, reserva de 1 h,
    # aquecedor um pouco antes de vencer). Ver app/source_cache.py e app/cache_warmer.py.
    SOURCE_CACHE_TTL: int = Field(default=300, ge=0)
    SOURCE_CACHE_STALE_MAX_AGE: int = Field(default=3600, ge=0)
    SOURCE_CACHE_MAX_ENTRIES: int = Field(default=64, ge=1)
    SOURCE_CACHE_WARM_ENABLED: bool = True
    SOURCE_CACHE_WARM_INTERVAL: int = Field(default=240, ge=30)

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
