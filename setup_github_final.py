#!/usr/bin/env python3
"""
Configuration finale GitHub pour PassPrint
Guide complet pour pousser le projet sur GitHub
"""
import os
import subprocess
import sys

def check_git():
    """Vérifier si Git est installé"""
    try:
        subprocess.run(['git', '--version'], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_git():
    """Guide d'installation de Git"""
    print("Git n'est pas installe sur votre systeme.")
    print()
    print("POUR INSTALLER GIT:")
    print("1. Allez sur: https://git-scm.com/downloads")
    print("2. Telechargez la version pour Windows")
    print("3. Installez avec les options par defaut")
    print("4. Redemarrez votre terminal/VSCode")
    print()
    print("VERIFICATION:")
    print("Dans un terminal, tapez: git --version")
    print("Vous devriez voir: git version 2.x.x")

def create_gitignore():
    """Créer un fichier .gitignore approprié"""
    gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Flask
instance/
.webassets-cache

# Environment variables
.env
.env.local
.env.production

# Database
*.db
*.sqlite3

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Temporary files
tmp/
temp/

# Reports and exports
reports/
exports/
backups/

# Node modules (si utilisé)
node_modules/

# Build outputs
build/
dist/
"""

    try:
        with open('.gitignore', 'w') as f:
            f.write(gitignore_content)
        print("Fichier .gitignore cree")
        return True
    except Exception as e:
        print(f"Erreur creation .gitignore: {e}")
        return False

def manual_git_setup():
    """Guide de configuration Git manuelle"""
    print("\n" + "="*60)
    print("CONFIGURATION GIT MANUELLE")
    print("="*60)
    print()
    print("APRES AVOIR INSTALLE GIT:")
    print()
    print("1. Ouvrez un terminal dans le dossier passprint-website")
    print("2. Tapez les commandes suivantes:")
    print()
    print("git init")
    print("git add .")
    print('git commit -m "Initial commit: PassPrint - Plateforme e-commerce complete"')
    print("git branch -M main")
    print("git remote add origin https://github.com/Maxim20018/passprint-website.git")
    print("git push -u origin main")
    print()
    print("="*60)

def main():
    """Fonction principale"""
    print("Configuration GitHub pour PassPrint")
    print("=" * 50)

    # Vérifier Git
    if not check_git():
        print("Git n'est pas installe.")
        install_git()
        manual_git_setup()
        return

    print("Git est installe")

    # Créer .gitignore
    if not create_gitignore():
        return

    print("\n" + "="*60)
    print("PROCHAINE ETAPE: CONFIGURATION GITHUB")
    print("="*60)
    print()
    print("1. Allez sur: https://github.com/Maxim20018/passprint-website")
    print("2. Cliquez sur 'Settings' > 'Secrets and variables' > 'Actions'")
    print("3. Ajoutez ces secrets:")
    print("   STRIPE_PUBLIC_KEY: pk_test_votre_cle")
    print("   STRIPE_SECRET_KEY: sk_test_votre_cle")
    print("   SMTP_USERNAME: votre_email@gmail.com")
    print("   SMTP_PASSWORD: votre_mot_de_passe_app")
    print()
    print("4. Allez sur 'Settings' > 'Pages'")
    print("5. Activez GitHub Pages avec 'main' branch")
    print()
    print("Votre site sera accessible sur:")
    print("https://Maxim20018.github.io/passprint-website/")
    print("="*60)

if __name__ == "__main__":
    main()