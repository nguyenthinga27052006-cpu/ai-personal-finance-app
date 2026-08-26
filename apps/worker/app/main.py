import os
import time

from redis import Redis


def main() -> None:
    redis_url = os.environ["REDIS_URL"]
    client = Redis.from_url(redis_url, socket_connect_timeout=3)
    client.ping()
    print("worker foundation ready", flush=True)

    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
