import pytest
from unittest.mock import patch, AsyncMock

from src.cache import cache_get, cache_set, cache_delete, cache_invalidate_pattern, cached


async def test_cache_get_no_redis():
    """Cache returns None when Redis not available."""
    result = await cache_get("test-key")
    assert result is None


async def test_cache_set_no_redis():
    """Cache set does nothing when Redis not available."""
    await cache_set("test-key", {"data": True})
    # Should not raise


async def test_cache_delete_no_redis():
    """Cache delete does nothing when Redis not available."""
    await cache_delete("test-key")


async def test_cache_invalidate_no_redis():
    """Cache invalidate does nothing when Redis not available."""
    await cache_invalidate_pattern("test*")


async def test_cached_decorator():
    """Cached decorator should call function when no cache."""
    call_count = 0

    class FakeService:
        @cached("test", ttl=60)
        async def get_data(self, key):
            nonlocal call_count
            call_count += 1
            return {"key": key}

    svc = FakeService()
    result = await svc.get_data("foo")
    assert result == {"key": "foo"}
    assert call_count == 1

    # Call again - still calls function since no Redis
    result = await svc.get_data("foo")
    assert call_count == 2


async def test_cache_with_fakeredis():
    """Test cache operations with fakeredis if available."""
    try:
        import fakeredis.aioredis
    except ImportError:
        pytest.skip("fakeredis not installed")

    import src.cache as cache_mod
    fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    original = cache_mod._redis
    cache_mod._redis = fake_redis

    try:
        await cache_set("test-key", {"hello": "world"}, ttl=60)
        result = await cache_get("test-key")
        assert result == {"hello": "world"}

        await cache_delete("test-key")
        result = await cache_get("test-key")
        assert result is None
    finally:
        cache_mod._redis = original
        await fake_redis.close()
