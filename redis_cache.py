#!/usr/bin/env python3
"""
Système de cache Redis pour PassPrint
Améliore les performances avec mise en cache intelligente
"""
import redis
import json
import hashlib
from typing import Any, Optional
from datetime import timedelta
import os

class RedisCache:
    """Système de cache Redis avancé"""

    def __init__(self):
        self.redis_client = None
        self.default_ttl = 3600  # 1 heure
        self.connect()

    def connect(self):
        """Connexion à Redis"""
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 0)),
                password=os.getenv('REDIS_PASSWORD'),
                decode_responses=True
            )
            self.redis_client.ping()
            print("Redis connecté avec succès")
        except Exception as e:
            print(f"Redis non disponible: {e}")
            self.redis_client = None

    def _make_key(self, key: str) -> str:
        """Créer une clé de cache unique"""
        return f"passprint:{hashlib.md5(key.encode()).hexdigest()}"

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Définir une valeur en cache"""
        if not self.redis_client:
            return False

        try:
            cache_key = self._make_key(key)
            serialized_value = json.dumps(value, default=str)
            ttl = ttl or self.default_ttl

            return self.redis_client.setex(cache_key, ttl, serialized_value)
        except Exception as e:
            print(f"Erreur cache set: {e}")
            return False

    def get(self, key: str) -> Any:
        """Récupérer une valeur du cache"""
        if not self.redis_client:
            return None

        try:
            cache_key = self._make_key(key)
            value = self.redis_client.get(cache_key)

            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Erreur cache get: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Supprimer une valeur du cache"""
        if not self.redis_client:
            return False

        try:
            cache_key = self._make_key(key)
            return self.redis_client.delete(cache_key) > 0
        except Exception as e:
            print(f"Erreur cache delete: {e}")
            return False

    def clear(self) -> bool:
        """Vider tout le cache"""
        if not self.redis_client:
            return False

        try:
            return self.redis_client.flushdb()
        except Exception as e:
            print(f"Erreur cache clear: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Vérifier si une clé existe en cache"""
        if not self.redis_client:
            return False

        try:
            cache_key = self._make_key(key)
            return self.redis_client.exists(cache_key) > 0
        except Exception as e:
            print(f"Erreur cache exists: {e}")
            return False

    def increment(self, key: str, amount: int = 1) -> int:
        """Incrémenter une valeur numérique"""
        if not self.redis_client:
            return 0

        try:
            cache_key = self._make_key(key)
            return self.redis_client.incr(cache_key, amount)
        except Exception as e:
            print(f"Erreur cache increment: {e}")
            return 0

# Instance globale du cache Redis
cache = RedisCache()

def cache_response(ttl: int = 3600):
    """Décorateur pour mettre en cache les réponses API"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Créer une clé unique basée sur la fonction et les arguments
            key_parts = [func.__name__]
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
            cache_key = ":".join(key_parts)

            # Vérifier le cache
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result

            # Exécuter la fonction
            result = func(*args, **kwargs)

            # Mettre en cache
            cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator

def invalidate_cache(pattern: str):
    """Invalider le cache selon un pattern"""
    if not cache.redis_client:
        return

    try:
        # Récupérer toutes les clés matching le pattern
        keys = cache.redis_client.keys(f"passprint:*{pattern}*")
        if keys:
            cache.redis_client.delete(*keys)
    except Exception as e:
        print(f"Erreur invalidation cache: {e}")

def get_cache_stats() -> dict:
    """Obtenir les statistiques du cache"""
    if not cache.redis_client:
        return {'error': 'Redis non disponible'}

    try:
        info = cache.redis_client.info()
        return {
            'connected': True,
            'keys': info.get('db0', {}).get('keys', 0),
            'memory_used': info.get('memory', {}).get('used_memory_human', '0B'),
            'uptime': info.get('uptime_in_days', 0)
        }
    except Exception as e:
        return {'error': str(e)}

if __name__ == "__main__":
    # Test du cache Redis
    print("Test du système de cache Redis...")

    # Test de base
    cache.set("test_key", {"test": "data"}, 60)
    result = cache.get("test_key")
    print(f"Cache test: {result}")

    print("Système de cache Redis opérationnel!")