#!/usr/bin/env python3
"""
Script de configuration GitHub pour PassPrint
Guide et automatisation pour pousser le projet sur GitHub
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

def init_git_repository():
    """Initialiser le repository Git"""
    try:
        # Vérifier si déjà initialisé
        if os.path.exists('.git'):
            print("Repository Git déjà initialisé")
            return True

        # Initialiser Git
        subprocess.run(['git', 'init'], check=True)
        print("Repository Git initialisé avec succès")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Erreur initialisation Git: {e}")
        return False

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
        print("Fichier .gitignore créé")
        return True
    except Exception as e:
        print(f"Erreur création .gitignore: {e}")
        return False

def add_files_to_git():
    """Ajouter les fichiers à Git"""
    try:
        subprocess.run(['git', 'add', '.'], check=True)
        print("Fichiers ajoutés à Git")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erreur ajout fichiers: {e}")
        return False

def commit_changes():
    """Créer le commit initial"""
    try:
        subprocess.run([
            'git', 'commit', '-m',
            'Initial commit: PassPrint - Plateforme e-commerce complète avec backend API, dashboard administration, et fonctionnalités avancées'
        ], check=True)
        print("Commit créé avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erreur commit: {e}")
        return False

def create_github_repository():
    """Guide pour créer le repository GitHub"""
    print("\n" + "="*60)
    print("📋 GUIDE CRÉATION REPOSITORY GITHUB")
    print("="*60)
    print()
    print("1. Allez sur: https://github.com")
    print("2. Cliquez sur 'New repository'")
    print("3. Nom du repository: 'passprint-website'")
    print("4. Description: 'Plateforme e-commerce complète pour imprimerie'")
    print("5. Choisissez 'Public' ou 'Private'")
    print("6. NE cochez PAS 'Add a README file'")
    print("7. Cliquez sur 'Create repository'")
    print()
    print("📝 Copiez l'URL du repository (https://github.com/VOTRE_USERNAME/passprint-website.git)")
    print("="*60)

    return input("Entrez l'URL de votre repository GitHub: ").strip()

def setup_remote_and_push(repo_url):
    """Configurer le remote et pousser"""
    try:
        # Ajouter le remote
        subprocess.run(['git', 'remote', 'add', 'origin', repo_url], check=True)

        # Créer la branche main
        subprocess.run(['git', 'branch', '-M', 'main'], check=True)

        # Pousser vers GitHub
        result = subprocess.run(['git', 'push', '-u', 'origin', 'main'],
                              capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Projet poussé sur GitHub avec succès!")
            print(f"🌐 Repository: {repo_url}")
            return True
        else:
            print(f"❌ Erreur push GitHub: {result.stderr}")
            return False

    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur configuration GitHub: {e}")
        return False

def main():
    """Fonction principale"""
    print("🚀 Configuration GitHub pour PassPrint")
    print("=" * 50)

    # Vérifier Git
    if not check_git():
        print("❌ Git n'est pas installé")
        print("📥 Installez Git depuis: https://git-scm.com/downloads")
        return

    print("✅ Git est installé")

    # Initialiser le repository
    if not init_git_repository():
        return

    # Créer .gitignore
    if not create_gitignore():
        return

    # Ajouter les fichiers
    if not add_files_to_git():
        return

    # Commit
    if not commit_changes():
        return

    # Guide GitHub
    repo_url = create_github_repository()

    if repo_url:
        # Setup remote et push
        if setup_remote_and_push(repo_url):
            print("\n🎉 Succès! Votre projet PassPrint est maintenant sur GitHub!")
            print(f"🔗 {repo_url}")
        else:
            print("\n⚠️  Le repository local est prêt, mais le push a échoué")
            print("💡 Vous pouvez pousser manuellement avec:")
            print(f"   git remote add origin {repo_url}")
            print("   git push -u origin main")
    else:
        print("\n⚠️  Configuration GitHub annulée")
        print("💡 Votre repository local est prêt")
        print("   Vous pouvez configurer GitHub plus tard avec:")
        print("   git remote add origin VOTRE_REPO_URL")
        print("   git push -u origin main")

if __name__ == "__main__":
    main()