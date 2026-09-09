import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from redis import Redis
from redis.exceptions import RedisError

from app.recommendation_scheduler import run_recommendation_cycle
from app.scheduler import run_once


def evaluate_api() -> int:
    request = Request(
        f"{os.environ.get('API_URL', 'http://api:8000')}/api/v1/internal/notifications/evaluate",
        method="POST",
        headers={"X-Worker-Token": os.environ["NOTIFICATION_WORKER_TOKEN"]},
    )
    with urlopen(request, timeout=20) as response:
        return int(response.read().decode().strip() or 0)


def evaluate_recommendations_api() -> int:
    request = Request(
        f"{os.environ.get('API_URL', 'http://api:8000')}/api/v1/recommendations/internal/evaluate",
        method="POST",
        headers={"X-Worker-Token": os.environ["NOTIFICATION_WORKER_TOKEN"]},
    )
    with urlopen(request, timeout=20) as response:
        return int(response.read().decode().strip() or 0)


def run_notification_cycle(client: Redis) -> None:
    try:
        created = run_once(client, evaluate_api)
        if created:
            print(f"notification cycle created {created} item(s)", flush=True)
    except (HTTPError, URLError, KeyError, RedisError, ValueError, OSError) as exc:
        print(f"notification cycle failed: {exc}", flush=True)


def run_recommendation_cycle_once(client: Redis) -> None:
    try:
        created = run_recommendation_cycle(client, evaluate_recommendations_api)
        if created:
            print(f"recommendation cycle created {created} item(s)", flush=True)
    except (HTTPError, URLError, KeyError, RedisError, ValueError, OSError) as exc:
        print(f"recommendation cycle failed: {exc}", flush=True)


def main() -> None:
    redis_url = os.environ["REDIS_URL"]
    client = Redis.from_url(redis_url, socket_connect_timeout=3)
    client.ping()
    print("worker foundation ready", flush=True)

    while True:
        run_notification_cycle(client)
        run_recommendation_cycle_once(client)
        time.sleep(60)


if __name__ == "__main__":
    main()
