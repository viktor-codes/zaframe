"""
Rate limiting для чувствительных эндпоинтов (Magic Link, refresh и т.д.).

Используется SlowAPI; лимиты привязаны к IP (get_remote_address).
In-memory backend по умолчанию; для нескольких инстансов — Redis (см. limits).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
