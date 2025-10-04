#!/usr/bin/env python3
"""
Système de sécurité avancé pour PassPrint
Protection CSRF, rate limiting, audit logs, sécurité des données
"""
import hashlib
import time
import re
import secrets
from collections import defaultdict
from datetime import datetime, timedelta
from functools import wraps
from flask import request, g, jsonify
import os
import logging
from models import db, AuditLog, User

class SecuritySystem:
    """Système de sécurité complet"""

    def __init__(self, app=None):
        self.app = app
        self.rate_limits = defaultdict(list)
        self.csrf_tokens = {}
        self.failed_logins = defaultdict(list)
        self.suspicious_ips = set()
        self.logger = logging.getLogger(__name__)

        # Configuration de sécurité
        self.max_login_attempts = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))
        self.lockout_duration = int(os.getenv('LOCKOUT_DURATION_MINUTES', '15'))
        self.password_min_length = int(os.getenv('PASSWORD_MIN_LENGTH', '8'))
        self.session_timeout = int(os.getenv('SESSION_TIMEOUT_MINUTES', '60'))

    def generate_csrf_token(self, session_id: str) -> str:
        """Générer un token CSRF sécurisé"""
        token_data = f"{session_id}_{time.time()}_{secrets.token_hex(32)}"
        token = hashlib.sha256(token_data.encode()).hexdigest()

        self.csrf_tokens[token] = {
            'session_id': session_id,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(hours=1),
            'used': False
        }
        return token

    def validate_csrf_token(self, token: str, session_id: str) -> bool:
        """Valider un token CSRF avec protection contre la réutilisation"""
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

        # Vérifier la réutilisation
        if token_data['used']:
            return False

        # Marquer comme utilisé
        token_data['used'] = True
        return True

    def check_rate_limit(self, identifier: str, limit: int = 100, window: int = 3600) -> dict:
        """
        Vérifier les limites de taux avec informations détaillées

        Returns:
            dict: {'allowed': bool, 'remaining': int, 'reset_time': datetime}
        """
        now = time.time()
        cutoff = now - window

        # Nettoyer les anciennes entrées
        self.rate_limits[identifier] = [t for t in self.rate_limits[identifier] if t > cutoff]

        # Vérifier la limite
        if len(self.rate_limits[identifier]) >= limit:
            reset_time = self.rate_limits[identifier][0] + window if self.rate_limits[identifier] else now + window
            return {
                'allowed': False,
                'remaining': 0,
                'reset_time': datetime.fromtimestamp(reset_time)
            }

        # Ajouter la requête actuelle
        self.rate_limits[identifier].append(now)

        remaining = limit - len(self.rate_limits[identifier])
        reset_time = now + window

        return {
            'allowed': True,
            'remaining': remaining,
            'reset_time': datetime.fromtimestamp(reset_time)
        }

    def validate_password_strength(self, password: str) -> dict:
        """Valider la force d'un mot de passe"""
        if not password:
            return {'valid': False, 'errors': ['Le mot de passe est requis']}

        errors = []

        if len(password) < self.password_min_length:
            errors.append(f'Le mot de passe doit contenir au moins {self.password_min_length} caractères')

        if not re.search(r'[A-Z]', password):
            errors.append('Le mot de passe doit contenir au moins une majuscule')

        if not re.search(r'[a-z]', password):
            errors.append('Le mot de passe doit contenir au moins une minuscule')

        if not re.search(r'\d', password):
            errors.append('Le mot de passe doit contenir au moins un chiffre')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append('Le mot de passe doit contenir au moins un caractère spécial')

        # Vérifier les mots de passe courants
        common_passwords = {'password', '123456', 'password123', 'admin', 'qwerty'}
        if password.lower() in common_passwords:
            errors.append('Ce mot de passe est trop courant')

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'strength': self._calculate_password_strength(password)
        }

    def _calculate_password_strength(self, password: str) -> str:
        """Calculer la force du mot de passe"""
        score = 0

        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if re.search(r'[A-Z]', password):
            score += 1
        if re.search(r'[a-z]', password):
            score += 1
        if re.search(r'\d', password):
            score += 1
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1

        if score <= 2:
            return 'weak'
        elif score <= 4:
            return 'medium'
        else:
            return 'strong'

    def check_account_lockout(self, email: str) -> dict:
        """Vérifier si un compte est verrouillé"""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=self.lockout_duration)

        # Nettoyer les anciennes tentatives
        self.failed_logins[email] = [
            attempt for attempt in self.failed_logins[email]
            if attempt > cutoff
        ]

        attempts = len(self.failed_logins[email])

        if attempts >= self.max_login_attempts:
            return {
                'locked': True,
                'remaining_time': self.failed_logins[email][0] + timedelta(minutes=self.lockout_duration) - now,
                'attempts': attempts
            }

        return {
            'locked': False,
            'remaining_attempts': self.max_login_attempts - attempts,
            'attempts': attempts
        }

    def record_failed_login(self, email: str, ip_address: str = None):
        """Enregistrer une tentative de connexion échouée"""
        now = datetime.utcnow()
        self.failed_logins[email].append(now)

        # Log de sécurité
        self.log_security_event(
            user_id=None,
            action='failed_login',
            details=f'Tentative de connexion échouée pour {email}',
            ip_address=ip_address,
            status='failure'
        )

    def record_successful_login(self, user_id: int, ip_address: str = None, user_agent: str = None):
        """Enregistrer une connexion réussie"""
        # Réinitialiser les tentatives échouées
        if user_id:
            user = User.query.get(user_id)
            if user:
                self.failed_logins[user.email] = []

        # Log de sécurité
        self.log_security_event(
            user_id=user_id,
            action='successful_login',
            details='Connexion réussie',
            ip_address=ip_address,
            user_agent=user_agent,
            status='success'
        )

    def detect_suspicious_activity(self, ip_address: str, user_agent: str = None) -> dict:
        """Détecter l'activité suspecte"""
        suspicious_indicators = []

        # Vérifier les IPs suspectes
        if ip_address in self.suspicious_ips:
            suspicious_indicators.append('IP dans la liste des IPs suspectes')

        # Vérifier les user-agents suspects
        if user_agent:
            bot_indicators = ['bot', 'crawler', 'spider', 'scraper']
            if any(indicator in user_agent.lower() for indicator in bot_indicators):
                suspicious_indicators.append('User-Agent suspect')

        # Vérifier le taux de requêtes
        rate_check = self.check_rate_limit(f"suspicious_{ip_address}", limit=1000, window=300)
        if not rate_check['allowed']:
            suspicious_indicators.append('Taux de requêtes élevé')

        return {
            'suspicious': len(suspicious_indicators) > 0,
            'indicators': suspicious_indicators,
            'risk_level': 'high' if len(suspicious_indicators) >= 2 else 'medium' if len(suspicious_indicators) == 1 else 'low'
        }

    def log_security_event(self, user_id: str = None, action: str = '', details: str = '',
                          ip_address: str = None, user_agent: str = None, resource_type: str = None,
                          resource_id: str = None, status: str = 'success'):
        """Enregistrer un événement de sécurité avec la nouvelle structure"""
        try:
            if not self.app:
                return

            with self.app.app_context():
                # Créer le log d'audit
                audit_log = AuditLog(
                    user_id=user_id,
                    action=action,
                    details=details,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    status=status
                )

                db.session.add(audit_log)
                db.session.commit()

                # Log additionnel pour les événements critiques
                if status == 'failure' or action in ['failed_login', 'unauthorized_access']:
                    self.logger.warning(f"Sécurité: {action} - {details} - IP: {ip_address}")

        except Exception as e:
            self.logger.error(f"Erreur enregistrement événement sécurité: {e}")

    def get_client_ip(self) -> str:
        """Obtenir l'adresse IP réelle du client"""
        # Vérifier les headers de proxy
        headers = ['X-Forwarded-For', 'X-Real-IP', 'CF-Connecting-IP']

        for header in headers:
            ip = request.headers.get(header)
            if ip:
                # Prendre la première IP si multiple
                return ip.split(',')[0].strip()

        return request.remote_addr or 'unknown'

    def sanitize_input(self, data: dict) -> dict:
        """Nettoyer et valider les données d'entrée"""
        sanitized = {}

        for key, value in data.items():
            if isinstance(value, str):
                # Supprimer les espaces en début et fin
                clean_value = value.strip()

                # Vérifier la longueur
                if len(clean_value) > 1000:  # Limite arbitraire
                    clean_value = clean_value[:1000]

                # Supprimer les caractères de contrôle
                clean_value = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', clean_value)

                sanitized[key] = clean_value
            else:
                sanitized[key] = value

        return sanitized

    def validate_email_format(self, email: str) -> bool:
        """Valider le format d'un email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def generate_secure_token(self, length: int = 32) -> str:
        """Générer un token sécurisé"""
        return secrets.token_urlsafe(length)

# Instance globale du système de sécurité
security_system = SecuritySystem()

# Décorateurs de sécurité Flask
def require_auth(f):
    """Décorateur nécessitant une authentification"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Vérifier le token JWT
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            security_system.log_security_event(
                action='unauthorized_access',
                details='Token manquant ou invalide',
                ip_address=security_system.get_client_ip(),
                status='failure'
            )
            return jsonify({'error': 'Authentification requise'}), 401

        token = auth_header.split(' ')[1]

        try:
            # Ici vous devriez décoder et vérifier le token JWT
            # Pour l'instant, on simule
            user_id = token  # Remplacer par la vraie logique JWT

            # Vérifier l'activité suspecte
            ip_address = security_system.get_client_ip()
            user_agent = request.headers.get('User-Agent')

            suspicious = security_system.detect_suspicious_activity(ip_address, user_agent)
            if suspicious['suspicious']:
                security_system.log_security_event(
                    user_id=user_id,
                    action='suspicious_activity',
                    details=f"Activité suspecte détectée: {', '.join(suspicious['indicators'])}",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    status='warning'
                )

            g.user_id = user_id
            return f(*args, **kwargs)

        except Exception as e:
            security_system.log_security_event(
                action='token_validation_failed',
                details=f'Erreur validation token: {str(e)}',
                ip_address=security_system.get_client_ip(),
                status='failure'
            )
            return jsonify({'error': 'Token invalide'}), 401

    return decorated

def rate_limit(limit: int = 100, window: int = 3600):
    """Décorateur de limitation de taux"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            identifier = security_system.get_client_ip()
            rate_check = security_system.check_rate_limit(identifier, limit, window)

            if not rate_check['allowed']:
                security_system.log_security_event(
                    action='rate_limit_exceeded',
                    details=f'Limite de taux dépassée: {limit} requêtes en {window} secondes',
                    ip_address=identifier,
                    status='warning'
                )
                return jsonify({
                    'error': 'Limite de taux dépassée',
                    'remaining': rate_check['remaining'],
                    'reset_time': rate_check['reset_time'].isoformat()
                }), 429

            return f(*args, **kwargs)
        return decorated
    return decorator

# Fonctions utilitaires
def generate_csrf_token(session_id: str) -> str:
    """Générer un token CSRF"""
    return security_system.generate_csrf_token(session_id)

def validate_csrf_token(token: str, session_id: str) -> bool:
    """Valider un token CSRF"""
    return security_system.validate_csrf_token(token, session_id)

def check_rate_limit(identifier: str, limit: int = 100, window: int = 3600) -> bool:
    """Vérifier les limites de taux"""
    return security_system.check_rate_limit(identifier, limit, window)['allowed']

def log_security_event(user_id: str = None, action: str = '', details: str = '',
                      ip_address: str = None, user_agent: str = None, resource_type: str = None,
                      resource_id: str = None, status: str = 'success'):
    """Enregistrer un événement de sécurité"""
    security_system.log_security_event(user_id, action, details, ip_address, user_agent,
                                     resource_type, resource_id, status)

def validate_password_strength(password: str) -> dict:
    """Valider la force d'un mot de passe"""
    return security_system.validate_password_strength(password)

def get_client_ip() -> str:
    """Obtenir l'adresse IP du client"""
    return security_system.get_client_ip()

def sanitize_input(data: dict) -> dict:
    """Nettoyer les données d'entrée"""
    return security_system.sanitize_input(data)

if __name__ == "__main__":
    print("🔒 Système de sécurité avancé opérationnel!")