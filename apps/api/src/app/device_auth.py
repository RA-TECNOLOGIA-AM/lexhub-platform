import hashlib
import hmac
from datetime import datetime
from typing import Any, Protocol

from postgrest.exceptions import APIError
from supabase import AsyncClient


class DeviceAuthRepository(Protocol):
    async def allow_request(self, bucket_key: str, limit: int, window_seconds: int) -> bool: ...

    async def cleanup_expired(self, now: datetime) -> None: ...

    async def create_session(
        self, device_code: str, user_code: str, expires_at: datetime
    ) -> bool: ...

    async def approve(self, user_code: str, user_id: str) -> str: ...

    async def claim(self, device_code: str, claim_id: str) -> dict[str, Any] | None: ...

    async def finish(self, device_code: str, claim_id: str, consume: bool) -> bool: ...


class SupabaseDeviceAuthRepository:
    def __init__(self, client: AsyncClient):
        self._client = client

    async def allow_request(self, bucket_key: str, limit: int, window_seconds: int) -> bool:
        response = await self._client.schema("api").rpc(
            "consume_device_auth_rate_limit",
            {
                "p_bucket_key": bucket_key,
                "p_limit": limit,
                "p_window_seconds": window_seconds,
            },
        ).execute()
        return response.data is True

    async def cleanup_expired(self, now: datetime) -> None:
        await (
            self._client.schema("api")
            .table("device_auth_sessions")
            .delete()
            .lt("expires_at", now.isoformat())
            .execute()
        )

    async def create_session(
        self, device_code: str, user_code: str, expires_at: datetime
    ) -> bool:
        try:
            await (
                self._client.schema("api")
                .table("device_auth_sessions")
                .insert(
                    {
                        "device_code": device_code,
                        "user_code": user_code,
                        "status": "pending",
                        "expires_at": expires_at.isoformat(),
                    }
                )
                .execute()
            )
        except APIError as exc:
            if exc.code == "23505":
                return False
            raise
        return True

    async def approve(self, user_code: str, user_id: str) -> str:
        response = await self._client.schema("api").rpc(
            "approve_device_auth_session",
            {"p_user_code": user_code, "p_user_id": user_id},
        ).execute()
        return str(response.data)

    async def claim(self, device_code: str, claim_id: str) -> dict[str, Any] | None:
        response = await self._client.schema("api").rpc(
            "claim_device_auth_session",
            {"p_device_code": device_code, "p_claim_id": claim_id},
        ).execute()
        if not response.data:
            return None
        return response.data[0]

    async def finish(self, device_code: str, claim_id: str, consume: bool) -> bool:
        response = await self._client.schema("api").rpc(
            "finish_device_auth_session",
            {
                "p_device_code": device_code,
                "p_claim_id": claim_id,
                "p_consume": consume,
            },
        ).execute()
        return response.data is True


def digest_device_value(secret: str, purpose: str, value: str) -> str:
    payload = f"lexhub-device-auth:{purpose}:{value}".encode()
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


class DeviceAuthUnavailable(RuntimeError):
    pass
