"""
Script d'initialisation de la base de données
Crée les tables et ajoute des données de base
"""
from app import create_app
from models import db, User, Product, NewsletterSubscriber
from werkzeug.security import generate_password_hash
import json

def init_database():
    """Initialiser la base de données avec des données de base"""
    app = create_app()

    with app.app_context():
        # Créer les tables
        print("🔄 Création des tables...")
        db.create_all()

        # Créer l'utilisateur administrateur par défaut
        admin_email = "admin@passprint.com"
        admin_exists = User.query.filter_by(email=admin_email).first()

        if not admin_exists:
            print("👤 Création de l'utilisateur administrateur...")
            admin = User(
                email=admin_email,
                password_hash=generate_password_hash("admin123"),  # À changer en production
                first_name="Administrateur",
                last_name="PassPrint",
                is_admin=True
            )
            db.session.add(admin)

        # Créer des produits de base
        print("📦 Création des produits de base...")

        products_data = [
            {
                "name": "Papier A4 80g Premium",
                "description": "Papier de qualité supérieure pour impressions professionnelles",
                "price": 3500.0,
                "category": "supplies",
                "stock_quantity": 100,
                "image_url": "images/Double A A4.jpg"
            },
            {
                "name": "Clé USB 32GB",
                "description": "Clé USB personnalisable avec votre logo",
                "price": 8500.0,
                "category": "usb",
                "stock_quantity": 50,
                "image_url": "images/32G.jpg"
            },
            {
                "name": "Banderole Publicitaire (2x1m)",
                "description": "Banderole PVC résistante aux intempéries",
                "price": 25000.0,
                "category": "print",
                "stock_quantity": 20,
                "image_url": "images/banderole.jpg"
            },
            {
                "name": "Stickers Personnalisés (A5)",
                "description": "Autocollants vinyle avec découpe personnalisée",
                "price": 15000.0,
                "category": "print",
                "stock_quantity": 30,
                "image_url": "images/macaron.jpg"
            },
            {
                "name": "Panneau Alucobond (1x1m)",
                "description": "Panneau rigide premium pour signalétique extérieure",
                "price": 45000.0,
                "category": "print",
                "stock_quantity": 15,
                "image_url": "images/grandformat.jpg"
            }
        ]

        for product_data in products_data:
            existing_product = Product.query.filter_by(name=product_data["name"]).first()
            if not existing_product:
                product = Product(**product_data)
                db.session.add(product)

        # Sauvegarder les changements
        db.session.commit()
        print("✅ Base de données initialisée avec succès!")

        # Afficher les informations de connexion
        print("\n🔐 Informations de connexion administrateur:")
        print(f"Email: {admin_email}")
        print("Mot de passe: admin123")
        print("\n⚠️  N'oubliez pas de changer le mot de passe en production!")

if __name__ == "__main__":
    init_database()