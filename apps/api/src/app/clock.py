"""O relógio da API, como dependency: as rotas pedem "agora" e os testes trocam a hora."""

from datetime import UTC, datetime


def get_now() -> datetime:
    """Dependency: agora, em UTC (trocável nos testes por app.dependency_overrides)."""
    return datetime.now(UTC)
