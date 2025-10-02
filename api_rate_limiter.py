#!/usr/bin/env python3
"""
Rate limiting pour l'API PassPrint
Limite les requêtes pour éviter les abus
"""
from collections import defaultdict
import time

class RateLimiter:
    """Système de rate limiting"""

    def __init__(self):
        self.requests = defaultdict(list)
        self.limits = {
            'default': {'requests': 100, 'window': 3600},  # 100 req/heure
            'auth': {'requests': 5, 'window': 300},       # 5 req/5min
            'upload': {'requests': 10, 'window': 3600},   # 10 uploads/heure
        }

    def is_allowed(self, identifier: str, endpoint_type: str = 'default') -> bool:
        """Vérifier si la requête est autorisée"""
        limit = self.limits.get(endpoint_type, self.limits['default'])
        now = time.time()
        cutoff = now - limit['window']

        # Nettoyer les anciennes requêtes
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff
        ]

        # Vérifier la limite
        if len(self.requests[identifier]) >= limit['requests']:
            return False

        # Ajouter la requête actuelle
        self.requests[identifier].append(now)
        return True

# Instance globale du rate limiter
rate_limiter = RateLimiter()

def check_rate_limit(identifier: str, endpoint_type: str = 'default') -> bool:
    """Vérifier les limites de taux"""
    return rate_limiter.is_allowed(identifier, endpoint_type)

if __name__ == "__main__":
    print("Système de rate limiting opérationnel!")