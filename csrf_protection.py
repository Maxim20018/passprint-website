#!/usr/bin/env python3
"""
Protection CSRF complète pour PassPrint
Sécurise les formulaires contre les attaques CSRF
"""
import hashlib
import os
import time
from flask import session, request, abort

class CSRFProtection:
    """Protection CSRF avancée"""

    def __init__(self):
        self.secret_key = os.getenv('SECRET_KEY', 'csrf-secret-key')

    def generate_token(self):
        """Générer un token CSRF"""
        timestamp = str(int(time.time()))
        token_data = f"{timestamp}:{os.urandom(32).hex()}"
        token = hashlib.sha256(f"{token_data}:{self.secret_key}".encode()).hexdigest()
        return f"{timestamp}:{token}"

    def validate_token(self, token):
        """Valider un token CSRF"""
        try:
            if not token or ':' not in token:
                return False

            timestamp_str, token_hash = token.split(':', 1)
            timestamp = int(timestamp_str)

            # Vérifier l'expiration (1 heure)
            if time.time() - timestamp > 3600:
                return False

            # Recalculer le hash
            token_data = f"{timestamp_str}:{token_hash.split(':')[0]}"
            expected_hash = hashlib.sha256(f"{token_data}:{self.secret_key}".encode()).hexdigest()

            return token_hash == expected_hash

        except Exception:
            return False

    def protect(self, f):
        """Décorateur de protection CSRF"""
        def decorated_function(*args, **kwargs):
            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')

                if not token or not self.validate_token(token):
                    abort(403, 'Token CSRF invalide ou manquant')

            return f(*args, **kwargs)
        return decorated_function

# Instance globale de protection CSRF
csrf_protection = CSRFProtection()

def generate_csrf_token():
    """Générer un token CSRF"""
    return csrf_protection.generate_token()

def validate_csrf_token(token):
    """Valider un token CSRF"""
    return csrf_protection.validate_token(token)

def csrf_protect(f):
    """Décorateur de protection CSRF"""
    return csrf_protection.protect(f)

if __name__ == "__main__":
    print("Protection CSRF opérationnelle!")