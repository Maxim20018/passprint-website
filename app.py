"""
Application Flask principale pour PassPrint
API Backend pour le site web PassPrint
"""
from flask import Flask, request, jsonify, send_from_directory, session, g
from flask_cors import CORS
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
import os
import json
import uuid
from datetime import datetime, timedelta
import stripe
import secrets
import bcrypt
from functools import wraps
import jwt
import logging
from email_validator import validate_email, EmailNotValidError
from threading import Thread
import sqlite3
from contextlib import contextmanager
import time

# Import de nos modules
from config import get_config
from models import db, User, Product, Order, OrderItem, Quote, Cart, File, NewsletterSubscriber, AuditLog
from pricing_engine import pricing_engine, calculate_product_price
from promo_engine import promo_engine, validate_and_apply_promo_code, create_new_promo_code

# Import avec gestion d'erreurs pour les modules optionnels
try:
    from logging_config import setup_logging, log_api_request, log_security_event, PerformanceLogger
    logging_available = True
except ImportError:
    logging_available = False
    print("Warning: Module logging_config non disponible - utilisation du logging basique")

try:
    from security_system import security_system, require_auth, rate_limit, validate_password_strength, sanitize_input
    security_available = True
except ImportError:
    security_available = False
    print("Warning: Module security_system non disponible - utilisation de la securite basique")

try:
    from api_docs import register_api_docs
    api_docs_available = True
except ImportError:
    api_docs_available = False
    print("Warning: Module api_docs non disponible - API documentation desactivee")

try:
    from monitoring_alerting import init_monitoring, get_monitoring_dashboard
    monitoring_available = True
except ImportError:
    monitoring_available = False
    print("Warning: Module monitoring_alerting non disponible - monitoring desactive")

try:
    from monitoring_config import init_monitoring_integration, get_monitoring_integration
    monitoring_integration_available = True
except ImportError:
    monitoring_integration_available = False
    print("Warning: Module monitoring_config non disponible - integrations monitoring desactivees")

try:
    from admin_dashboard_professional import register_admin_dashboard
    admin_dashboard_available = True
except ImportError:
    admin_dashboard_available = False
    print("Warning: Module admin_dashboard_professional non disponible - dashboard admin basique")

def create_app():
    """Création de l'application Flask"""
    app = Flask(__name__)

    # Configuration basique depuis l'environnement
    config = get_config()
    app.config.from_object(config)

    # Configuration de sécurité renforcée - OBLIGATOIRE en production
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    if not SECRET_KEY or not JWT_SECRET_KEY:
        raise RuntimeError("SECRET_KEY et JWT_SECRET_KEY obligatoires en production!")
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY

    # URL de base configurable
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///passprint.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'pool_size': 10,
        'max_overflow': 20
    }
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

    # Configuration CORS sécurisée
    cors_origins = os.getenv('CORS_ORIGINS', 'https://passprint-website.onrender.com')
    CORS(app, origins=cors_origins.split(','), supports_credentials=True)

    # Initialisation des extensions
    db.init_app(app)

    # Configuration Stripe
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    if not stripe.api_key:
        app.logger.warning("STRIPE_SECRET_KEY non configurée - paiements désactivés")

    # Configuration email
    app.config['MAIL_SERVER'] = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('SMTP_PORT', 587))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_USERNAME'] = os.getenv('SMTP_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('SMTP_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('SMTP_USERNAME', 'noreply@passprint.com')

    # Configuration du logging
    if logging_available:
        logger, security_logger = setup_logging(app)
        app.logger = logger
    else:
        # Logging basique
        logging.basicConfig(level=logging.INFO)
        app.logger = logging.getLogger(__name__)

    # Créer les dossiers nécessaires
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('backups', exist_ok=True)

    # Initialiser le système de sécurité
    if security_available:
        security_system.app = app

    # Enregistrer la documentation API
    if api_docs_available:
        register_api_docs(app)

    # Initialiser le système de monitoring si activé
    if monitoring_available and app.config.get('MONITORING_CONFIG', {}).get('enabled', False):
        init_monitoring(app)

    # Initialiser les intégrations de monitoring
    if monitoring_integration_available:
        init_monitoring_integration(app)

    # Enregistrer le dashboard admin professionnel
    if admin_dashboard_available:
        register_admin_dashboard(app)

    return app

app = create_app()

# Fonctions utilitaires pour l'authentification
def generate_password_hash(password):
    """Générer un hash sécurisé du mot de passe"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password_hash(hashed_password, password):
    """Vérifier un mot de passe"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def generate_token(user_id):
    """Générer un token JWT"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=1),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    """Vérifier et décoder un token JWT"""
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Décorateur pour protéger les routes nécessitant un token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'error': 'Token manquant'}), 401

        if token.startswith('Bearer '):
            token = token.split(' ')[1]

        user_id = verify_token(token)
        if not user_id:
            return jsonify({'error': 'Token invalide ou expiré'}), 401

        return f(user_id, *args, **kwargs)
    return decorated

def admin_required(f):
    """Décorateur pour protéger les routes admin"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'error': 'Token manquant'}), 401

        if token.startswith('Bearer '):
            token = token.split(' ')[1]

        user_id = verify_token(token)
        if not user_id:
            return jsonify({'error': 'Token invalide ou expiré'}), 401

        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({'error': 'Accès administrateur requis'}), 403

        return f(user_id, *args, **kwargs)
    return decorated

# Fonctions d'envoi d'emails
def send_email_async(app, msg):
    """Envoyer un email de manière asynchrone"""
    with app.app_context():
        try:
            from flask_mail import Mail
            mail = Mail(app)
            mail.send(msg)
            print(f"Email envoye a {msg.recipients}")
        except Exception as e:
            print(f"Erreur envoi email: {e}")

def send_order_confirmation_email(order, customer_email):
    """Envoyer email de confirmation de commande"""
    try:
        app = create_app()

        msg = Message(
            subject=f"Confirmation de commande #{order.order_number} - PassPrint",
            recipients=[customer_email],
            html=f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #2D1B69 0%, #FF6B35 100%); color: white; padding: 2rem; text-align: center;">
                    <h1 style="margin: 0;">PassPrint</h1>
                    <p style="margin: 0.5rem 0 0 0;">Confirmation de commande</p>
                </div>

                <div style="padding: 2rem; background: #f8f9fa;">
                    <h2 style="color: #2D1B69;">Bonjour!</h2>
                    <p>Merci pour votre commande. Voici les détails de votre commande #{order.order_number}:</p>

                    <div style="background: white; padding: 1.5rem; border-radius: 8px; margin: 1rem 0;">
                        <h3>Détails de la commande</h3>
                        <p><strong>Montant total:</strong> {format_price(order.total_amount)}</p>
                        <p><strong>Date:</strong> {order.created_at.strftime('%d/%m/%Y %H:%M')}</p>
                        <p><strong>Statut:</strong> {get_status_label(order.status)}</p>
                    </div>

                    <div style="text-align: center; margin: 2rem 0;">
                        <a href="{BASE_URL}/pages/contact.html"
                           style="background: #FF6B35; color: white; padding: 1rem 2rem; text-decoration: none; border-radius: 8px;">
                            Nous contacter
                        </a>
                    </div>

                    <p style="color: #666; font-size: 0.9rem;">
                        Cet email a été envoyé automatiquement. Merci de ne pas répondre directement.
                    </p>
                </div>

                <div style="background: #2D1B69; color: white; padding: 1rem; text-align: center;">
                    <p style="margin: 0;">&copy; 2025 PassPrint. Tous droits réservés.</p>
                </div>
            </div>
            """
        )

        # Envoyer en asynchrone
        thread = Thread(target=send_email_async, args=(app, msg))
        thread.start()

    except Exception as e:
        print(f"Erreur envoi email confirmation: {e}")

def send_quote_email(quote, customer_email):
    """Envoyer email de devis"""
    try:
        app = create_app()

        msg = Message(
            subject=f"Devis #{quote.quote_number} - PassPrint",
            recipients=[customer_email],
            html=f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #2D1B69 0%, #FF6B35 100%); color: white; padding: 2rem; text-align: center;">
                    <h1 style="margin: 0;">PassPrint</h1>
                    <p style="margin: 0.5rem 0 0 0;">Votre devis personnalisé</p>
                </div>

                <div style="padding: 2rem; background: #f8f9fa;">
                    <h2 style="color: #2D1B69;">Devis #{quote.quote_number}</h2>

                    <div style="background: white; padding: 1.5rem; border-radius: 8px; margin: 1rem 0;">
                        <h3>Détails du projet</h3>
                        <p><strong>Projet:</strong> {quote.project_name or 'Non spécifié'}</p>
                        <p><strong>Description:</strong> {quote.project_description or 'Non spécifiée'}</p>
                        <p><strong>Format:</strong> {quote.format or 'Non spécifié'}</p>
                        <p><strong>Quantité:</strong> {quote.quantity or 'Non spécifiée'}</p>
                        <p><strong>Prix estimé:</strong> {format_price(quote.estimated_price or 0)}</p>
                        <p><strong>Valide jusqu'au:</strong> {quote.valid_until.strftime('%d/%m/%Y') if quote.valid_until else 'Non spécifié'}</p>
                    </div>

                    <div style="text-align: center; margin: 2rem 0;">
                        <a href="{BASE_URL}/pages/contact.html"
                           style="background: #FF6B35; color: white; padding: 1rem 2rem; text-decoration: none; border-radius: 8px;">
                            Accepter le devis
                        </a>
                    </div>
                </div>
            </div>
            """
        )

        thread = Thread(target=send_email_async, args=(app, msg))
        thread.start()

    except Exception as e:
        print(f"Erreur envoi email devis: {e}")

def send_welcome_email(user_email, user_name):
    """Envoyer email de bienvenue"""
    try:
        app = create_app()

        msg = Message(
            subject="Bienvenue chez PassPrint!",
            recipients=[user_email],
            html=f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #2D1B69 0%, #FF6B35 100%); color: white; padding: 2rem; text-align: center;">
                    <h1 style="margin: 0;">PassPrint</h1>
                    <p style="margin: 0.5rem 0 0 0;">Bienvenue!</p>
                </div>

                <div style="padding: 2rem; background: #f8f9fa;">
                    <h2 style="color: #2D1B69;">Bonjour {user_name}!</h2>
                    <p>Merci de vous être inscrit chez PassPrint. Votre compte a été créé avec succès.</p>

                    <div style="background: white; padding: 1.5rem; border-radius: 8px; margin: 1rem 0;">
                        <h3>Vos avantages:</h3>
                        <ul>
                            <li>Devis personnalisés en 2h</li>
                            <li>Suivi de commandes en temps réel</li>
                            <li>Support client dédié</li>
                            <li>Accès à nos services premium</li>
                        </ul>
                    </div>

                    <div style="text-align: center; margin: 2rem 0;">
                        <a href="{BASE_URL}"
                           style="background: #FF6B35; color: white; padding: 1rem 2rem; text-decoration: none; border-radius: 8px;">
                            Découvrir nos services
                        </a>
                    </div>
                </div>
            </div>
            """
        )

        from flask_mail import Mail
        mail = Mail(app)
        from flask_mail import Mail
        mail = Mail(app)
        thread = Thread(target=send_email_async, args=(app, msg))
        thread.start()

    except Exception as e:
        print(f"Erreur envoi email bienvenue: {e}")

def format_price(price):
    """Formater le prix en FCFA"""
    return f"{price:,.0f} FCFA".replace(",", " ")

def get_status_label(status):
    """Obtenir le libellé du statut"""
    labels = {
        'pending': 'En attente',
        'confirmed': 'Confirmée',
        'processing': 'En cours',
        'shipped': 'Expédiée',
        'delivered': 'Livrée',
        'cancelled': 'Annulée'
    }
    return labels.get(status, status)

# Routes utilitaires
@app.route('/api/health')
def health_check():
    """Vérification de santé de l'API"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@app.route('/')
def index():
    """Page d'accueil principale"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Servir les fichiers statiques"""
    return send_from_directory('.', path)

@app.route('/admin/monitoring')
def monitoring_dashboard():
    """Dashboard de monitoring"""
    return send_from_directory('.', 'monitoring_dashboard.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard principal"""
    return send_from_directory('.', 'dashboard.html')

@app.route('/admin')
def admin():
    """Dashboard admin professionnel"""
    if admin_dashboard_available:
        # Importer le template depuis le module admin_dashboard_professional
        from admin_dashboard_professional import ADMIN_DASHBOARD_TEMPLATE
        return ADMIN_DASHBOARD_TEMPLATE
    else:
        # Fallback vers le dashboard basique
        return send_from_directory('.', 'admin.html')

def get_config():
    """Configuration publique pour le frontend"""
    return {
        'stripe_public_key': os.getenv('STRIPE_PUBLIC_KEY', 'pk_test_dev_key'),
        'upload_max_size': int(os.getenv('MAX_CONTENT_LENGTH', '52428800'))
    }

# Routes d'authentification
@app.route('/api/auth/register', methods=['POST'])
def register():
    """Inscription utilisateur"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données manquantes'}), 400

        # Validation basique des données
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email et mot de passe requis'}), 400

        # Validation email basique
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', data['email']):
            return jsonify({'error': 'Email invalide'}), 400

        # Validation mot de passe basique
        if len(data['password']) < 8:
            return jsonify({'error': 'Le mot de passe doit contenir au moins 8 caractères'}), 400

        email = data['email'].lower().strip()

        # Vérifier si l'utilisateur existe déjà
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'Email déjà utilisé'}), 409

        # Créer nouvel utilisateur
        new_user = User(
            email=email,
            password_hash=generate_password_hash(data['password']),
            first_name=data.get('first_name', '').strip(),
            last_name=data.get('last_name', '').strip(),
            phone=data.get('phone', '').strip(),
            company=data.get('company', '').strip()
        )

        db.session.add(new_user)
        db.session.commit()

        # Générer token JWT
        token = generate_token(new_user.id)

        # Envoyer email de bienvenue de manière asynchrone
        if new_user.email:
            try:
                send_welcome_email(new_user.email, f"{new_user.first_name} {new_user.last_name}")
            except Exception as e:
                app.logger.warning(f"Erreur envoi email bienvenue: {e}")

        return jsonify({
            'message': 'Utilisateur créé avec succès',
            'user': new_user.to_dict(),
            'token': token
        }), 201

    except Exception as e:
        app.logger.error(f"Erreur inscription utilisateur: {e}")
        db.session.rollback()
        return jsonify({'error': 'Erreur interne du serveur'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Connexion utilisateur"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données manquantes'}), 400

        # Validation basique des données
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email et mot de passe requis'}), 400

        # Validation email basique
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', data['email']):
            return jsonify({'error': 'Email invalide'}), 400

        email = data['email'].lower().strip()

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, data['password']):
            return jsonify({'error': 'Identifiants invalides'}), 401

        # Générer token JWT
        token = generate_token(user.id)

        return jsonify({
            'message': 'Connexion réussie',
            'user': user.to_dict(),
            'token': token
        })

    except Exception as e:
        app.logger.error(f"Erreur connexion utilisateur: {e}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

@app.route('/api/auth/verify', methods=['GET', 'POST'])
@token_required
def verify_token_endpoint(user_id):
    """Vérifier la validité d'un token"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404

        return jsonify({
            'valid': True,
            'user': user.to_dict()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/change-password', methods=['POST'])
@token_required
def change_password(user_id):
    """Changer le mot de passe"""
    try:
        data = request.get_json()

        if not data or not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Mots de passe requis'}), 400

        user = User.query.get(user_id)

        # Vérifier l'ancien mot de passe
        if not check_password_hash(user.password_hash, data['current_password']):
            return jsonify({'error': 'Mot de passe actuel incorrect'}), 401

        # Validation nouveau mot de passe
        if len(data['new_password']) < 8:
            return jsonify({'error': 'Le nouveau mot de passe doit contenir au moins 8 caractères'}), 400

        # Mettre à jour le mot de passe
        user.password_hash = generate_password_hash(data['new_password'])
        user.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({'message': 'Mot de passe changé avec succès'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Demander une réinitialisation de mot de passe"""
    try:
        data = request.get_json()

        if not data or not data.get('email'):
            return jsonify({'error': 'Email requis'}), 400

        # Validation email
        try:
            valid_email = validate_email(data['email'])
            email = valid_email.email
        except EmailNotValidError:
            return jsonify({'error': 'Email invalide'}), 400

        user = User.query.filter_by(email=email).first()

        if user:
            # Générer token de réinitialisation (valide 1 heure)
            reset_token = secrets.token_urlsafe(32)

            # Ici vous pourriez stocker le token en base avec expiration
            # Pour l'instant, on simule l'envoi d'email
            print(f"🔑 Token de réinitialisation pour {email}: {reset_token}")

        return jsonify({
            'message': 'Si l\'email existe, un lien de réinitialisation a été envoyé'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/send-test-email', methods=['POST'])
@admin_required
def send_test_email(user_id):
    """Envoyer un email de test (admin)"""
    try:
        data = request.get_json()

        if not data or not data.get('email') or not data.get('type'):
            return jsonify({'error': 'Email et type requis'}), 400

        app, mail = create_app()

        if data['type'] == 'welcome':
            send_welcome_email(data['email'], 'Utilisateur Test')
        elif data['type'] == 'order_confirmation':
            # Créer une commande de test
            test_order = type('TestOrder', (), {
                'order_number': 'TEST001',
                'total_amount': 50000,
                'status': 'confirmed',
                'created_at': datetime.utcnow()
            })()
            send_order_confirmation_email(test_order, data['email'])
        elif data['type'] == 'quote':
            # Créer un devis de test
            test_quote = type('TestQuote', (), {
                'quote_number': 'DEVTEST001',
                'project_name': 'Projet Test',
                'project_description': 'Description test',
                'format': 'A3',
                'quantity': 100,
                'estimated_price': 75000,
                'valid_until': datetime.utcnow() + timedelta(days=30)
            })()
            send_quote_email(test_quote, data['email'])

        return jsonify({'message': 'Email de test envoyé'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/email-settings', methods=['GET', 'POST'])
@admin_required
def email_settings(user_id):
    """Configuration email (admin)"""
    try:
        if request.method == 'GET':
            return jsonify({
                'smtp_server': app.config.get('MAIL_SERVER'),
                'smtp_port': app.config.get('MAIL_PORT'),
                'smtp_username': app.config.get('MAIL_USERNAME'),
                'mail_configured': bool(app.config.get('MAIL_USERNAME'))
            })

        elif request.method == 'POST':
            data = request.get_json()

            # Ici vous pourriez mettre à jour la configuration
            # Pour l'instant, on retourne juste un succès
            return jsonify({'message': 'Configuration email mise à jour'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Routes produits
@app.route('/api/products')
def get_products():
    """Récupérer tous les produits"""
    try:
        products = Product.query.filter_by(is_active=True).all()
        return jsonify([product.to_dict() for product in products])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:product_id>')
def get_product(product_id):
    """Récupérer un produit spécifique"""
    try:
        product = Product.query.get_or_404(product_id)
        if not product.is_active:
            return jsonify({'error': 'Produit non disponible'}), 404
        return jsonify(product.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Routes panier
@app.route('/api/cart', methods=['GET', 'POST'])
def manage_cart():
    """Gérer le panier d'achat"""
    try:
        session_id = request.headers.get('Session-ID') or str(uuid.uuid4())

        if request.method == 'GET':
            # Récupérer le panier
            cart = Cart.query.filter_by(session_id=session_id).first()
            if not cart:
                return jsonify({'items': [], 'total': 0})

            items = json.loads(cart.items) if cart.items else []
            total = sum(item.get('price', 0) * item.get('quantity', 0) for item in items)

            return jsonify({
                'items': items,
                'total': total,
                'session_id': session_id
            })

        elif request.method == 'POST':
            # Ajouter/modifier élément du panier
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Données manquantes'}), 400

            cart = Cart.query.filter_by(session_id=session_id).first()
            if not cart:
                cart = Cart(session_id=session_id, items='[]')
                db.session.add(cart)

            items = json.loads(cart.items) if cart.items else []

            # Vérifier si le produit existe déjà
            existing_item_index = None
            for i, item in enumerate(items):
                if item.get('product_id') == data.get('product_id'):
                    existing_item_index = i
                    break

            if existing_item_index is not None:
                # Mettre à jour la quantité
                items[existing_item_index]['quantity'] = data.get('quantity', 1)
                if items[existing_item_index]['quantity'] <= 0:
                    items.pop(existing_item_index)
            else:
                # Ajouter nouvel élément
                product = Product.query.get(data.get('product_id'))
                if not product or not product.is_active:
                    return jsonify({'error': 'Produit non disponible'}), 404

                new_item = {
                    'product_id': product.id,
                    'name': product.name,
                    'price': product.price,
                    'quantity': data.get('quantity', 1),
                    'specifications': data.get('specifications', {})
                }
                items.append(new_item)

            cart.items = json.dumps(items)
            cart.updated_at = datetime.utcnow()
            db.session.commit()

            # Calculer le total
            total = sum(item.get('price', 0) * item.get('quantity', 0) for item in items)

            return jsonify({
                'items': items,
                'total': total,
                'session_id': session_id
            })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/cart/<int:product_id>', methods=['DELETE'])
def remove_from_cart(product_id):
    """Retirer un élément du panier"""
    try:
        session_id = request.headers.get('Session-ID') or str(uuid.uuid4())

        cart = Cart.query.filter_by(session_id=session_id).first()
        if not cart:
            return jsonify({'error': 'Panier vide'}), 404

        items = json.loads(cart.items) if cart.items else []

        # Retirer l'élément
        items = [item for item in items if item.get('product_id') != product_id]

        cart.items = json.dumps(items)
        cart.updated_at = datetime.utcnow()
        db.session.commit()

        total = sum(item.get('price', 0) * item.get('quantity', 0) for item in items)

        return jsonify({
            'items': items,
            'total': total,
            'session_id': session_id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Routes commandes
@app.route('/api/orders', methods=['POST'])
def create_order():
    """Créer une nouvelle commande"""
    try:
        data = request.get_json()
        session_id = request.headers.get('Session-ID')

        if not data or not session_id:
            return jsonify({'error': 'Données manquantes'}), 400

        # Récupérer le panier
        cart = Cart.query.filter_by(session_id=session_id).first()
        if not cart:
            return jsonify({'error': 'Panier vide'}), 404

        items = json.loads(cart.items) if cart.items else []
        if not items:
            return jsonify({'error': 'Panier vide'}), 404

        # Créer la commande
        order_number = f"PP{datetime.now().strftime('%Y%m%d%H%M%S')}"

        new_order = Order(
            order_number=order_number,
            customer_id=data.get('customer_id'),
            total_amount=sum(item.get('price', 0) * item.get('quantity', 0) for item in items),
            shipping_address=data.get('shipping_address'),
            shipping_phone=data.get('shipping_phone'),
            shipping_email=data.get('shipping_email'),
            notes=data.get('notes')
        )

        db.session.add(new_order)
        db.session.flush()  # Pour obtenir l'ID de la commande

        # Créer les éléments de commande
        for item_data in items:
            product = Product.query.get(item_data.get('product_id'))
            if product:
                order_item = OrderItem(
                    order_id=new_order.id,
                    product_id=product.id,
                    quantity=item_data.get('quantity', 1),
                    unit_price=item_data.get('price', product.price),
                    total_price=item_data.get('price', product.price) * item_data.get('quantity', 1),
                    specifications=json.dumps(item_data.get('specifications', {}))
                )
                db.session.add(order_item)

        # Vider le panier
        cart.items = '[]'

        # Envoyer email de confirmation si email fourni
        if data.get('shipping_email'):
            send_order_confirmation_email(new_order, data['shipping_email'])

        db.session.commit()

        return jsonify({
            'message': 'Commande créée avec succès',
            'order': new_order.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/<order_number>')
def get_order(order_number):
    """Récupérer une commande"""
    try:
        order = Order.query.filter_by(order_number=order_number).first_or_404()
        return jsonify(order.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Routes devis
@app.route('/api/quotes', methods=['POST'])
def create_quote():
    """Créer un devis"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Données manquantes'}), 400

        # Générer numéro de devis
        quote_number = f"DEV{datetime.now().strftime('%Y%m%d%H%M%S')}"

        new_quote = Quote(
            quote_number=quote_number,
            customer_id=data.get('customer_id'),
            project_name=data.get('project_name'),
            project_description=data.get('project_description'),
            project_type=data.get('project_type'),
            format=data.get('format'),
            quantity=data.get('quantity'),
            material=data.get('material'),
            finishing=data.get('finishing'),
            estimated_price=data.get('estimated_price'),
            valid_until=datetime.utcnow() + timedelta(days=30)  # Valide 30 jours
        )

        db.session.add(new_quote)

        # Récupérer l'utilisateur pour l'email
        user = User.query.get(data.get('customer_id'))
        if user and user.email:
            send_quote_email(new_quote, user.email)

        db.session.commit()

        return jsonify({
            'message': 'Devis créé avec succès',
            'quote': new_quote.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/quotes/<quote_number>')
def get_quote(quote_number):
    """Récupérer un devis"""
    try:
        quote = Quote.query.filter_by(quote_number=quote_number).first_or_404()
        return jsonify(quote.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Routes upload de fichiers
@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Uploader un fichier"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nom de fichier vide'}), 400

        if file:
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

            file.save(file_path)

            # Analyser le fichier
            file_size = os.path.getsize(file_path)
            file_type = filename.split('.')[-1].lower() if '.' in filename else 'unknown'

            # Créer entrée dans la base de données
            db_file = File(
                filename=unique_filename,
                original_filename=filename,
                file_path=file_path,
                file_size=file_size,
                file_type=file_type,
                mime_type=file.content_type
            )

            db.session.add(db_file)
            db.session.commit()

            return jsonify({
                'message': 'Fichier uploadé avec succès',
                'file': db_file.to_dict()
            }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<int:file_id>')
def get_file(file_id):
    """Récupérer un fichier"""
    try:
        file = File.query.get_or_404(file_id)
        return send_from_directory(app.config['UPLOAD_FOLDER'], file.filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Routes Stripe
@app.route('/api/create-payment-intent', methods=['POST'])
def create_payment_intent():
    """Créer une intention de paiement Stripe"""
    try:
        data = request.get_json()
        amount = data.get('amount')  # Montant en centimes

        if not amount or amount <= 0:
            return jsonify({'error': 'Montant invalide'}), 400

        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='xof',  # Franc CFA
            metadata={
                'order_id': data.get('order_id', ''),
                'customer_email': data.get('customer_email', '')
            }
        )

        return jsonify({
            'client_secret': intent.client_secret,
            'payment_intent_id': intent.id
        })

    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Routes newsletter
@app.route('/api/newsletter/subscribe', methods=['POST'])
def subscribe_newsletter():
    """S'abonner à la newsletter"""
    try:
        data = request.get_json()

        if not data or not data.get('email'):
            return jsonify({'error': 'Email requis'}), 400

        # Vérifier si déjà abonné
        existing = NewsletterSubscriber.query.filter_by(email=data['email']).first()
        if existing:
            return jsonify({'error': 'Email déjà abonné'}), 409

        subscriber = NewsletterSubscriber(
            email=data['email'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name')
        )

        db.session.add(subscriber)
        db.session.commit()

        return jsonify({
            'message': 'Inscription à la newsletter réussie',
            'subscriber': subscriber.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Webhook Stripe
@app.route('/api/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    """Webhook pour les événements Stripe"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, app.config['STRIPE_WEBHOOK_SECRET']
        )

        # Traiter l'événement
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            # Mettre à jour le statut de la commande
            # Implémentation selon vos besoins

        return jsonify({'received': True})

    except ValueError as e:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        return jsonify({'error': 'Invalid signature'}), 400

# Route pour servir les fichiers statiques
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Servir les fichiers uploadés"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Routes Dashboard Administration
@app.route('/api/admin/dashboard')
@admin_required
def admin_dashboard(user_id):
    """Tableau de bord administrateur"""
    try:
        # Statistiques générales
        total_users = User.query.count()
        total_orders = Order.query.count()
        total_products = Product.query.count()
        total_quotes = Quote.query.count()

        # Commandes récentes
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()

        # Commandes en attente
        pending_orders = Order.query.filter_by(status='pending').count()

        # Chiffre d'affaires du mois
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_revenue = db.session.query(db.func.sum(Order.total_amount)).filter(
            Order.created_at >= current_month,
            Order.payment_status == 'paid'
        ).scalar() or 0

        # Produits en rupture de stock
        out_of_stock = Product.query.filter(Product.stock_quantity <= 0, Product.is_active == True).count()

        return jsonify({
            'stats': {
                'total_users': total_users,
                'total_orders': total_orders,
                'total_products': total_products,
                'total_quotes': total_quotes,
                'pending_orders': pending_orders,
                'monthly_revenue': float(monthly_revenue),
                'out_of_stock': out_of_stock
            },
            'recent_orders': [order.to_dict() for order in recent_orders]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/orders')
@admin_required
def admin_orders(user_id):
    """Gestion des commandes (admin)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')

        query = Order.query

        if status:
            query = query.filter_by(status=status)

        orders = query.order_by(Order.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'orders': [order.to_dict() for order in orders.items],
            'pagination': {
                'page': orders.page,
                'per_page': orders.per_page,
                'total': orders.total,
                'pages': orders.pages
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/orders/<order_number>', methods=['PUT'])
@admin_required
def update_order(user_id, order_number):
    """Mettre à jour une commande (admin)"""
    try:
        order = Order.query.filter_by(order_number=order_number).first_or_404()
        data = request.get_json()

        # Mettre à jour les champs autorisés
        allowed_fields = ['status', 'payment_status', 'internal_notes', 'shipping_address', 'shipping_phone']
        for field in allowed_fields:
            if field in data:
                setattr(order, field, data[field])

        order.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'message': 'Commande mise à jour avec succès',
            'order': order.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/products', methods=['POST'])
@admin_required
def create_product(user_id):
    """Créer un produit (admin)"""
    try:
        data = request.get_json()

        if not data or not data.get('name') or not data.get('price'):
            return jsonify({'error': 'Nom et prix requis'}), 400

        new_product = Product(
            name=data['name'],
            description=data.get('description', ''),
            price=float(data['price']),
            category=data.get('category', 'other'),
            stock_quantity=data.get('stock_quantity', 0),
            image_url=data.get('image_url', ''),
            is_active=data.get('is_active', True)
        )

        db.session.add(new_product)
        db.session.commit()

        return jsonify({
            'message': 'Produit créé avec succès',
            'product': new_product.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/products/<int:product_id>', methods=['PUT'])
@admin_required
def update_product(user_id, product_id):
    """Mettre à jour un produit (admin)"""
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()

        # Mettre à jour les champs
        allowed_fields = ['name', 'description', 'price', 'category', 'stock_quantity', 'image_url', 'is_active']
        for field in allowed_fields:
            if field in data:
                if field == 'price':
                    setattr(product, field, float(data[field]))
                else:
                    setattr(product, field, data[field])

        db.session.commit()

        return jsonify({
            'message': 'Produit mis à jour avec succès',
            'product': product.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/users')
@admin_required
def admin_users(user_id):
    """Gestion des utilisateurs (admin)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        users = User.query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'pagination': {
                'page': users.page,
                'per_page': users.per_page,
                'total': users.total,
                'pages': users.pages
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/analytics')
@admin_required
def admin_analytics(user_id):
    """Analytics et statistiques (admin)"""
    try:
        # Ventes par mois (12 derniers mois)
        monthly_sales = []
        for i in range(11, -1, -1):
            month_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_date = month_date - timedelta(days=month_date.day - 1)  # Premier jour du mois
            month_date = month_date - timedelta(days=i*31)  # Mois précédent

            next_month = month_date + timedelta(days=31)
            next_month = next_month.replace(day=1)

            revenue = db.session.query(db.func.sum(Order.total_amount)).filter(
                Order.created_at >= month_date,
                Order.created_at < next_month,
                Order.payment_status == 'paid'
            ).scalar() or 0

            monthly_sales.append({
                'month': month_date.strftime('%Y-%m'),
                'revenue': float(revenue)
            })

        # Top produits
        top_products = db.session.query(
            Product, db.func.sum(OrderItem.quantity).label('total_quantity')
        ).join(OrderItem).join(Order).filter(
            Order.payment_status == 'paid'
        ).group_by(Product.id).order_by(
            db.func.sum(OrderItem.quantity).desc()
        ).limit(5).all()

        # Commandes par statut
        status_counts = db.session.query(
            Order.status, db.func.count(Order.id)
        ).group_by(Order.status).all()

        return jsonify({
            'monthly_sales': monthly_sales,
            'top_products': [
                {
                    'product': product.to_dict(),
                    'total_sold': int(total_quantity)
                } for product, total_quantity in top_products
            ],
            'status_counts': {
                status: count for status, count in status_counts
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API de calcul automatique des prix
@app.route('/api/pricing/calculate', methods=['POST'])
def calculate_pricing():
    """Calculer le prix d'un produit selon ses spécifications"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Données manquantes'}), 400

        # Utiliser le moteur de tarification
        result = pricing_engine.calculate_price(data)

        if 'error' in result:
            return jsonify(result), 400

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': f'Erreur de calcul: {str(e)}'}), 500

@app.route('/api/pricing/product-range/<product_type>')
def get_product_price_range(product_type):
    """Obtenir la fourchette de prix pour un type de produit"""
    try:
        format_size = request.args.get('format', 'A3')
        result = pricing_engine.get_price_range(product_type, format_size)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pricing/bulk-discount/<product_type>')
def get_bulk_discount(product_type):
    """Obtenir les remises en fonction de la quantité"""
    try:
        quantity = request.args.get('quantity', 1, type=int)
        result = pricing_engine.calculate_bulk_discount(product_type, quantity)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pricing/finishing-options')
def get_finishing_options():
    """Obtenir les options de finition disponibles"""
    try:
        result = pricing_engine.get_finishing_options()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pricing/delivery-time', methods=['POST'])
def estimate_delivery():
    """Estimer le délai de livraison"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Données manquantes'}), 400

        result = pricing_engine.estimate_delivery_time(
            data.get('product_type', 'banderole'),
            data.get('quantity', 1),
            data.get('deadline', 'standard')
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pricing/formats')
def get_formats():
    """Obtenir les formats disponibles"""
    try:
        from pricing_engine import get_available_formats
        formats = get_available_formats()
        return jsonify({'formats': formats})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pricing/deadlines')
def get_deadlines():
    """Obtenir les délais disponibles"""
    try:
        from pricing_engine import get_available_deadlines
        deadlines = get_available_deadlines()
        return jsonify({'deadlines': deadlines})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API des codes promo
@app.route('/api/promo/validate', methods=['POST'])
def validate_promo():
    """Valider un code promo"""
    try:
        data = request.get_json()

        if not data or not data.get('code'):
            return jsonify({'error': 'Code promo requis'}), 400

        cart_total = data.get('cart_total', 0)
        user_id = data.get('user_id')
        categories = data.get('categories', [])

        result = promo_engine.validate_promo_code(data['code'], cart_total, user_id, categories)

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/promo/apply', methods=['POST'])
def apply_promo():
    """Appliquer un code promo"""
    try:
        data = request.get_json()

        if not data or not data.get('code'):
            return jsonify({'error': 'Code promo requis'}), 400

        user_id = data.get('user_id')
        result = promo_engine.apply_promo_code(data['code'], user_id)

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/promo/create', methods=['POST'])
@admin_required
def create_promo(user_id):
    """Créer un code promo (admin)"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Données manquantes'}), 400

        result = promo_engine.create_promo_code(data)

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/promo/list')
def list_promo_codes():
    """Lister tous les codes promo"""
    try:
        result = promo_engine.get_all_promo_codes()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/promo/stats')
@admin_required
def promo_stats(user_id):
    """Statistiques des codes promo (admin)"""
    try:
        result = promo_engine.get_promo_stats()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/promo/<code>/deactivate', methods=['PUT'])
@admin_required
def deactivate_promo(user_id, code):
    """Désactiver un code promo (admin)"""
    try:
        result = promo_engine.deactivate_promo_code(code)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Gestion des erreurs
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Ressource non trouvée'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Erreur interne du serveur'}), 500

def create_default_admin():
    """Créer un administrateur par défaut si aucun n'existe"""
    try:
        # Vérifier si un admin existe déjà
        admin_exists = User.query.filter_by(is_admin=True).first()
        if admin_exists:
            print("Administrateur deja existant")
            return

        # Créer l'admin par défaut
        default_admin = User(
            email='admin@passprint.com',
            password_hash=generate_password_hash('admin123'),
            first_name='Admin',
            last_name='PassPrint',
            phone='+2250102030405',
            company='PassPrint',
            is_admin=True
        )

        db.session.add(default_admin)
        db.session.commit()

        print("=== COMPTE ADMINISTRATEUR PAR DEFAUT ===")
        print("Email: admin@passprint.com")
        print("Mot de passe: admin123")
        print("")
        print("INSTRUCTIONS IMPORTANTES:")
        print("1. Connectez-vous avec ces identifiants")
        print("2. Changez immediatement le mot de passe")
        print("3. Creez des comptes admin supplementaires")
        print("4. Supprimez ce compte de demonstration")
        print("")
        print("SECURITE PRODUCTION:")
        print("- Utilisez HTTPS en production")
        print("- Configurez des mots de passe forts")
        print("- Activez l'authentification a deux facteurs")
        print("- Surveillez les logs de connexion")
        print("=======================================")

    except Exception as e:
        print(f"Erreur creation admin par defaut: {e}")
        db.session.rollback()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Créer les tables si elles n'existent pas
        create_default_admin()  # Créer l'admin par défaut

    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )