from collections.abc import Callable

from redis import Redis


def run_once(redis: Redis, evaluate: Callable[[], int], *, lock_key: str = "notifications:cycle") -> int:
    lock = redis.lock(lock_key, timeout=55, blocking=False)
    if not lock.acquire(blocking=False):
        return 0
    try:
        return evaluate()
    finally:
        lock.release()