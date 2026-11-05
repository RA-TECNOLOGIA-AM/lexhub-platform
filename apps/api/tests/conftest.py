import os

import pytest
from fastapi.testclient import TestClient

# Valores fixos para os testes não dependerem do .env local.
os.environ.update(
    SUPABASE_URL="https://example.supabase.co",
    SUPABASE_PUBLISHABLE_KEY="sb_publishable_test",
    SUPABASE_SECRET_KEY="",
)


@pytest.fixture
def client():
    from app.main import create_app

    with TestClient(create_app()) as c:
        yield c
