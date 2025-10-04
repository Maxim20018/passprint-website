"""
Configuration de l'application PassPrint
"""
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class Config:
    """Configuration de base"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///passprint.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # File upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'ai', 'eps', 'zip'}

    # Pagination
    ITEMS_PER_PAGE = 20

    # Email configuration
    MAIL_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('SMTP_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.getenv('SMTP_USERNAME')
    MAIL_PASSWORD = os.getenv('SMTP_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('SMTP_USERNAME', 'noreply@passprint.com')

class DevelopmentConfig(Config):
    """Configuration de développement"""
    DEBUG = True
    DEVELOPMENT = True
    TESTING = False

    # Stripe test keys
    STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY', 'pk_test_dev_key')
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', 'sk_test_dev_key')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', 'whsec_dev_key')

class ProductionConfig(Config):
    """Configuration de production"""
    DEBUG = False
    DEVELOPMENT = False
    TESTING = False

    # Stripe live keys (à configurer en production)
    STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY', 'pk_live_key')
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', 'sk_live_key')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', 'whsec_live_key')

class TestingConfig(Config):
    """Configuration de test"""
    DEBUG = True
    DEVELOPMENT = False
    TESTING = True

    # Database de test
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'

    # Désactiver les emails en test
    MAIL_SUPPRESS_SEND = True

# Configuration selon l'environnement
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Retourne la configuration selon l'environnement"""
    env = os.getenv('FLASK_ENV', 'development')
    config_class = config.get(env, config['default'])

    # Créer une instance pour permettre la modification
    instance = config_class()

    # Configuration spécifique selon l'environnement
    if env == 'production':
        # Configuration de sécurité renforcée en production
        instance.SECRET_KEY = os.getenv('SECRET_KEY')
        if not instance.SECRET_KEY or len(instance.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY doit être définie et contenir au moins 32 caractères en production")

        instance.JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
        if not instance.JWT_SECRET_KEY or len(instance.JWT_SECRET_KEY) < 32:
            raise ValueError("JWT_SECRET_KEY doit être définie et contenir au moins 32 caractères en production")

        # Configuration de la base de données en production
        instance.SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
        if not instance.SQLALCHEMY_DATABASE_URI:
            raise ValueError("DATABASE_URL doit être définie en production")

        # Configuration Redis en production
        instance.REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

        # Configuration CDN en production
        instance.CDN_ENABLED = os.getenv('CDN_ENABLED', 'false').lower() == 'true'
        instance.CDN_BASE_URL = os.getenv('CDN_BASE_URL', 'https://cdn.passprint.com')

        # Configuration monitoring en production
        instance.SENTRY_DSN = os.getenv('SENTRY_DSN')
        instance.PROMETHEUS_ENABLED = os.getenv('PROMETHEUS_ENABLED', 'false').lower() == 'true'

        # Configuration des sauvegardes en production
        instance.BACKUP_ENABLED = os.getenv('BACKUP_ENABLED', 'true').lower() == 'true'
        instance.BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', '30'))

        # Configuration des emails en production
        instance.MAIL_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        instance.MAIL_PORT = int(os.getenv('SMTP_PORT', '587'))
        instance.MAIL_USERNAME = os.getenv('SMTP_USERNAME')
        instance.MAIL_PASSWORD = os.getenv('SMTP_PASSWORD')

        if not instance.MAIL_USERNAME or not instance.MAIL_PASSWORD:
            raise ValueError("Configuration email requise en production")

        # Configuration Stripe en production
        instance.STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY')
        instance.STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
        instance.STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

        if not instance.STRIPE_SECRET_KEY:
            raise ValueError("Configuration Stripe requise en production")

        # Configuration des logs en production
        instance.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        instance.EXTERNAL_LOG_URL = os.getenv('EXTERNAL_LOG_URL')

        # Configuration de sécurité renforcée
        instance.MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))
        instance.LOCKOUT_DURATION_MINUTES = int(os.getenv('LOCKOUT_DURATION_MINUTES', '15'))
        instance.PASSWORD_MIN_LENGTH = int(os.getenv('PASSWORD_MIN_LENGTH', '12'))

        # Configuration des performances
        instance.CACHE_TTL = int(os.getenv('CACHE_TTL', '300'))
        instance.RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', '100'))

        # Configuration des workers Celery
        instance.CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        instance.CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    elif env == 'testing':
        # Configuration spécifique aux tests
        instance.TESTING = True
        instance.WTF_CSRF_ENABLED = False
        instance.SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
        instance.REDIS_URL = 'redis://localhost:6379/1'  # Base de données Redis séparée pour les tests
        instance.MAIL_SUPPRESS_SEND = True
        instance.LOG_LEVEL = 'DEBUG'

        # Désactiver les sauvegardes automatiques en test
        instance.BACKUP_ENABLED = False

        # Configuration Celery pour les tests
        instance.CELERY_BROKER_URL = 'redis://localhost:6379/1'
        instance.CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
        instance.CELERY_TASK_ALWAYS_EAGER = True
        instance.CELERY_TASK_EAGER_PROPAGATES = True

    elif env == 'development':
        # Configuration de développement
        instance.DEBUG = True
        instance.TEMPLATES_AUTO_RELOAD = True
        instance.SEND_FILE_MAX_AGE_DEFAULT = 0

        # Configuration Redis pour le développement
        instance.REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

        # Configuration des sauvegardes en développement
        instance.BACKUP_ENABLED = os.getenv('BACKUP_ENABLED', 'false').lower() == 'true'

        # Configuration Celery pour le développement
        instance.CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        instance.CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # Configuration commune à tous les environnements
    instance.HOST = os.getenv('HOST', '0.0.0.0')
    instance.PORT = int(os.getenv('PORT', '5000'))
    instance.DEBUG = os.getenv('DEBUG', 'false' if env == 'production' else 'true').lower() == 'true'

    # Configuration des chemins
    instance.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    instance.STATIC_FOLDER = os.path.join(instance.BASE_DIR, 'static')
    instance.UPLOAD_FOLDER = os.path.join(instance.BASE_DIR, 'uploads')
    instance.LOGS_FOLDER = os.path.join(instance.BASE_DIR, 'logs')
    instance.BACKUPS_FOLDER = os.path.join(instance.BASE_DIR, 'backups')

    # Créer les dossiers nécessaires
    for folder in [instance.UPLOAD_FOLDER, instance.LOGS_FOLDER, instance.BACKUPS_FOLDER]:
        os.makedirs(folder, exist_ok=True)

    # Configuration des extensions de fichiers autorisées
    instance.ALLOWED_EXTENSIONS = {
        'images': {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'},
        'documents': {'pdf', 'doc', 'docx', 'txt'},
        'archives': {'zip', 'rar', '7z'},
        'design': {'ai', 'eps', 'psd', 'svg'}
    }

    # Configuration des limites de fichiers
    instance.MAX_FILE_SIZE = {
        'images': 10 * 1024 * 1024,  # 10MB
        'documents': 25 * 1024 * 1024,  # 25MB
        'archives': 50 * 1024 * 1024,  # 50MB
        'design': 100 * 1024 * 1024  # 100MB
    }

    # Configuration des timeouts
    instance.TIMEOUTS = {
        'REQUEST_TIMEOUT': int(os.getenv('REQUEST_TIMEOUT', '30')),
        'UPLOAD_TIMEOUT': int(os.getenv('UPLOAD_TIMEOUT', '300')),
        'PROCESSING_TIMEOUT': int(os.getenv('PROCESSING_TIMEOUT', '600'))
    }

    # Configuration des langues et locales
    instance.SUPPORTED_LANGUAGES = ['fr', 'en']
    instance.DEFAULT_LANGUAGE = 'fr'

    # Configuration des devises
    instance.SUPPORTED_CURRENCIES = ['XOF', 'EUR', 'USD']
    instance.DEFAULT_CURRENCY = 'XOF'

    # Configuration des unités de mesure
    instance.UNITS = {
        'length': ['mm', 'cm', 'm', 'inch'],
        'weight': ['g', 'kg', 'lb'],
        'quantity': ['unit', 'pack', 'box']
    }

    # Configuration des catégories de produits
    instance.PRODUCT_CATEGORIES = {
        'print': {
            'name': 'Impression',
            'subcategories': ['cartes', 'flyers', 'affiches', 'banderoles', 'autocollants']
        },
        'supplies': {
            'name': 'Fournitures',
            'subcategories': ['papier', 'encre', 'toner', 'accessoires']
        },
        'usb': {
            'name': 'Clés USB',
            'subcategories': ['8gb', '16gb', '32gb', '64gb', '128gb']
        },
        'other': {
            'name': 'Autres',
            'subcategories': ['services', 'consultation', 'design']
        }
    }

    # Configuration des statuts de commande
    instance.ORDER_STATUS = {
        'pending': {'name': 'En attente', 'color': 'orange', 'icon': 'clock'},
        'confirmed': {'name': 'Confirmée', 'color': 'blue', 'icon': 'check-circle'},
        'processing': {'name': 'En cours', 'color': 'yellow', 'icon': 'cog'},
        'shipped': {'name': 'Expédiée', 'color': 'purple', 'icon': 'truck'},
        'delivered': {'name': 'Livrée', 'color': 'green', 'icon': 'check'},
        'cancelled': {'name': 'Annulée', 'color': 'red', 'icon': 'times-circle'}
    }

    # Configuration des méthodes de paiement
    instance.PAYMENT_METHODS = {
        'stripe': {
            'enabled': True,
            'currencies': ['XOF', 'EUR', 'USD'],
            'webhook_url': os.getenv('STRIPE_WEBHOOK_URL')
        },
        'bank_transfer': {
            'enabled': True,
            'currencies': ['XOF', 'EUR', 'USD']
        },
        'cash': {
            'enabled': True,
            'currencies': ['XOF']
        }
    }

    # Configuration des notifications
    instance.NOTIFICATIONS = {
        'email': {
            'enabled': True,
            'templates': {
                'welcome': 'emails/welcome.html',
                'order_confirmation': 'emails/order_confirmation.html',
                'quote_ready': 'emails/quote_ready.html',
                'payment_received': 'emails/payment_received.html'
            }
        },
        'sms': {
            'enabled': os.getenv('SMS_ENABLED', 'false').lower() == 'true',
            'provider': os.getenv('SMS_PROVIDER', 'twilio'),
            'api_key': os.getenv('SMS_API_KEY'),
            'api_secret': os.getenv('SMS_API_SECRET')
        },
        'push': {
            'enabled': os.getenv('PUSH_ENABLED', 'false').lower() == 'true',
            'vapid_public': os.getenv('VAPID_PUBLIC_KEY'),
            'vapid_private': os.getenv('VAPID_PRIVATE_KEY')
        }
    }

    # Configuration des intégrations tierces
    instance.INTEGRATIONS = {
        'google_analytics': {
            'enabled': os.getenv('GA_ENABLED', 'false').lower() == 'true',
            'tracking_id': os.getenv('GA_TRACKING_ID')
        },
        'facebook_pixel': {
            'enabled': os.getenv('FB_PIXEL_ENABLED', 'false').lower() == 'true',
            'pixel_id': os.getenv('FB_PIXEL_ID')
        },
        'mailchimp': {
            'enabled': os.getenv('MAILCHIMP_ENABLED', 'false').lower() == 'true',
            'api_key': os.getenv('MAILCHIMP_API_KEY'),
            'list_id': os.getenv('MAILCHIMP_LIST_ID')
        },
        'zapier': {
            'enabled': os.getenv('ZAPIER_ENABLED', 'false').lower() == 'true',
            'webhook_url': os.getenv('ZAPIER_WEBHOOK_URL')
        }
    }

    # Configuration des fonctionnalités expérimentales
    instance.FEATURE_FLAGS = {
        'advanced_analytics': os.getenv('FEATURE_ADVANCED_ANALYTICS', 'false').lower() == 'true',
        'ai_pricing': os.getenv('FEATURE_AI_PRICING', 'false').lower() == 'true',
        'real_time_chat': os.getenv('FEATURE_REAL_TIME_CHAT', 'false').lower() == 'true',
        'mobile_app': os.getenv('FEATURE_MOBILE_APP', 'false').lower() == 'true',
        'api_v2': os.getenv('FEATURE_API_V2', 'false').lower() == 'true'
    }

    # Configuration des limites système
    instance.LIMITS = {
        'max_orders_per_day': int(os.getenv('MAX_ORDERS_PER_DAY', '1000')),
        'max_users_per_day': int(os.getenv('MAX_USERS_PER_DAY', '100')),
        'max_file_uploads_per_hour': int(os.getenv('MAX_FILE_UPLOADS_PER_HOUR', '50')),
        'max_api_requests_per_minute': int(os.getenv('MAX_API_REQUESTS_PER_MINUTE', '1000')),
        'max_quote_requests_per_hour': int(os.getenv('MAX_QUOTE_REQUESTS_PER_HOUR', '20'))
    }

    # Configuration des politiques de rétention
    instance.RETENTION_POLICIES = {
        'audit_logs_days': int(os.getenv('AUDIT_LOGS_RETENTION_DAYS', '365')),
        'user_data_days': int(os.getenv('USER_DATA_RETENTION_DAYS', '2555')),  # 7 ans
        'order_data_days': int(os.getenv('ORDER_DATA_RETENTION_DAYS', '2555')),  # 7 ans
        'backup_retention_days': int(os.getenv('BACKUP_RETENTION_DAYS', '90')),
        'temp_files_hours': int(os.getenv('TEMP_FILES_RETENTION_HOURS', '24'))
    }

    # Configuration des seuils d'alerte
    instance.ALERT_THRESHOLDS = {
        'disk_usage_percent': int(os.getenv('DISK_USAGE_ALERT_PERCENT', '80')),
        'memory_usage_percent': int(os.getenv('MEMORY_USAGE_ALERT_PERCENT', '85')),
        'cpu_usage_percent': int(os.getenv('CPU_USAGE_ALERT_PERCENT', '75')),
        'error_rate_percent': int(os.getenv('ERROR_RATE_ALERT_PERCENT', '5')),
        'response_time_ms': int(os.getenv('RESPONSE_TIME_ALERT_MS', '5000'))
    }

    # Configuration des sauvegardes automatiques
    instance.BACKUP_CONFIG = {
        'enabled': os.getenv('BACKUP_ENABLED', 'true' if env == 'production' else 'false').lower() == 'true',
        'frequency_hours': int(os.getenv('BACKUP_FREQUENCY_HOURS', '24')),
        'retention_days': int(os.getenv('BACKUP_RETENTION_DAYS', '30')),
        'compression_enabled': os.getenv('BACKUP_COMPRESSION', 'true').lower() == 'true',
        'encryption_enabled': os.getenv('BACKUP_ENCRYPTION', 'false').lower() == 'true',
        'cloud_upload': os.getenv('BACKUP_CLOUD_UPLOAD', 'false').lower() == 'true'
    }

    # Configuration du monitoring
    instance.MONITORING_CONFIG = {
        'enabled': os.getenv('MONITORING_ENABLED', 'true' if env == 'production' else 'false').lower() == 'true',
        'metrics_enabled': os.getenv('METRICS_ENABLED', 'true').lower() == 'true',
        'tracing_enabled': os.getenv('TRACING_ENABLED', 'false').lower() == 'true',
        'log_aggregation': os.getenv('LOG_AGGREGATION', 'false').lower() == 'true',
        'alerting_enabled': os.getenv('ALERTING_ENABLED', 'true' if env == 'production' else 'false').lower() == 'true'
    }

    # Configuration des performances
    instance.PERFORMANCE_CONFIG = {
        'cache_enabled': os.getenv('CACHE_ENABLED', 'true').lower() == 'true',
        'compression_enabled': os.getenv('COMPRESSION_ENABLED', 'true').lower() == 'true',
        'minify_html': os.getenv('MINIFY_HTML', 'false').lower() == 'true',
        'optimize_images': os.getenv('OPTIMIZE_IMAGES', 'true').lower() == 'true',
        'lazy_loading': os.getenv('LAZY_LOADING', 'true').lower() == 'true',
        'cdn_enabled': os.getenv('CDN_ENABLED', 'false').lower() == 'true'
    }

    # Configuration de débogage
    instance.DEBUG_CONFIG = {
        'show_sql_queries': os.getenv('DEBUG_SHOW_SQL', 'false').lower() == 'true',
        'show_cache_stats': os.getenv('DEBUG_SHOW_CACHE', 'false').lower() == 'true',
        'show_performance_metrics': os.getenv('DEBUG_SHOW_PERFORMANCE', 'false').lower() == 'true',
        'enable_profiler': os.getenv('DEBUG_ENABLE_PROFILER', 'false').lower() == 'true'
    }

    return instance