from app.config import Settings

BASE = {"SUPABASE_URL": "https://x.supabase.co", "SUPABASE_PUBLISHABLE_KEY": "pk"}


def settings(**env) -> Settings:
    # _env_file=None: o teste não lê o .env local (que tem credenciais reais).
    return Settings(_env_file=None, **BASE, **env)


def test_banco_sem_variaveis_fica_desligado():
    assert settings().source_dsn("ng") is None


def test_variaveis_separadas_como_na_v1():
    s = settings(
        DB_NG_HOST="10.0.0.1",
        DB_NG_PORT=6543,
        DB_NG_USER="u",
        DB_NG_PASSWORD="p",
        DB_NG_NAME="operacao_ng",
    )
    assert s.source_dsn("ng") == {
        "host": "10.0.0.1",
        "port": 6543,
        "user": "u",
        "password": "p",
        "database": "operacao_ng",
    }


def test_url_tem_prioridade_sobre_as_variaveis():
    s = settings(DB_LEXPRE_URL="postgresql://u:p@h:5432/db", DB_LEXPRE_HOST="outro")
    assert s.source_dsn("lexpre") == {"dsn": "postgresql://u:p@h:5432/db"}


def test_concorrencia_padrao_igual_a_v1():
    s = settings()
    assert [s.source_concurrency(n) for n in ("ng", "laadv", "lexflow", "lexpre")] == [2, 2, 4, 4]


def test_service_role_da_v1_vale_como_chave_secreta():
    assert settings(SUPABASE_SERVICE_ROLE_KEY="sr").supabase_secret_key == "sr"
    assert (
        settings(SUPABASE_SECRET_KEY="sk", SUPABASE_SERVICE_ROLE_KEY="sr").supabase_secret_key
        == "sk"
    )
