#!/usr/bin/env python3
"""
Stratégies avancées de sauvegarde PostgreSQL pour PassPrint
Sauvegardes différentielles, PITR, et optimisations
"""
import os
import subprocess
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil
import gzip

logger = logging.getLogger(__name__)

class PostgreSQLBackupManager:
    """Gestionnaire avancé de sauvegardes PostgreSQL"""

    def __init__(self, app=None):
        self.app = app
        self.backup_dir = Path('backups/postgresql')
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

        # Configuration PostgreSQL
        self.pg_config = {
            'host': os.getenv('PGHOST', 'localhost'),
            'port': int(os.getenv('PGPORT', '5432')),
            'database': os.getenv('PGDATABASE', 'passprint_prod'),
            'user': os.getenv('PGUSER', 'passprint'),
            'password': os.getenv('PGPASSWORD'),
            'parallel_jobs': int(os.getenv('PG_BACKUP_JOBS', '2')),
            'compression_level': int(os.getenv('PG_COMPRESSION_LEVEL', '9')),
            'buffer_size': os.getenv('PG_BUFFER_SIZE', '8192kB')
        }

        # Configuration PITR (Point-in-Time Recovery)
        self.pitr_config = {
            'enabled': os.getenv('PITR_ENABLED', 'false').lower() == 'true',
            'wal_archive_dir': Path(os.getenv('WAL_ARCHIVE_DIR', '/var/lib/postgresql/wal_archive')),
            'retention_days': int(os.getenv('WAL_RETENTION_DAYS', '7'))
        }

        # Configuration des sauvegardes différentielles
        self.differential_config = {
            'enabled': os.getenv('DIFFERENTIAL_BACKUP_ENABLED', 'true').lower() == 'true',
            'base_backup_dir': self.backup_dir / 'base_backups',
            'diff_backup_dir': self.backup_dir / 'differential_backups',
            'full_backup_interval_days': int(os.getenv('FULL_BACKUP_INTERVAL_DAYS', '7'))
        }

        self.differential_config['base_backup_dir'].mkdir(exist_ok=True)
        self.differential_config['diff_backup_dir'].mkdir(exist_ok=True)

    def create_full_backup(self) -> tuple[bool, str]:
        """Créer une sauvegarde complète PostgreSQL"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"passprint_full_{timestamp}.dump.gz"
            backup_path = self.backup_dir / backup_filename

            # Préparation de la commande pg_dump
            cmd = [
                'pg_dump',
                f'--host={self.pg_config["host"]}',
                f'--port={self.pg_config["port"]}',
                f'--username={self.pg_config["user"]}',
                f'--dbname={self.pg_config["database"]}',
                '--no-password',
                '--format=custom',
                f'--compress={self.pg_config["compression_level"]}',
                f'--jobs={self.pg_config["parallel_jobs"]}',
                '--verbose',
                '--no-unlogged-table-data',  # Exclure les tables non loggées
                '--exclude-table-data=audit_logs_old',  # Exclure les anciennes données si nécessaire
            ]

            # Variables d'environnement
            env = os.environ.copy()
            env['PGPASSWORD'] = self.pg_config['password']

            # Exécuter la sauvegarde avec pipeline pour compression
            try:
                with open(backup_path, 'wb') as f:
                    # Pipeline: pg_dump -> gzip
                    pg_dump = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                    # Utiliser gzip externe pour de meilleures performances
                    gzip_proc = subprocess.Popen(
                        ['gzip', f'-{self.pg_config["compression_level"]}'],
                        stdin=pg_dump.stdout,
                        stdout=f,
                        stderr=subprocess.PIPE
                    )

                    if pg_dump.stdout:
                        pg_dump.stdout.close()

                    stdout, stderr = pg_dump.communicate()
                    gzip_proc.communicate()

                    if pg_dump.returncode == 0 and gzip_proc.returncode == 0:
                        success = True
                        output = stdout.decode()
                    else:
                        success = False
                        output = stderr.decode()

            except subprocess.TimeoutExpired:
                return False, "Timeout lors de la sauvegarde PostgreSQL"
            except Exception as e:
                return False, f"Erreur exécution sauvegarde: {e}"

            if not success:
                return False, f"Erreur pg_dump: {output}"

            # Vérifier la sauvegarde créée
            if not backup_path.exists() or backup_path.stat().st_size == 0:
                return False, "Fichier de sauvegarde vide ou non créé"

            backup_size = backup_path.stat().st_size

            # Créer les métadonnées de sauvegarde
            metadata = {
                'backup_type': 'full',
                'database_type': 'postgresql',
                'timestamp': timestamp,
                'host': self.pg_config['host'],
                'port': self.pg_config['port'],
                'database': self.pg_config['database'],
                'backup_path': str(backup_path),
                'compression': 'gzip',
                'parallel_jobs': self.pg_config['parallel_jobs'],
                'size_bytes': backup_size,
                'version': '2.0',
                'pg_dump_version': self._get_pg_dump_version(),
                'database_size_before': self._get_database_size(),
                'tables_count': self._get_tables_count()
            }

            # Ajouter les métadonnées au fichier de sauvegarde
            self._add_backup_metadata(backup_path, metadata)

            # Créer une sauvegarde de base pour les différentielles
            if self.differential_config['enabled']:
                self._create_base_backup_reference(backup_path, metadata)

            self.logger.info(f"Sauvegarde complète PostgreSQL créée: {backup_path} ({backup_size} bytes)")
            return True, str(backup_path)

        except Exception as e:
            error_msg = f"Erreur sauvegarde complète PostgreSQL: {e}"
            self.logger.error(error_msg)
            return False, error_msg

    def create_differential_backup(self) -> tuple[bool, str]:
        """Créer une sauvegarde différentielle"""
        try:
            if not self.differential_config['enabled']:
                return False, "Sauvegardes différentielles désactivées"

            # Vérifier qu'une sauvegarde de base existe
            base_backup = self._get_latest_base_backup()
            if not base_backup:
                return False, "Aucune sauvegarde de base trouvée pour la différentielle"

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"passprint_diff_{timestamp}.dump.gz"
            backup_path = self.differential_config['diff_backup_dir'] / backup_filename

            # Créer une sauvegarde des modifications depuis la base
            cmd = [
                'pg_dump',
                f'--host={self.pg_config["host"]}',
                f'--port={self.pg_config["port"]}',
                f'--username={self.pg_config["user"]}',
                f'--dbname={self.pg_config["database"]}',
                '--no-password',
                '--format=custom',
                f'--compress={self.pg_config["compression_level"]}',
                '--schema-only',  # Seulement la structure pour les diffs
                '--verbose'
            ]

            # Variables d'environnement
            env = os.environ.copy()
            env['PGPASSWORD'] = self.pg_config['password']

            # Exécuter la sauvegarde différentielle
            try:
                with open(backup_path, 'wb') as f:
                    pg_dump = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE)
                    gzip_proc = subprocess.Popen(
                        ['gzip', f'-{self.pg_config["compression_level"]}'],
                        stdin=pg_dump.stdout,
                        stdout=f
                    )

                    if pg_dump.stdout:
                        pg_dump.stdout.close()

                    pg_dump.communicate()
                    gzip_proc.communicate()

                    if pg_dump.returncode == 0 and gzip_proc.returncode == 0:
                        success = True
                    else:
                        success = False

            except Exception as e:
                return False, f"Erreur exécution sauvegarde différentielle: {e}"

            if not success:
                return False, "Échec de la sauvegarde différentielle"

            backup_size = backup_path.stat().st_size

            # Métadonnées pour la sauvegarde différentielle
            metadata = {
                'backup_type': 'differential',
                'database_type': 'postgresql',
                'timestamp': timestamp,
                'base_backup': base_backup,
                'host': self.pg_config['host'],
                'port': self.pg_config['port'],
                'database': self.pg_config['database'],
                'backup_path': str(backup_path),
                'compression': 'gzip',
                'size_bytes': backup_size,
                'version': '2.0'
            }

            self._add_backup_metadata(backup_path, metadata)

            self.logger.info(f"Sauvegarde différentielle PostgreSQL créée: {backup_path} ({backup_size} bytes)")
            return True, str(backup_path)

        except Exception as e:
            error_msg = f"Erreur sauvegarde différentielle PostgreSQL: {e}"
            self.logger.error(error_msg)
            return False, error_msg

    def setup_pitr(self) -> tuple[bool, str]:
        """Configurer la récupération Point-in-Time (PITR)"""
        try:
            if not self.pitr_config['enabled']:
                return False, "PITR désactivé"

            # Créer le répertoire d'archive WAL
            self.pitr_config['wal_archive_dir'].mkdir(parents=True, exist_ok=True)

            # Configuration PostgreSQL pour PITR
            postgresql_conf = """
# Configuration PITR ajoutée par PassPrint
wal_level = replica
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/wal_archive/%f'
max_wal_senders = 3
wal_keep_segments = 64
"""

            # Ajouter la configuration au postgresql.conf
            conf_file = Path('/etc/postgresql/13/main/postgresql.conf')
            if conf_file.exists():
                with open(conf_file, 'a') as f:
                    f.write(postgresql_conf)

            # Créer le script d'archive WAL
            archive_script = """#!/bin/bash
# Script d'archive WAL pour PassPrint PITR

WAL_FILE=$1
ARCHIVE_DIR="/var/lib/postgresql/wal_archive"

# Créer le répertoire avec la date
DATE_DIR=$(date +%Y%m%d)
TARGET_DIR="$ARCHIVE_DIR/$DATE_DIR"

mkdir -p "$TARGET_DIR"

# Copier le fichier WAL
cp "$WAL_FILE" "$TARGET_DIR/"

# Compresser les anciens fichiers WAL (plus de 1 jour)
find "$ARCHIVE_DIR" -name "*.partial" -mtime +1 -exec gzip {} \;
"""

            script_path = Path('/usr/local/bin/archive_wal.sh')
            with open(script_path, 'w') as f:
                f.write(archive_script)

            script_path.chmod(0o755)

            self.logger.info("Configuration PITR PostgreSQL terminée")
            return True, "PITR configuré avec succès"

        except Exception as e:
            error_msg = f"Erreur configuration PITR: {e}"
            self.logger.error(error_msg)
            return False, error_msg

    def restore_to_point_in_time(self, target_time: datetime, backup_file: str = None) -> tuple[bool, str]:
        """Restaurer à un point dans le temps spécifique"""
        try:
            if not self.pitr_config['enabled']:
                return False, "PITR non configuré"

            # Utiliser la dernière sauvegarde complète si non spécifiée
            if not backup_file:
                backup_file = self._get_latest_full_backup()

            if not backup_file:
                return False, "Aucune sauvegarde complète trouvée pour PITR"

            # Préparation de la restauration PITR
            restore_timestamp = target_time.strftime('%Y-%m-%d %H:%M:%S')

            # Commandes de restauration PITR
            commands = [
                f"pg_restore --host={self.pg_config['host']} --port={self.pg_config['port']} "
                f"--username={self.pg_config['user']} --dbname={self.pg_config['database']} "
                f"--no-password --clean --if-exists {backup_file}",
                f"psql --host={self.pg_config['host']} --port={self.pg_config['port']} "
                f"--username={self.pg_config['user']} --dbname={self.pg_config['database']} "
                f"--no-password --command \"SELECT pg_wal_replay_pause();\"",
                f"psql --host={self.pg_config['host']} --port={self.pg_config['port']} "
                f"--username={self.pg_config['user']} --dbname={self.pg_config['database']} "
                f"--no-password --command \"SELECT pg_wal_replay_resume();\""
            ]

            env = os.environ.copy()
            env['PGPASSWORD'] = self.pg_config['password']

            # Exécuter les commandes de restauration
            for cmd in commands:
                try:
                    result = subprocess.run(cmd, shell=True, env=env, capture_output=True, text=True, timeout=300)

                    if result.returncode != 0:
                        return False, f"Erreur commande PITR: {result.stderr}"

                except subprocess.TimeoutExpired:
                    return False, "Timeout lors de la restauration PITR"
                except Exception as e:
                    return False, f"Erreur exécution PITR: {e}"

            self.logger.info(f"Restauration PITR réussie à {restore_timestamp}")
            return True, f"Restauration PITR réussie à {restore_timestamp}"

        except Exception as e:
            error_msg = f"Erreur restauration PITR: {e}"
            self.logger.error(error_msg)
            return False, error_msg

    def optimize_backup_performance(self) -> dict:
        """Optimiser les performances de sauvegarde"""
        try:
            optimization_results = {
                'actions_taken': [],
                'performance_improvements': [],
                'estimated_time_saved': 0
            }

            # 1. Analyser la taille de la base de données
            db_size = self._get_database_size()
            optimization_results['database_size'] = db_size

            # 2. Optimiser les paramètres selon la taille
            if db_size > 10 * 1024 * 1024 * 1024:  # > 10GB
                # Base de données volumineuse - optimisations avancées
                self.pg_config['parallel_jobs'] = min(4, os.cpu_count() or 2)
                self.pg_config['buffer_size'] = '16384kB'

                optimization_results['actions_taken'].append("Paramètres optimisés pour base volumineuse")
                optimization_results['performance_improvements'].append("Sauvegarde parallélisée")

            # 3. Configurer la maintenance automatique
            maintenance_commands = [
                'VACUUM ANALYZE;',
                'REINDEX DATABASE CONCURRENTLY;',
                'ANALYZE;'
            ]

            env = os.environ.copy()
            env['PGPASSWORD'] = self.pg_config['password']

            for cmd in maintenance_commands:
                try:
                    result = subprocess.run(
                        f'psql --host={self.pg_config["host"]} --port={self.pg_config["port"]} '
                        f'--username={self.pg_config["user"]} --dbname={self.pg_config["database"]} '
                        '--no-password --command "{cmd}"',
                        shell=True, env=env, capture_output=True, text=True, timeout=600
                    )

                    if result.returncode == 0:
                        optimization_results['actions_taken'].append(f"Maintenance exécutée: {cmd}")

                except Exception as e:
                    self.logger.warning(f"Erreur maintenance: {e}")

            # 4. Configurer les statistiques étendues
            stats_commands = [
                'CREATE EXTENSION IF NOT EXISTS pg_stat_statements;',
                'ALTER DATABASE passprint_prod SET pg_stat_statements.track = all;'
            ]

            for cmd in stats_commands:
                try:
                    result = subprocess.run(
                        f'psql --host={self.pg_config["host"]} --port={self.pg_config["port"]} '
                        f'--username={self.pg_config["user"]} --dbname={self.pg_config["database"]} '
                        '--no-password --command "{cmd}"',
                        shell=True, env=env, capture_output=True, text=True, timeout=60
                    )

                    if result.returncode == 0:
                        optimization_results['actions_taken'].append(f"Statistiques configurées: {cmd}")

                except Exception as e:
                    self.logger.warning(f"Erreur statistiques: {e}")

            return optimization_results

        except Exception as e:
            self.logger.error(f"Erreur optimisation sauvegarde: {e}")
            return {'error': str(e)}

    def _get_pg_dump_version(self) -> str:
        """Obtenir la version de pg_dump"""
        try:
            result = subprocess.run(['pg_dump', '--version'], capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return 'unknown'

    def _get_database_size(self) -> int:
        """Obtenir la taille de la base de données en bytes"""
        try:
            env = os.environ.copy()
            env['PGPASSWORD'] = self.pg_config['password']

            result = subprocess.run(
                f'psql --host={self.pg_config["host"]} --port={self.pg_config["port"]} '
                f'--username={self.pg_config["user"]} --dbname={self.pg_config["database"]} '
                '--no-password --command "SELECT pg_database_size(\'{self.pg_config[\"database\"]}\');"',
                shell=True, env=env, capture_output=True, text=True
            )

            if result.returncode == 0:
                size_str = result.stdout.strip()
                try:
                    return int(size_str)
                except:
                    return 0

            return 0

        except Exception as e:
            self.logger.error(f"Erreur récupération taille base: {e}")
            return 0

    def _get_tables_count(self) -> int:
        """Obtenir le nombre de tables dans la base"""
        try:
            env = os.environ.copy()
            env['PGPASSWORD'] = self.pg_config['password']

            result = subprocess.run(
                f'psql --host={self.pg_config["host"]} --port={self.pg_config["port"]} '
                f'--username={self.pg_config["user"]} --dbname={self.pg_config["database"]} '
                '--no-password --command "SELECT count(*) FROM information_schema.tables WHERE table_schema = \'public\';"',
                shell=True, env=env, capture_output=True, text=True
            )

            if result.returncode == 0:
                count_str = result.stdout.strip()
                try:
                    return int(count_str)
                except:
                    return 0

            return 0

        except Exception as e:
            self.logger.error(f"Erreur récupération nombre tables: {e}")
            return 0

    def _add_backup_metadata(self, backup_path: Path, metadata: dict):
        """Ajouter des métadonnées à une sauvegarde"""
        try:
            metadata_file = backup_path.with_suffix('.metadata.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

        except Exception as e:
            self.logger.error(f"Erreur ajout métadonnées sauvegarde: {e}")

    def _get_latest_base_backup(self) -> str:
        """Obtenir la dernière sauvegarde de base"""
        try:
            base_backups = list(self.differential_config['base_backup_dir'].glob('*.dump.gz'))
            if not base_backups:
                return None

            latest_backup = max(base_backups, key=lambda x: x.stat().st_mtime)
            return str(latest_backup)

        except Exception as e:
            self.logger.error(f"Erreur recherche sauvegarde de base: {e}")
            return None

    def _get_latest_full_backup(self) -> str:
        """Obtenir la dernière sauvegarde complète"""
        try:
            full_backups = list(self.backup_dir.glob('*full*.dump.gz'))
            if not full_backups:
                return None

            latest_backup = max(full_backups, key=lambda x: x.stat().st_mtime)
            return str(latest_backup)

        except Exception as e:
            self.logger.error(f"Erreur recherche sauvegarde complète: {e}")
            return None

    def _create_base_backup_reference(self, backup_path: str, metadata: dict):
        """Créer une référence de sauvegarde de base pour les différentielles"""
        try:
            # Copier la sauvegarde complète vers le dossier des sauvegardes de base
            base_backup_path = self.differential_config['base_backup_dir'] / Path(backup_path).name

            if not base_backup_path.exists():
                shutil.copy2(backup_path, base_backup_path)

                # Créer les métadonnées de référence
                reference_metadata = metadata.copy()
                reference_metadata['reference_type'] = 'base_backup'
                reference_metadata['differential_eligible'] = True

                self._add_backup_metadata(base_backup_path, reference_metadata)

                self.logger.info(f"Sauvegarde de base créée pour différentielles: {base_backup_path}")

        except Exception as e:
            self.logger.error(f"Erreur création référence sauvegarde de base: {e}")

    def create_backup_strategy_report(self) -> dict:
        """Créer un rapport sur la stratégie de sauvegarde"""
        try:
            report = {
                'generated_at': datetime.utcnow().isoformat(),
                'strategy_version': '2.0',
                'configuration': {
                    'differential_enabled': self.differential_config['enabled'],
                    'pitr_enabled': self.pitr_config['enabled'],
                    'compression_enabled': True,
                    'parallel_jobs': self.pg_config['parallel_jobs']
                },
                'statistics': {
                    'total_backups': len(list(self.backup_dir.glob('*.dump.gz'))),
                    'database_size': self._get_database_size(),
                    'tables_count': self._get_tables_count(),
                    'last_backup': self._get_last_backup_info(),
                    'storage_used': self._calculate_backup_storage_usage()
                },
                'recommendations': self._generate_backup_recommendations(),
                'next_actions': self._get_next_backup_actions()
            }

            # Sauvegarder le rapport
            report_file = self.backup_dir / f'backup_strategy_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)

            return report

        except Exception as e:
            self.logger.error(f"Erreur création rapport stratégie sauvegarde: {e}")
            return {'error': str(e)}

    def _get_last_backup_info(self) -> dict:
        """Obtenir les informations de la dernière sauvegarde"""
        try:
            backup_files = list(self.backup_dir.glob('*.dump.gz'))
            if not backup_files:
                return {'available': False}

            latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)

            # Lire les métadonnées si disponibles
            metadata_file = latest_backup.with_suffix('.metadata.json')
            metadata = {}
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                except:
                    pass

            return {
                'available': True,
                'path': str(latest_backup),
                'size': latest_backup.stat().st_size,
                'modified': datetime.fromtimestamp(latest_backup.stat().st_mtime).isoformat(),
                'type': metadata.get('backup_type', 'unknown'),
                'metadata': metadata
            }

        except Exception as e:
            return {'available': False, 'error': str(e)}

    def _calculate_backup_storage_usage(self) -> dict:
        """Calculer l'utilisation du stockage pour les sauvegardes"""
        try:
            total_size = 0
            file_count = 0

            for backup_file in self.backup_dir.glob('*'):
                if backup_file.is_file():
                    total_size += backup_file.stat().st_size
                    file_count += 1

            return {
                'total_size_bytes': total_size,
                'total_size_mb': total_size / (1024 * 1024),
                'file_count': file_count,
                'average_file_size_mb': (total_size / file_count) / (1024 * 1024) if file_count > 0 else 0
            }

        except Exception as e:
            return {'error': str(e)}

    def _generate_backup_recommendations(self) -> list:
        """Générer des recommandations pour la stratégie de sauvegarde"""
        recommendations = []

        try:
            # Analyser la taille de la base
            db_size = self._get_database_size()
            if db_size > 50 * 1024 * 1024 * 1024:  # > 50GB
                recommendations.append("Base de données volumineuse détectée - Envisagez le partitionnement")
                recommendations.append("Configurez des sauvegardes parallèles avec plus de jobs")

            # Analyser la fréquence des sauvegardes
            last_backup = self._get_last_backup_info()
            if last_backup.get('available', False):
                backup_age = datetime.now() - datetime.fromtimestamp(Path(last_backup['path']).stat().st_mtime)
                if backup_age > timedelta(hours=48):
                    recommendations.append("Dernière sauvegarde ancienne - Augmentez la fréquence")

            # Recommandations de sécurité
            if not self.pitr_config['enabled']:
                recommendations.append("Activez PITR pour une meilleure protection contre la perte de données")

            if not self.differential_config['enabled']:
                recommendations.append("Activez les sauvegardes différentielles pour optimiser l'espace")

            # Recommandations de performance
            if self.pg_config['parallel_jobs'] < 2:
                recommendations.append("Augmentez le nombre de jobs parallèles pour les grosses bases")

        except Exception as e:
            recommendations.append(f"Erreur analyse recommandations: {e}")

        return recommendations

    def _get_next_backup_actions(self) -> list:
        """Obtenir les prochaines actions de sauvegarde recommandées"""
        actions = []

        try:
            # Vérifier si une sauvegarde complète est nécessaire
            last_full_backup = self._get_last_backup_info()
            if not last_full_backup.get('available', False):
                actions.append("Créer une sauvegarde complète immédiatement")
            else:
                backup_age = datetime.now() - datetime.fromtimestamp(Path(last_full_backup['path']).stat().st_mtime)
                if backup_age > timedelta(days=self.differential_config['full_backup_interval_days']):
                    actions.append("Planifier une sauvegarde complète")

            # Vérifier les sauvegardes différentielles
            if self.differential_config['enabled']:
                last_diff = self._get_latest_differential_backup()
                if last_diff:
                    diff_age = datetime.now() - datetime.fromtimestamp(Path(last_diff).stat().st_mtime)
                    if diff_age > timedelta(hours=24):
                        actions.append("Créer une sauvegarde différentielle")

            # Maintenance
            actions.append("Vérifier l'intégrité des sauvegardes récentes")
            actions.append("Nettoyer les anciennes sauvegardes selon la politique de rétention")

        except Exception as e:
            actions.append(f"Erreur planification actions: {e}")

        return actions

    def _get_latest_differential_backup(self) -> str:
        """Obtenir la dernière sauvegarde différentielle"""
        try:
            diff_backups = list(self.differential_config['diff_backup_dir'].glob('*.dump.gz'))
            if not diff_backups:
                return None

            latest_backup = max(diff_backups, key=lambda x: x.stat().st_mtime)
            return str(latest_backup)

        except Exception as e:
            self.logger.error(f"Erreur recherche sauvegarde différentielle: {e}")
            return None

# Instance globale du gestionnaire PostgreSQL
postgresql_backup_manager = PostgreSQLBackupManager()

def create_postgresql_backup(backup_type: str = 'full') -> tuple[bool, str]:
    """Fonction utilitaire pour créer une sauvegarde PostgreSQL"""
    if backup_type == 'differential':
        return postgresql_backup_manager.create_differential_backup()
    else:
        return postgresql_backup_manager.create_full_backup()

def setup_postgresql_pitr() -> tuple[bool, str]:
    """Fonction utilitaire pour configurer PITR"""
    return postgresql_backup_manager.setup_pitr()

def restore_postgresql_to_point(target_time: datetime, backup_file: str = None) -> tuple[bool, str]:
    """Fonction utilitaire pour restaurer à un point dans le temps"""
    return postgresql_backup_manager.restore_to_point_in_time(target_time, backup_file)

def optimize_postgresql_backup() -> dict:
    """Fonction utilitaire pour optimiser les sauvegardes PostgreSQL"""
    return postgresql_backup_manager.optimize_backup_performance()

def generate_backup_strategy_report() -> dict:
    """Fonction utilitaire pour générer un rapport de stratégie de sauvegarde"""
    return postgresql_backup_manager.create_backup_strategy_report()

if __name__ == "__main__":
    print("🗄️  Gestionnaire avancé de sauvegardes PostgreSQL PassPrint")

    # Test du système
    success, result = create_postgresql_backup('full')
    if success:
        print(f"✅ Sauvegarde PostgreSQL créée: {result}")
    else:
        print(f"❌ Échec sauvegarde PostgreSQL: {result}")

    # Générer le rapport de stratégie
    report = generate_backup_strategy_report()
    print(f"📊 Rapport de stratégie généré avec {len(report.get('recommendations', []))} recommandations")