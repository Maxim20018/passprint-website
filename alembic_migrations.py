#!/usr/bin/env python3
"""
Migrations Alembic pour PassPrint
Gère les migrations de base de données
"""
import os
import subprocess

def run_alembic_command(command):
    """Exécuter une commande Alembic"""
    try:
        result = subprocess.run(
            ['alembic', command],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def create_migration(message="Auto migration"):
    """Créer une nouvelle migration"""
    success, stdout, stderr = run_alembic_command(f'revision --autogenerate -m "{message}"')
    return success

def upgrade_database():
    """Mettre à jour la base de données"""
    success, stdout, stderr = run_alembic_command('upgrade head')
    return success

def downgrade_database():
    """Revenir en arrière"""
    success, stdout, stderr = run_alembic_command('downgrade -1')
    return success

if __name__ == "__main__":
    print("Migrations Alembic opérationnelles!")