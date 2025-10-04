#!/usr/bin/env python3
"""
Documentation et schémas API pour PassPrint
Utilise Flask-RESTX pour la documentation automatique
"""
from flask_restx import Api, Resource, fields, reqparse
from flask import Blueprint, request
from models import User, Product, Order, Quote, Cart, File, NewsletterSubscriber
from security_system import require_auth, rate_limit, sanitize_input, validate_password_strength
from logging_config import log_api_request, log_security_event, PerformanceLogger
import json

# Créer le blueprint pour l'API
api_bp = Blueprint('api', __name__)

# Configuration de l'API
api = Api(
    api_bp,
    version='1.0',
    title='PassPrint API',
    description='API de production pour la plateforme PassPrint',
    doc='/docs',
    authorizations={
        'Bearer Auth': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'JWT Authorization header using the Bearer scheme'
        }
    },
    security='Bearer Auth'
)

# Namespaces pour organiser l'API
auth_ns = api.namespace('auth', description='Opérations d\'authentification')
products_ns = api.namespace('products', description='Gestion des produits')
orders_ns = api.namespace('orders', description='Gestion des commandes')
quotes_ns = api.namespace('quotes', description='Gestion des devis')
cart_ns = api.namespace('cart', description='Gestion du panier')
files_ns = api.namespace('files', description='Gestion des fichiers')
admin_ns = api.namespace('admin', description='Fonctions administrateur')
system_ns = api.namespace('system', description='Informations système')

# Modèles de données pour la validation et la documentation
user_model = api.model('User', {
    'id': fields.Integer(readOnly=True, description='ID unique de l\'utilisateur'),
    'email': fields.String(required=True, description='Adresse email'),
    'first_name': fields.String(required=True, description='Prénom'),
    'last_name': fields.String(required=True, description='Nom de famille'),
    'phone': fields.String(description='Numéro de téléphone'),
    'company': fields.String(description='Entreprise'),
    'is_admin': fields.Boolean(description='Droits administrateur'),
    'created_at': fields.DateTime(description='Date de création')
})

product_model = api.model('Product', {
    'id': fields.Integer(readOnly=True, description='ID unique du produit'),
    'name': fields.String(required=True, description='Nom du produit'),
    'description': fields.String(description='Description du produit'),
    'price': fields.Float(required=True, description='Prix en FCFA'),
    'category': fields.String(required=True, description='Catégorie'),
    'stock_quantity': fields.Integer(description='Quantité en stock'),
    'image_url': fields.String(description='URL de l\'image'),
    'is_active': fields.Boolean(description='Produit actif'),
    'created_at': fields.DateTime(description='Date de création')
})

order_model = api.model('Order', {
    'id': fields.Integer(readOnly=True, description='ID unique de la commande'),
    'order_number': fields.String(readOnly=True, description='Numéro de commande'),
    'customer_id': fields.Integer(required=True, description='ID du client'),
    'total_amount': fields.Float(required=True, description='Montant total'),
    'status': fields.String(description='Statut de la commande'),
    'payment_status': fields.String(description='Statut du paiement'),
    'shipping_address': fields.String(description='Adresse de livraison'),
    'shipping_phone': fields.String(description='Téléphone de livraison'),
    'shipping_email': fields.String(description='Email de livraison'),
    'notes': fields.String(description='Notes'),
    'created_at': fields.DateTime(description='Date de création'),
    'items': fields.List(fields.Nested({
        'id': fields.Integer,
        'product_id': fields.Integer,
        'product_name': fields.String,
        'quantity': fields.Integer,
        'unit_price': fields.Float,
        'total_price': fields.Float
    }))
})

quote_model = api.model('Quote', {
    'id': fields.Integer(readOnly=True, description='ID unique du devis'),
    'quote_number': fields.String(readOnly=True, description='Numéro de devis'),
    'customer_id': fields.Integer(required=True, description='ID du client'),
    'project_name': fields.String(description='Nom du projet'),
    'project_description': fields.String(description='Description du projet'),
    'project_type': fields.String(description='Type de projet'),
    'format': fields.String(description='Format'),
    'quantity': fields.Integer(description='Quantité'),
    'material': fields.String(description='Matériau'),
    'finishing': fields.String(description='Finition'),
    'estimated_price': fields.Float(description='Prix estimé'),
    'status': fields.String(description='Statut du devis'),
    'valid_until': fields.DateTime(description='Date d\'expiration')
})

cart_model = api.model('Cart', {
    'session_id': fields.String(description='ID de session'),
    'items': fields.List(fields.Nested({
        'product_id': fields.Integer,
        'name': fields.String,
        'price': fields.Float,
        'quantity': fields.Integer,
        'specifications': fields.Raw
    })),
    'total': fields.Float(description='Total du panier')
})

file_model = api.model('File', {
    'id': fields.Integer(readOnly=True, description='ID unique du fichier'),
    'filename': fields.String(description='Nom du fichier'),
    'original_filename': fields.String(description='Nom original'),
    'file_path': fields.String(description='Chemin du fichier'),
    'file_size': fields.Integer(description='Taille en octets'),
    'file_type': fields.String(description='Type de fichier'),
    'mime_type': fields.String(description='Type MIME'),
    'uploaded_at': fields.DateTime(description='Date d\'upload')
})

# Modèles pour les requêtes
register_model = api.model('Register', {
    'email': fields.String(required=True, description='Adresse email'),
    'password': fields.String(required=True, description='Mot de passe'),
    'first_name': fields.String(required=True, description='Prénom'),
    'last_name': fields.String(required=True, description='Nom de famille'),
    'phone': fields.String(description='Numéro de téléphone'),
    'company': fields.String(description='Entreprise')
})

login_model = api.model('Login', {
    'email': fields.String(required=True, description='Adresse email'),
    'password': fields.String(required=True, description='Mot de passe')
})

password_change_model = api.model('PasswordChange', {
    'current_password': fields.String(required=True, description='Mot de passe actuel'),
    'new_password': fields.String(required=True, description='Nouveau mot de passe')
})

product_create_model = api.model('ProductCreate', {
    'name': fields.String(required=True, description='Nom du produit'),
    'description': fields.String(description='Description'),
    'price': fields.Float(required=True, description='Prix'),
    'category': fields.String(required=True, description='Catégorie'),
    'stock_quantity': fields.Integer(description='Quantité en stock'),
    'image_url': fields.String(description='URL de l\'image'),
    'is_active': fields.Boolean(description='Produit actif')
})

# Parsers pour la validation des arguments
pagination_parser = reqparse.RequestParser()
pagination_parser.add_argument('page', type=int, default=1, help='Numéro de page')
pagination_parser.add_argument('per_page', type=int, default=20, help='Éléments par page')
pagination_parser.add_argument('sort_by', type=str, help='Champ de tri')
pagination_parser.add_argument('sort_order', type=str, choices=['asc', 'desc'], default='asc', help='Ordre de tri')

product_filter_parser = pagination_parser.copy()
product_filter_parser.add_argument('category', type=str, help='Filtrer par catégorie')
product_filter_parser.add_argument('min_price', type=float, help='Prix minimum')
product_filter_parser.add_argument('max_price', type=float, help='Prix maximum')
product_filter_parser.add_argument('in_stock', type=bool, help='Uniquement en stock')

# Classes de ressources API avec documentation intégrée

@auth_ns.route('/register')
class RegisterAPI(Resource):
    @api.expect(register_model)
    @api.response(201, 'Utilisateur créé avec succès', user_model)
    @api.response(400, 'Données invalides')
    @api.response(409, 'Email déjà utilisé')
    @rate_limit(limit=5, window=300)
    def post(self):
        """Créer un nouveau compte utilisateur"""
        with PerformanceLogger('user_registration'):
            try:
                data = request.get_json()
                if not data:
                    return {'error': 'Données manquantes'}, 400

                # Validation avec le système de sécurité
                data = sanitize_input(data)

                if not data.get('email') or not data.get('password'):
                    return {'error': 'Email et mot de passe requis'}, 400

                password_validation = validate_password_strength(data['password'])
                if not password_validation['valid']:
                    return {
                        'error': 'Mot de passe trop faible',
                        'requirements': password_validation['errors']
                    }, 400

                # Création de l'utilisateur (logique existante)
                from app import User, db, generate_password_hash, generate_token, send_welcome_email

                email = data['email'].lower().strip()
                existing_user = User.query.filter_by(email=email).first()

                if existing_user:
                    return {'error': 'Email déjà utilisé'}, 409

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

                token = generate_token(new_user.id)

                if new_user.email:
                    try:
                        send_welcome_email(new_user.email, f"{new_user.first_name} {new_user.last_name}")
                    except Exception as e:
                        print(f"Erreur envoi email: {e}")

                log_api_request('/api/auth/register', 'POST', 201)

                return {
                    'message': 'Utilisateur créé avec succès',
                    'user': new_user.to_dict(),
                    'token': token
                }, 201

            except Exception as e:
                return {'error': 'Erreur interne du serveur'}, 500

@auth_ns.route('/login')
class LoginAPI(Resource):
    @api.expect(login_model)
    @api.response(200, 'Connexion réussie')
    @api.response(400, 'Données invalides')
    @api.response(401, 'Identifiants invalides')
    @api.response(423, 'Compte verrouillé')
    @rate_limit(limit=5, window=300)
    def post(self):
        """Se connecter à un compte existant"""
        with PerformanceLogger('user_login'):
            try:
                data = request.get_json()
                if not data:
                    return {'error': 'Données manquantes'}, 400

                data = sanitize_input(data)

                if not data.get('email') or not data.get('password'):
                    return {'error': 'Email et mot de passe requis'}, 400

                from app import User, check_password_hash, generate_token
                from security_system import security_system

                email = data['email'].lower().strip()

                # Vérifier le verrouillage du compte
                lockout_check = security_system.check_account_lockout(email)
                if lockout_check['locked']:
                    return {
                        'error': 'Compte temporairement verrouillé',
                        'remaining_time': str(lockout_check['remaining_time'])
                    }, 423

                user = User.query.filter_by(email=email).first()

                if not user or not check_password_hash(user.password_hash, data['password']):
                    security_system.record_failed_login(email, security_system.get_client_ip())
                    return {'error': 'Identifiants invalides'}, 401

                security_system.record_successful_login(user.id, security_system.get_client_ip())
                token = generate_token(user.id)

                log_api_request('/api/auth/login', 'POST', 200)

                return {
                    'message': 'Connexion réussie',
                    'user': user.to_dict(),
                    'token': token
                }

            except Exception as e:
                return {'error': 'Erreur interne du serveur'}, 500

@products_ns.route('')
class ProductsAPI(Resource):
    @api.expect(product_filter_parser)
    @api.response(200, 'Liste des produits', {
        'products': fields.List(fields.Nested(product_model)),
        'pagination': fields.Nested({
            'page': fields.Integer,
            'per_page': fields.Integer,
            'total': fields.Integer,
            'pages': fields.Integer
        })
    })
    def get(self):
        """Récupérer la liste des produits avec filtrage et pagination"""
        with PerformanceLogger('get_products'):
            try:
                args = product_filter_parser.parse_args()

                query = Product.query.filter_by(is_active=True)

                # Appliquer les filtres
                if args.category:
                    query = query.filter_by(category=args.category)
                if args.min_price is not None:
                    query = query.filter(Product.price >= args.min_price)
                if args.max_price is not None:
                    query = query.filter(Product.price <= args.max_price)
                if args.in_stock:
                    query = query.filter(Product.stock_quantity > 0)

                # Appliquer le tri
                sort_by = args.sort_by or 'created_at'
                sort_order = args.sort_order == 'desc'

                if sort_order:
                    query = query.order_by(getattr(Product, sort_by).desc())
                else:
                    query = query.order_by(getattr(Product, sort_by).asc())

                # Pagination
                page = args.page
                per_page = min(args.per_page, 100)  # Limite à 100 éléments

                products_paginated = query.paginate(page=page, per_page=per_page, error_out=False)

                result = {
                    'products': [product.to_dict() for product in products_paginated.items],
                    'pagination': {
                        'page': products_paginated.page,
                        'per_page': products_paginated.per_page,
                        'total': products_paginated.total,
                        'pages': products_paginated.pages
                    }
                }

                log_api_request('/api/products', 'GET', 200)
                return result, 200

            except Exception as e:
                return {'error': 'Erreur interne du serveur'}, 500

@products_ns.route('/<int:product_id>')
class ProductAPI(Resource):
    @api.response(200, 'Produit trouvé', product_model)
    @api.response(404, 'Produit non trouvé')
    def get(self, product_id):
        """Récupérer un produit spécifique"""
        with PerformanceLogger('get_product'):
            try:
                product = Product.query.get_or_404(product_id)
                if not product.is_active:
                    return {'error': 'Produit non disponible'}, 404

                log_api_request(f'/api/products/{product_id}', 'GET', 200)
                return product.to_dict(), 200

            except Exception as e:
                return {'error': 'Erreur interne du serveur'}, 500

@orders_ns.route('')
class OrdersAPI(Resource):
    @api.expect(order_model)
    @api.response(201, 'Commande créée', order_model)
    @api.response(400, 'Données invalides')
    @require_auth
    def post(self):
        """Créer une nouvelle commande"""
        with PerformanceLogger('create_order'):
            try:
                user_id = g.user_id
                data = request.get_json()

                if not data:
                    return {'error': 'Données manquantes'}, 400

                # Logique de création de commande existante
                from app import Cart, Order, OrderItem, Product, db, send_order_confirmation_email

                session_id = request.headers.get('Session-ID') or str(uuid.uuid4())

                cart = Cart.query.filter_by(session_id=session_id).first()
                if not cart:
                    return {'error': 'Panier vide'}, 404

                items = json.loads(cart.items) if cart.items else []
                if not items:
                    return {'error': 'Panier vide'}, 404

                order_number = f"PP{datetime.now().strftime('%Y%m%d%H%M%S')}"

                new_order = Order(
                    order_number=order_number,
                    customer_id=user_id,
                    total_amount=sum(item.get('price', 0) * item.get('quantity', 0) for item in items),
                    shipping_address=data.get('shipping_address'),
                    shipping_phone=data.get('shipping_phone'),
                    shipping_email=data.get('shipping_email'),
                    notes=data.get('notes')
                )

                db.session.add(new_order)
                db.session.flush()

                for item_data in items:
                    product = Product.query.get(item_data.get('product_id'))
                    if product:
                        order_item = OrderItem(
                            order_id=new_order.id,
                            product_id=product.id,
                            quantity=item_data.get('quantity', 1),
                            unit_price=item_data.get('price', product.price),
                            total_price=item_data.get('price', product.price) * item_data.get('quantity', 1)
                        )
                        db.session.add(order_item)

                cart.items = '[]'
                db.session.commit()

                if data.get('shipping_email'):
                    send_order_confirmation_email(new_order, data['shipping_email'])

                log_api_request('/api/orders', 'POST', 201)
                return {
                    'message': 'Commande créée avec succès',
                    'order': new_order.to_dict()
                }, 201

            except Exception as e:
                return {'error': 'Erreur interne du serveur'}, 500

@system_ns.route('/health')
class HealthAPI(Resource):
    @api.response(200, 'Système opérationnel')
    def get(self):
        """Vérification de santé du système"""
        with PerformanceLogger('health_check'):
            try:
                from datetime import datetime

                # Vérifier la base de données
                db_health = True
                try:
                    User.query.first()
                except Exception:
                    db_health = False

                # Informations système
                health_info = {
                    'status': 'healthy' if db_health else 'degraded',
                    'timestamp': datetime.utcnow().isoformat(),
                    'version': '1.0.0',
                    'services': {
                        'database': 'ok' if db_health else 'error',
                        'api': 'ok'
                    }
                }

                status_code = 200 if db_health else 503
                log_api_request('/api/system/health', 'GET', status_code)

                return health_info, status_code

            except Exception as e:
                return {'error': 'Erreur interne du serveur'}, 500

@system_ns.route('/info')
class SystemInfoAPI(Resource):
    @api.response(200, 'Informations système')
    def get(self):
        """Informations sur le système"""
        with PerformanceLogger('system_info'):
            try:
                import platform
                import psutil
                from datetime import datetime

                system_info = {
                    'name': 'PassPrint API',
                    'version': '1.0.0',
                    'python_version': platform.python_version(),
                    'platform': platform.platform(),
                    'uptime': 'unknown',  # Calculer depuis le démarrage
                    'memory': {
                        'total': psutil.virtual_memory().total,
                        'available': psutil.virtual_memory().available,
                        'percent': psutil.virtual_memory().percent
                    },
                    'cpu': {
                        'count': psutil.cpu_count(),
                        'percent': psutil.cpu_percent(interval=1)
                    },
                    'disk': {
                        'total': psutil.disk_usage('/').total,
                        'free': psutil.disk_usage('/').free,
                        'percent': psutil.disk_usage('/').percent
                    }
                }

                log_api_request('/api/system/info', 'GET', 200)
                return system_info, 200

            except Exception as e:
                return {'error': 'Erreur récupération informations système'}, 500

# Enregistrer le blueprint
def register_api_docs(app):
    """Enregistrer la documentation API dans l'application"""
    app.register_blueprint(api_bp, url_prefix='/api')

    # Ajouter la documentation à l'URL racine de l'API
    @app.route('/api')
    def api_docs():
        return api.as_dict()

    return app

if __name__ == "__main__":
    print("📚 Documentation API PassPrint configurée")