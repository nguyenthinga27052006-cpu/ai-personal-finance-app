from collections.abc import Callable

from redis import Redis


def run_recommendation_cycle(redis: Redis, evaluate: Callable[[], int]) -> int:
    lock = redis.lock("recommendations:cycle", timeout=55, blocking=False)
    if not lock.acquire(blocking=False):
        return 0
    try:
        return evaluate()
    finally:
        lock.release()