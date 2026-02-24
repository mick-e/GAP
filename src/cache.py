import json
import hashlib
import logging
from typing import Any

from src.config import get_settings

logger = logging.getLogger(__name__)

_redis = None


async def init_redis():
    global _redis
    settings = get_settings()
    if not settings.redis_url:
        logger.info("No REDIS_URL configured, caching disabled")
        return
    try:
        import redis.asyncio as aioredis
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        await _redis.ping()
        logger.info("Redis connected")
    except Exception as e:
        logger.warning(f"Redis unavailable, caching disabled: {e}")
        _redis = None


async def close_redis():
    global _redis
    if _redis:
        await _redis.close()
        _redis = None


def get_redis():
    return _redis


def _make_key(prefix: str, *args, **kwargs) -> str:
    raw = f"{prefix}:{args}:{sorted(kwargs.items())}"
    return f"bhapi:{hashlib.md5(raw.encode()).hexdigest()}"


async def cache_get(key: str) -> Any | None:
    if _redis is None:
        return None
    try:
        data = await _redis.get(key)
        return json.loads(data) if data else None
    except Exception:
        return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    if _redis is None:
        return
    try:
        await _redis.set(key, json.dumps(value, default=str), ex=ttl)
    except Exception:
        pass


async def cache_delete(key: str) -> None:
    if _redis is None:
        return
    try:
        await _redis.delete(key)
    except Exception:
        pass


async def cache_invalidate_pattern(pattern: str) -> None:
    if _redis is None:
        return
    try:
        cursor = 0
        while True:
            cursor, keys = await _redis.scan(cursor, match=f"bhapi:{pattern}*", count=100)
            if keys:
                await _redis.delete(*keys)
            if cursor == 0:
                break
    except Exception:
        pass


def cached(prefix: str, ttl: int = 300):
    """Decorator for caching async function results."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            key = _make_key(prefix, *args[1:], **kwargs)  # skip self
            result = await cache_get(key)
            if result is not None:
                return result
            result = await func(*args, **kwargs)
            await cache_set(key, result, ttl)
            return result
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator
