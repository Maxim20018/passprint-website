#!/usr/bin/env python3
"""
Système de sauvegarde et récupération automatique pour PassPrint
Sauvegarde base de données, fichiers, et récupération après désastre
"""
import os
import shutil
import sqlite3
import psycopg2
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import gzip
import json
import logging
import tarfile
import zipfile
import tempfile
import threading
from contextlib import contextmanager
from typing import Dict, List, Optional, Tuple
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

from models import db, BackupLog, SystemConfig
from config import get_config
from monitoring_config import get_monitoring_integration

class BackupSystem:
    """Système de sauvegarde et récupération complet"""

    def __init__(self, app=None):
        self.app = app
        self.backup_dir = Path('backups')
        self.backup_dir.mkdir(exist_ok=True)
        self.temp_dir = Path('temp')
        self.temp_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)

        # Configuration depuis variables d'environnement
        self.retention_days = int(os.getenv('BACKUP_RETENTION_DAYS', '30'))
        self.max_backups = int(os.getenv('MAX_BACKUPS', '10'))
        self.compression_enabled = os.getenv('BACKUP_COMPRESSION', 'true').lower() == 'true'
        self.encryption_enabled = os.getenv('BACKUP_ENCRYPTION', 'false').lower() == 'true'
        self.cloud_backup_enabled = os.getenv('CLOUD_BACKUP_ENABLED', 'false').lower() == 'true'

        # Configuration PostgreSQL avancée
        self.pg_config = {
            'parallel_jobs': int(os.getenv('PG_BACKUP_JOBS', '2')),
            'buffer_size': os.getenv('PG_BUFFER_SIZE', '8192'),
            'compression_level': int(os.getenv('PG_COMPRESSION_LEVEL', '9')),
            'verbose': os.getenv('PG_VERBOSE', 'false').lower() == 'true'
        }

        # Configuration des snapshots de fichiers
        self.snapshot_config = {
            'create_snapshots': os.getenv('SNAPSHOT_ENABLED', 'true').lower() == 'true',
            'snapshot_dir': Path(os.getenv('SNAPSHOT_DIR', 'snapshots')),
            'snapshot_retention': int(os.getenv('SNAPSHOT_RETENTION_DAYS', '7'))
        }
        self.snapshot_config['snapshot_dir'].mkdir(exist_ok=True)

    def create_database_backup(self, backup_type: str = 'full') -> Tuple[bool, str]:
        """Créer une sauvegarde de la base de données"""
        try:
            config = get_config()
            db_url = config.SQLALCHEMY_DATABASE_URI

            if 'sqlite' in db_url:
                return self._backup_sqlite(db_url, backup_type)
            elif 'postgresql' in db_url:
                return self._backup_postgresql(db_url, backup_type)
            else:
                error_msg = f"Type de base de données non supporté: {db_url}"
                self.logger.error(error_msg)
                return False, error_msg

        except Exception as e:
            error_msg = f"Erreur sauvegarde base de données: {e}"
            self.logger.error(error_msg)
            self._log_backup_failure('database', error_msg)
            return False, error_msg

    def _backup_sqlite(self, db_url: str, backup_type: str) -> Tuple[bool, str]:
        """Sauvegarder une base SQLite avec métadonnées"""
        try:
            db_path = db_url.replace('sqlite:///', '')

            if not os.path.exists(db_path):
                error_msg = f"Fichier base de données non trouvé: {db_path}"
                return False, error_msg

            # Vérifier l'intégrité de la base avant sauvegarde
            if not self._verify_database_integrity(db_path):
                error_msg = "Échec de vérification d'intégrité de la base de données"
                return False, error_msg

            # Créer le nom du fichier de sauvegarde
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"passprint_sqlite_{backup_type}_{timestamp}.db.gz"
            backup_path = self.backup_dir / backup_filename

            # Créer la sauvegarde avec métadonnées
            backup_info = {
                'backup_type': backup_type,
                'database_type': 'sqlite',
                'timestamp': timestamp,
                'original_path': db_path,
                'backup_path': str(backup_path),
                'compression': 'gzip' if self.compression_enabled else 'none',
                'version': '1.0'
            }

            # Compresser le fichier avec métadonnées
            with open(db_path, 'rb') as f_in:
                with gzip.open(backup_path, 'wb') as f_out:
                    # Écrire les métadonnées
                    metadata = json.dumps(backup_info).encode()
                    f_out.write(metadata + b'\n')
                    # Copier les données de la base
                    shutil.copyfileobj(f_in, f_out)

            # Vérifier la sauvegarde créée
            if not self._verify_backup_integrity(backup_path):
                error_msg = "Échec de vérification d'intégrité de la sauvegarde"
                return False, error_msg

            backup_size = backup_path.stat().st_size

            # Enregistrer dans les logs
            self._log_backup_success('database', str(backup_path), backup_size, backup_info)

            self.logger.info(f"Sauvegarde SQLite créée: {backup_path} ({backup_size} bytes)")
            return True, str(backup_path)

        except Exception as e:
            error_msg = f"Erreur sauvegarde SQLite: {e}"
            self.logger.error(error_msg)
            return False, error_msg

    def _backup_postgresql(self, db_url: str, backup_type: str) -> Tuple[bool, str]:
        """Sauvegarder PostgreSQL avec options avancées"""
        try:
            # Parser l'URL PostgreSQL
            import re
            pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
            match = re.match(pattern, db_url)

            if not match:
                error_msg = "Format d'URL PostgreSQL invalide"
                return False, error_msg

            user, password, host, port, database = match.groups()

            # Créer le nom du fichier de sauvegarde
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"passprint_postgres_{backup_type}_{timestamp}.dump"
            if self.compression_enabled:
                backup_filename += '.gz'
            backup_path = self.backup_dir / backup_filename

            # Préparation des options pg_dump
            cmd = [
                'pg_dump',
                f'--host={host}',
                f'--port={port}',
                f'--username={user}',
                f'--dbname={database}',
                '--no-password',
                '--format=custom' if backup_type == 'full' else '--data-only',
                f'--compress={self.pg_config["compression_level"]}',
                f'--jobs={self.pg_config["parallel_jobs"]}'
            ]

            if backup_type == 'schema':
                cmd.append('--schema-only')
            elif backup_type == 'data':
                cmd.append('--data-only')

            if self.pg_config['verbose']:
                cmd.append('--verbose')

            # Définir le mot de passe
            env = os.environ.copy()
            env['PGPASSWORD'] = password

            # Exécuter la sauvegarde
            try:
                if self.compression_enabled:
                    # Utiliser gzip pour la compression
                    with open(backup_path, 'wb') as f:
                        # Exécuter pg_dump sans compression interne
                        cmd.remove(f'--compress={self.pg_config["compression_level"]}')

                        # Pipeline: pg_dump -> gzip
                        pg_dump = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
                        gzip_proc = subprocess.Popen(['gzip', f'-{self.pg_config["compression_level"]}'],
                                                   stdin=pg_dump.stdout, stdout=f)

                        pg_dump.stdout.close()
                        gzip_proc.communicate()

                        if pg_dump.returncode == 0 and gzip_proc.returncode == 0:
                            success = True
                        else:
                            success = False
                else:
                    # Sauvegarde sans compression
                    with open(backup_path, 'wb') as f:
                        result = subprocess.run(cmd, env=env, stdout=f, check=True, timeout=3600)
                        success = result.returncode == 0

                if not success:
                    error_msg = "Échec de l'exécution de pg_dump"
                    return False, error_msg

            except subprocess.TimeoutExpired:
                error_msg = "Timeout lors de la sauvegarde PostgreSQL"
                return False, error_msg
            except subprocess.CalledProcessError as e:
                error_msg = f"Erreur pg_dump: {e}"
                return False, error_msg

            # Vérifier la sauvegarde créée
            if not backup_path.exists() or backup_path.stat().st_size == 0:
                error_msg = "Fichier de sauvegarde vide ou non créé"
                return False, error_msg

            backup_size = backup_path.stat().st_size

            # Créer les métadonnées de sauvegarde
            backup_info = {
                'backup_type': backup_type,
                'database_type': 'postgresql',
                'timestamp': timestamp,
                'host': host,
                'port': port,
                'database': database,
                'backup_path': str(backup_path),
                'compression': 'gzip' if self.compression_enabled else 'none',
                'parallel_jobs': self.pg_config['parallel_jobs'],
                'version': '1.0'
            }

            # Ajouter les métadonnées au fichier de sauvegarde
            self._add_backup_metadata(backup_path, backup_info)

            # Enregistrer dans les logs
            self._log_backup_success('database', str(backup_path), backup_size, backup_info)

            self.logger.info(f"Sauvegarde PostgreSQL créée: {backup_path} ({backup_size} bytes)")
            return True, str(backup_path)

        except Exception as e:
            error_msg = f"Erreur sauvegarde PostgreSQL: {e}"
            self.logger.error(error_msg)
            return False, error_msg

    def create_files_backup(self, backup_type: str = 'incremental') -> Tuple[bool, str]:
        """Créer une sauvegarde des fichiers avec gestion différentielle"""
        try:
            # Déterminer les dossiers à sauvegarder
            backup_dirs = {
                'uploads': Path('uploads'),
                'static': Path('static'),
                'logs': Path('logs'),
                'config': Path('instance')  # Configuration sensible
            }

            # Vérifier que les dossiers existent
            existing_dirs = {k: v for k, v in backup_dirs.items() if v.exists()}

            if not existing_dirs:
                error_msg = "Aucun dossier à sauvegarder trouvé"
                return False, error_msg

            # Créer le nom du fichier de sauvegarde
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"passprint_files_{backup_type}_{timestamp}.tar.gz"
            backup_path = self.backup_dir / backup_filename

            # Créer l'archive avec métadonnées
            backup_info = {
                'backup_type': backup_type,
                'file_type': 'filesystem',
                'timestamp': timestamp,
                'directories': list(existing_dirs.keys()),
                'compression': 'gzip' if self.compression_enabled else 'none',
                'version': '1.0'
            }

            # Créer l'archive tar
            try:
                with tarfile.open(backup_path, 'w:gz' if self.compression_enabled else 'w') as tar:
                    for dir_name, dir_path in existing_dirs.items():
                        if dir_path.exists():
                            self.logger.info(f"Ajout du dossier {dir_name} à la sauvegarde")
                            tar.add(dir_path, arcname=f'passprint/{dir_name}')

                # Ajouter les métadonnées
                metadata_file = self.temp_dir / f'metadata_{timestamp}.json'
                with open(metadata_file, 'w') as f:
                    json.dump(backup_info, f, indent=2)

                # Ajouter les métadonnées à l'archive
                tar.add(metadata_file, arcname='metadata.json')

                # Nettoyer le fichier temporaire
                metadata_file.unlink()

            except Exception as e:
                error_msg = f"Erreur création archive: {e}"
                return False, error_msg

            backup_size = backup_path.stat().st_size

            # Enregistrer dans les logs
            self._log_backup_success('files', str(backup_path), backup_size, backup_info)

            self.logger.info(f"Sauvegarde fichiers créée: {backup_path} ({backup_size} bytes)")
            return True, str(backup_path)

        except Exception as e:
            error_msg = f"Erreur sauvegarde fichiers: {e}"
            self.logger.error(error_msg)
            self._log_backup_failure('files', error_msg)
            return False, error_msg

    def create_snapshot(self, snapshot_name: str = None) -> Tuple[bool, str]:
        """Créer un snapshot du système de fichiers"""
        try:
            if not self.snapshot_config['create_snapshots']:
                return False, "Snapshots désactivés"

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            snapshot_name = snapshot_name or f"passprint_snapshot_{timestamp}"
            snapshot_path = self.snapshot_config['snapshot_dir'] / snapshot_name

            # Créer le snapshot (copie complète pour la simplicité)
            # En production, utiliser LVM, Btrfs, ou ZFS snapshots
            snapshot_path.mkdir(exist_ok=True)

            # Copier les dossiers critiques
            critical_dirs = ['uploads', 'static', 'logs']
            snapshot_info = {
                'snapshot_name': snapshot_name,
                'timestamp': timestamp,
                'type': 'filesystem_copy',
                'directories': critical_dirs,
                'size': 0
            }

            total_size = 0
            for dir_name in critical_dirs:
                src_path = Path(dir_name)
                dst_path = snapshot_path / dir_name

                if src_path.exists():
                    if dst_path.exists():
                        shutil.rmtree(dst_path)
                    shutil.copytree(src_path, dst_path)
                    dir_size = sum(f.stat().st_size for f in dst_path.rglob('*') if f.is_file())
                    total_size += dir_size

            snapshot_info['size'] = total_size

            # Sauvegarder les métadonnées du snapshot
            metadata_file = snapshot_path / 'snapshot_metadata.json'
            with open(metadata_file, 'w') as f:
                json.dump(snapshot_info, f, indent=2)

            self.logger.info(f"Snapshot créé: {snapshot_path} ({total_size} bytes)")
            return True, str(snapshot_path)

        except Exception as e:
            error_msg = f"Erreur création snapshot: {e}"
            self.logger.error(error_msg)
            return False, error_msg

    def create_full_backup(self) -> Tuple[bool, str]:
        """Créer une sauvegarde complète (base + fichiers + snapshot)"""
        try:
            self.logger.info("Démarrage sauvegarde complète...")

            backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_info = {
                'backup_type': 'full',
                'timestamp': backup_timestamp,
                'components': [],
                'status': 'in_progress'
            }

            results = []

            # 1. Sauvegarde base de données
            db_success, db_path = self.create_database_backup('full')
            if db_success:
                backup_info['components'].append('database')
                results.append(f"DB: {db_path}")
            else:
                self.logger.error("Échec sauvegarde base de données")

            # 2. Sauvegarde fichiers
            files_success, files_path = self.create_files_backup('full')
            if files_success:
                backup_info['components'].append('files')
                results.append(f"Files: {files_path}")
            else:
                self.logger.error("Échec sauvegarde fichiers")

            # 3. Créer snapshot
            snapshot_success, snapshot_path = self.create_snapshot(f"full_backup_{backup_timestamp}")
            if snapshot_success:
                backup_info['components'].append('snapshot')
                results.append(f"Snapshot: {snapshot_path}")
            else:
                self.logger.error("Échec création snapshot")

            # 4. Nettoyer anciennes sauvegardes
            cleanup_success = self.cleanup_old_backups()

            # Résultat final
            backup_info['status'] = 'completed' if (db_success and files_success) else 'partial'
            backup_info['results'] = results

            if db_success and files_success:
                self.logger.info("Sauvegarde complète réussie")
                self._log_backup_success('full', f"full_backup_{backup_timestamp}", 0, backup_info)
                return True, f"full_backup_{backup_timestamp}"
            else:
                self.logger.error("Échec sauvegarde complète")
                self._log_backup_failure('full', "Sauvegarde incomplète")
                return False, "Échec sauvegarde complète"

        except Exception as e:
            error_msg = f"Erreur sauvegarde complète: {e}"
            self.logger.error(error_msg)
            self._log_backup_failure('full', error_msg)
            return False, error_msg

    def _verify_database_integrity(self, db_path: str) -> bool:
        """Vérifier l'intégrité de la base de données"""
        try:
            if 'sqlite' in db_path:
                # Test de connexion SQLite
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                conn.close()

                return result and result[0] == 'ok'

            elif 'postgresql' in db_path:
                # Test de connexion PostgreSQL
                import psycopg2
                conn = psycopg2.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                conn.close()

                return result and result[0] == 1

            return True

        except Exception as e:
            self.logger.error(f"Erreur vérification intégrité DB: {e}")
            return False

    def _verify_backup_integrity(self, backup_path: Path) -> bool:
        """Vérifier l'intégrité d'une sauvegarde"""
        try:
            if backup_path.suffix == '.gz':
                # Vérifier le fichier gzip
                with gzip.open(backup_path, 'rb') as f:
                    # Lire seulement l'en-tête pour vérifier
                    header = f.read(1024)
                    return len(header) > 0
            else:
                # Vérifier le fichier normal
                return backup_path.exists() and backup_path.stat().st_size > 0

        except Exception as e:
            self.logger.error(f"Erreur vérification sauvegarde: {e}")
            return False

    def _add_backup_metadata(self, backup_path: Path, metadata: dict):
        """Ajouter des métadonnées à une sauvegarde"""
        try:
            metadata_file = backup_path.with_suffix('.metadata.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

        except Exception as e:
            self.logger.error(f"Erreur ajout métadonnées sauvegarde: {e}")

    def _log_backup_success(self, backup_type: str, file_path: str, file_size: int, metadata: dict):
        """Enregistrer une sauvegarde réussie"""
        try:
            if self.app:
                with self.app.app_context():
                    log_entry = BackupLog(
                        backup_type=backup_type,
                        file_path=file_path,
                        file_size=file_size,
                        status='success',
                        completed_at=datetime.utcnow()
                    )
                    db.session.add(log_entry)
                    db.session.commit()

                    # Envoyer une notification de succès
                    self._send_backup_notification('success', backup_type, file_path, file_size)

        except Exception as e:
            self.logger.error(f"Erreur enregistrement log sauvegarde: {e}")

    def _log_backup_failure(self, backup_type: str, error_message: str):
        """Enregistrer un échec de sauvegarde"""
        try:
            if self.app:
                with self.app.app_context():
                    log_entry = BackupLog(
                        backup_type=backup_type,
                        status='failed',
                        error_message=error_message,
                        completed_at=datetime.utcnow()
                    )
                    db.session.add(log_entry)
                    db.session.commit()

                    # Envoyer une notification d'échec
                    self._send_backup_notification('failure', backup_type, None, 0, error_message)

        except Exception as e:
            self.logger.error(f"Erreur enregistrement log échec sauvegarde: {e}")

    def _send_backup_notification(self, status: str, backup_type: str, file_path: str = None,
                                file_size: int = 0, error_message: str = None):
        """Envoyer une notification de sauvegarde"""
        try:
            monitoring = get_monitoring_integration()
            if monitoring:
                event_type = 'backup_success' if status == 'success' else 'backup_failure'

                details = f"Sauvegarde {backup_type} {status}"
                if file_path:
                    details += f": {file_path} ({file_size} bytes)"
                if error_message:
                    details += f" - Erreur: {error_message}"

                monitoring.record_security_event(event_type, 'medium')

        except Exception as e:
            self.logger.error(f"Erreur envoi notification sauvegarde: {e}")

    def cleanup_old_backups(self) -> bool:
        """Nettoyer les anciennes sauvegardes avec politique de rétention"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)

            # Nettoyer les sauvegardes
            deleted_count = 0
            for backup_file in self.backup_dir.glob('passprint_*'):
                if backup_file.is_file():
                    file_modified = datetime.fromtimestamp(backup_file.stat().st_mtime)

                    if file_modified < cutoff_date:
                        backup_file.unlink()
                        deleted_count += 1
                        self.logger.info(f"Ancienne sauvegarde supprimée: {backup_file}")

            # Politique de rétention intelligente: garder plus de sauvegardes récentes
            backup_files = []
            for backup_file in self.backup_dir.glob('passprint_*'):
                if backup_file.is_file():
                    backup_files.append(backup_file)

            # Trier par date de modification
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # Supprimer les sauvegardes excédentaires
            for old_backup in backup_files[self.max_backups:]:
                old_backup.unlink()
                deleted_count += 1
                self.logger.info(f"Sauvegarde ancienne supprimée (limite atteinte): {old_backup}")

            # Nettoyer aussi les snapshots anciens
            self._cleanup_old_snapshots()

            self.logger.info(f"Nettoyage terminé: {deleted_count} sauvegardes supprimées")
            return True

        except Exception as e:
            self.logger.error(f"Erreur nettoyage sauvegardes: {e}")
            return False

    def _cleanup_old_snapshots(self):
        """Nettoyer les anciens snapshots"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.snapshot_config['snapshot_retention'])

            for snapshot_dir in self.snapshot_config['snapshot_dir'].iterdir():
                if snapshot_dir.is_dir():
                    # Vérifier la date du snapshot depuis les métadonnées
                    metadata_file = snapshot_dir / 'snapshot_metadata.json'
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, 'r') as f:
                                metadata = json.load(f)

                            snapshot_date = datetime.fromisoformat(metadata['timestamp'])

                            if snapshot_date < cutoff_date:
                                shutil.rmtree(snapshot_dir)
                                self.logger.info(f"Ancien snapshot supprimé: {snapshot_dir}")

                        except Exception as e:
                            self.logger.warning(f"Erreur lecture métadonnées snapshot {snapshot_dir}: {e}")

        except Exception as e:
            self.logger.error(f"Erreur nettoyage snapshots: {e}")

    def get_backup_status(self) -> List[Dict]:
        """Obtenir le statut détaillé des sauvegardes"""
        try:
            if not self.app:
                return []

            with self.app.app_context():
                logs = BackupLog.query.order_by(BackupLog.created_at.desc()).limit(50).all()
                return [log.to_dict() for log in logs]

        except Exception as e:
            self.logger.error(f"Erreur récupération statut sauvegardes: {e}")
            return []

    def restore_database(self, backup_path: str, target_db_url: str = None) -> Tuple[bool, str]:
        """Restaurer une sauvegarde de base de données"""
        try:
            backup_path = Path(backup_path)

            if not backup_path.exists():
                error_msg = f"Fichier de sauvegarde non trouvé: {backup_path}"
                return False, error_msg

            # Déterminer le type de sauvegarde depuis le nom du fichier
            if 'sqlite' in backup_path.name:
                return self._restore_sqlite(backup_path, target_db_url)
            elif 'postgres' in backup_path.name:
                return self._restore_postgresql(backup_path, target_db_url)
            else:
                error_msg = f"Type de sauvegarde non reconnu: {backup_path.name}"
                return False, error_msg

        except Exception as e:
            error_msg = f"Erreur restauration base de données: {e}"
            self.logger.error(error_msg)
            return False, error_msg

    def _restore_sqlite(self, backup_path: Path, target_db_url: str = None) -> Tuple[bool, str]:
        """Restaurer une sauvegarde SQLite"""
        try:
            config = get_config()
            db_url = target_db_url or config.SQLALCHEMY_DATABASE_URI
            db_path = db_url.replace('sqlite:///', '')

            # Créer une sauvegarde de la base actuelle avant restauration
            if os.path.exists(db_path):
                emergency_backup = self.backup_dir / f"emergency_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2(db_path, emergency_backup)
                self.logger.info(f"Sauvegarde d'urgence créée: {emergency_backup}")

            # Décompresser et restaurer
            if backup_path.suffix == '.gz':
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(db_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                shutil.copy2(backup_path, db_path)

            # Vérifier la restauration
            if self._verify_database_integrity(db_path):
                self.logger.info(f"Base de données restaurée: {db_path}")
                return True, db_path
            else:
                error_msg = "Échec de vérification après restauration"
                return False, error_msg

        except Exception as e:
            error_msg = f"Erreur restauration SQLite: {e}"
            return False, error_msg

    def _restore_postgresql(self, backup_path: Path, target_db_url: str = None) -> Tuple[bool, str]:
        """Restaurer une sauvegarde PostgreSQL"""
        try:
            config = get_config()
            db_url = target_db_url or config.SQLALCHEMY_DATABASE_URI

            # Parser l'URL PostgreSQL
            import re
            pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
            match = re.match(pattern, db_url)

            if not match:
                error_msg = "Format d'URL PostgreSQL cible invalide"
                return False, error_msg

            user, password, host, port, database = match.groups()

            # Préparation de la restauration
            env = os.environ.copy()
            env['PGPASSWORD'] = password

            try:
                if backup_path.suffix == '.gz':
                    # Pipeline: gunzip -> psql
                    gunzip = subprocess.Popen(['gunzip', '-c', str(backup_path)],
                                            stdout=subprocess.PIPE)
                    psql = subprocess.Popen([
                        'psql',
                        f'--host={host}',
                        f'--port={port}',
                        f'--username={user}',
                        f'--dbname={database}',
                        '--no-password',
                        '--quiet'
                    ], env=env, stdin=gunzip.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                    gunzip.stdout.close()
                    stdout, stderr = psql.communicate()

                    if psql.returncode == 0:
                        self.logger.info(f"Base PostgreSQL restaurée: {database}")
                        return True, database
                    else:
                        error_msg = f"Erreur psql: {stderr.decode()}"
                        return False, error_msg

                else:
                    # Restauration directe
                    result = subprocess.run([
                        'psql',
                        f'--host={host}',
                        f'--port={port}',
                        f'--username={user}',
                        f'--dbname={database}',
                        '--no-password',
                        f'--file={backup_path}'
                    ], env=env, capture_output=True, text=True, timeout=3600)

                    if result.returncode == 0:
                        self.logger.info(f"Base PostgreSQL restaurée: {database}")
                        return True, database
                    else:
                        error_msg = f"Erreur psql: {result.stderr}"
                        return False, error_msg

            except subprocess.TimeoutExpired:
                error_msg = "Timeout lors de la restauration PostgreSQL"
                return False, error_msg

        except Exception as e:
            error_msg = f"Erreur restauration PostgreSQL: {e}"
            return False, error_msg

    def restore_files(self, backup_path: str, target_dirs: Dict[str, str] = None) -> Tuple[bool, str]:
        """Restaurer une sauvegarde de fichiers"""
        try:
            backup_path = Path(backup_path)

            if not backup_path.exists():
                error_msg = f"Fichier de sauvegarde non trouvé: {backup_path}"
                return False, error_msg

            # Créer des sauvegardes des fichiers actuels
            if target_dirs:
                for dir_name in target_dirs.keys():
                    dir_path = Path(dir_name)
                    if dir_path.exists():
                        emergency_backup = self.backup_dir / f"emergency_files_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        shutil.copytree(dir_path, emergency_backup / dir_name)
                        self.logger.info(f"Sauvegarde d'urgence fichiers créée: {emergency_backup}")

            # Extraire l'archive
            with tarfile.open(backup_path, 'r:gz') as tar:
                # Extraire dans un dossier temporaire d'abord
                temp_restore_dir = self.temp_dir / f'restore_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
                temp_restore_dir.mkdir()

                tar.extractall(temp_restore_dir)

                # Restaurer les fichiers
                for extracted_item in temp_restore_dir.rglob('*'):
                    if extracted_item.is_file():
                        relative_path = extracted_item.relative_to(temp_restore_dir)

                        # Déterminer le dossier cible
                        if target_dirs:
                            target_dir = target_dirs.get(str(relative_path.parts[0]), str(relative_path.parts[0]))
                        else:
                            target_dir = str(relative_path.parts[0])

                        target_path = Path(target_dir) / Path(*relative_path.parts[1:])

                        # Créer le dossier cible si nécessaire
                        target_path.parent.mkdir(parents=True, exist_ok=True)

                        # Restaurer le fichier
                        shutil.copy2(extracted_item, target_path)

                # Nettoyer le dossier temporaire
                shutil.rmtree(temp_restore_dir)

            self.logger.info(f"Fichiers restaurés depuis: {backup_path}")
            return True, str(backup_path)

        except Exception as e:
            error_msg = f"Erreur restauration fichiers: {e}"
            self.logger.error(error_msg)
            return False, error_msg

    def create_disaster_recovery_plan(self) -> Dict:
        """Créer un plan de récupération après désastre"""
        try:
            plan = {
                'created_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'steps': [
                    {
                        'order': 1,
                        'type': 'assessment',
                        'title': 'Évaluation de la situation',
                        'description': 'Évaluer l\'étendue du désastre et identifier les systèmes affectés',
                        'estimated_time': '15 minutes'
                    },
                    {
                        'order': 2,
                        'type': 'communication',
                        'title': 'Communication d\'urgence',
                        'description': 'Notifier les équipes concernées et les utilisateurs',
                        'estimated_time': '10 minutes'
                    },
                    {
                        'order': 3,
                        'type': 'infrastructure',
                        'title': 'Vérification de l\'infrastructure',
                        'description': 'Vérifier que les serveurs, réseau, et stockage sont opérationnels',
                        'estimated_time': '30 minutes'
                    },
                    {
                        'order': 4,
                        'type': 'database',
                        'title': 'Restauration de la base de données',
                        'description': 'Restaurer la dernière sauvegarde valide de la base de données',
                        'estimated_time': '45 minutes',
                        'script': 'restore_latest_database.sh'
                    },
                    {
                        'order': 5,
                        'type': 'files',
                        'title': 'Restauration des fichiers',
                        'description': 'Restaurer les fichiers utilisateurs et assets statiques',
                        'estimated_time': '30 minutes',
                        'script': 'restore_files.sh'
                    },
                    {
                        'order': 6,
                        'type': 'application',
                        'title': 'Redéploiement de l\'application',
                        'description': 'Redémarrer l\'application et vérifier le bon fonctionnement',
                        'estimated_time': '20 minutes',
                        'script': 'restart_application.sh'
                    },
                    {
                        'order': 7,
                        'type': 'verification',
                        'title': 'Vérification post-restauration',
                        'description': 'Vérifier que tous les systèmes fonctionnent correctement',
                        'estimated_time': '30 minutes'
                    },
                    {
                        'order': 8,
                        'type': 'communication',
                        'title': 'Communication de résolution',
                        'description': 'Informer les utilisateurs que le système est restauré',
                        'estimated_time': '10 minutes'
                    }
                ],
                'estimated_total_time': '3 heures 10 minutes',
                'contact_information': {
                    'technical_team': os.getenv('TECH_TEAM_CONTACT', 'tech@passprint.com'),
                    'backup_locations': [
                        'Local: /backups/',
                        'Cloud: S3 bucket passprint-backups'
                    ]
                },
                'latest_backup_info': self._get_latest_backup_info()
            }

            # Sauvegarder le plan
            plan_file = self.backup_dir / f'disaster_recovery_plan_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(plan_file, 'w') as f:
                json.dump(plan, f, indent=2)

            return plan

        except Exception as e:
            self.logger.error(f"Erreur création plan récupération: {e}")
            return {'error': str(e)}

    def _get_latest_backup_info(self) -> Dict:
        """Obtenir les informations de la dernière sauvegarde"""
        try:
            backup_files = list(self.backup_dir.glob('passprint_*'))
            if not backup_files:
                return {'available': False}

            latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)

            return {
                'available': True,
                'path': str(latest_backup),
                'size': latest_backup.stat().st_size,
                'modified': datetime.fromtimestamp(latest_backup.stat().st_mtime).isoformat(),
                'type': 'database' if 'postgres' in latest_backup.name or 'sqlite' in latest_backup.name else 'files'
            }

        except Exception as e:
            return {'available': False, 'error': str(e)}

    def test_backup_integrity(self, backup_path: str) -> Tuple[bool, str]:
        """Tester l'intégrité d'une sauvegarde"""
        try:
            backup_path = Path(backup_path)

            if not backup_path.exists():
                return False, "Fichier de sauvegarde non trouvé"

            # Test selon le type de sauvegarde
            if 'sqlite' in backup_path.name:
                # Test de décompression et vérification
                with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
                    try:
                        with gzip.open(backup_path, 'rb') as f_in:
                            shutil.copyfileobj(f_in, temp_file)
                        temp_file.close()

                        # Vérifier l'intégrité SQLite
                        return self._verify_database_integrity(temp_file.name), "Test SQLite réussi"

                    finally:
                        os.unlink(temp_file.name)

            elif 'postgres' in backup_path.name:
                # Test de base pour PostgreSQL (lecture de l'en-tête)
                try:
                    if backup_path.suffix == '.gz':
                        with gzip.open(backup_path, 'rb') as f:
                            header = f.read(1024)
                    else:
                        with open(backup_path, 'rb') as f:
                            header = f.read(1024)

                    # Vérifier que c'est un dump PostgreSQL valide
                    if b'PostgreSQL' in header or b'pg_dump' in header:
                        return True, "En-tête PostgreSQL valide"
                    else:
                        return False, "En-tête PostgreSQL invalide"

                except Exception as e:
                    return False, f"Erreur lecture sauvegarde PostgreSQL: {e}"

            else:
                return True, "Test de base réussi"

        except Exception as e:
            return False, f"Erreur test intégrité: {e}"

# Instance globale du système de sauvegarde
backup_system = BackupSystem()

def create_full_backup():
    """Fonction utilitaire pour créer une sauvegarde complète"""
    success, result = backup_system.create_full_backup()
    return success

def get_backup_status():
    """Fonction utilitaire pour obtenir le statut des sauvegardes"""
    return backup_system.get_backup_status()

def restore_database(backup_path: str, target_db_url: str = None):
    """Fonction utilitaire pour restaurer la base de données"""
    success, result = backup_system.restore_database(backup_path, target_db_url)
    return success

def create_disaster_recovery_plan():
    """Fonction utilitaire pour créer un plan de récupération"""
    return backup_system.create_disaster_recovery_plan()

if __name__ == "__main__":
    print("🛡️  Système de sauvegarde et récupération PassPrint")

    # Test du système
    success, result = create_full_backup()
    if success:
        print(f"✅ Sauvegarde créée avec succès: {result}")
    else:
        print(f"❌ Échec de la sauvegarde: {result}")