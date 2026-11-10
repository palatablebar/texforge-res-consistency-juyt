"""Redis 客户端：限流窗口、配方生成锁、预设存储。"""
import redis

from app.config.settings import settings

_client = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


def acquire_generation_lock(recipe_id: int, ttl: int = 300) -> bool:
    return bool(get_redis().set(f"qlock:{recipe_id}", "1", nx=True, ex=ttl))


def release_generation_lock(recipe_id: int) -> None:
    try:
        get_redis().delete(f"qlock:{recipe_id}")
    except Exception:  # noqa: BLE001
        pass


def sliding_window_hit(key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
    """简单滑动窗口：INCR + EXPIRE。返回 (是否放行, retry_after)。"""
    try:
        client = get_redis()
        pipe = client.pipeline()
        pipe.incr(key)
        pipe.ttl(key)
        count, ttl = pipe.execute()
        if ttl is None or ttl < 0:
            client.expire(key, window_seconds)
            ttl = window_seconds
        if count > limit:
            return False, int(ttl)
        return True, 0
    except Exception:  # noqa: BLE001 - Redis 异常时放行，避免阻塞业务
        return True, 0
