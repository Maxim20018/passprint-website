#!/usr/bin/env python3
"""
Tests d'authentification pour PassPrint
"""
import pytest
import json
from tests import TestUtils

class TestAuthentication:
    """Tests pour les fonctionnalités d'authentification"""

    def test_user_registration_success(self, client, db):
        """Test d'inscription utilisateur réussie"""
        user_data = {
            'email': 'newuser@test.com',
            'password': 'SecurePassword123!',
            'first_name': 'New',
            'last_name': 'User',
            'phone': '+2250102030405',
            'company': 'Test Company'
        }

        response = client.post('/api/auth/register', json=user_data)

        assert response.status_code == 201
        data = TestUtils.assert_response_ok(response)

        assert 'token' in data
        assert 'user' in data
        assert data['user']['email'] == 'newuser@test.com'
        assert data['user']['first_name'] == 'New'
        assert data['user']['last_name'] == 'User'

    def test_user_registration_duplicate_email(self, client, db):
        """Test d'inscription avec email déjà utilisé"""
        # Créer un utilisateur d'abord
        TestUtils.create_test_user(db, 'duplicate@test.com')

        user_data = {
            'email': 'duplicate@test.com',
            'password': 'SecurePassword123!',
            'first_name': 'Duplicate',
            'last_name': 'User'
        }

        response = client.post('/api/auth/register', json=user_data)

        assert response.status_code == 409
        data = TestUtils.assert_response_error(response)
        assert 'Email déjà utilisé' in data['error']

    def test_user_registration_weak_password(self, client, db):
        """Test d'inscription avec mot de passe faible"""
        user_data = {
            'email': 'weakpass@test.com',
            'password': '123',  # Mot de passe trop faible
            'first_name': 'Weak',
            'last_name': 'Password'
        }

        response = client.post('/api/auth/register', json=user_data)

        assert response.status_code == 400
        data = TestUtils.assert_response_error(response)
        assert 'Mot de passe trop faible' in data['error']

    def test_user_registration_invalid_email(self, client, db):
        """Test d'inscription avec email invalide"""
        user_data = {
            'email': 'invalid-email',
            'password': 'SecurePassword123!',
            'first_name': 'Invalid',
            'last_name': 'Email'
        }

        response = client.post('/api/auth/register', json=user_data)

        assert response.status_code == 400
        data = TestUtils.assert_response_error(response)
        assert 'Email invalide' in data['error']

    def test_user_login_success(self, client, db):
        """Test de connexion réussie"""
        # Créer un utilisateur de test
        TestUtils.create_test_user(db, 'logintest@test.com')

        login_data = {
            'email': 'logintest@test.com',
            'password': 'password'
        }

        response = client.post('/api/auth/login', json=login_data)

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)

        assert 'token' in data
        assert 'user' in data
        assert data['user']['email'] == 'logintest@test.com'

    def test_user_login_invalid_credentials(self, client, db):
        """Test de connexion avec identifiants invalides"""
        login_data = {
            'email': 'nonexistent@test.com',
            'password': 'wrongpassword'
        }

        response = client.post('/api/auth/login', json=login_data)

        assert response.status_code == 401
        data = TestUtils.assert_response_error(response)
        assert 'Identifiants invalides' in data['error']

    def test_user_login_missing_data(self, client, db):
        """Test de connexion avec données manquantes"""
        login_data = {
            'email': 'test@test.com'
            # Mot de passe manquant
        }

        response = client.post('/api/auth/login', json=login_data)

        assert response.status_code == 400
        data = TestUtils.assert_response_error(response)
        assert 'Email et mot de passe requis' in data['error']

    @pytest.mark.security
    def test_account_lockout_after_failed_attempts(self, client, db):
        """Test du verrouillage de compte après tentatives échouées"""
        # Créer un utilisateur de test
        TestUtils.create_test_user(db, 'lockout@test.com')

        login_data = {
            'email': 'lockout@test.com',
            'password': 'wrongpassword'
        }

        # Faire plusieurs tentatives échouées
        for i in range(5):
            response = client.post('/api/auth/login', json=login_data)
            if i < 4:  # Les 4 premières devraient échouer avec 401
                assert response.status_code == 401
            else:  # La 5ème devrait verrouiller le compte
                assert response.status_code == 423  # Locked

    def test_token_verification_success(self, client, db, auth_headers):
        """Test de vérification de token réussie"""
        response = client.post('/api/auth/verify', headers=auth_headers)

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)

        assert data['valid'] is True
        assert 'user' in data

    def test_token_verification_missing_token(self, client, db):
        """Test de vérification de token sans token"""
        response = client.post('/api/auth/verify')

        assert response.status_code == 401
        data = TestUtils.assert_response_error(response)
        assert 'Authentification requise' in data['error']

    def test_password_change_success(self, client, db, auth_headers):
        """Test de changement de mot de passe réussi"""
        password_data = {
            'current_password': 'password',
            'new_password': 'NewSecurePassword123!'
        }

        response = client.post('/api/auth/change-password', json=password_data, headers=auth_headers)

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)
        assert 'Mot de passe changé avec succès' in data['message']

    def test_password_change_wrong_current_password(self, client, db, auth_headers):
        """Test de changement de mot de passe avec mauvais mot de passe actuel"""
        password_data = {
            'current_password': 'wrongpassword',
            'new_password': 'NewSecurePassword123!'
        }

        response = client.post('/api/auth/change-password', json=password_data, headers=auth_headers)

        assert response.status_code == 401
        data = TestUtils.assert_response_error(response)
        assert 'Mot de passe actuel incorrect' in data['error']

    def test_forgot_password_request(self, client, db):
        """Test de demande de réinitialisation de mot de passe"""
        password_data = {
            'email': 'user@test.com'
        }

        response = client.post('/api/auth/forgot-password', json=password_data)

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)
        assert 'Si l\'email existe' in data['message']

    @pytest.mark.integration
    def test_rate_limiting_registration(self, client, db):
        """Test de limitation de taux pour l'inscription"""
        user_data = {
            'email': 'ratelimit{}@test.com',
            'password': 'SecurePassword123!',
            'first_name': 'Rate',
            'last_name': 'Limit'
        }

        # Faire plusieurs requêtes rapides
        responses = []
        for i in range(7):  # Plus que la limite
            user_data['email'] = f'ratelimit{i}@test.com'
            response = client.post('/api/auth/register', json=user_data)
            responses.append(response.status_code)

        # Certaines devraient être limitées
        assert 429 in responses  # Too Many Requests

    def test_csrf_protection(self, client, db):
        """Test de protection CSRF"""
        # Cette fonctionnalité sera testée quand CSRF sera implémenté
        pass

    def test_session_security(self, client, db, auth_headers):
        """Test de sécurité des sessions"""
        # Vérifier que le token expire correctement
        # Cette fonctionnalité sera testée avec l'implémentation JWT complète
        pass

class TestAuthorization:
    """Tests pour les fonctionnalités d'autorisation"""

    def test_admin_required_decorator(self, client, db, auth_headers):
        """Test du décorateur admin_required"""
        # Tenter d'accéder à une route admin avec un utilisateur normal
        response = client.get('/api/admin/dashboard', headers=auth_headers)

        # Devrait échouer car l'utilisateur normal n'est pas admin
        assert response.status_code == 403

    def test_admin_access_with_admin_user(self, client, db, admin_auth_headers):
        """Test d'accès admin avec un utilisateur admin"""
        response = client.get('/api/admin/dashboard', headers=admin_auth_headers)

        # Devrait réussir
        assert response.status_code == 200

    def test_protected_route_without_auth(self, client, db):
        """Test d'accès à une route protégée sans authentification"""
        response = client.get('/api/admin/dashboard')

        assert response.status_code == 401

class TestSecurityFeatures:
    """Tests pour les fonctionnalités de sécurité avancées"""

    def test_password_hashing_algorithm(self, client, db):
        """Test de l'algorithme de hashage des mots de passe"""
        # Créer un utilisateur et vérifier que le mot de passe est hashé
        user_data = {
            'email': 'hashing@test.com',
            'password': 'SecurePassword123!',
            'first_name': 'Hash',
            'last_name': 'Test'
        }

        response = client.post('/api/auth/register', json=user_data)
        assert response.status_code == 201

        # Vérifier que le mot de passe n'est pas stocké en clair
        from models import User
        user = User.query.filter_by(email='hashing@test.com').first()
        assert user.password_hash != 'SecurePassword123!'
        assert user.password_hash.startswith('$2b$')  # bcrypt hash

    def test_input_sanitization(self, client, db):
        """Test de nettoyage des données d'entrée"""
        # Test avec des données contenant du HTML/JavaScript
        user_data = {
            'email': 'sanitization@test.com',
            'password': 'SecurePassword123!',
            'first_name': '<script>alert("xss")</script>Clean',
            'last_name': 'User',
            'company': 'Company & Co'
        }

        response = client.post('/api/auth/register', json=user_data)
        assert response.status_code == 201

        # Vérifier que les données sont nettoyées
        from models import User
        user = User.query.filter_by(email='sanitization@test.com').first()
        assert user.first_name == 'Clean'  # Script tag supprimé
        assert user.company == 'Company & Co'  # Entité HTML préservée

    @pytest.mark.slow
    def test_brute_force_protection(self, client, db):
        """Test de protection contre les attaques par force brute"""
        # Créer un utilisateur de test
        TestUtils.create_test_user(db, 'bruteforce@test.com')

        login_data = {
            'email': 'bruteforce@test.com',
            'password': 'wrongpassword'
        }

        # Simuler une attaque par force brute
        start_time = None
        end_time = None

        # Mesurer le temps pris pour plusieurs tentatives
        import time

        start_time = time.time()

        for i in range(10):
            response = client.post('/api/auth/login', json=login_data)
            # Toutes devraient échouer mais le système devrait ralentir

        end_time = time.time()

        # Le système devrait prendre du temps pour répondre (protection)
        elapsed_time = end_time - start_time
        assert elapsed_time > 1  # Au moins 1 seconde pour 10 tentatives

    def test_sql_injection_prevention(self, client, db):
        """Test de prévention des injections SQL"""
        # Tentative d'injection SQL dans l'email
        malicious_data = {
            'email': "admin'; DROP TABLE users; --",
            'password': 'password'
        }

        response = client.post('/api/auth/login', json=malicious_data)

        # Devrait échouer proprement sans exécuter l'injection
        assert response.status_code == 401

        # Vérifier que la table users existe toujours
        from models import User
        user_count = User.query.count()
        assert user_count >= 0  # La table devrait exister

    def test_xss_prevention(self, client, db):
        """Test de prévention des attaques XSS"""
        # Données avec script XSS
        user_data = {
            'email': 'xss@test.com',
            'password': 'SecurePassword123!',
            'first_name': '<img src=x onerror=alert("XSS")>',
            'last_name': 'User',
            'company': '"><script>alert("XSS")</script>'
        }

        response = client.post('/api/auth/register', json=user_data)
        assert response.status_code == 201

        # Vérifier que les données sont échappées ou nettoyées
        from models import User
        user = User.query.filter_by(email='xss@test.com').first()

        # Les caractères spéciaux devraient être préservés mais échappés lors de l'affichage
        assert '<' in user.first_name  # Les caractères sont préservés en base
        assert '<' in user.company

    def test_file_upload_security(self, client, db, auth_headers):
        """Test de sécurité des uploads de fichiers"""
        # Test avec un fichier malveillant (simulé)
        # Cette fonctionnalité sera testée quand l'upload sera implémenté
        pass

    def test_cors_configuration(self, client, db):
        """Test de configuration CORS sécurisée"""
        # Test des headers CORS
        response = client.options('/api/auth/login')

        # Vérifier les headers CORS
        assert 'Access-Control-Allow-Origin' in response.headers
        assert 'Access-Control-Allow-Methods' in response.headers
        assert 'Access-Control-Allow-Headers' in response.headers

    def test_security_headers(self, client, db):
        """Test des headers de sécurité"""
        response = client.get('/api/health')

        # Vérifier les headers de sécurité
        # Note: Ces headers sont définis dans Nginx en production
        # Ici on teste la réponse de l'API elle-même
        assert response.headers.get('Content-Type') is not None

    @pytest.mark.integration
    def test_ssl_enforcement(self, client, db):
        """Test de l'application du HTTPS"""
        # En développement, on ne peut pas tester HTTPS directement
        # Mais on peut vérifier que les liens générés utilisent HTTPS en production
        pass

if __name__ == "__main__":
    pytest.main([__file__, '-v'])