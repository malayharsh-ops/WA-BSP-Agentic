"""
Conversation session management backed by Redis.

Session key: session:{phone_number}
TTL: 24 hours
"""

import json
import redis.asyncio as aioredis
from app.config import settings

SESSION_TTL = 86400  # 24h


class SessionStore:
    def __init__(self):
        self._redis: aioredis.Redis | None = None

    async def _get_client(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    async def get(self, phone: str) -> dict:
        client = await self._get_client()
        raw = await client.get(f"session:{phone}")
        if raw:
            return json.loads(raw)
        return {
            "phone": phone,
            "stage": "QUALIFYING",
            "messages": [],
            "collected": {},
            "loop_hashes": [],
            "loop_stage_turns": 0,
            "loop_last_stage": None,
            "score": 0,
            "language": "hi",
            "loop_escalated": False,
        }

    async def save(self, phone: str, session: dict) -> None:
        client = await self._get_client()
        # Keep only last 20 messages to cap memory
        if len(session.get("messages", [])) > 20:
            session["messages"] = session["messages"][-20:]
        await client.setex(f"session:{phone}", SESSION_TTL, json.dumps(session))

    async def delete(self, phone: str) -> None:
        client = await self._get_client()
        await client.delete(f"session:{phone}")

    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()


# Module-level singleton
session_store = SessionStore()
