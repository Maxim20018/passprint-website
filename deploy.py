#!/usr/bin/env python3
"""
Script de déploiement pour PassPrint
Configure l'application pour la production
"""
import os
import subprocess
import sys
from config import ProductionConfig

def check_python_version():
    """Vérifier la version Python"""
    print("🐍 Vérification de Python...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ requis")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True

def install_dependencies():
    """Installer les dépendances"""
    print("📦 Installation des dépendances...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dépendances installées")
        return True
    except subprocess.CalledProcessError:
        print("❌ Erreur installation dépendances")
        return False

def setup_database():
    """Configurer la base de données"""
    print("🗄️  Configuration base de données...")
    try:
        # Utiliser PostgreSQL en production
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            print("⚠️  DATABASE_URL non configurée, utilisation SQLite")
            db_url = 'sqlite:///passprint.db'

        print(f"📊 Base de données: {db_url.split('://')[0]}")
        return True
    except Exception as e:
        print(f"❌ Erreur configuration DB: {e}")
        return False

def setup_ssl():
    """Configurer SSL/TLS"""
    print("🔒 Configuration SSL...")
    try:
        # Vérifier si les certificats existent
        ssl_cert = "/etc/ssl/certs/passprint.crt"
        ssl_key = "/etc/ssl/private/passprint.key"

        if os.path.exists(ssl_cert) and os.path.exists(ssl_key):
            print("✅ Certificats SSL trouvés")
            return True
        else:
            print("⚠️  Certificats SSL non trouvés")
            print("💡 Générez les certificats avec: sudo certbot certonly --standalone -d votre-domaine.com")
            return False
    except Exception as e:
        print(f"❌ Erreur SSL: {e}")
        return False

def create_directories():
    """Créer les répertoires nécessaires"""
    print("📁 Création des répertoires...")
    dirs = ['uploads', 'backups', 'logs', 'static']

    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
        print(f"  ✅ {dir_name}/")

    return True

def setup_nginx():
    """Configurer Nginx"""
    print("🌐 Configuration Nginx...")
    try:
        nginx_config = """
server {
    listen 80;
    server_name _;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name _;

    ssl_certificate /etc/ssl/certs/passprint.crt;
    ssl_certificate_key /etc/ssl/private/passprint.key;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
"""

        with open('/etc/nginx/sites-available/passprint', 'w') as f:
            f.write(nginx_config)

        # Activer le site
        subprocess.run(['sudo', 'ln', '-sf', '/etc/nginx/sites-available/passprint', '/etc/nginx/sites-enabled/'], check=True)
        subprocess.run(['sudo', 'nginx', '-t'], check=True)

        print("✅ Configuration Nginx créée")
        return True

    except Exception as e:
        print(f"❌ Erreur Nginx: {e}")
        return False

def setup_systemd():
    """Configurer systemd"""
    print("⚙️  Configuration systemd...")
    try:
        service_config = """
[Unit]
Description=PassPrint API Server
After=network.target

[Service]
User=passprint
Group=passprint
WorkingDirectory=/opt/passprint-website
Environment=FLASK_ENV=production
Environment=PATH=/opt/passprint-website/venv/bin
ExecStart=/opt/passprint-website/venv/bin/python app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""

        with open('/etc/systemd/system/passprint.service', 'w') as f:
            f.write(service_config)

        subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
        print("✅ Service systemd configuré")
        return True

    except Exception as e:
        print(f"❌ Erreur systemd: {e}")
        return False

def setup_firewall():
    """Configurer le firewall"""
    print("🔥 Configuration firewall...")
    try:
        # Autoriser les ports 80, 443, 5000, 5001
        ports = [80, 443, 5000, 5001]
        for port in ports:
            subprocess.run(['sudo', 'ufw', 'allow', str(port)], check=True)

        print("✅ Ports autorisés dans le firewall")
        return True
    except Exception as e:
        print(f"❌ Erreur firewall: {e}")
        return False

def generate_env_file():
    """Générer le fichier .env de production"""
    print("📝 Génération .env de production...")
    try:
        env_content = """# Production Environment Variables
FLASK_ENV=production
DEBUG=False

# Database
DATABASE_URL=postgresql://passprint:password@localhost/passprint_prod

# Security
SECRET_KEY=changez_avec_une_cle_securisee_256_bits
JWT_SECRET_KEY=changez_avec_une_cle_jwt_securisee

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=contact@passprint.com
SMTP_PASSWORD=votre_mot_de_passe_app

# Stripe (clés de production)
STRIPE_PUBLIC_KEY=pk_live_votre_cle_stripe
STRIPE_SECRET_KEY=sk_live_votre_cle_stripe
STRIPE_WEBHOOK_SECRET=whsec_votre_webhook_secret

# File Upload
UPLOAD_FOLDER=/opt/passprint-website/uploads/
MAX_CONTENT_LENGTH=52428800

# Logging
LOG_LEVEL=INFO
"""

        with open('.env.production', 'w') as f:
            f.write(env_content)

        print("✅ .env.production créé")
        print("💡 Modifiez les valeurs selon votre configuration")
        return True

    except Exception as e:
        print(f"❌ Erreur génération .env: {e}")
        return False

def run_migrations():
    """Exécuter les migrations"""
    print("🗄️  Exécution des migrations...")
    try:
        from app import create_app
        app = create_app()

        with app.app_context():
            from models import db
            db.create_all()

        print("✅ Migrations exécutées")
        return True
    except Exception as e:
        print(f"❌ Erreur migrations: {e}")
        return False

def main():
    """Fonction principale de déploiement"""
    print("🚀 Déploiement PassPrint en production")
    print("=" * 50)

    if not check_python_version():
        return False

    steps = [
        ("Installation dépendances", install_dependencies),
        ("Configuration base de données", setup_database),
        ("Configuration SSL", setup_ssl),
        ("Création répertoires", create_directories),
        ("Configuration Nginx", setup_nginx),
        ("Configuration systemd", setup_systemd),
        ("Configuration firewall", setup_firewall),
        ("Génération .env", generate_env_file),
        ("Migrations base de données", run_migrations),
    ]

    success = True
    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        if not step_func():
            success = False
            print(f"❌ Échec: {step_name}")

    if success:
        print("\n🎉 Déploiement réussi!")
        print("\n📋 Prochaines étapes:")
        print("1. Modifiez .env.production avec vos vraies valeurs")
        print("2. Redémarrez Nginx: sudo systemctl reload nginx")
        print("3. Activez le service: sudo systemctl enable passprint")
        print("4. Démarrez le service: sudo systemctl start passprint")
        print("5. Vérifiez les logs: sudo journalctl -u passprint -f")
    else:
        print("\n❌ Déploiement échoué")
        print("🔧 Corrigez les erreurs et relancez le script")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)