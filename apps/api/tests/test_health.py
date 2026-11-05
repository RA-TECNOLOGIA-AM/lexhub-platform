import asyncio

import httpx

from app.routes import health


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_supabase_health_up(client, monkeypatch):
    async def fake_check(settings):
        return True, None

    monkeypatch.setattr(health, "check_supabase", fake_check)
    r = client.get("/health/supabase")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "supabase": "up"}


def test_supabase_health_down(client, monkeypatch):
    async def fake_check(settings):
        return False, "connection refused"

    monkeypatch.setattr(health, "check_supabase", fake_check)
    r = client.get("/health/supabase")
    assert r.status_code == 503
    assert r.json() == {"status": "error", "supabase": "down", "detail": "connection refused"}


def test_check_supabase_sends_apikey():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["apikey"] = request.headers.get("apikey")
        return httpx.Response(200, json={})

    from app.config import Settings

    s = Settings(SUPABASE_URL="https://x.supabase.co", SUPABASE_PUBLISHABLE_KEY="pk")
    ok, err = asyncio.run(health.check_supabase(s, transport=httpx.MockTransport(handler)))
    assert ok and err is None
    assert seen == {"url": "https://x.supabase.co/auth/v1/health", "apikey": "pk"}
