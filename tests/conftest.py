#!/usr/bin/env python3
"""
Configuration pytest pour PassPrint
Fixtures et configuration partagées entre tous les tests
"""
import os
import sys
import pytest
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration des fixtures pytest
@pytest.fixture(scope='session', autouse=True)
def setup_test_environment():
    """Configuration automatique de l'environnement de test"""
    # Définir les variables d'environnement de test
    os.environ.setdefault('FLASK_ENV', 'testing')
    os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-testing-only')
    os.environ.setdefault('JWT_SECRET_KEY', 'test-jwt-secret-key-for-testing-only')
    os.environ.setdefault('DATABASE_URL', 'sqlite:///test.db')
    os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/1')

    # Désactiver les fonctionnalités externes en test
    os.environ.setdefault('SMTP_SERVER', 'localhost')
    os.environ.setdefault('SMTP_PORT', '1025')
    os.environ.setdefault('MAIL_SUPPRESS_SEND', 'true')

    # Configuration Celery pour les tests
    os.environ.setdefault('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    os.environ.setdefault('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
    os.environ.setdefault('CELERY_TASK_ALWAYS_EAGER', 'true')
    os.environ.setdefault('CELERY_TASK_EAGER_PROPAGATES', 'true')

    print("🧪 Configuration environnement de test activée")

@pytest.fixture(scope='function', autouse=True)
def cleanup_after_test():
    """Nettoyage après chaque test"""
    yield  # Exécuter le test

    # Nettoyer les fichiers temporaires créés pendant le test
    import shutil
    from pathlib import Path

    temp_dirs = ['uploads', 'logs', 'backups']
    for temp_dir in temp_dirs:
        temp_path = Path(temp_dir)
        if temp_path.exists():
            # Supprimer seulement les fichiers créés pendant le test
            for file_path in temp_path.glob('test_*'):
                if file_path.is_file():
                    file_path.unlink()

@pytest.fixture
def sample_file_data():
    """Fixture pour des données de fichier de test"""
    return {
        'name': 'test_file.pdf',
        'content': b'%PDF-1.4\n%test pdf content',
        'content_type': 'application/pdf'
    }

@pytest.fixture
def sample_image_data():
    """Fixture pour des données d'image de test"""
    return {
        'name': 'test_image.jpg',
        'content': b'\xff\xd8\xff\xe0\x00\x10JFIF',  # En-tête JPEG
        'content_type': 'image/jpeg'
    }

@pytest.fixture
def mock_stripe_payment():
    """Fixture pour simuler un paiement Stripe"""
    return {
        'id': 'pi_test_mock_payment',
        'amount': 50000,
        'currency': 'xof',
        'status': 'succeeded',
        'client_secret': 'pi_test_secret_mock'
    }

@pytest.fixture
def mock_email_service():
    """Fixture pour simuler le service email"""
    return {
        'sent_emails': [],
        'send_email': lambda to, subject, body: mock_email_service['sent_emails'].append({
            'to': to,
            'subject': subject,
            'body': body,
            'timestamp': datetime.utcnow()
        })
    }

# Configuration des marqueurs de test
def pytest_configure(config):
    """Configuration pytest avancée"""
    # Marqueurs personnalisés
    config.addinivalue_line(
        "markers", "unit: tests unitaires rapides"
    )
    config.addinivalue_line(
        "markers", "integration: tests d'intégration nécessitant des services externes"
    )
    config.addinivalue_line(
        "markers", "e2e: tests end-to-end complets"
    )
    config.addinivalue_line(
        "markers", "performance: tests de performance"
    )
    config.addinivalue_line(
        "markers", "security: tests de sécurité"
    )
    config.addinivalue_line(
        "markers", "database: tests nécessitant la base de données"
    )

    # Configuration des timeouts
    config.addinivalue_line("timeout", "300")  # 5 minutes max par test
    config.addinivalue_line("timeout_method", "thread")

def pytest_collection_modifyitems(config, items):
    """Modifier la collection de tests"""
    # Ajouter des marqueurs automatiquement basés sur le nom du fichier
    for item in items:
        # Tests unitaires
        if 'test_' in item.nodeid and 'integration' not in item.nodeid:
            item.add_marker(pytest.mark.unit)

        # Tests de base de données
        if 'database' in item.nodeid or any(keyword in item.nodeid for keyword in ['model', 'db']):
            item.add_marker(pytest.mark.database)

        # Tests de performance
        if 'performance' in item.nodeid or 'benchmark' in item.nodeid:
            item.add_marker(pytest.mark.performance)

        # Tests end-to-end
        if 'e2e' in item.nodeid or 'workflow' in item.nodeid:
            item.add_marker(pytest.mark.e2e)

# Hooks pour les rapports de test
@pytest.hookimpl(tryfirst=True)
def pytest_runtest_logstart(nodeid, location):
    """Logger le début de chaque test"""
    print(f"\n🧪 Démarrage test: {nodeid}")

@pytest.hookimpl(trylast=True)
def pytest_runtest_logfinish(nodeid, location):
    """Logger la fin de chaque test"""
    print(f"✅ Test terminé: {nodeid}")

# Configuration pour les tests parallèles
def pytest_configure_parallel_tests(config):
    """Configuration pour l'exécution parallèle des tests"""
    if hasattr(config, 'workerinput'):
        # Exécution en parallèle
        worker_id = config.workerinput['workerid']
        print(f"👷 Worker {worker_id} démarré")

# Utilitaires pour les tests
class TestDataFactory:
    """Factory pour créer des données de test"""

    @staticmethod
    def create_user(overrides=None):
        """Créer un utilisateur de test"""
        defaults = {
            'email': 'factory_user@test.com',
            'password': 'FactoryPassword123!',
            'first_name': 'Factory',
            'last_name': 'User',
            'phone': '+2250102030405',
            'company': 'Factory Company'
        }
        defaults.update(overrides or {})
        return defaults

    @staticmethod
    def create_product(overrides=None):
        """Créer un produit de test"""
        defaults = {
            'name': 'Factory Product',
            'description': 'Produit créé par la factory',
            'price': 25000,
            'category': 'print',
            'stock_quantity': 100,
            'is_active': True
        }
        defaults.update(overrides or {})
        return defaults

    @staticmethod
    def create_order(user_id, overrides=None):
        """Créer une commande de test"""
        defaults = {
            'customer_id': user_id,
            'total_amount': 50000,
            'status': 'pending',
            'payment_status': 'pending',
            'shipping_address': '123 Factory Street',
            'shipping_phone': '+2250102030405',
            'shipping_email': 'factory@test.com'
        }
        defaults.update(overrides or {})
        return defaults

    @staticmethod
    def create_quote(user_id, overrides=None):
        """Créer un devis de test"""
        defaults = {
            'customer_id': user_id,
            'project_name': 'Factory Project',
            'project_description': 'Projet créé par la factory',
            'project_type': 'print',
            'format': 'A3',
            'quantity': 100,
            'estimated_price': 75000,
            'status': 'draft'
        }
        defaults.update(overrides or {})
        return defaults

# Exporter les utilitaires
__all__ = ['TestDataFactory']