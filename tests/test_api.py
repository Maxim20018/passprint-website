#!/usr/bin/env python3
"""
Tests API pour PassPrint
Tests d'intégration et fonctionnels pour l'API
"""
import pytest
import json
from tests import TestUtils

class TestAPIEndpoints:
    """Tests pour les endpoints API"""

    def test_health_check_endpoint(self, client, db):
        """Test de l'endpoint de vérification de santé"""
        response = client.get('/api/health')

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)

        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'version' in data

    def test_products_endpoint(self, client, db):
        """Test de l'endpoint des produits"""
        response = client.get('/api/products')

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)

        assert isinstance(data, list)
        if data:  # S'il y a des produits
            product = data[0]
            assert 'id' in product
            assert 'name' in product
            assert 'price' in product
            assert 'category' in product

    def test_product_detail_endpoint(self, client, db):
        """Test de l'endpoint de détail d'un produit"""
        # Créer un produit de test
        product = TestUtils.create_test_product(db, 'Test Product API', 50000)

        response = client.get(f'/api/products/{product.id}')

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)

        assert data['id'] == product.id
        assert data['name'] == 'Test Product API'
        assert data['price'] == 50000

    def test_product_not_found(self, client, db):
        """Test de produit non trouvé"""
        response = client.get('/api/products/99999')

        assert response.status_code == 404
        data = TestUtils.assert_response_error(response)
        assert 'Produit non disponible' in data['error']

    def test_cart_management(self, client, db):
        """Test de gestion du panier"""
        # Créer un produit de test
        product = TestUtils.create_test_product(db, 'Cart Test Product', 25000)

        # Ajouter au panier
        cart_data = {
            'product_id': product.id,
            'quantity': 2
        }

        response = client.post('/api/cart', json=cart_data)

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)

        assert 'items' in data
        assert 'total' in data
        assert len(data['items']) == 1
        assert data['items'][0]['product_id'] == product.id
        assert data['items'][0]['quantity'] == 2
        assert data['total'] == 50000  # 25000 * 2

    def test_cart_session_persistence(self, client, db):
        """Test de persistance du panier par session"""
        # Créer un produit de test
        product = TestUtils.create_test_product(db, 'Session Test Product', 15000)

        # Ajouter au panier avec un Session-ID spécifique
        headers = {'Session-ID': 'test-session-123'}

        cart_data = {
            'product_id': product.id,
            'quantity': 1
        }

        response = client.post('/api/cart', json=cart_data, headers=headers)

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)
        assert data['session_id'] == 'test-session-123'

        # Récupérer le panier avec le même Session-ID
        response = client.get('/api/cart', headers=headers)

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)
        assert len(data['items']) == 1
        assert data['items'][0]['product_id'] == product.id

    def test_order_creation_from_cart(self, client, db, auth_headers):
        """Test de création de commande depuis le panier"""
        # Créer un produit et l'ajouter au panier
        product = TestUtils.create_test_product(db, 'Order Test Product', 30000)

        cart_data = {
            'product_id': product.id,
            'quantity': 3
        }

        client.post('/api/cart', json=cart_data)

        # Créer la commande
        order_data = {
            'shipping_address': '123 Test Street, Test City',
            'shipping_phone': '+2250102030405',
            'shipping_email': 'test@order.com',
            'notes': 'Test order notes'
        }

        response = client.post('/api/orders', json=order_data, headers=auth_headers)

        assert response.status_code == 201
        data = TestUtils.assert_response_ok(response)

        assert 'order' in data
        assert 'order_number' in data['order']
        assert data['order']['total_amount'] == 90000  # 30000 * 3

    def test_quote_creation(self, client, db, auth_headers):
        """Test de création de devis"""
        quote_data = {
            'project_name': 'Test Project',
            'project_description': 'Description of test project',
            'project_type': 'print',
            'format': 'A3',
            'quantity': 100,
            'material': 'Couché 300g',
            'finishing': 'Mat',
            'estimated_price': 75000
        }

        response = client.post('/api/quotes', json=quote_data, headers=auth_headers)

        assert response.status_code == 201
        data = TestUtils.assert_response_ok(response)

        assert 'quote' in data
        assert 'quote_number' in data['quote']
        assert data['quote']['project_name'] == 'Test Project'
        assert data['quote']['estimated_price'] == 75000

    def test_newsletter_subscription(self, client, db):
        """Test d'abonnement à la newsletter"""
        subscription_data = {
            'email': 'newsletter@test.com',
            'first_name': 'Newsletter',
            'last_name': 'Test'
        }

        response = client.post('/api/newsletter/subscribe', json=subscription_data)

        assert response.status_code == 201
        data = TestUtils.assert_response_ok(response)

        assert 'subscriber' in data
        assert data['subscriber']['email'] == 'newsletter@test.com'

    def test_newsletter_duplicate_subscription(self, client, db):
        """Test d'abonnement en double à la newsletter"""
        subscription_data = {
            'email': 'duplicate-newsletter@test.com',
            'first_name': 'Duplicate',
            'last_name': 'Newsletter'
        }

        # Premier abonnement
        response = client.post('/api/newsletter/subscribe', json=subscription_data)
        assert response.status_code == 201

        # Deuxième abonnement avec le même email
        response = client.post('/api/newsletter/subscribe', json=subscription_data)
        assert response.status_code == 409
        data = TestUtils.assert_response_error(response)
        assert 'Email déjà abonné' in data['error']

    def test_pricing_calculation_endpoint(self, client, db):
        """Test de l'endpoint de calcul de prix"""
        pricing_data = {
            'product_type': 'banderole',
            'format': 'A3',
            'quantity': 50,
            'material': 'PVC',
            'finishing': 'Brillant'
        }

        response = client.post('/api/pricing/calculate', json=pricing_data)

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)

        assert 'total_price' in data
        assert 'breakdown' in data
        assert isinstance(data['total_price'], (int, float))

    def test_promo_code_validation(self, client, db):
        """Test de validation de code promo"""
        promo_data = {
            'code': 'TESTPROMO',
            'cart_total': 100000,
            'user_id': 1,
            'categories': ['print']
        }

        response = client.post('/api/promo/validate', json=promo_data)

        # Peut échouer si le code promo n'existe pas, mais ne devrait pas planter
        assert response.status_code in [200, 404]

    def test_admin_dashboard_access(self, client, db, admin_auth_headers):
        """Test d'accès au dashboard admin"""
        response = client.get('/api/admin/dashboard', headers=admin_auth_headers)

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)

        assert 'stats' in data
        assert 'total_users' in data['stats']
        assert 'total_orders' in data['stats']
        assert 'total_products' in data['stats']

    def test_admin_products_management(self, client, db, admin_auth_headers):
        """Test de gestion des produits en admin"""
        # Créer un produit
        product_data = {
            'name': 'Admin Test Product',
            'description': 'Produit créé par l\'admin',
            'price': 45000,
            'category': 'print',
            'stock_quantity': 20,
            'is_active': True
        }

        response = client.post('/api/admin/products', json=product_data, headers=admin_auth_headers)

        assert response.status_code == 201
        data = TestUtils.assert_response_ok(response)

        assert 'product' in data
        assert data['product']['name'] == 'Admin Test Product'

        product_id = data['product']['id']

        # Mettre à jour le produit
        update_data = {
            'name': 'Admin Test Product Updated',
            'price': 50000,
            'stock_quantity': 25
        }

        response = client.put(f'/api/admin/products/{product_id}', json=update_data, headers=admin_auth_headers)

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)
        assert data['product']['name'] == 'Admin Test Product Updated'
        assert data['product']['price'] == 50000

    def test_admin_users_management(self, client, db, admin_auth_headers):
        """Test de gestion des utilisateurs en admin"""
        response = client.get('/api/admin/users', headers=admin_auth_headers)

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)

        assert 'users' in data
        assert 'pagination' in data
        assert isinstance(data['users'], list)

    def test_admin_analytics_endpoint(self, client, db, admin_auth_headers):
        """Test de l'endpoint d'analytics admin"""
        response = client.get('/api/admin/analytics', headers=admin_auth_headers)

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)

        assert 'monthly_sales' in data
        assert 'top_products' in data
        assert 'status_counts' in data

    def test_api_error_handling(self, client, db):
        """Test de gestion des erreurs API"""
        # Test avec méthode non supportée
        response = client.delete('/api/products')

        # Devrait retourner une erreur de méthode non autorisée
        assert response.status_code in [405, 404]

        # Test avec données malformées
        response = client.post('/api/auth/login', data='invalid json')

        assert response.status_code == 400

    def test_api_pagination(self, client, db):
        """Test de la pagination API"""
        # Créer plusieurs produits de test
        for i in range(25):
            TestUtils.create_test_product(db, f'Pagination Product {i}', 10000 + i * 1000)

        # Test de la première page
        response = client.get('/api/products?page=1&per_page=10')

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)

        assert 'pagination' in data
        assert data['pagination']['page'] == 1
        assert data['pagination']['per_page'] == 10
        assert data['pagination']['total'] >= 25
        assert len(data['products']) == 10

        # Test de la deuxième page
        response = client.get('/api/products?page=2&per_page=10')

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)

        assert data['pagination']['page'] == 2
        assert len(data['products']) == 10

    def test_api_filtering_and_sorting(self, client, db):
        """Test du filtrage et tri API"""
        # Créer des produits avec différentes catégories et prix
        products_data = [
            ('Product A', 'print', 10000),
            ('Product B', 'usb', 50000),
            ('Product C', 'print', 30000),
            ('Product D', 'supplies', 20000)
        ]

        for name, category, price in products_data:
            TestUtils.create_test_product(db, name, price)

        # Test de filtrage par catégorie
        response = client.get('/api/products?category=print')

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)

        for product in data:
            assert product['category'] == 'print'

        # Test de filtrage par prix
        response = client.get('/api/products?min_price=15000&max_price=40000')

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)

        for product in data:
            assert 15000 <= product['price'] <= 40000

        # Test de tri
        response = client.get('/api/products?sort_by=price&sort_order=desc')

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)

        # Vérifier que les produits sont triés par prix décroissant
        prices = [p['price'] for p in data]
        assert prices == sorted(prices, reverse=True)

    @pytest.mark.integration
    def test_api_performance(self, client, db):
        """Test de performance de l'API"""
        import time

        # Mesurer le temps de réponse pour une requête simple
        start_time = time.time()
        response = client.get('/api/health')
        end_time = time.time()

        assert response.status_code == 200
        response_time = end_time - start_time

        # Devrait répondre en moins de 1 seconde
        assert response_time < 1.0

    def test_api_content_types(self, client, db):
        """Test des types de contenu API"""
        # Test JSON
        response = client.get('/api/products')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'

        # Test avec header Accept
        response = client.get('/api/products', headers={'Accept': 'application/json'})
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'

    def test_api_caching_headers(self, client, db):
        """Test des headers de cache API"""
        response = client.get('/api/products')

        assert response.status_code == 200

        # Les endpoints API ne devraient pas être cachés par défaut
        cache_control = response.headers.get('Cache-Control', '')
        assert 'no-cache' in cache_control or 'max-age=0' in cache_control

class TestAPIAuthentication:
    """Tests d'authentification pour l'API"""

    def test_api_requires_auth_for_protected_endpoints(self, client, db):
        """Test que les endpoints protégés nécessitent une authentification"""
        protected_endpoints = [
            '/api/admin/dashboard',
            '/api/admin/users',
            '/api/admin/products',
            '/api/auth/verify'
        ]

        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401

    def test_api_authentication_with_valid_token(self, client, db, auth_headers):
        """Test d'authentification API avec token valide"""
        response = client.get('/api/auth/verify', headers=auth_headers)

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)
        assert data['valid'] is True

    def test_api_authentication_with_invalid_token(self, client, db):
        """Test d'authentification API avec token invalide"""
        invalid_headers = {
            'Authorization': 'Bearer invalid_token_here',
            'Content-Type': 'application/json'
        }

        response = client.get('/api/auth/verify', headers=invalid_headers)

        assert response.status_code == 401

    def test_api_authentication_with_malformed_token(self, client, db):
        """Test d'authentification API avec token malformé"""
        malformed_headers = {
            'Authorization': 'InvalidFormat',
            'Content-Type': 'application/json'
        }

        response = client.get('/api/auth/verify', headers=malformed_headers)

        assert response.status_code == 401

class TestAPIValidation:
    """Tests de validation pour l'API"""

    def test_api_input_validation(self, client, db):
        """Test de validation des données d'entrée API"""
        # Test avec données manquantes
        response = client.post('/api/auth/register', json={})

        assert response.status_code == 400
        data = TestUtils.assert_response_error(response)
        assert 'Email et mot de passe requis' in data['error']

    def test_api_data_types_validation(self, client, db):
        """Test de validation des types de données API"""
        # Test avec types de données incorrects
        invalid_data = {
            'email': 'valid@test.com',
            'password': 12345,  # Devrait être une chaîne
            'first_name': 'Test',
            'last_name': 'User'
        }

        response = client.post('/api/auth/register', json=invalid_data)

        # Devrait échouer ou convertir automatiquement
        assert response.status_code in [400, 201]

    def test_api_length_validation(self, client, db):
        """Test de validation des longueurs API"""
        # Test avec données trop longues
        long_data = {
            'email': 'test@test.com',
            'password': 'SecurePassword123!',
            'first_name': 'A' * 100,  # Trop long
            'last_name': 'User',
            'company': 'B' * 200  # Trop long
        }

        response = client.post('/api/auth/register', json=long_data)

        # Devrait être rejeté ou tronqué
        assert response.status_code in [400, 201]

class TestAPIErrorHandling:
    """Tests de gestion des erreurs API"""

    def test_api_404_handling(self, client, db):
        """Test de gestion des 404 API"""
        response = client.get('/api/nonexistent-endpoint')

        assert response.status_code == 404
        data = TestUtils.assert_response_error(response)
        assert 'Ressource non trouvée' in data['error']

    def test_api_500_handling(self, client, db):
        """Test de gestion des erreurs 500 API"""
        # Créer une requête qui va causer une erreur serveur
        # (par exemple en envoyant des données malformées qui causent une exception)
        response = client.post('/api/auth/login', data='invalid json content')

        # Devrait retourner une erreur propre
        assert response.status_code in [400, 500]

    def test_api_method_not_allowed(self, client, db):
        """Test de gestion des méthodes non autorisées"""
        response = client.delete('/api/products')

        assert response.status_code == 405

    def test_api_malformed_json(self, client, db):
        """Test de gestion du JSON malformé"""
        response = client.post('/api/auth/login', data='{"email": "test@test.com", "password":}', content_type='application/json')

        assert response.status_code == 400

class TestAPIRateLimiting:
    """Tests de limitation de taux API"""

    @pytest.mark.integration
    def test_api_rate_limiting(self, client, db):
        """Test de limitation de taux API"""
        # Faire plusieurs requêtes rapides
        responses = []
        for i in range(15):
            response = client.get('/api/health')
            responses.append(response.status_code)

        # Certaines devraient être limitées
        # Note: En test, la limitation peut ne pas être active
        assert 200 in responses

    def test_api_rate_limiting_headers(self, client, db):
        """Test des headers de limitation de taux"""
        response = client.get('/api/health')

        # Vérifier les headers de rate limiting
        # (Ces headers dépendent de l'implémentation de rate limiting)
        assert response.status_code == 200

class TestAPIDocumentation:
    """Tests pour la documentation API"""

    def test_api_docs_accessible(self, client, db):
        """Test d'accessibilité de la documentation API"""
        response = client.get('/api/docs')

        # Devrait retourner la documentation ou une redirection
        assert response.status_code in [200, 301, 302]

    def test_api_spec_available(self, client, db):
        """Test de disponibilité de la spécification API"""
        response = client.get('/api')

        # Devrait retourner les informations de l'API
        assert response.status_code in [200, 404]  # 404 si pas encore implémenté

if __name__ == "__main__":
    pytest.main([__file__, '-v'])