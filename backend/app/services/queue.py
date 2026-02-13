import json
from typing import Any

import redis

from app.core.config import get_settings

settings = get_settings()

CRAWL_QUEUE = 'gov:crawl:queue'
AI_QUEUE = 'gov:ai:queue'


def get_redis_client() -> redis.Redis:
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


def enqueue(queue_name: str, payload: dict[str, Any]) -> None:
    client = get_redis_client()
    client.rpush(queue_name, json.dumps(payload, ensure_ascii=False))


def dequeue(queue_name: str, timeout: int = 5) -> dict[str, Any] | None:
    client = get_redis_client()
    item = client.blpop(queue_name, timeout=timeout)
    if not item:
        return None
    _, raw = item
    return json.loads(raw)
