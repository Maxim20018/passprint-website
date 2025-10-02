#!/usr/bin/env python3
"""
Serveur PassPrint avec API intégrée
Combine le serveur statique et l'API Flask
"""
import os
import sys
import subprocess
import webbrowser
from threading import Thread
import time
import http.server
import socketserver
import socket

# Configuration
PORT = 5000
API_PORT = 5001

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handler personnalisé pour servir les fichiers statiques"""

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def guess_type(self, path):
        """Déterminer le type MIME"""
        mimetype, encoding = super().guess_type(path)

        # Support pour les fichiers SVG
        if path.endswith('.svg'):
            return 'image/svg+xml'
        elif path.endswith('.js'):
            return 'application/javascript'
        elif path.endswith('.css'):
            return 'text/css'

        return mimetype

def start_static_server():
    """Démarrer le serveur de fichiers statiques"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"📁 Serveur de fichiers démarré sur le port {PORT}")
        print(f"🌐 http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Serveur de fichiers arrêté")
            httpd.shutdown()

def start_api_server():
    """Démarrer le serveur API Flask"""
    try:
        print(f"🚀 Démarrage de l'API Flask sur le port {API_PORT}...")
        subprocess.run([
            sys.executable, "app.py"
        ], cwd=os.path.dirname(os.path.abspath(__file__)))
    except KeyboardInterrupt:
        print("\n🛑 Serveur API arrêté")
    except Exception as e:
        print(f"❌ Erreur lors du démarrage de l'API: {e}")

def check_requirements():
    """Verifier si les dependances sont installees"""
    try:
        import flask
        import flask_sqlalchemy
        import flask_cors
        print("Toutes les dependances sont installees")
        return True
    except ImportError as e:
        print(f"Dependances manquantes: {e}")
        print("Installation des dependances...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
            print("Dependances installees avec succes")
            return True
        except subprocess.CalledProcessError:
            print("Erreur lors de l'installation des dependances")
            print("Lancez: pip install -r requirements.txt")
            return False

def initialize_database():
    """Initialiser la base de donnees"""
    print("Initialisation de la base de donnees...")
    try:
        subprocess.run([sys.executable, "init_db.py"], check=True)
        print("Base de donnees initialisee")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'initialisation de la base de donnees: {e}")
        return False
    except FileNotFoundError:
        print("Script d'initialisation non trouve, creation de la base de donnees basique...")
        try:
            from app import create_app
            app = create_app()
            with app.app_context():
                from models import db
                db.create_all()
            print("Base de donnees creee")
        except Exception as e:
            print(f"Erreur lors de la creation de la base de donnees: {e}")
            return False
    return True

def get_local_ip():
    """Obtenir l'adresse IP locale"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

def main():
    """Fonction principale"""
    print("Demarrage de PassPrint Server...")
    print("=" * 50)

    # Verifier les dependances
    if not check_requirements():
        print("Impossible de continuer sans les dependances")
        input("Appuyez sur Entree pour quitter...")
        return

    # Initialiser la base de donnees
    if not initialize_database():
        print("Impossible de continuer sans base de donnees")
        input("Appuyez sur Entree pour quitter...")
        return

    # Obtenir l'adresse IP locale
    local_ip = get_local_ip()

    print("Serveur pret!")
    print(f"Site web: http://localhost:{PORT}")
    print(f"Reseau: http://{local_ip}:{PORT}")
    print(f"API: http://localhost:{API_PORT}")
    print(f"QR Code: Utilisez http://{local_ip}:{PORT}")
    print("-" * 50)

    # Creer le dossier uploads s'il n'existe pas
    os.makedirs("uploads", exist_ok=True)

    # Creer le QR code
    try:
        from qr_generator import create_qr_code
        url = f"http://{local_ip}:{PORT}"
        print(f"Generation du QR code pour: {url}")
        create_qr_code()
        print("QR code cree: qr_code.png")
    except Exception as e:
        print(f"Impossible de creer le QR code: {e}")

    print("Ouvrir automatiquement le navigateur...")
    try:
        webbrowser.open(f'http://localhost:{PORT}')
    except:
        print("Ouvrez manuellement: http://localhost:{PORT}")

    print("\nAppuyez sur Ctrl+C pour arreter les serveurs")

    try:
        # Démarrer les serveurs dans des threads séparés
        static_thread = Thread(target=start_static_server, daemon=True)
        api_thread = Thread(target=start_api_server, daemon=True)

        static_thread.start()
        api_thread.start()

        # Garder le programme en vie
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Arrêt des serveurs...")
        print("✅ Serveurs arrêtés avec succès")
        print("👋 Au revoir!")

if __name__ == "__main__":
    main()