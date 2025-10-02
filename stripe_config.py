#!/usr/bin/env python3
"""
Configuration Stripe pour PassPrint
"""
import stripe
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def configure_stripe():
    """Configurer Stripe avec les clés appropriées"""
    # Récupérer les clés depuis les variables d'environnement
    public_key = os.getenv('STRIPE_PUBLIC_KEY')
    secret_key = os.getenv('STRIPE_SECRET_KEY')

    if not public_key or not secret_key:
        print("⚠️  Clés Stripe non configurées")
        print("💡 Ajoutez vos clés dans le fichier .env")
        return False

    # Configurer Stripe
    stripe.api_key = secret_key

    print("✅ Stripe configuré avec succès")
    print(f"🔑 Clé publique: {public_key[:20]}...")
    print(f"🔐 Clé secrète: {secret_key[:20]}...")

    return True

def create_test_products():
    """Créer des produits de test dans Stripe"""
    try:
        # Produits de test
        products = [
            {
                'name': 'Banderole Publicitaire Standard',
                'price': 25000,  # 25,000 FCFA
                'description': 'Banderole PVC 2x1m résistante'
            },
            {
                'name': 'Stickers Personnalisés',
                'price': 15000,  # 15,000 FCFA
                'description': '100 stickers vinyle découpés'
            },
            {
                'name': 'Clé USB 32GB',
                'price': 8500,   # 8,500 FCFA
                'description': 'Clé USB personnalisable'
            }
        ]

        print("📦 Création des produits Stripe...")

        for product_data in products:
            # Créer le produit
            product = stripe.Product.create(
                name=product_data['name'],
                description=product_data['description'],
                type='service'
            )

            # Créer le prix en FCFA (pas de décimales)
            price = stripe.Price.create(
                product=product.id,
                unit_amount=product_data['price'],
                currency='xof',  # Franc CFA
            )

            print(f"  ✅ {product_data['name']}: {product_data['price']} FCFA")

        return True

    except Exception as e:
        print(f"❌ Erreur création produits Stripe: {e}")
        return False

def test_stripe_connection():
    """Tester la connexion Stripe"""
    try:
        # Tester la connexion en récupérant le solde
        balance = stripe.Balance.retrieve()
        print("✅ Connexion Stripe réussie")
        print(f"💰 Solde disponible: {balance.available[0].amount if balance.available else 0} {balance.currency}")

        return True

    except stripe.error.AuthenticationError:
        print("❌ Erreur d'authentification Stripe")
        print("💡 Vérifiez vos clés API Stripe")
        return False

    except Exception as e:
        print(f"❌ Erreur connexion Stripe: {e}")
        return False

def main():
    """Configuration principale Stripe"""
    print("💳 Configuration Stripe pour PassPrint")
    print("=" * 50)

    if not configure_stripe():
        print("❌ Configuration Stripe échouée")
        return False

    if test_stripe_connection():
        print("✅ Stripe fonctionne correctement")

        # Demander si l'utilisateur veut créer des produits de test
        create_products = input("Créer des produits de test Stripe? (o/n): ").lower().strip()
        if create_products == 'o':
            create_test_products()
    else:
        print("❌ Impossible de continuer sans connexion Stripe valide")

    print("\n🎉 Configuration Stripe terminée!")
    print("\n📋 Prochaines étapes:")
    print("1. Testez les paiements avec les clés de test")
    print("2. Passez en production avec les clés live")
    print("3. Configurez les webhooks Stripe")

if __name__ == "__main__":
    main()