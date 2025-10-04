#!/usr/bin/env python3
"""
Script d'initialisation de la base de données avec migrations
"""
import os
import sys
from flask import Flask
from config import get_config
from models import db
import logging

def create_app():
    """Créer l'application Flask"""
    app = Flask(__name__)
    app.config.from_object(get_config())
    db.init_app(app)
    return app

def init_database():
    """Initialiser la base de données avec les migrations"""
    app = create_app()

    with app.app_context():
        try:
            # Créer les tables depuis les modèles (fallback)
            print("📊 Création des tables depuis les modèles...")
            db.create_all()
            print("✅ Tables créées avec succès")

            # Insérer des données de base si nécessaire
            seed_database()

            print("🎉 Base de données initialisée avec succès!")
            return True

        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
            return False

def seed_database():
    """Insérer des données de base"""
    try:
        from models import User, Product, SystemConfig

        # Vérifier si l'utilisateur admin existe déjà
        admin_exists = User.query.filter_by(is_admin=True).first()
        if not admin_exists:
            # Créer un utilisateur admin par défaut
            admin_user = User(
                email='admin@passprint.com',
                password_hash='$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeehdBP6fEtTT2/Dm',  # 'password'
                first_name='Admin',
                last_name='PassPrint',
                is_admin=True
            )
            db.session.add(admin_user)
            print("👤 Utilisateur admin créé: admin@passprint.com / password")

        # Ajouter des configurations système par défaut
        default_configs = [
            {'key': 'app_name', 'value': 'PassPrint', 'description': 'Nom de l\'application'},
            {'key': 'app_version', 'value': '1.0.0', 'description': 'Version de l\'application'},
            {'key': 'maintenance_mode', 'value': 'false', 'description': 'Mode maintenance'},
            {'key': 'backup_frequency', 'value': 'daily', 'description': 'Fréquence des sauvegardes'},
        ]

        for config_data in default_configs:
            config_exists = SystemConfig.query.filter_by(key=config_data['key']).first()
            if not config_exists:
                config = SystemConfig(**config_data)
                db.session.add(config)

        # Ajouter des produits de démonstration
        demo_products = [
            {
                'name': 'Carte de visite standard',
                'description': 'Carte de visite 300g couché mat',
                'price': 25000,
                'category': 'print',
                'stock_quantity': 1000
            },
            {
                'name': 'Flyer A5',
                'description': 'Flyer A5 135g couché brillant',
                'price': 15000,
                'category': 'print',
                'stock_quantity': 500
            },
            {
                'name': 'Clé USB 32GB',
                'description': 'Clé USB personnalisée 32GB',
                'price': 85000,
                'category': 'usb',
                'stock_quantity': 50
            }
        ]

        for product_data in demo_products:
            product_exists = Product.query.filter_by(name=product_data['name']).first()
            if not product_exists:
                product = Product(**product_data)
                db.session.add(product)

        db.session.commit()
        print("📦 Données de démonstration ajoutées")

    except Exception as e:
        print(f"⚠️  Erreur lors de l'ajout des données de base: {e}")
        db.session.rollback()

def run_migrations():
    """Exécuter les migrations Alembic"""
    try:
        print("🔄 Exécution des migrations...")
        os.system('alembic upgrade head')
        print("✅ Migrations exécutées avec succès")
        return True
    except Exception as e:
        print(f"❌ Erreur lors des migrations: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚀 Initialisation de la base de données PassPrint")
    print("=" * 50)

    # Demander confirmation en production
    if os.getenv('FLASK_ENV') == 'production':
        confirm = input("Êtes-vous sûr de vouloir réinitialiser la base de données? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Opération annulée")
            return

    success = True

    # Exécuter les migrations
    if not run_migrations():
        success = False

    # Initialiser la base de données
    if not init_database():
        success = False

    if success:
        print("\n🎉 Initialisation réussie!")
        print("\n📋 Informations de connexion:")
        print("Admin: admin@passprint.com / password")
        print("API: http://localhost:5000/api/health")
    else:
        print("\n❌ Échec de l'initialisation")
        sys.exit(1)

if __name__ == "__main__":
    main()