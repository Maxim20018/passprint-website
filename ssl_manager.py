#!/usr/bin/env python3
"""
Gestionnaire SSL pour PassPrint
Gère les certificats SSL automatiquement
"""
import os
import subprocess
import shutil

class SSLManager:
    """Gestionnaire de certificats SSL"""

    def __init__(self):
        self.certbot_path = "/usr/bin/certbot"
        self.nginx_path = "/etc/nginx/sites-available"
        self.ssl_dir = "/etc/ssl/certs"

    def install_certbot(self):
        """Installer certbot"""
        try:
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            subprocess.run(['sudo', 'apt', 'install', 'certbot', 'python3-certbot-nginx'], check=True)
            return True
        except Exception as e:
            print(f"Erreur installation certbot: {e}")
            return False

    def generate_certificate(self, domain: str):
        """Générer un certificat SSL"""
        try:
            subprocess.run([
                'sudo', 'certbot', '--nginx',
                '-d', domain,
                '--non-interactive',
                '--agree-tos',
                '-m', f'admin@{domain}'
            ], check=True)
            return True
        except Exception as e:
            print(f"Erreur génération certificat: {e}")
            return False

    def renew_certificates(self):
        """Renouveler les certificats"""
        try:
            subprocess.run(['sudo', 'certbot', 'renew'], check=True)
            return True
        except Exception as e:
            print(f"Erreur renouvellement: {e}")
            return False

# Instance globale du gestionnaire SSL
ssl_manager = SSLManager()

def setup_ssl(domain: str):
    """Configurer SSL pour un domaine"""
    return ssl_manager.generate_certificate(domain)

def renew_ssl():
    """Renouveler les certificats SSL"""
    return ssl_manager.renew_certificates()

if __name__ == "__main__":
    print("Gestionnaire SSL opérationnel!")