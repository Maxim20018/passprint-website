#!/usr/bin/env python3
"""
Système de cache Redis avancé pour PassPrint
Améliore les performances avec multi-niveaux et invalidation intelligente
"""
import redis
import json
import hashlib
import pickle
from datetime import datetime, timedelta
from functools import wraps
import os
import logging
from typing import Any, Optional, Dict, List, Union
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class CacheManager:
    """Gestionnaire de cache Redis avancé"""

    def __init__(self, app=None):
        self.app = app
        self.redis_client = None
        self.memory_cache = {}  # Cache mémoire de secours

        # Configuration
        self.default_ttl = int(os.getenv('CACHE_TTL', '300'))  # 5 minutes
        self.long_ttl = int(os.getenv('CACHE_LONG_TTL', '3600'))  # 1 heure
        self.short_ttl = int(os.getenv('CACHE_SHORT_TTL', '60'))  # 1 minute

        # Configuration des niveaux de cache
        self.cache_levels = {
            'memory': {'enabled': True, 'max_size': 1000},
            'redis': {'enabled': True, 'prefix': 'passprint:'}
        }

        self.connect()

    def connect(self):
        """Connexion à Redis avec reconnexion automatique"""
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                max_connections=20
            )

            # Test de connexion
            self.redis_client.ping()
            logger.info("✅ Connexion Redis établie")

        except Exception as e:
            logger.error(f"❌ Erreur connexion Redis: {e}")
            self.redis_client = None

    def generate_key(self, namespace: str, *args, **kwargs) -> str:
        """Générer une clé de cache unique et déterministe"""
        # Créer une signature basée sur les arguments
        key_components = [namespace]

        for arg in args:
            if isinstance(arg, (dict, list)):
                key_components.append(json.dumps(arg, sort_keys=True, default=str))
            else:
                key_components.append(str(arg))

        for k, v in sorted(kwargs.items()):
            if isinstance(v, (dict, list)):
                key_components.append(f"{k}:{json.dumps(v, sort_keys=True, default=str)}")
            else:
                key_components.append(f"{k}:{v}")

        key_string = "|".join(key_components)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:32]

        return f"{self.cache_levels['redis']['prefix']}{namespace}:{key_hash}"

    def set(self, key: str, data: Any, ttl: int = None, namespace: str = 'default') -> bool:
        """Stocker des données avec gestion multi-niveaux"""
        try:
            # Sérialiser les données
            if self.app:
                serialized_data = json.dumps(data, default=str, cls=CustomJSONEncoder)
            else:
                serialized_data = pickle.dumps(data)

            ttl = ttl or self.default_ttl

            # Cache Redis (niveau principal)
            if self.redis_client and self.cache_levels['redis']['enabled']:
                try:
                    redis_key = f"{key}:{namespace}"
                    self.redis_client.setex(redis_key, ttl, serialized_data)
                except Exception as e:
                    logger.warning(f"Erreur cache Redis: {e}")

            # Cache mémoire (niveau secours)
            if self.cache_levels['memory']['enabled']:
                self._set_memory_cache(key, data, ttl)

            return True

        except Exception as e:
            logger.error(f"Erreur cache set: {e}")
            return False

    def get(self, key: str, namespace: str = 'default') -> Any:
        """Récupérer des données avec fallback multi-niveaux"""
        # Essaie le cache mémoire d'abord (plus rapide)
        if self.cache_levels['memory']['enabled']:
            memory_data = self._get_memory_cache(key)
            if memory_data is not None:
                return memory_data

        # Essaie Redis ensuite
        if self.redis_client and self.cache_levels['redis']['enabled']:
            try:
                redis_key = f"{key}:{namespace}"
                data = self.redis_client.get(redis_key)
                if data:
                    if self.app:
                        return json.loads(data)
                    else:
                        return pickle.loads(data)
            except Exception as e:
                logger.warning(f"Erreur cache Redis get: {e}")

        return None

    def delete(self, key: str, namespace: str = 'default') -> bool:
        """Supprimer une clé de tous les niveaux de cache"""
        try:
            # Supprimer de Redis
            if self.redis_client and self.cache_levels['redis']['enabled']:
                redis_key = f"{key}:{namespace}"
                self.redis_client.delete(redis_key)

            # Supprimer du cache mémoire
            if self.cache_levels['memory']['enabled']:
                self._delete_memory_cache(key)

            return True

        except Exception as e:
            logger.error(f"Erreur cache delete: {e}")
            return False

    def exists(self, key: str, namespace: str = 'default') -> bool:
        """Vérifier l'existence dans n'importe quel niveau de cache"""
        # Vérifier le cache mémoire
        if self.cache_levels['memory']['enabled'] and key in self.memory_cache:
            return True

        # Vérifier Redis
        if self.redis_client and self.cache_levels['redis']['enabled']:
            try:
                redis_key = f"{key}:{namespace}"
                return self.redis_client.exists(redis_key) > 0
            except Exception as e:
                logger.warning(f"Erreur cache Redis exists: {e}")

        return False

    def clear_namespace(self, namespace: str):
        """Vider tous les caches d'un namespace"""
        try:
            # Vider Redis
            if self.redis_client and self.cache_levels['redis']['enabled']:
                pattern = f"{self.cache_levels['redis']['prefix']}{namespace}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)

            # Vider le cache mémoire
            if self.cache_levels['memory']['enabled']:
                keys_to_delete = [k for k in self.memory_cache.keys() if k.startswith(f"{namespace}:")]
                for key in keys_to_delete:
                    del self.memory_cache[key]

            logger.info(f"Cache namespace '{namespace}' vidé")
            return True

        except Exception as e:
            logger.error(f"Erreur cache clear namespace: {e}")
            return False

    def clear_all(self):
        """Vider tout le cache"""
        try:
            # Vider Redis
            if self.redis_client and self.cache_levels['redis']['enabled']:
                pattern = f"{self.cache_levels['redis']['prefix']}*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)

            # Vider le cache mémoire
            if self.cache_levels['memory']['enabled']:
                self.memory_cache.clear()

            logger.info("Tout le cache vidé")
            return True

        except Exception as e:
            logger.error(f"Erreur cache clear all: {e}")
            return False

    def _set_memory_cache(self, key: str, data: Any, ttl: int):
        """Gérer le cache mémoire avec limite de taille"""
        current_time = datetime.utcnow()
        expiry = current_time + timedelta(seconds=ttl)

        # Vérifier la limite de taille
        if len(self.memory_cache) >= self.cache_levels['memory']['max_size']:
            # Supprimer les entrées expirées
            self._cleanup_memory_cache()

            # Si toujours plein, supprimer les plus anciennes
            if len(self.memory_cache) >= self.cache_levels['memory']['max_size']:
                oldest_keys = sorted(self.memory_cache.keys(),
                                   key=lambda k: self.memory_cache[k]['expiry'])[:10]
                for old_key in oldest_keys:
                    del self.memory_cache[old_key]

        self.memory_cache[key] = {
            'data': data,
            'expiry': expiry
        }

    def _get_memory_cache(self, key: str) -> Any:
        """Récupérer du cache mémoire avec vérification d'expiration"""
        if key not in self.memory_cache:
            return None

        cache_entry = self.memory_cache[key]

        # Vérifier l'expiration
        if cache_entry['expiry'] < datetime.utcnow():
            del self.memory_cache[key]
            return None

        return cache_entry['data']

    def _delete_memory_cache(self, key: str):
        """Supprimer du cache mémoire"""
        if key in self.memory_cache:
            del self.memory_cache[key]

    def _cleanup_memory_cache(self):
        """Nettoyer les entrées expirées du cache mémoire"""
        current_time = datetime.utcnow()
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if entry['expiry'] < current_time
        ]

        for key in expired_keys:
            del self.memory_cache[key]

    def get_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques détaillées du cache"""
        stats = {
            'memory_cache': {
                'enabled': self.cache_levels['memory']['enabled'],
                'size': len(self.memory_cache),
                'max_size': self.cache_levels['memory']['max_size']
            },
            'redis_cache': {
                'enabled': self.cache_levels['redis']['enabled'],
                'connected': self.redis_client is not None
            }
        }

        if self.redis_client:
            try:
                info = self.redis_client.info()
                stats['redis_cache'].update({
                    'total_commands': info.get('total_commands_processed', 0),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0),
                    'memory_used': info.get('used_memory_human', '0B'),
                    'uptime_days': info.get('uptime_in_days', 0),
                    'connected_clients': info.get('connected_clients', 0),
                    'keys_count': len(self.redis_client.keys(f"{self.cache_levels['redis']['prefix']}*"))
                })
            except Exception as e:
                stats['redis_cache']['error'] = str(e)

        return stats

    def health_check(self) -> Dict[str, Any]:
        """Vérification de santé du système de cache"""
        health = {
            'status': 'healthy',
            'memory_cache': 'ok',
            'redis_cache': 'ok' if self.redis_client else 'disconnected'
        }

        # Test Redis
        if self.redis_client:
            try:
                self.redis_client.ping()
            except Exception:
                health['status'] = 'degraded'
                health['redis_cache'] = 'error'

        # Test cache mémoire
        try:
            self._cleanup_memory_cache()
        except Exception:
            health['status'] = 'degraded'
            health['memory_cache'] = 'error'

        return health

# Cache de modèles de données
class ModelCache:
    """Cache spécialisé pour les modèles de données"""

    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager

    def get_products(self, category: str = None, active_only: bool = True) -> List[Dict]:
        """Cache pour les produits"""
        key = self.cache.generate_key('products', category or 'all', active_only)
        cached = self.cache.get(key, 'products')

        if cached is not None:
            return cached

        # Logique de récupération depuis la base de données
        from models import Product

        query = Product.query
        if category:
            query = query.filter_by(category=category)
        if active_only:
            query = query.filter_by(is_active=True)

        products = [p.to_dict() for p in query.all()]

        # Mettre en cache
        self.cache.set(key, products, ttl=self.cache.long_ttl, namespace='products')
        return products

    def get_product(self, product_id: int) -> Optional[Dict]:
        """Cache pour un produit spécifique"""
        key = self.cache.generate_key('product', product_id)
        cached = self.cache.get(key, 'products')

        if cached is not None:
            return cached

        # Logique de récupération
        from models import Product
        product = Product.query.get(product_id)

        if product and product.is_active:
            product_dict = product.to_dict()
            self.cache.set(key, product_dict, ttl=self.cache.long_ttl, namespace='products')
            return product_dict

        return None

    def invalidate_products(self):
        """Invalider tout le cache des produits"""
        self.cache.clear_namespace('products')

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Cache pour les utilisateurs"""
        key = self.cache.generate_key('user', user_id)
        cached = self.cache.get(key, 'users')

        if cached is not None:
            return cached

        from models import User
        user = User.query.get(user_id)

        if user:
            user_dict = user.to_dict()
            self.cache.set(key, user_dict, ttl=self.cache.long_ttl, namespace='users')
            return user_dict

        return None

    def invalidate_user(self, user_id: int):
        """Invalider le cache d'un utilisateur spécifique"""
        key = self.cache.generate_key('user', user_id)
        self.cache.delete(key, 'users')

# Cache de configuration système
class ConfigCache:
    """Cache pour la configuration système"""

    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager

    def get_config(self, key: str, default: Any = None) -> Any:
        """Récupérer une configuration en cache"""
        cache_key = self.cache.generate_key('config', key)
        cached = self.cache.get(cache_key, 'config')

        if cached is not None:
            return cached

        # Récupérer depuis la base de données
        from models import SystemConfig
        config = SystemConfig.query.filter_by(key=key).first()

        if config:
            value = self._convert_value(config.value, config.data_type)
            self.cache.set(cache_key, value, ttl=self.cache.long_ttl, namespace='config')
            return value

        return default

    def set_config(self, key: str, value: Any, data_type: str = 'string'):
        """Mettre à jour une configuration en cache"""
        # Invalider le cache existant
        cache_key = self.cache.generate_key('config', key)
        self.cache.delete(cache_key, 'config')

        # Remettre en cache avec la nouvelle valeur
        self.cache.set(cache_key, value, ttl=self.cache.long_ttl, namespace='config')

    def _convert_value(self, value: str, data_type: str) -> Any:
        """Convertir la valeur selon son type"""
        if data_type == 'int':
            return int(value)
        elif data_type == 'float':
            return float(value)
        elif data_type == 'bool':
            return value.lower() in ('true', '1', 'yes', 'on')
        elif data_type == 'json':
            return json.loads(value)
        else:
            return value

# Décorateurs de cache
def cached(ttl: int = None, namespace: str = 'default', key_prefix: str = None):
    """Décorateur de cache pour les fonctions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Générer la clé de cache
            prefix = key_prefix or func.__name__
            cache_key = cache_manager.generate_key(prefix, *args, **kwargs)

            # Vérifier le cache
            cached_result = cache_manager.get(cache_key, namespace)
            if cached_result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_result

            # Exécuter la fonction
            logger.debug(f"Cache miss: {cache_key}")
            result = func(*args, **kwargs)

            # Mettre en cache
            cache_manager.set(cache_key, result, ttl=ttl, namespace=namespace)
            return result
        return wrapper
    return decorator

def cache_invalidate(namespace: str, key_pattern: str = None):
    """Décorateur pour invalider le cache après exécution"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Invalider le cache
            if key_pattern:
                cache_manager.clear_pattern(f"{namespace}:{key_pattern}")
            else:
                cache_manager.clear_namespace(namespace)

            return result
        return wrapper
    return decorator

# Context manager pour le cache conditionnel
@contextmanager
def conditional_cache(condition: bool = True, ttl: int = None, namespace: str = 'default'):
    """Context manager pour le cache conditionnel"""
    if not condition:
        yield None
        return

    cache_context = {
        'start_time': datetime.utcnow(),
        'operations': []
    }

    def cache_get(key: str):
        cache_key = cache_manager.generate_key(key)
        result = cache_manager.get(cache_key, namespace)
        cache_context['operations'].append(('get', key, result is not None))
        return result

    def cache_set(key: str, value: Any, custom_ttl: int = None):
        cache_key = cache_manager.generate_key(key)
        success = cache_manager.set(cache_key, value, ttl=custom_ttl or ttl, namespace=namespace)
        cache_context['operations'].append(('set', key, success))
        return success

    yield {
        'get': cache_get,
        'set': cache_set,
        'context': cache_context
    }

# Encoder JSON personnalisé pour les objets datetime
class CustomJSONEncoder(json.JSONEncoder):
    """Encodeur JSON personnalisé pour gérer les objets datetime"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Instance globale du cache
cache_manager = CacheManager()

# Instances spécialisées
model_cache = ModelCache(cache_manager)
config_cache = ConfigCache(cache_manager)

# Fonctions utilitaires
def get_cache_stats() -> Dict[str, Any]:
    """Obtenir les statistiques du cache"""
    return cache_manager.get_stats()

def clear_cache(namespace: str = None):
    """Vider le cache"""
    if namespace:
        return cache_manager.clear_namespace(namespace)
    else:
        return cache_manager.clear_all()

def cache_health_check() -> Dict[str, Any]:
    """Vérification de santé du cache"""
    return cache_manager.health_check()

if __name__ == "__main__":
    print("🚀 Cache Redis avancé PassPrint opérationnel!")

    # Test du système de cache
    test_key = cache_manager.generate_key('test', 'data')
    cache_manager.set(test_key, {'test': 'data'})

    retrieved = cache_manager.get(test_key)
    print(f"✅ Test cache: {retrieved}")

    stats = get_cache_stats()
    print(f"📊 Statistiques: {stats}")