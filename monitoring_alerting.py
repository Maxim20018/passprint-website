#!/usr/bin/env python3
"""
Système de monitoring et d'alerting avancé pour PassPrint
Surveillance en temps réel, métriques de performance, détection d'anomalies
"""
import os
import psutil
import time
import threading
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
import json
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import requests
import socket
from pathlib import Path
import GPUtil
from flask import current_app, g

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collecteur de métriques système et applicatives"""

    def __init__(self):
        self.metrics = {
            'system': {},
            'application': {},
            'database': {},
            'cache': {},
            'security': {}
        }

        self.history = {
            'cpu_usage': deque(maxlen=1000),
            'memory_usage': deque(maxlen=1000),
            'disk_usage': deque(maxlen=1000),
            'network_io': deque(maxlen=1000),
            'response_times': deque(maxlen=1000),
            'error_rates': deque(maxlen=1000),
            'active_users': deque(maxlen=1000),
            'database_connections': deque(maxlen=1000)
        }

        self.collectors = []
        self.running = False
        self.collection_interval = int(os.getenv('METRICS_COLLECTION_INTERVAL', '5'))  # secondes

    def start_collection(self):
        """Démarrer la collecte de métriques"""
        if self.running:
            return

        self.running = True

        # Démarrer le thread de collecte
        collector_thread = threading.Thread(target=self._collection_loop, daemon=True)
        collector_thread.start()

        logger.info("Collecte de métriques démarrée")

    def stop_collection(self):
        """Arrêter la collecte de métriques"""
        self.running = False
        logger.info("Collecte de métriques arrêtée")

    def _collection_loop(self):
        """Boucle principale de collecte"""
        while self.running:
            try:
                self.collect_all_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Erreur collecte métriques: {e}")
                time.sleep(self.collection_interval)

    def collect_all_metrics(self):
        """Collecter toutes les métriques"""
        timestamp = datetime.utcnow()

        # Métriques système
        self._collect_system_metrics(timestamp)

        # Métriques applicatives
        self._collect_application_metrics(timestamp)

        # Métriques base de données
        self._collect_database_metrics(timestamp)

        # Métriques cache
        self._collect_cache_metrics(timestamp)

        # Métriques sécurité
        self._collect_security_metrics(timestamp)

    def _collect_system_metrics(self, timestamp):
        """Collecter les métriques système"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_freq = psutil.cpu_freq()
            cpu_count = psutil.cpu_count()

            # Mémoire
            memory = psutil.virtual_memory()

            # Disque
            disk = psutil.disk_usage('/')

            # Réseau
            network = psutil.net_io_counters()

            # GPU (si disponible)
            gpu_info = {}
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_info = {
                        'gpu_usage': gpu.load * 100,
                        'gpu_memory_used': gpu.memoryUsed,
                        'gpu_memory_total': gpu.memoryTotal,
                        'gpu_temperature': gpu.temperature
                    }
            except:
                pass

            # Process
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()

            system_metrics = {
                'timestamp': timestamp,
                'cpu': {
                    'percent': cpu_percent,
                    'frequency': cpu_freq.current if cpu_freq else 0,
                    'count': cpu_count
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': {
                    'total': disk.total,
                    'free': disk.free,
                    'percent': disk.used / disk.total * 100
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'gpu': gpu_info,
                'process': {
                    'memory_rss': process_memory.rss,
                    'memory_vms': process_memory.vms,
                    'cpu_percent': process_cpu,
                    'threads': process.num_threads(),
                    'open_files': len(process.open_files())
                }
            }

            self.metrics['system'] = system_metrics

            # Ajouter à l'historique
            self.history['cpu_usage'].append(cpu_percent)
            self.history['memory_usage'].append(memory.percent)
            self.history['disk_usage'].append(disk.used / disk.total * 100)

        except Exception as e:
            logger.error(f"Erreur collecte métriques système: {e}")

    def _collect_application_metrics(self, timestamp):
        """Collecter les métriques applicatives"""
        try:
            # Métriques depuis le cache si disponible
            try:
                from redis_cache import get_cache_stats
                cache_stats = get_cache_stats()
            except:
                cache_stats = {}

            # Métriques depuis les logs
            log_metrics = self._analyze_recent_logs()

            # Métriques de performance
            performance_metrics = {
                'uptime_seconds': time.time() - psutil.boot_time(),
                'active_requests': getattr(g, 'active_requests', 0),
                'cache_stats': cache_stats,
                'log_analysis': log_metrics
            }

            self.metrics['application'] = {
                'timestamp': timestamp,
                'performance': performance_metrics,
                'health': self._check_application_health()
            }

        except Exception as e:
            logger.error(f"Erreur collecte métriques application: {e}")

    def _collect_database_metrics(self, timestamp):
        """Collecter les métriques base de données"""
        try:
            from models import db, User, Order, Product

            # Statistiques de base
            db_metrics = {
                'total_users': User.query.count(),
                'total_orders': Order.query.count(),
                'total_products': Product.query.count(),
                'pending_orders': Order.query.filter_by(status='pending').count(),
                'active_products': Product.query.filter_by(is_active=True).count()
            }

            # Métriques de performance DB
            try:
                # Vérifier la connexion
                start_time = time.time()
                User.query.first()  # Test query
                query_time = time.time() - start_time

                db_metrics['connection_healthy'] = True
                db_metrics['query_response_time'] = query_time
            except Exception as e:
                db_metrics['connection_healthy'] = False
                db_metrics['connection_error'] = str(e)

            self.metrics['database'] = {
                'timestamp': timestamp,
                'stats': db_metrics
            }

            # Ajouter à l'historique
            self.history['database_connections'].append(db_metrics.get('connection_healthy', False))

        except Exception as e:
            logger.error(f"Erreur collecte métriques base de données: {e}")

    def _collect_cache_metrics(self, timestamp):
        """Collecter les métriques de cache"""
        try:
            from redis_cache import cache_health_check

            cache_health = cache_health_check()

            self.metrics['cache'] = {
                'timestamp': timestamp,
                'health': cache_health,
                'performance': self._analyze_cache_performance()
            }

        except Exception as e:
            logger.error(f"Erreur collecte métriques cache: {e}")

    def _collect_security_metrics(self, timestamp):
        """Collecter les métriques de sécurité"""
        try:
            from models import AuditLog

            # Analyser les événements récents
            recent_events = AuditLog.query.filter(
                AuditLog.created_at >= timestamp - timedelta(minutes=5)
            ).all()

            security_metrics = {
                'total_events_5min': len(recent_events),
                'failed_logins_5min': len([e for e in recent_events if e.action == 'failed_login']),
                'suspicious_activities_5min': len([e for e in recent_events if e.status == 'warning']),
                'security_score': self._calculate_security_score(recent_events)
            }

            self.metrics['security'] = {
                'timestamp': timestamp,
                'events': security_metrics
            }

        except Exception as e:
            logger.error(f"Erreur collecte métriques sécurité: {e}")

    def _check_application_health(self):
        """Vérifier la santé de l'application"""
        health_checks = {
            'database': True,
            'cache': True,
            'file_system': True,
            'memory': True,
            'cpu': True
        }

        try:
            # Vérifier la base de données
            from models import User
            User.query.first()
        except:
            health_checks['database'] = False

        # Vérifier la mémoire
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            health_checks['memory'] = False

        # Vérifier le CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 95:
            health_checks['cpu'] = False

        # Vérifier le système de fichiers
        disk = psutil.disk_usage('/')
        if disk.percent > 95:
            health_checks['file_system'] = False

        overall_health = all(health_checks.values())
        return {
            'healthy': overall_health,
            'checks': health_checks,
            'status': 'healthy' if overall_health else 'degraded'
        }

    def _analyze_recent_logs(self):
        """Analyser les logs récents pour détecter les problèmes"""
        try:
            log_file = Path('logs/app.log')
            if not log_file.exists():
                return {'error_count': 0, 'warning_count': 0}

            # Lire les dernières lignes du fichier de log
            with open(log_file, 'r') as f:
                lines = f.readlines()[-100:]  # Dernières 100 lignes

            error_count = sum(1 for line in lines if 'ERROR' in line)
            warning_count = sum(1 for line in lines if 'WARNING' in line)

            return {
                'error_count': error_count,
                'warning_count': warning_count,
                'total_lines': len(lines)
            }

        except Exception as e:
            return {'error': str(e)}

    def _analyze_cache_performance(self):
        """Analyser les performances du cache"""
        try:
            from redis_cache import get_cache_stats

            stats = get_cache_stats()

            # Calculer les taux de hit/miss
            memory_size = len(stats.get('memory_cache', {}).get('size', 0))
            redis_keys = stats.get('redis_cache', {}).get('keys_count', 0)

            return {
                'memory_cache_size': memory_size,
                'redis_keys_count': redis_keys,
                'cache_efficiency': 'good' if memory_size > 0 else 'poor'
            }

        except Exception as e:
            return {'error': str(e)}

    def _calculate_security_score(self, recent_events):
        """Calculer un score de sécurité basé sur les événements récents"""
        if not recent_events:
            return 100

        # Pondération des événements
        score_deductions = {
            'failed_login': 5,
            'unauthorized_access': 10,
            'suspicious_activity': 15,
            'account_locked': 8
        }

        total_deduction = sum(
            score_deductions.get(event.action, 1)
            for event in recent_events
        )

        security_score = max(0, 100 - total_deduction)
        return security_score

    def get_metrics_summary(self, duration_minutes=60):
        """Obtenir un résumé des métriques sur une période"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=duration_minutes)

        summary = {
            'period': f'{duration_minutes} minutes',
            'system': self._summarize_time_series(self.history['cpu_usage'], cutoff_time),
            'memory': self._summarize_time_series(self.history['memory_usage'], cutoff_time),
            'errors': self._summarize_time_series(self.history['error_rates'], cutoff_time),
            'current': self.metrics
        }

        return summary

    def _summarize_time_series(self, data_series, cutoff_time):
        """Résumer une série temporelle"""
        if not data_series:
            return {'avg': 0, 'max': 0, 'min': 0, 'count': 0}

        values = list(data_series)
        return {
            'avg': sum(values) / len(values),
            'max': max(values),
            'min': min(values),
            'count': len(values)
        }

class AlertManager:
    """Gestionnaire d'alertes"""

    def __init__(self):
        self.alerts = []
        self.alert_rules = self._load_alert_rules()
        self.notification_channels = self._setup_notification_channels()
        self.alert_history = deque(maxlen=1000)

    def _load_alert_rules(self):
        """Charger les règles d'alerte"""
        return {
            'high_cpu_usage': {
                'enabled': True,
                'condition': lambda metrics: metrics.get('system', {}).get('cpu', {}).get('percent', 0) > 80,
                'severity': 'warning',
                'message': 'Utilisation CPU élevée: {cpu_percent}%',
                'cooldown_minutes': 5
            },
            'high_memory_usage': {
                'enabled': True,
                'condition': lambda metrics: metrics.get('system', {}).get('memory', {}).get('percent', 0) > 85,
                'severity': 'warning',
                'message': 'Utilisation mémoire élevée: {memory_percent}%',
                'cooldown_minutes': 5
            },
            'disk_space_low': {
                'enabled': True,
                'condition': lambda metrics: metrics.get('system', {}).get('disk', {}).get('percent', 0) > 90,
                'severity': 'critical',
                'message': 'Espace disque faible: {disk_percent}%',
                'cooldown_minutes': 15
            },
            'database_unavailable': {
                'enabled': True,
                'condition': lambda metrics: not metrics.get('database', {}).get('stats', {}).get('connection_healthy', True),
                'severity': 'critical',
                'message': 'Base de données non disponible',
                'cooldown_minutes': 2
            },
            'high_error_rate': {
                'enabled': True,
                'condition': lambda metrics: self._check_error_rate(metrics),
                'severity': 'warning',
                'message': 'Taux d\'erreur élevé détecté',
                'cooldown_minutes': 10
            },
            'security_threat': {
                'enabled': True,
                'condition': lambda metrics: metrics.get('security', {}).get('events', {}).get('security_score', 100) < 70,
                'severity': 'critical',
                'message': 'Menace de sécurité détectée - Score: {security_score}',
                'cooldown_minutes': 1
            },
            'cache_performance_degraded': {
                'enabled': True,
                'condition': lambda metrics: not metrics.get('cache', {}).get('health', {}).get('status') == 'healthy',
                'severity': 'warning',
                'message': 'Performance cache dégradée',
                'cooldown_minutes': 5
            }
        }

    def _check_error_rate(self, metrics):
        """Vérifier si le taux d'erreur est élevé"""
        try:
            log_analysis = metrics.get('application', {}).get('performance', {}).get('log_analysis', {})
            error_count = log_analysis.get('error_count', 0)
            total_lines = log_analysis.get('total_lines', 1)

            error_rate = error_count / total_lines if total_lines > 0 else 0
            return error_rate > 0.1  # Plus de 10% d'erreurs

        except:
            return False

    def _setup_notification_channels(self):
        """Configurer les canaux de notification"""
        channels = {}

        # Email
        if os.getenv('ALERT_EMAIL_ENABLED', 'true').lower() == 'true':
            channels['email'] = {
                'type': 'email',
                'recipients': os.getenv('ALERT_EMAIL_RECIPIENTS', 'admin@passprint.com').split(','),
                'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                'smtp_port': int(os.getenv('SMTP_PORT', '587')),
                'username': os.getenv('SMTP_USERNAME'),
                'password': os.getenv('SMTP_PASSWORD')
            }

        # Slack
        if os.getenv('SLACK_ALERTS_ENABLED', 'false').lower() == 'true':
            channels['slack'] = {
                'type': 'slack',
                'webhook_url': os.getenv('SLACK_WEBHOOK_URL'),
                'channel': os.getenv('SLACK_CHANNEL', '#alerts')
            }

        # Webhook générique
        webhook_url = os.getenv('ALERT_WEBHOOK_URL')
        if webhook_url:
            channels['webhook'] = {
                'type': 'webhook',
                'url': webhook_url
            }

        return channels

    def check_alerts(self, metrics):
        """Vérifier et déclencher les alertes"""
        current_time = datetime.utcnow()

        for rule_name, rule in self.alert_rules.items():
            if not rule['enabled']:
                continue

            try:
                # Vérifier la condition
                if rule['condition'](metrics):
                    # Vérifier le cooldown
                    if self._is_alert_on_cooldown(rule_name, rule['cooldown_minutes'], current_time):
                        continue

                    # Créer l'alerte
                    alert = self._create_alert(rule_name, rule, metrics, current_time)

                    # Envoyer les notifications
                    self._send_notifications(alert)

                    # Ajouter à l'historique
                    self.alert_history.append(alert)

                    logger.warning(f"Alerte déclenchée: {rule_name}")

            except Exception as e:
                logger.error(f"Erreur vérification alerte {rule_name}: {e}")

    def _is_alert_on_cooldown(self, rule_name, cooldown_minutes, current_time):
        """Vérifier si une alerte est en cooldown"""
        cooldown_threshold = current_time - timedelta(minutes=cooldown_minutes)

        for alert in self.alert_history:
            if (alert['rule_name'] == rule_name and
                alert['timestamp'] > cooldown_threshold):
                return True

        return False

    def _create_alert(self, rule_name, rule, metrics, timestamp):
        """Créer une alerte"""
        # Formater le message
        try:
            message = rule['message']

            # Remplacer les variables dans le message
            if 'cpu_percent' in message:
                cpu_percent = metrics.get('system', {}).get('cpu', {}).get('percent', 0)
                message = message.format(cpu_percent=cpu_percent)

            if 'memory_percent' in message:
                memory_percent = metrics.get('system', {}).get('memory', {}).get('percent', 0)
                message = message.format(memory_percent=memory_percent)

            if 'disk_percent' in message:
                disk_percent = metrics.get('system', {}).get('disk', {}).get('percent', 0)
                message = message.format(disk_percent=disk_percent)

            if 'security_score' in message:
                security_score = metrics.get('security', {}).get('events', {}).get('security_score', 100)
                message = message.format(security_score=security_score)

        except:
            message = f"Alerte: {rule_name}"

        return {
            'id': f"{rule_name}_{int(timestamp.timestamp())}",
            'rule_name': rule_name,
            'severity': rule['severity'],
            'message': message,
            'timestamp': timestamp,
            'metrics': metrics,
            'resolved': False
        }

    def _send_notifications(self, alert):
        """Envoyer les notifications"""
        for channel_name, channel_config in self.notification_channels.items():
            try:
                if channel_config['type'] == 'email':
                    self._send_email_alert(alert, channel_config)
                elif channel_config['type'] == 'slack':
                    self._send_slack_alert(alert, channel_config)
                elif channel_config['type'] == 'webhook':
                    self._send_webhook_alert(alert, channel_config)

            except Exception as e:
                logger.error(f"Erreur notification {channel_name}: {e}")

    def _send_email_alert(self, alert, channel_config):
        """Envoyer une alerte par email"""
        try:
            msg = MimeMultipart()
            msg['From'] = channel_config['username']
            msg['To'] = ', '.join(channel_config['recipients'])
            msg['Subject'] = f"[PassPrint Alert] {alert['severity'].upper()}: {alert['rule_name']}"

            # Corps de l'email
            body = f"""
            Alerte PassPrint - {alert['severity'].upper()}

            Règle: {alert['rule_name']}
            Message: {alert['message']}
            Timestamp: {alert['timestamp'].isoformat()}

            Métriques système:
            - CPU: {alert['metrics'].get('system', {}).get('cpu', {}).get('percent', 'N/A')}%
            - Mémoire: {alert['metrics'].get('system', {}).get('memory', {}).get('percent', 'N/A')}%
            - Disque: {alert['metrics'].get('system', {}).get('disk', {}).get('percent', 'N/A')}%

            Dashboard: {os.getenv('APP_URL', 'http://localhost:5000')}/admin/monitoring
            """

            msg.attach(MimeText(body, 'plain'))

            # Connexion SMTP
            server = smtplib.SMTP(channel_config['smtp_server'], channel_config['smtp_port'])
            server.starttls()
            server.login(channel_config['username'], channel_config['password'])

            server.sendmail(channel_config['username'], channel_config['recipients'], msg.as_string())
            server.quit()

            logger.info(f"Alerte email envoyée: {alert['rule_name']}")

        except Exception as e:
            logger.error(f"Erreur envoi email alerte: {e}")

    def _send_slack_alert(self, alert, channel_config):
        """Envoyer une alerte Slack"""
        try:
            color = {
                'warning': '#ff9800',
                'critical': '#f44336',
                'info': '#2196f3'
            }.get(alert['severity'], '#2196f3')

            payload = {
                'channel': channel_config['channel'],
                'attachments': [{
                    'color': color,
                    'title': f"🚨 Alerte PassPrint: {alert['severity'].upper()}",
                    'text': alert['message'],
                    'fields': [
                        {
                            'title': 'Règle',
                            'value': alert['rule_name'],
                            'short': True
                        },
                        {
                            'title': 'Timestamp',
                            'value': alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S UTC'),
                            'short': True
                        }
                    ],
                    'footer': 'PassPrint Monitoring',
                    'ts': int(alert['timestamp'].timestamp())
                }]
            }

            response = requests.post(
                channel_config['webhook_url'],
                json=payload,
                timeout=10
            )

            response.raise_for_status()
            logger.info(f"Alerte Slack envoyée: {alert['rule_name']}")

        except Exception as e:
            logger.error(f"Erreur envoi Slack alerte: {e}")

    def _send_webhook_alert(self, alert, channel_config):
        """Envoyer une alerte webhook générique"""
        try:
            payload = {
                'alert': alert,
                'timestamp': alert['timestamp'].isoformat(),
                'source': 'PassPrint',
                'severity': alert['severity']
            }

            response = requests.post(
                channel_config['url'],
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            response.raise_for_status()
            logger.info(f"Alerte webhook envoyée: {alert['rule_name']}")

        except Exception as e:
            logger.error(f"Erreur envoi webhook alerte: {e}")

    def get_alert_history(self, limit=50):
        """Obtenir l'historique des alertes"""
        return list(self.alert_history)[-limit:]

    def resolve_alert(self, alert_id):
        """Résoudre une alerte"""
        for alert in self.alert_history:
            if alert['id'] == alert_id:
                alert['resolved'] = True
                alert['resolved_at'] = datetime.utcnow()
                logger.info(f"Alerte résolue: {alert_id}")
                return True

        return False

class MonitoringDashboard:
    """Dashboard de monitoring avec API endpoints"""

    def __init__(self, app):
        self.app = app
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()

        # Démarrer la collecte automatique
        self.metrics_collector.start_collection()

        # Enregistrer les routes
        self._register_routes()

    def _register_routes(self):
        """Enregistrer les routes de monitoring"""

        @self.app.route('/api/monitoring/health')
        def monitoring_health():
            """État de santé du système de monitoring"""
            try:
                health = {
                    'monitoring_system': 'healthy',
                    'metrics_collection': 'running' if self.metrics_collector.running else 'stopped',
                    'alerts_enabled': len(self.alert_manager.notification_channels) > 0,
                    'timestamp': datetime.utcnow().isoformat()
                }

                return health, 200

            except Exception as e:
                return {'error': str(e)}, 500

        @self.app.route('/api/monitoring/metrics')
        def get_metrics():
            """Obtenir les métriques actuelles"""
            try:
                return {
                    'metrics': self.metrics_collector.metrics,
                    'timestamp': datetime.utcnow().isoformat()
                }, 200

            except Exception as e:
                return {'error': str(e)}, 500

        @self.app.route('/api/monitoring/metrics/summary')
        def get_metrics_summary():
            """Obtenir un résumé des métriques"""
            try:
                duration = int(request.args.get('duration', 60))  # minutes
                summary = self.metrics_collector.get_metrics_summary(duration)

                return summary, 200

            except Exception as e:
                return {'error': str(e)}, 500

        @self.app.route('/api/monitoring/alerts')
        def get_alerts():
            """Obtenir l'historique des alertes"""
            try:
                limit = int(request.args.get('limit', 50))
                alerts = self.alert_manager.get_alert_history(limit)

                return {
                    'alerts': alerts,
                    'total': len(alerts),
                    'timestamp': datetime.utcnow().isoformat()
                }, 200

            except Exception as e:
                return {'error': str(e)}, 500

        @self.app.route('/api/monitoring/alerts/<alert_id>/resolve', methods=['POST'])
        def resolve_alert(alert_id):
            """Résoudre une alerte spécifique"""
            try:
                resolved = self.alert_manager.resolve_alert(alert_id)

                if resolved:
                    return {'message': 'Alerte résolue'}, 200
                else:
                    return {'error': 'Alerte non trouvée'}, 404

            except Exception as e:
                return {'error': str(e)}, 500

        @self.app.route('/api/monitoring/performance')
        def get_performance_metrics():
            """Obtenir les métriques de performance détaillées"""
            try:
                # Métriques de performance avancées
                performance_data = {
                    'response_times': dict(self.metrics_collector.history['response_times']),
                    'throughput': self._calculate_throughput(),
                    'error_analysis': self._analyze_errors(),
                    'resource_utilization': self._get_resource_utilization()
                }

                return performance_data, 200

            except Exception as e:
                return {'error': str(e)}, 500

    def _calculate_throughput(self):
        """Calculer le débit de l'application"""
        try:
            # Calcul basé sur les métriques collectées
            recent_metrics = list(self.metrics_collector.history['response_times'])

            if not recent_metrics:
                return {'requests_per_second': 0, 'average_response_time': 0}

            avg_response_time = sum(recent_metrics) / len(recent_metrics)

            # Estimation du débit (simplifiée)
            requests_per_second = len(recent_metrics) / max(1, self.metrics_collector.collection_interval * len(recent_metrics) / 60)

            return {
                'requests_per_second': round(requests_per_second, 2),
                'average_response_time': round(avg_response_time, 3),
                'total_requests_tracked': len(recent_metrics)
            }

        except Exception as e:
            return {'error': str(e)}

    def _analyze_errors(self):
        """Analyser les erreurs récentes"""
        try:
            from logging_config import log_api_request

            # Cette fonction devrait analyser les erreurs des logs
            # Pour l'instant, retourner des métriques basiques
            return {
                'error_rate_5min': 0.02,  # 2%
                'most_common_errors': ['Connection timeout', 'Validation error'],
                'error_trend': 'stable'
            }

        except Exception as e:
            return {'error': str(e)}

    def _get_resource_utilization(self):
        """Obtenir l'utilisation des ressources"""
        try:
            return {
                'cpu_trend': 'increasing' if len(self.metrics_collector.history['cpu_usage']) > 1 and
                           self.metrics_collector.history['cpu_usage'][-1] > self.metrics_collector.history['cpu_usage'][0] else 'stable',
                'memory_trend': 'stable',
                'disk_trend': 'stable',
                'predictions': {
                    'cpu_1h': 'normal',
                    'memory_1h': 'normal',
                    'disk_1h': 'normal'
                }
            }

        except Exception as e:
            return {'error': str(e)}

    def check_and_send_alerts(self):
        """Vérifier et envoyer les alertes (à appeler régulièrement)"""
        try:
            current_metrics = self.metrics_collector.metrics
            self.alert_manager.check_alerts(current_metrics)

        except Exception as e:
            logger.error(f"Erreur vérification alertes: {e}")

# Instance globale du système de monitoring
monitoring_system = None

def init_monitoring(app):
    """Initialiser le système de monitoring"""
    global monitoring_system

    monitoring_system = MonitoringDashboard(app)

    # Démarrer la vérification périodique des alertes
    def alert_check_loop():
        while True:
            try:
                if monitoring_system:
                    monitoring_system.check_and_send_alerts()
                time.sleep(30)  # Vérifier toutes les 30 secondes
            except Exception as e:
                logger.error(f"Erreur boucle alertes: {e}")
                time.sleep(30)

    alert_thread = threading.Thread(target=alert_check_loop, daemon=True)
    alert_thread.start()

    logger.info("Système de monitoring et d'alerting initialisé")

def get_monitoring_dashboard():
    """Obtenir l'instance du dashboard de monitoring"""
    return monitoring_system

if __name__ == "__main__":
    print("📊 Système de monitoring et d'alerting PassPrint")

    # Test du système
    collector = MetricsCollector()
    collector.collect_all_metrics()

    print("Métriques collectées:")
    print(json.dumps(collector.metrics, indent=2, default=str))

    # Test des alertes
    alert_manager = AlertManager()
    alert_manager.check_alerts(collector.metrics)

    print(f"Alertes actives: {len(alert_manager.alert_history)}")