"""
Cache em memória com TTL (Time-to-Live) para scrapers
Evita requests repetidos às fontes externas e respeita rate limits
"""
import time
from typing import Any, Optional
from threading import Lock


class TTLCache:
    """Cache com expiração automática baseada em tempo"""

    def __init__(self, ttl_seconds: int = 3600):
        self._cache: dict = {}
        self._ttl = ttl_seconds
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        """Retorna valor do cache, ou None se expirado/inexistente"""
        with self._lock:
            item = self._cache.get(key)
            if item is None:
                return None
            value, expires_at = item
            if time.monotonic() > expires_at:
                del self._cache[key]
                return None
            return value

    def set(self, key: str, value: Any) -> None:
        """Armazena valor com TTL"""
        with self._lock:
            self._cache[key] = (value, time.monotonic() + self._ttl)

    def delete(self, key: str) -> None:
        """Remove entrada do cache"""
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        """Limpa todo o cache"""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """Retorna número de entradas no cache (incluindo expiradas)"""
        with self._lock:
            return len(self._cache)

    def purge_expired(self) -> int:
        """Remove entradas expiradas, retorna quantidade removida"""
        now = time.monotonic()
        with self._lock:
            expired = [k for k, (_, exp) in self._cache.items() if now > exp]
            for k in expired:
                del self._cache[k]
            return len(expired)


# Instâncias compartilhadas com diferentes TTLs
cache_curto = TTLCache(ttl_seconds=300)    # 5 minutos
cache_medio = TTLCache(ttl_seconds=3600)   # 1 hora
cache_longo = TTLCache(ttl_seconds=86400)  # 24 horas
