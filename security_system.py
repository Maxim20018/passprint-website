#!/usr/bin/env python3
"""
Système de sécurité avancé pour PassPrint
Protection CSRF, rate limiting, audit logs
"""
import hashlib
import time
from collections import defaultdict
from datetime import datetime, timedelta
import sqlite3
import os

class SecuritySystem:
    """Système de sécurité complet"""

    def __init__(self):
        self.db_path = 'passprint.db'
        self.rate_limits = defaultdict(list)
        self.csrf_tokens = {}

    def generate_csrf_token(self, session_id: str) -> str:
        """Générer un token CSRF"""
        token = hashlib.sha256(f"{session_id}_{time.time()}_{os.urandom(32).hex()}".encode()).hexdigest()
        self.csrf_tokens[token] = {
            'session_id': session_id,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(hours=1)
        }
        return token

    def validate_csrf_token(self, token: str, session_id: str) -> bool:
        """Valider un token CSRF"""
        if token not in self.csrf_tokens:
            return False

        token_data = self.csrf_tokens[token]

        # Vérifier l'expiration
        if token_data['expires_at'] < datetime.utcnow():
            del self.csrf_tokens[token]
            return False

        # Vérifier la session
        if token_data['session_id'] != session_id:
            return False

        return True

    def check_rate_limit(self, identifier: str, limit: int = 100, window: int = 3600) -> bool:
        """
        Vérifier les limites de taux

        Args:
            identifier: Identifiant (IP, user_id, etc.)
            limit: Nombre maximum de requêtes
            window: Fenêtre de temps en secondes

        Returns:
            True si dans les limites, False sinon
        """
        now = time.time()
        cutoff = now - window

        # Nettoyer les anciennes entrées
        self.rate_limits[identifier] = [t for t in self.rate_limits[identifier] if t > cutoff]

        # Vérifier la limite
        if len(self.rate_limits[identifier]) >= limit:
            return False

        # Ajouter la requête actuelle
        self.rate_limits[identifier].append(now)
        return True

    def log_audit_event(self, user_id: str, action: str, details: str, ip_address: str = None):
        """Enregistrer un événement d'audit"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO audit_logs (user_id, action, details, ip_address, created_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, action, details, ip_address))

                conn.commit()

        except Exception as e:
            print(f"Erreur log audit: {e}")

    def get_audit_logs(self, limit: int = 100) -> list:
        """Récupérer les logs d'audit"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT * FROM audit_logs
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (limit,))

                return [
                    {
                        'id': row[0],
                        'user_id': row[1],
                        'action': row[2],
                        'details': row[3],
                        'ip_address': row[4],
                        'created_at': row[5]
                    }
                    for row in cursor.fetchall()
                ]

        except Exception as e:
            return []

# Instance globale du système de sécurité
security_system = SecuritySystem()

def generate_csrf_token(session_id: str) -> str:
    """Générer un token CSRF"""
    return security_system.generate_csrf_token(session_id)

def validate_csrf_token(token: str, session_id: str) -> bool:
    """Valider un token CSRF"""
    return security_system.validate_csrf_token(token, session_id)

def check_rate_limit(identifier: str, limit: int = 100, window: int = 3600) -> bool:
    """Vérifier les limites de taux"""
    return security_system.check_rate_limit(identifier, limit, window)

def log_audit_event(user_id: str, action: str, details: str, ip_address: str = None):
    """Enregistrer un événement d'audit"""
    security_system.log_audit_event(user_id, action, details, ip_address)

if __name__ == "__main__":
    print("Système de sécurité avancé opérationnel!")