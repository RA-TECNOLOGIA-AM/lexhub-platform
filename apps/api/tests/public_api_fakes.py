"""Repositório da chave de API em memória, para os testes da API pública (serviço, rotas e dados)."""

import asyncio
import functools
import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime

from app.public_api.store import ApiKey, KeyAccess, Reachable, RefreshRow


@dataclass
class FakeApiKeyRepo:
    keys: dict[str, ApiKey] = field(default_factory=dict)
    refresh: dict[str, RefreshRow] = field(default_factory=dict)  # id -> linha
    replaced: dict[str, str] = field(default_factory=dict)
    last_used: dict[str, datetime] = field(default_factory=dict)
    # (key_id, org_slug, unit_code, dashboard_key) -> KeyAccess
    access: dict[tuple[str, str, str, str], KeyAccess] = field(default_factory=dict)
    reach: dict[str, list[Reachable]] = field(default_factory=dict)
    calls: list[str] = field(default_factory=list)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def add_key(
        self, key_id="k1", user_id="u1", org_id="o1", org_slug="lexgroup", status="active", tvs=None
    ):
        self.keys[key_id] = ApiKey(key_id, org_id, org_slug, user_id, status, tvs)
        return self.keys[key_id]

    async def get_key(self, key_id):
        self.calls.append("get_key")
        return self.keys.get(key_id)

    async def get_active_key_for(self, user_id, org_slug):
        return next(
            (
                k
                for k in self.keys.values()
                if k.user_id == user_id and k.org_slug == org_slug and k.status == "active"
            ),
            None,
        )

    async def get_refresh(self, token_hash):
        return next((r for r in self.refresh.values() if r.token_hash == token_hash), None)

    async def consume_refresh(self, refresh_id, now):
        async with self._lock:
            await asyncio.sleep(0)
            r = self.refresh[refresh_id]
            if r.used_at is not None or r.revoked_at is not None:
                return False
            self.refresh[refresh_id] = replace(r, used_at=now)
            return True

    async def insert_refresh(self, key_id, token_hash, expires_at):
        rid = str(uuid.uuid4())
        self.refresh[rid] = RefreshRow(rid, key_id, token_hash, expires_at, None, None)
        return rid

    async def mark_replaced(self, refresh_id, new_id):
        self.replaced[refresh_id] = new_id

    async def revoke_all(self, key_id, now):
        for rid, r in list(self.refresh.items()):
            if r.key_id == key_id and r.revoked_at is None:
                self.refresh[rid] = replace(r, revoked_at=now)
        self.keys[key_id] = replace(self.keys[key_id], tokens_valid_since=now)

    async def touch_last_used(self, key_id, now):
        self.last_used[key_id] = now

    async def resolve(self, key_id, org_slug, unit_code, dashboard_key):
        return self.access.get((key_id, org_slug, unit_code, dashboard_key))

    async def reachable(self, key_id):
        return self.reach.get(key_id, [])


def sync(fn):
    """Roda um teste async com asyncio.run (o projeto não usa pytest-asyncio)."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        return asyncio.run(fn(*args, **kwargs))

    return wrapper
