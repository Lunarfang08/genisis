from redis.asyncio import Redis


class RedisManager:
    """Owns the asynchronous Redis client lifecycle."""

    def __init__(self, redis_url: str) -> None:
        self._client = Redis.from_url(
            redis_url,
            decode_responses=True,
            health_check_interval=30,
        )

    async def ping(self) -> None:
        await self._client.ping()

    async def allow_request(self, key: str, limit: int, window_seconds: int) -> bool:
        """Fixed-window limiter. Fail open if Redis is unavailable."""
        try:
            count = await self._client.incr(key)
            if count == 1:
                await self._client.expire(key, window_seconds)
            return bool(count <= limit)
        except Exception:
            return True

    async def acquire_lease(self, key: str, owner: str, ttl_seconds: int) -> bool:
        """Acquire a short single-writer lease; fail closed when coordination is down."""
        try:
            acquired = await self._client.set(key, owner, ex=ttl_seconds, nx=True)
            if acquired:
                return True
            if await self._client.get(key) == owner:
                await self._client.expire(key, ttl_seconds)
                return True
            return False
        except Exception:
            return False

    async def publish(self, channel: str, payload: str) -> int:
        return int(await self._client.publish(channel, payload))

    async def close(self) -> None:
        await self._client.aclose()
