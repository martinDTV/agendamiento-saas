"""
Tracking de agentes de soporte online por tenant — usa Redis directamente.

Set por tenant: `support:online:{tenant_id}` → user_ids de soporte conectados.
"""

import os
import redis


_client = None


def _get_redis():
    global _client
    if _client is None:
        _client = redis.from_url(os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/2'))
    return _client


def _key(tenant_id) -> str:
    return f'support:online:{tenant_id}'


def mark_online(tenant_id, user_id) -> None:
    _get_redis().sadd(_key(tenant_id), str(user_id))


def mark_offline(tenant_id, user_id) -> None:
    _get_redis().srem(_key(tenant_id), str(user_id))


def online_user_ids(tenant_id) -> list[int]:
    raw = _get_redis().smembers(_key(tenant_id))
    out = []
    for v in raw:
        try:
            out.append(int(v))
        except (TypeError, ValueError):
            continue
    return out


def is_online(tenant_id, user_id) -> bool:
    return _get_redis().sismember(_key(tenant_id), str(user_id))
