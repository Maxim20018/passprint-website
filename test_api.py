#!/usr/bin/env python3
"""
Script de test pour l'API PassPrint
Vérifie que tous les endpoints fonctionnent correctement
"""
import requests
import json
import time

BASE_URL = "http://localhost:5001"

def test_health():
    """Test de santé de l'API"""
    print("🏥 Test de santé...")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 200:
            print("✅ API répond correctement")
            return True
        else:
            print(f"❌ API ne répond pas: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def test_config():
    """Test de la configuration publique"""
    print("⚙️  Test de configuration...")
    try:
        response = requests.get(f"{BASE_URL}/api/config")
        if response.status_code == 200:
            config = response.json()
            print(f"✅ Configuration récupérée: {config}")
            return True
        else:
            print(f"❌ Erreur configuration: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_products():
    """Test des produits"""
    print("📦 Test des produits...")
    try:
        response = requests.get(f"{BASE_URL}/api/products")
        if response.status_code == 200:
            products = response.json()
            print(f"✅ {len(products)} produits trouvés")
            if products:
                print(f"   Premier produit: {products[0]['name']}")
            return True
        else:
            print(f"❌ Erreur produits: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_cart():
    """Test du panier"""
    print("🛒 Test du panier...")
    try:
        # Ajouter un produit au panier
        cart_data = {
            "product_id": 1,
            "quantity": 2,
            "specifications": {"format": "A4", "couleur": "quadri"}
        }

        response = requests.post(
            f"{BASE_URL}/api/cart",
            json=cart_data,
            headers={'Session-ID': 'test_session_123'}
        )

        if response.status_code == 200:
            cart = response.json()
            print(f"✅ Panier créé: {len(cart['items'])} éléments")
            print(f"   Total: {cart['total']} FCFA")
            return True
        else:
            print(f"❌ Erreur panier: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_quote():
    """Test des devis"""
    print("📝 Test des devis...")
    try:
        quote_data = {
            "customer_id": 1,
            "project_name": "Test Project",
            "project_description": "Test de création de devis",
            "project_type": "print",
            "format": "A3",
            "quantity": 100,
            "estimated_price": 50000
        }

        response = requests.post(f"{BASE_URL}/api/quotes", json=quote_data)

        if response.status_code == 201:
            quote = response.json()
            print(f"✅ Devis créé: {quote['quote']['quote_number']}")
            return True
        else:
            print(f"❌ Erreur devis: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_newsletter():
    """Test de la newsletter"""
    print("📧 Test newsletter...")
    try:
        newsletter_data = {
            "email": f"test_{int(time.time())}@example.com",
            "first_name": "Test",
            "last_name": "User"
        }

        response = requests.post(f"{BASE_URL}/api/newsletter/subscribe", json=newsletter_data)

        if response.status_code in [201, 409]:  # 409 si déjà abonné
            print("✅ Newsletter OK")
            return True
        else:
            print(f"❌ Erreur newsletter: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def run_all_tests():
    """Exécuter tous les tests"""
    print("🧪 Démarrage des tests API...")
    print("=" * 50)

    tests = [
        ("Santé API", test_health),
        ("Configuration", test_config),
        ("Produits", test_products),
        ("Panier", test_cart),
        ("Devis", test_quote),
        ("Newsletter", test_newsletter),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}:")
        if test_func():
            passed += 1
        time.sleep(1)  # Petite pause entre les tests

    print("\n" + "=" * 50)
    print(f"📊 Résultats: {passed}/{total} tests réussis")

    if passed == total:
        print("🎉 Tous les tests sont passés!")
        print("🚀 Votre API PassPrint est prête!")
    else:
        print("⚠️  Certains tests ont échoué")
        print("🔧 Vérifiez la configuration et relancez les tests")

    return passed == total

if __name__ == "__main__":
    success = run_all_tests()

    if not success:
        print("\n💡 Pour démarrer l'API:")
        print("   python app.py")
        print("   ou utilisez start_server_with_api.bat")

    input("\nAppuyez sur Entrée pour quitter...")