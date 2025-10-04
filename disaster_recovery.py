#!/usr/bin/env python3
"""
Système de récupération après désastre pour PassPrint
Procédures de récupération automatique et manuelle
"""
import os
import json
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import logging
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import tempfile

from backup_system import backup_system
from monitoring_config import get_monitoring_integration

logger = logging.getLogger(__name__)

class DisasterRecoveryManager:
    """Gestionnaire de récupération après désastre"""

    def __init__(self, app=None):
        self.app = app
        self.recovery_scripts_dir = Path('recovery_scripts')
        self.recovery_scripts_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)

        # Configuration des seuils de désastre
        self.disaster_thresholds = {
            'database_unavailable_minutes': int(os.getenv('DB_UNAVAILABLE_THRESHOLD', '5')),
            'high_error_rate_percent': float(os.getenv('ERROR_RATE_THRESHOLD', '10.0')),
            'system_resource_exhaustion_percent': float(os.getenv('RESOURCE_THRESHOLD', '95.0')),
            'security_incident_score': int(os.getenv('SECURITY_THRESHOLD', '80'))
        }

    def detect_disaster(self, system_metrics: dict) -> Dict:
        """Détecter si une situation de désastre est en cours"""
        try:
            disaster_indicators = []
            severity_score = 0

            # Vérifier la disponibilité de la base de données
            db_healthy = system_metrics.get('database', {}).get('stats', {}).get('connection_healthy', True)
            if not db_healthy:
                disaster_indicators.append('database_unavailable')
                severity_score += 30

            # Vérifier le taux d'erreur
            error_rate = self._calculate_error_rate(system_metrics)
            if error_rate > self.disaster_thresholds['high_error_rate_percent']:
                disaster_indicators.append('high_error_rate')
                severity_score += 25

            # Vérifier l'utilisation des ressources système
            cpu_usage = system_metrics.get('system', {}).get('cpu', {}).get('percent', 0)
            memory_usage = system_metrics.get('system', {}).get('memory', {}).get('percent', 0)
            disk_usage = system_metrics.get('system', {}).get('disk', {}).get('percent', 0)

            if cpu_usage > self.disaster_thresholds['system_resource_exhaustion_percent']:
                disaster_indicators.append('high_cpu_usage')
                severity_score += 15

            if memory_usage > self.disaster_thresholds['system_resource_exhaustion_percent']:
                disaster_indicators.append('high_memory_usage')
                severity_score += 15

            if disk_usage > self.disaster_thresholds['system_resource_exhaustion_percent']:
                disaster_indicators.append('low_disk_space')
                severity_score += 20

            # Vérifier le score de sécurité
            security_score = system_metrics.get('security', {}).get('events', {}).get('security_score', 100)
            if security_score < self.disaster_thresholds['security_incident_score']:
                disaster_indicators.append('security_incident')
                severity_score += 25

            # Déterminer le niveau de sévérité
            if severity_score >= 70:
                disaster_level = 'critical'
            elif severity_score >= 40:
                disaster_level = 'high'
            elif severity_score >= 20:
                disaster_level = 'medium'
            else:
                disaster_level = 'low'

            return {
                'disaster_detected': len(disaster_indicators) > 0,
                'severity': disaster_level,
                'severity_score': severity_score,
                'indicators': disaster_indicators,
                'timestamp': datetime.utcnow().isoformat(),
                'recommendations': self._get_recovery_recommendations(disaster_indicators, disaster_level)
            }

        except Exception as e:
            self.logger.error(f"Erreur détection désastre: {e}")
            return {
                'disaster_detected': False,
                'error': str(e)
            }

    def _calculate_error_rate(self, metrics: dict) -> float:
        """Calculer le taux d'erreur actuel"""
        try:
            log_analysis = metrics.get('application', {}).get('performance', {}).get('log_analysis', {})
            error_count = log_analysis.get('error_count', 0)
            total_lines = log_analysis.get('total_lines', 1)

            return (error_count / total_lines) * 100 if total_lines > 0 else 0

        except Exception:
            return 0.0

    def _get_recovery_recommendations(self, indicators: list, severity: str) -> List[str]:
        """Obtenir les recommandations de récupération"""
        recommendations = []

        if 'database_unavailable' in indicators:
            recommendations.append("Restaurer la base de données depuis la dernière sauvegarde")
            recommendations.append("Vérifier la connectivité réseau à la base de données")

        if 'high_error_rate' in indicators:
            recommendations.append("Analyser les erreurs dans les logs récents")
            recommendations.append("Vérifier la charge du serveur et les ressources disponibles")

        if 'high_cpu_usage' in indicators or 'high_memory_usage' in indicators:
            recommendations.append("Redémarrer les services non essentiels")
            recommendations.append("Vérifier les processus zombies")

        if 'low_disk_space' in indicators:
            recommendations.append("Libérer de l'espace disque")
            recommendations.append("Archiver les anciens logs et sauvegardes")

        if 'security_incident' in indicators:
            recommendations.append("Activer le mode sécurité renforcée")
            recommendations.append("Auditer les accès récents")

        # Recommandations générales selon la sévérité
        if severity == 'critical':
            recommendations.insert(0, "🚨 DÉSASTRE CRITIQUE DÉTECTÉ - Action immédiate requise")
            recommendations.append("Contacter l'équipe technique d'urgence")
            recommendations.append("Préparer la restauration complète du système")

        elif severity == 'high':
            recommendations.insert(0, "⚠️ Problème majeur détecté - Intervention nécessaire")
            recommendations.append("Surveiller l'évolution de la situation")

        return recommendations

    def initiate_automatic_recovery(self, disaster_info: dict) -> Dict:
        """Initier la récupération automatique"""
        try:
            recovery_result = {
                'recovery_initiated': True,
                'timestamp': datetime.utcnow().isoformat(),
                'actions_taken': [],
                'success': True,
                'errors': []
            }

            severity = disaster_info.get('severity', 'low')

            # Actions automatiques selon la sévérité
            if severity == 'critical':
                # Récupération critique
                recovery_result.update(self._execute_critical_recovery())

            elif severity == 'high':
                # Récupération majeure
                recovery_result.update(self._execute_major_recovery())

            else:
                # Récupération mineure
                recovery_result.update(self._execute_minor_recovery())

            # Créer un rapport de récupération
            self._create_recovery_report(recovery_result)

            return recovery_result

        except Exception as e:
            self.logger.error(f"Erreur récupération automatique: {e}")
            return {
                'recovery_initiated': False,
                'success': False,
                'error': str(e)
            }

    def _execute_critical_recovery(self) -> Dict:
        """Exécuter la récupération critique"""
        actions = []
        errors = []

        try:
            # 1. Créer une sauvegarde d'urgence
            emergency_backup = backup_system.create_snapshot("emergency_before_recovery")
            if emergency_backup[0]:
                actions.append("Sauvegarde d'urgence créée")
            else:
                errors.append(f"Échec sauvegarde d'urgence: {emergency_backup[1]}")

            # 2. Tenter de redémarrer les services essentiels
            services_restart = self._restart_essential_services()
            if services_restart['success']:
                actions.append("Services essentiels redémarrés")
            else:
                errors.append(f"Échec redémarrage services: {services_restart['error']}")

            # 3. Restaurer la dernière sauvegarde valide
            latest_backup = self._find_latest_valid_backup()
            if latest_backup:
                restore_result = self._restore_from_backup(latest_backup)
                if restore_result['success']:
                    actions.append(f"Sauvegarde restaurée: {latest_backup}")
                else:
                    errors.append(f"Échec restauration: {restore_result['error']}")
            else:
                errors.append("Aucune sauvegarde valide trouvée")

        except Exception as e:
            errors.append(f"Erreur récupération critique: {e}")

        return {
            'actions_taken': actions,
            'errors': errors,
            'success': len(errors) == 0
        }

    def _execute_major_recovery(self) -> Dict:
        """Exécuter la récupération majeure"""
        actions = []
        errors = []

        try:
            # 1. Nettoyer les processus problématiques
            cleanup_result = self._cleanup_problematic_processes()
            if cleanup_result['success']:
                actions.append("Processus problématiques nettoyés")
            else:
                errors.append(f"Échec nettoyage processus: {cleanup_result['error']}")

            # 2. Vérifier et réparer la base de données
            db_check = self._check_and_repair_database()
            if db_check['success']:
                actions.append("Base de données vérifiée et réparée")
            else:
                errors.append(f"Problème base de données: {db_check['error']}")

            # 3. Redémarrer l'application
            app_restart = self._restart_application()
            if app_restart['success']:
                actions.append("Application redémarrée")
            else:
                errors.append(f"Échec redémarrage application: {app_restart['error']}")

        except Exception as e:
            errors.append(f"Erreur récupération majeure: {e}")

        return {
            'actions_taken': actions,
            'errors': errors,
            'success': len(errors) == 0
        }

    def _execute_minor_recovery(self) -> Dict:
        """Exécuter la récupération mineure"""
        actions = []
        errors = []

        try:
            # 1. Vider les caches problématiques
            cache_clear = self._clear_problematic_caches()
            if cache_clear['success']:
                actions.append("Caches problématiques vidés")
            else:
                errors.append(f"Échec vidage caches: {cache_clear['error']}")

            # 2. Redémarrer les workers Celery si nécessaire
            celery_restart = self._restart_celery_workers()
            if celery_restart['success']:
                actions.append("Workers Celery redémarrés")
            else:
                errors.append(f"Échec redémarrage Celery: {celery_restart['error']}")

        except Exception as e:
            errors.append(f"Erreur récupération mineure: {e}")

        return {
            'actions_taken': actions,
            'errors': errors,
            'success': len(errors) == 0
        }

    def _restart_essential_services(self) -> Dict:
        """Redémarrer les services essentiels"""
        try:
            # Redémarrer Redis
            redis_restart = self._restart_service('redis')

            # Redémarrer PostgreSQL si applicable
            db_restart = self._restart_service('postgresql')

            # Redémarrer Nginx
            nginx_restart = self._restart_service('nginx')

            success = redis_restart.get('success', False)

            return {
                'success': success,
                'details': {
                    'redis': redis_restart,
                    'database': db_restart,
                    'nginx': nginx_restart
                }
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _restart_service(self, service_name: str) -> Dict:
        """Redémarrer un service spécifique"""
        try:
            if service_name == 'redis':
                # Commande pour redémarrer Redis
                result = subprocess.run(['sudo', 'systemctl', 'restart', 'redis'],
                                      capture_output=True, text=True, timeout=30)

                return {
                    'success': result.returncode == 0,
                    'output': result.stdout,
                    'error': result.stderr
                }

            elif service_name == 'postgresql':
                # Commande pour redémarrer PostgreSQL
                result = subprocess.run(['sudo', 'systemctl', 'restart', 'postgresql'],
                                      capture_output=True, text=True, timeout=60)

                return {
                    'success': result.returncode == 0,
                    'output': result.stdout,
                    'error': result.stderr
                }

            elif service_name == 'nginx':
                # Commande pour redémarrer Nginx
                result = subprocess.run(['sudo', 'systemctl', 'restart', 'nginx'],
                                      capture_output=True, text=True, timeout=30)

                return {
                    'success': result.returncode == 0,
                    'output': result.stdout,
                    'error': result.stderr
                }

            return {'success': False, 'error': f'Service {service_name} non supporté'}

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': f'Timeout redémarrage {service_name}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _cleanup_problematic_processes(self) -> Dict:
        """Nettoyer les processus problématiques"""
        try:
            # Identifier les processus Python zombies ou problématiques
            result = subprocess.run(['pgrep', '-f', 'python.*passprint'],
                                  capture_output=True, text=True)

            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                killed_count = 0

                for pid in pids:
                    if pid:
                        try:
                            subprocess.run(['kill', '-TERM', pid], timeout=10)
                            killed_count += 1
                        except:
                            pass

                return {
                    'success': True,
                    'processes_killed': killed_count
                }
            else:
                return {'success': True, 'processes_killed': 0}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _check_and_repair_database(self) -> Dict:
        """Vérifier et réparer la base de données"""
        try:
            from config import get_config

            config = get_config()
            db_url = config.SQLALCHEMY_DATABASE_URI

            if 'sqlite' in db_url:
                return self._repair_sqlite_database(db_url)
            elif 'postgresql' in db_url:
                return self._repair_postgresql_database(db_url)
            else:
                return {'success': False, 'error': 'Type de base non supporté'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _repair_sqlite_database(self, db_url: str) -> Dict:
        """Réparer une base SQLite"""
        try:
            db_path = db_url.replace('sqlite:///', '')

            # Vérifier l'intégrité
            integrity_result = subprocess.run([
                'sqlite3', db_path, 'PRAGMA integrity_check;'
            ], capture_output=True, text=True, timeout=30)

            if integrity_result.returncode == 0:
                integrity_output = integrity_result.stdout.strip()

                if integrity_output == 'ok':
                    return {'success': True, 'message': 'Base SQLite intègre'}
                else:
                    # Tentative de réparation
                    repair_result = subprocess.run([
                        'sqlite3', db_path, 'REINDEX;'
                    ], capture_output=True, timeout=60)

                    return {
                        'success': repair_result.returncode == 0,
                        'integrity_issues': integrity_output,
                        'repaired': repair_result.returncode == 0
                    }
            else:
                return {
                    'success': False,
                    'error': f'Erreur vérification intégrité: {integrity_result.stderr}'
                }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _repair_postgresql_database(self, db_url: str) -> Dict:
        """Réparer une base PostgreSQL"""
        try:
            # Parser l'URL
            import re
            pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
            match = re.match(pattern, db_url)

            if not match:
                return {'success': False, 'error': 'Format URL PostgreSQL invalide'}

            user, password, host, port, database = match.groups()

            # Commandes de réparation PostgreSQL
            commands = [
                f'REINDEX DATABASE {database};',
                f'VACUUM ANALYZE {database};',
                f'CHECKPOINT;'
            ]

            env = os.environ.copy()
            env['PGPASSWORD'] = password

            success_count = 0
            for cmd in commands:
                try:
                    result = subprocess.run([
                        'psql',
                        f'--host={host}',
                        f'--port={port}',
                        f'--username={user}',
                        f'--dbname={database}',
                        '--no-password',
                        '--command', cmd
                    ], env=env, capture_output=True, text=True, timeout=300)

                    if result.returncode == 0:
                        success_count += 1

                except Exception as e:
                    self.logger.warning(f"Erreur commande réparation PostgreSQL: {cmd} - {e}")

            return {
                'success': success_count > 0,
                'commands_executed': success_count,
                'total_commands': len(commands)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _restart_application(self) -> Dict:
        """Redémarrer l'application"""
        try:
            # Redémarrer l'application Flask via supervisor ou systemd
            result = subprocess.run([
                'sudo', 'systemctl', 'restart', 'passprint'
            ], capture_output=True, text=True, timeout=60)

            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _clear_problematic_caches(self) -> Dict:
        """Vider les caches problématiques"""
        try:
            from redis_cache import clear_cache

            # Vider tous les caches
            cache_cleared = clear_cache()

            return {
                'success': True,
                'cache_cleared': cache_cleared
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _restart_celery_workers(self) -> Dict:
        """Redémarrer les workers Celery"""
        try:
            # Redémarrer les workers Celery
            result = subprocess.run([
                'sudo', 'systemctl', 'restart', 'celery-workers'
            ], capture_output=True, text=True, timeout=60)

            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _find_latest_valid_backup(self) -> str:
        """Trouver la dernière sauvegarde valide"""
        try:
            backup_dir = Path('backups')
            if not backup_dir.exists():
                return None

            # Chercher les sauvegardes récentes
            backup_files = []
            for backup_file in backup_dir.glob('passprint_*'):
                if backup_file.is_file() and backup_file.stat().st_mtime > (datetime.now() - timedelta(hours=24)).timestamp():
                    backup_files.append(backup_file)

            if not backup_files:
                return None

            # Retourner la plus récente
            latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
            return str(latest_backup)

        except Exception as e:
            self.logger.error(f"Erreur recherche sauvegarde valide: {e}")
            return None

    def _restore_from_backup(self, backup_path: str) -> Dict:
        """Restaurer depuis une sauvegarde"""
        try:
            # Restaurer la base de données
            db_restore_success, db_result = backup_system.restore_database(backup_path)

            # Restaurer les fichiers si c'est une sauvegarde complète
            files_restore_success = True
            files_result = "Pas de fichiers à restaurer"

            if 'full' in backup_path or 'files' in backup_path:
                files_restore_success, files_result = backup_system.restore_files(backup_path)

            return {
                'success': db_restore_success and files_restore_success,
                'database_restored': db_restore_success,
                'files_restored': files_restore_success,
                'details': {
                    'database': db_result,
                    'files': files_result
                }
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _create_recovery_report(self, recovery_result: dict):
        """Créer un rapport de récupération"""
        try:
            report = {
                'recovery_timestamp': datetime.utcnow().isoformat(),
                'recovery_result': recovery_result,
                'system_status': self._get_current_system_status(),
                'next_steps': self._get_next_steps(recovery_result)
            }

            # Sauvegarder le rapport
            report_file = Path('backups') / f'recovery_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)

            # Envoyer le rapport par email si configuré
            self._send_recovery_report_email(report)

        except Exception as e:
            self.logger.error(f"Erreur création rapport récupération: {e}")

    def _get_current_system_status(self) -> Dict:
        """Obtenir le statut actuel du système"""
        try:
            from monitoring_alerting import MetricsCollector

            collector = MetricsCollector()
            collector.collect_all_metrics()

            return {
                'timestamp': datetime.utcnow().isoformat(),
                'system_healthy': collector.metrics.get('application', {}).get('health', {}).get('healthy', False),
                'database_healthy': collector.metrics.get('database', {}).get('stats', {}).get('connection_healthy', False),
                'cache_healthy': collector.metrics.get('cache', {}).get('health', {}).get('status') == 'healthy'
            }

        except Exception as e:
            return {'error': str(e)}

    def _get_next_steps(self, recovery_result: dict) -> List[str]:
        """Obtenir les prochaines étapes recommandées"""
        next_steps = []

        if not recovery_result.get('success', False):
            next_steps.append("Récupération automatique échouée - Intervention manuelle requise")
            next_steps.append("Contacter l'équipe d'astreinte")
            next_steps.append("Analyser les logs d'erreur en détail")

        next_steps.append("Vérifier que tous les services sont opérationnels")
        next_steps.append("Tester les fonctionnalités critiques")
        next_steps.append("Créer un rapport d'incident")

        return next_steps

    def _send_recovery_report_email(self, report: dict):
        """Envoyer le rapport de récupération par email"""
        try:
            # Configuration email
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_username = os.getenv('SMTP_USERNAME')
            smtp_password = os.getenv('SMTP_PASSWORD')

            if not smtp_username or not smtp_password:
                return

            # Destinataires
            recipients = os.getenv('RECOVERY_EMAIL_RECIPIENTS', 'admin@passprint.com').split(',')

            # Créer l'email
            msg = MimeMultipart()
            msg['From'] = smtp_username
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"[PassPrint] Rapport de récupération - {report['recovery_timestamp']}"

            # Corps de l'email
            body = f"""
            Rapport de récupération PassPrint

            Timestamp: {report['recovery_timestamp']}
            Succès: {'Oui' if report['recovery_result'].get('success', False) else 'Non'}

            Actions prises:
            {chr(10).join(f"- {action}" for action in report['recovery_result'].get('actions_taken', []))}

            Erreurs rencontrées:
            {chr(10).join(f"- {error}" for error in report['recovery_result'].get('errors', []))}

            État système actuel:
            - Système sain: {'Oui' if report['system_status'].get('system_healthy', False) else 'Non'}
            - Base de données: {'Saine' if report['system_status'].get('database_healthy', False) else 'Problématique'}
            - Cache: {'Sain' if report['system_status'].get('cache_healthy', False) else 'Problématique'}

            Prochaines étapes:
            {chr(10).join(f"- {step}" for step in report.get('next_steps', []))}

            Ce rapport a été généré automatiquement par le système de récupération après désastre.
            """

            msg.attach(MimeText(body, 'plain'))

            # Envoyer l'email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(smtp_username, recipients, msg.as_string())
            server.quit()

            self.logger.info("Rapport de récupération envoyé par email")

        except Exception as e:
            self.logger.error(f"Erreur envoi email rapport récupération: {e}")

    def create_recovery_scripts(self):
        """Créer les scripts de récupération automatique"""
        try:
            scripts_created = []

            # Script de récupération de base de données
            db_script = self._create_database_recovery_script()
            scripts_created.append(db_script)

            # Script de récupération de fichiers
            files_script = self._create_files_recovery_script()
            scripts_created.append(files_script)

            # Script de récupération complète
            full_script = self._create_full_recovery_script()
            scripts_created.append(full_script)

            # Script de vérification post-récupération
            verify_script = self._create_verification_script()
            scripts_created.append(verify_script)

            self.logger.info(f"Scripts de récupération créés: {len(scripts_created)}")
            return scripts_created

        except Exception as e:
            self.logger.error(f"Erreur création scripts récupération: {e}")
            return []

    def _create_database_recovery_script(self) -> str:
        """Créer le script de récupération de base de données"""
        script_content = """#!/bin/bash
# Script de récupération de base de données PassPrint
# Usage: ./recover_database.sh [backup_file]

set -e

BACKUP_FILE=${1:-"latest"}
LOG_FILE="/var/log/passprint/database_recovery.log"

echo "$(date): Démarrage récupération base de données" >> "$LOG_FILE"

if [ "$BACKUP_FILE" = "latest" ]; then
    # Trouver la dernière sauvegarde
    BACKUP_FILE=$(find /backups -name "passprint_*sqlite*" -o -name "passprint_*postgres*" | sort -r | head -1)
fi

if [ -z "$BACKUP_FILE" ]; then
    echo "$(date): Aucune sauvegarde trouvée" >> "$LOG_FILE"
    exit 1
fi

echo "$(date): Utilisation sauvegarde: $BACKUP_FILE" >> "$LOG_FILE"

# Arrêter l'application
sudo systemctl stop passprint

# Créer une sauvegarde d'urgence
EMERGENCY_BACKUP="/backups/emergency_$(date +%Y%m%d_%H%M%S).db"
cp /opt/passprint-website/passprint.db "$EMERGENCY_BACKUP" 2>/dev/null || true

# Restaurer la sauvegarde
if [[ "$BACKUP_FILE" == *"postgres"* ]]; then
    # Restauration PostgreSQL
    pg_restore -h localhost -U passprint -d passprint_prod -c "$BACKUP_FILE"
elif [[ "$BACKUP_FILE" == *"sqlite"* ]]; then
    # Restauration SQLite
    gunzip -c "$BACKUP_FILE" > /opt/passprint-website/passprint.db
    chown passprint:passprint /opt/passprint-website/passprint.db
fi

# Redémarrer l'application
sudo systemctl start passprint

# Vérification
sleep 10
curl -f http://localhost:5000/api/health || exit 1

echo "$(date): Récupération base de données terminée avec succès" >> "$LOG_FILE"
"""

        script_path = self.recovery_scripts_dir / 'recover_database.sh'
        with open(script_path, 'w') as f:
            f.write(script_content)

        script_path.chmod(0o755)
        return str(script_path)

    def _create_files_recovery_script(self) -> str:
        """Créer le script de récupération de fichiers"""
        script_content = """#!/bin/bash
# Script de récupération de fichiers PassPrint
# Usage: ./recover_files.sh [backup_file]

set -e

BACKUP_FILE=${1:-"latest"}
LOG_FILE="/var/log/passprint/files_recovery.log"

echo "$(date): Démarrage récupération fichiers" >> "$LOG_FILE"

if [ "$BACKUP_FILE" = "latest" ]; then
    # Trouver la dernière sauvegarde de fichiers
    BACKUP_FILE=$(find /backups -name "*files*" | sort -r | head -1)
fi

if [ -z "$BACKUP_FILE" ]; then
    echo "$(date): Aucune sauvegarde de fichiers trouvée" >> "$LOG_FILE"
    exit 1
fi

echo "$(date): Utilisation sauvegarde: $BACKUP_FILE" >> "$LOG_FILE"

# Créer des sauvegardes des fichiers actuels
for dir in uploads static logs; do
    if [ -d "/opt/passprint-website/$dir" ]; then
        BACKUP_DIR="/backups/emergency_files_$(date +%Y%m%d_%H%M%S)/$dir"
        mkdir -p "$BACKUP_DIR"
        cp -r "/opt/passprint-website/$dir" "$BACKUP_DIR" 2>/dev/null || true
    fi
done

# Extraire la sauvegarde
cd /opt/passprint-website
tar -xzf "$BACKUP_FILE"

# Restaurer les permissions
chown -R passprint:passprint uploads static logs

echo "$(date): Récupération fichiers terminée avec succès" >> "$LOG_FILE"
"""

        script_path = self.recovery_scripts_dir / 'recover_files.sh'
        with open(script_path, 'w') as f:
            f.write(script_content)

        script_path.chmod(0o755)
        return str(script_path)

    def _create_full_recovery_script(self) -> str:
        """Créer le script de récupération complète"""
        script_content = """#!/bin/bash
# Script de récupération complète PassPrint
# Usage: ./recover_full.sh

set -e

LOG_FILE="/var/log/passprint/full_recovery.log"

echo "$(date): Démarrage récupération complète" >> "$LOG_FILE"

# 1. Récupération base de données
echo "$(date): Étape 1/4 - Récupération base de données" >> "$LOG_FILE"
./recover_database.sh

# 2. Récupération fichiers
echo "$(date): Étape 2/4 - Récupération fichiers" >> "$LOG_FILE"
./recover_files.sh

# 3. Redémarrage services
echo "$(date): Étape 3/4 - Redémarrage services" >> "$LOG_FILE"
sudo systemctl restart redis postgresql nginx passprint celery-workers

# 4. Vérification
echo "$(date): Étape 4/4 - Vérification" >> "$LOG_FILE"
sleep 30

# Vérifications de base
curl -f http://localhost:5000/api/health || exit 1
curl -f http://localhost:5000/api/products || exit 1

echo "$(date): Récupération complète terminée avec succès" >> "$LOG_FILE"
"""

        script_path = self.recovery_scripts_dir / 'recover_full.sh'
        with open(script_path, 'w') as f:
            f.write(script_content)

        script_path.chmod(0o755)
        return str(script_path)

    def _create_verification_script(self) -> str:
        """Créer le script de vérification post-récupération"""
        script_content = """#!/bin/bash
# Script de vérification post-récupération PassPrint
# Usage: ./verify_recovery.sh

LOG_FILE="/var/log/passprint/verification.log"

echo "$(date): Démarrage vérification post-récupération" >> "$LOG_FILE"

ERRORS=0

# 1. Vérifier la santé de l'API
echo "$(date): Vérification API..." >> "$LOG_FILE"
if curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "$(date): ✅ API opérationnelle" >> "$LOG_FILE"
else
    echo "$(date): ❌ API non opérationnelle" >> "$LOG_FILE"
    ERRORS=$((ERRORS + 1))
fi

# 2. Vérifier la base de données
echo "$(date): Vérification base de données..." >> "$LOG_FILE"
if curl -f http://localhost:5000/api/products > /dev/null 2>&1; then
    echo "$(date): ✅ Base de données accessible" >> "$LOG_FILE"
else
    echo "$(date): ❌ Base de données inaccessible" >> "$LOG_FILE"
    ERRORS=$((ERRORS + 1))
fi

# 3. Vérifier les services
echo "$(date): Vérification services..." >> "$LOG_FILE"
SERVICES=("redis" "postgresql" "nginx" "passprint")
for service in "${SERVICES[@]}"; do
    if sudo systemctl is-active --quiet "$service"; then
        echo "$(date): ✅ Service $service actif" >> "$LOG_FILE"
    else
        echo "$(date): ❌ Service $service inactif" >> "$LOG_FILE"
        ERRORS=$((ERRORS + 1))
    fi
done

# 4. Vérifier les sauvegardes récentes
echo "$(date): Vérification sauvegardes..." >> "$LOG_FILE"
if find /backups -name "passprint_*" -mtime -1 | grep -q .; then
    echo "$(date): ✅ Sauvegardes récentes trouvées" >> "$LOG_FILE"
else
    echo "$(date): ⚠️ Aucune sauvegarde récente" >> "$LOG_FILE"
fi

# Résultat final
if [ $ERRORS -eq 0 ]; then
    echo "$(date): ✅ Vérification réussie - Système opérationnel" >> "$LOG_FILE"
    exit 0
else
    echo "$(date): ❌ $ERRORS erreurs détectées" >> "$LOG_FILE"
    exit 1
fi
"""

        script_path = self.recovery_scripts_dir / 'verify_recovery.sh'
        with open(script_path, 'w') as f:
            f.write(script_content)

        script_path.chmod(0o755)
        return str(script_path)

    def simulate_disaster_scenario(self, scenario_type: str) -> Dict:
        """Simuler un scénario de désastre pour les tests"""
        try:
            simulation_result = {
                'scenario': scenario_type,
                'timestamp': datetime.utcnow().isoformat(),
                'steps': [],
                'success': True
            }

            if scenario_type == 'database_failure':
                simulation_result['steps'] = self._simulate_database_failure()
            elif scenario_type == 'disk_space_exhaustion':
                simulation_result['steps'] = self._simulate_disk_space_exhaustion()
            elif scenario_type == 'high_cpu_usage':
                simulation_result['steps'] = self._simulate_high_cpu_usage()
            elif scenario_type == 'security_incident':
                simulation_result['steps'] = self._simulate_security_incident()
            else:
                return {'success': False, 'error': f'Scénario non supporté: {scenario_type}'}

            return simulation_result

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _simulate_database_failure(self) -> List[str]:
        """Simuler une panne de base de données"""
        steps = [
            "Arrêt du service PostgreSQL",
            "Suppression du fichier de base de données",
            "Tentative de connexion échouée",
            "Détection du désastre",
            "Récupération automatique",
            "Restauration depuis sauvegarde",
            "Vérification de l'intégrité"
        ]

        # En développement, on simule seulement
        self.logger.info("Simulation panne base de données (mode développement)")

        return steps

    def _simulate_disk_space_exhaustion(self) -> List[str]:
        """Simuler l'épuisement de l'espace disque"""
        steps = [
            "Création de fichiers volumineux",
            "Surveillance de l'espace disque",
            "Détection du seuil critique",
            "Déclenchement de l'alerte",
            "Nettoyage automatique",
            "Libération d'espace"
        ]

        self.logger.info("Simulation épuisement espace disque (mode développement)")

        return steps

    def _simulate_high_cpu_usage(self) -> List[str]:
        """Simuler une utilisation CPU élevée"""
        steps = [
            "Lancement de processus intensifs",
            "Surveillance de l'utilisation CPU",
            "Détection du seuil élevé",
            "Déclenchement de l'alerte",
            "Optimisation automatique",
            "Retour à la normale"
        ]

        self.logger.info("Simulation utilisation CPU élevée (mode développement)")

        return steps

    def _simulate_security_incident(self) -> List[str]:
        """Simuler un incident de sécurité"""
        steps = [
            "Tentatives de connexion multiples",
            "Détection d'activité suspecte",
            "Verrouillage automatique du compte",
            "Déclenchement de l'alerte sécurité",
            "Audit des accès",
            "Mesures correctives"
        ]

        self.logger.info("Simulation incident sécurité (mode développement)")

        return steps

# Instance globale du gestionnaire de récupération
disaster_recovery_manager = DisasterRecoveryManager()

def detect_disaster(system_metrics: dict) -> Dict:
    """Fonction utilitaire pour détecter un désastre"""
    return disaster_recovery_manager.detect_disaster(system_metrics)

def initiate_recovery(disaster_info: dict) -> Dict:
    """Fonction utilitaire pour initier la récupération"""
    return disaster_recovery_manager.initiate_automatic_recovery(disaster_info)

def create_recovery_scripts():
    """Fonction utilitaire pour créer les scripts de récupération"""
    return disaster_recovery_manager.create_recovery_scripts()

def simulate_disaster_scenario(scenario_type: str) -> Dict:
    """Fonction utilitaire pour simuler un scénario de désastre"""
    return disaster_recovery_manager.simulate_disaster_scenario(scenario_type)

if __name__ == "__main__":
    print("🛡️  Système de récupération après désastre PassPrint")

    # Créer les scripts de récupération
    scripts = create_recovery_scripts()
    print(f"✅ Scripts de récupération créés: {len(scripts)}")

    # Test de détection de désastre
    test_metrics = {
        'system': {
            'cpu': {'percent': 95},
            'memory': {'percent': 90},
            'disk': {'percent': 85}
        },
        'database': {
            'stats': {'connection_healthy': False}
        }
    }

    disaster_info = detect_disaster(test_metrics)
    print(f"Détection désastre: {disaster_info}")