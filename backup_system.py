#!/usr/bin/env python3
"""
Système de sauvegarde automatique pour PassPrint
Sauvegarde la base de données et les fichiers
"""
import shutil
import os
from datetime import datetime
import schedule
import time
import threading

class BackupSystem:
    """Système de sauvegarde automatique"""

    def __init__(self):
        self.backup_dir = "backups"
        os.makedirs(self.backup_dir, exist_ok=True)

    def backup_database(self):
        """Sauvegarder la base de données"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f"passprint_backup_{timestamp}.db")

            shutil.copy2("passprint.db", backup_file)

            print(f"Base de données sauvegardée: {backup_file}")
            return True
        except Exception as e:
            print(f"Erreur sauvegarde DB: {e}")
            return False

    def backup_files(self):
        """Sauvegarder les fichiers uploadés"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(self.backup_dir, f"files_backup_{timestamp}")

            if os.path.exists("uploads"):
                shutil.copytree("uploads", backup_dir)

            print(f"Fichiers sauvegardés: {backup_dir}")
            return True
        except Exception as e:
            print(f"Erreur sauvegarde fichiers: {e}")
            return False

    def cleanup_old_backups(self, days=7):
        """Nettoyer les anciennes sauvegardes"""
        try:
            cutoff_date = datetime.now().timestamp() - (days * 24 * 3600)

            for item in os.listdir(self.backup_dir):
                item_path = os.path.join(self.backup_dir, item)
                if os.path.getctime(item_path) < cutoff_date:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)

            print(f"Anciennes sauvegardes nettoyées (>{days} jours)")
            return True
        except Exception as e:
            print(f"Erreur nettoyage: {e}")
            return False

# Instance globale du système de sauvegarde
backup_system = BackupSystem()

def create_backup():
    """Créer une sauvegarde complète"""
    backup_system.backup_database()
    backup_system.backup_files()
    backup_system.cleanup_old_backups()

def schedule_backups():
    """Planifier les sauvegardes automatiques"""
    schedule.every().day.at("02:00").do(create_backup)
    schedule.every().day.at("14:00").do(create_backup)

    while True:
        schedule.run_pending()
        time.sleep(3600)  # Vérifier chaque heure

if __name__ == "__main__":
    print("Système de sauvegarde opérationnel!")