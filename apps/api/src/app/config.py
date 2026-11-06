from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    SUPABASE_URL: str
    SUPABASE_PUBLISHABLE_KEY: str
    # Chave secreta server-side (ignora RLS). Opcional; nunca expor ao frontend.
    SUPABASE_SECRET_KEY: str = ""
    # Só para projetos com o segredo JWT legado (HS256). Projetos novos usam
    # chaves assimétricas publicadas no JWKS e não precisam disto.
    SUPABASE_JWT_SECRET: str = ""
    JWT_AUDIENCE: str = "authenticated"
    # Conexão direta ao Postgres (pooler do Supabase). Usada para a checagem de
    # acesso (app_private) e a auditoria. Vazio = rotas protegidas respondem 503.
    DATABASE_URL: str = ""
    CORS_ORIGINS: str = Field(default="", description="Origens separadas por vírgula")

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def jwt_issuer(self) -> str:
        return f"{self.SUPABASE_URL.rstrip('/')}/auth/v1"

    @property
    def jwks_url(self) -> str:
        return f"{self.jwt_issuer}/.well-known/jwks.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
