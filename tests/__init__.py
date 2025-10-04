#!/usr/bin/env python3
"""
Package de tests pour PassPrint
Configuration et utilitaires pour les tests
"""
import os
import sys
import pytest
from datetime import datetime

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration des tests
os.environ.setdefault('FLASK_ENV', 'testing')

def pytest_configure(config):
    """Configuration pytest"""
    # Marquer les tests qui nécessitent des services externes
    config.addinivalue_line(
        "markers", "integration: tests d'intégration nécessitant des services externes"
    )
    config.addinivalue_line(
        "markers", "slow: tests lents à exécuter"
    )
    config.addinivalue_line(
        "markers", "security: tests de sécurité"
    )

def pytest_collection_modifyitems(config, items):
    """Modifier la collection de tests"""
    # Ajouter des marqueurs automatiquement
    for item in items:
        # Marquer les tests d'intégration
        if 'integration' in item.nodeid or 'test_api' in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Marquer les tests lents
        if 'slow' in item.nodeid or 'performance' in item.nodeid:
            item.add_marker(pytest.mark.slow)

        # Marquer les tests de sécurité
        if 'security' in item.nodeid or 'auth' in item.nodeid:
            item.add_marker(pytest.mark.security)

# Fixtures communes
@pytest.fixture(scope='session')
def app():
    """Fixture pour l'application Flask en mode test"""
    from app import create_app
    app = create_app()

    # Configuration de test
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///test.db',
        'SECRET_KEY': 'test-secret-key',
        'JWT_SECRET_KEY': 'test-jwt-secret-key'
    })

    return app

@pytest.fixture(scope='session')
def client(app):
    """Fixture pour le client de test Flask"""
    return app.test_client()

@pytest.fixture(scope='function')
def db(app):
    """Fixture pour la base de données de test"""
    from models import db

    with app.app_context():
        # Créer les tables
        db.create_all()

        # Insérer des données de test
        seed_test_data()

        yield db

        # Nettoyer après chaque test
        db.session.remove()
        db.drop_all()

def seed_test_data():
    """Insérer des données de test"""
    from models import User, Product, SystemConfig

    # Utilisateur de test admin
    admin_user = User(
        email='admin@test.com',
        password_hash='$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeehdBP6fEtTT2/Dm',  # 'password'
        first_name='Admin',
        last_name='Test',
        is_admin=True
    )
    db.session.add(admin_user)

    # Utilisateur de test normal
    normal_user = User(
        email='user@test.com',
        password_hash='$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeehdBP6fEtTT2/Dm',  # 'password'
        first_name='User',
        last_name='Test',
        is_admin=False
    )
    db.session.add(normal_user)

    # Produits de test
    products = [
        Product(
            name='Carte de visite standard',
            description='Carte de visite 300g couché mat',
            price=25000,
            category='print',
            stock_quantity=100
        ),
        Product(
            name='Flyer A5',
            description='Flyer A5 135g couché brillant',
            price=15000,
            category='print',
            stock_quantity=50
        ),
        Product(
            name='Clé USB 32GB',
            description='Clé USB personnalisée 32GB',
            price=85000,
            category='usb',
            stock_quantity=25
        )
    ]

    for product in products:
        db.session.add(product)

    # Configuration système de test
    configs = [
        SystemConfig(key='app_name', value='PassPrint Test', description='Nom de l\'application de test'),
        SystemConfig(key='maintenance_mode', value='false', description='Mode maintenance'),
        SystemConfig(key='backup_frequency', value='daily', description='Fréquence des sauvegardes')
    ]

    for config in configs:
        db.session.add(config)

    db.session.commit()

@pytest.fixture
def auth_headers(client, db):
    """Fixture pour les headers d'authentification"""
    # Se connecter avec l'utilisateur de test
    login_data = {
        'email': 'user@test.com',
        'password': 'password'
    }

    response = client.post('/api/auth/login', json=login_data)
    assert response.status_code == 200

    data = response.get_json()
    token = data['token']

    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

@pytest.fixture
def admin_auth_headers(client, db):
    """Fixture pour les headers d'authentification admin"""
    # Se connecter avec l'utilisateur admin de test
    login_data = {
        'email': 'admin@test.com',
        'password': 'password'
    }

    response = client.post('/api/auth/login', json=login_data)
    assert response.status_code == 200

    data = response.get_json()
    token = data['token']

    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

# Utilitaires de test
class TestUtils:
    """Utilitaires pour les tests"""

    @staticmethod
    def assert_response_ok(response):
        """Vérifier qu'une réponse est OK"""
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None
        return data

    @staticmethod
    def assert_response_error(response, expected_status=None):
        """Vérifier qu'une réponse contient une erreur"""
        if expected_status:
            assert response.status_code == expected_status

        data = response.get_json()
        assert 'error' in data
        return data

    @staticmethod
    def create_test_user(db, email='test@example.com', is_admin=False):
        """Créer un utilisateur de test"""
        from models import User

        user = User(
            email=email,
            password_hash='$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeehdBP6fEtTT2/Dm',  # 'password'
            first_name='Test',
            last_name='User',
            is_admin=is_admin
        )
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def create_test_product(db, name='Produit Test', price=10000):
        """Créer un produit de test"""
        from models import Product

        product = Product(
            name=name,
            description='Description de test',
            price=price,
            category='print',
            stock_quantity=10
        )
        db.session.add(product)
        db.session.commit()
        return product

    @staticmethod
    def create_test_order(db, user_id, total_amount=50000):
        """Créer une commande de test"""
        from models import Order

        order = Order(
            order_number=f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}",
            customer_id=user_id,
            total_amount=total_amount,
            status='pending'
        )
        db.session.add(order)
        db.session.commit()
        return order

# Exporter les utilitaires
__all__ = ['TestUtils']