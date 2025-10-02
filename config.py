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
    return config_class()