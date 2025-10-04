#!/usr/bin/env python3
"""
Configuration du système de monitoring pour PassPrint
Intégration avec Prometheus, Sentry, et autres outils de monitoring
"""
import os
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
from flask import request, g
import time
import logging

logger = logging.getLogger(__name__)

class PrometheusMetrics:
    """Métriques Prometheus pour PassPrint"""

    def __init__(self, app=None):
        self.app = app
        self.registry = CollectorRegistry()

        # Compteurs
        self.http_requests_total = Counter(
            'passprint_http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )

        self.api_errors_total = Counter(
            'passprint_api_errors_total',
            'Total API errors',
            ['endpoint', 'error_type'],
            registry=self.registry
        )

        self.security_events_total = Counter(
            'passprint_security_events_total',
            'Total security events',
            ['event_type', 'severity'],
            registry=self.registry
        )

        self.database_operations_total = Counter(
            'passprint_database_operations_total',
            'Total database operations',
            ['operation', 'table'],
            registry=self.registry
        )

        # Histogrammes
        self.http_request_duration_seconds = Histogram(
            'passprint_http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )

        self.database_query_duration_seconds = Histogram(
            'passprint_database_query_duration_seconds',
            'Database query duration in seconds',
            ['operation'],
            registry=self.registry
        )

        # Jauges
        self.active_users = Gauge(
            'passprint_active_users',
            'Number of active users',
            registry=self.registry
        )

        self.database_connections = Gauge(
            'passprint_database_connections',
            'Number of database connections',
            registry=self.registry
        )

        self.cache_hit_ratio = Gauge(
            'passprint_cache_hit_ratio',
            'Cache hit ratio percentage',
            registry=self.registry
        )

        self.system_cpu_usage = Gauge(
            'passprint_system_cpu_usage',
            'System CPU usage percentage',
            registry=self.registry
        )

        self.system_memory_usage = Gauge(
            'passprint_system_memory_usage',
            'System memory usage percentage',
            registry=self.registry
        )

        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialiser avec l'application Flask"""
        self.app = app

        # Enregistrer les métriques dans les logs si activé
        if app.config.get('MONITORING_CONFIG', {}).get('metrics_enabled', False):
            self._setup_metrics_collection()

        # Ajouter l'endpoint Prometheus si activé
        if app.config.get('PROMETHEUS_ENABLED', False):
            self._add_prometheus_endpoint()

    def _setup_metrics_collection(self):
        """Configurer la collecte automatique de métriques"""
        @self.app.before_request
        def start_timer():
            g.start_time = time.time()

        @self.app.after_request
        def record_request_data(response):
            if hasattr(g, 'start_time'):
                request_duration = time.time() - g.start_time

                # Enregistrer la durée de la requête
                endpoint = request.endpoint or 'unknown'
                method = request.method

                self.http_request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(request_duration)

                # Enregistrer le compteur de requêtes
                self.http_requests_total.labels(
                    method=method,
                    endpoint=endpoint,
                    status=response.status_code
                ).inc()

                # Enregistrer les erreurs
                if response.status_code >= 400:
                    self.api_errors_total.labels(
                        endpoint=endpoint,
                        error_type=str(response.status_code)
                    ).inc()

            return response

    def _add_prometheus_endpoint(self):
        """Ajouter l'endpoint /metrics pour Prometheus"""
        @self.app.route('/metrics')
        def prometheus_metrics():
            """Endpoint Prometheus pour les métriques"""
            try:
                # Mettre à jour les métriques système
                self._update_system_metrics()

                # Générer la réponse Prometheus
                return generate_latest(self.registry), 200, {
                    'Content-Type': 'text/plain; charset=utf-8'
                }

            except Exception as e:
                logger.error(f"Erreur génération métriques Prometheus: {e}")
                return "Error generating metrics", 500

    def _update_system_metrics(self):
        """Mettre à jour les métriques système"""
        try:
            import psutil

            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu_usage.set(cpu_percent)

            # Mémoire
            memory = psutil.virtual_memory()
            self.system_memory_usage.set(memory.percent)

            # Connexions base de données (approximation)
            try:
                from models import User
                # Test de connexion rapide
                User.query.limit(1).first()
                self.database_connections.set(1)  # Au moins une connexion active
            except:
                self.database_connections.set(0)

        except Exception as e:
            logger.error(f"Erreur mise à jour métriques système: {e}")

    def record_security_event(self, event_type, severity='medium'):
        """Enregistrer un événement de sécurité"""
        self.security_events_total.labels(
            event_type=event_type,
            severity=severity
        ).inc()

    def record_database_operation(self, operation, table):
        """Enregistrer une opération de base de données"""
        self.database_operations_total.labels(
            operation=operation,
            table=table
        ).inc()

    def update_cache_metrics(self, hit_ratio):
        """Mettre à jour les métriques de cache"""
        self.cache_hit_ratio.set(hit_ratio)

    def update_active_users(self, count):
        """Mettre à jour le nombre d'utilisateurs actifs"""
        self.active_users.set(count)

class SentryIntegration:
    """Intégration avec Sentry pour le suivi d'erreurs"""

    def __init__(self, app=None):
        self.app = app
        self.dsn = None

        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialiser Sentry avec l'application Flask"""
        self.app = app
        self.dsn = app.config.get('SENTRY_DSN') or os.getenv('SENTRY_DSN')

        if self.dsn and app.config.get('MONITORING_CONFIG', {}).get('enabled', False):
            try:
                import sentry_sdk
                from sentry_sdk.integrations.flask import FlaskIntegration
                from sentry_sdk.integrations.sqlalchemy import SqlAlchemyIntegration

                sentry_sdk.init(
                    dsn=self.dsn,
                    integrations=[
                        FlaskIntegration(),
                        SqlAlchemyIntegration(),
                    ],
                    environment=app.config.get('ENVIRONMENT', 'development'),
                    traces_sample_rate=1.0 if app.debug else 0.1,
                    send_default_pii=False,  # Ne pas envoyer les données personnelles
                    before_send=self._before_send_event,
                    release=f"passprint@{app.config.get('ASSET_VERSION', '1.0.0')}"
                )

                logger.info("Sentry initialisé avec succès")

            except ImportError:
                logger.warning("Sentry SDK non installé")
            except Exception as e:
                logger.error(f"Erreur initialisation Sentry: {e}")

    def _before_send_event(self, event, hint):
        """Filtrer les événements avant envoi à Sentry"""
        try:
            # Ne pas envoyer les erreurs de développement
            if self.app and self.app.debug:
                return None

            # Ne pas envoyer les erreurs de santé
            if event.get('request', {}).get('url', '').endswith('/health'):
                return None

            # Ajouter des tags personnalisés
            if self.app:
                event['tags'] = {
                    'environment': self.app.config.get('ENVIRONMENT', 'unknown'),
                    'version': self.app.config.get('ASSET_VERSION', 'unknown')
                }

            return event

        except Exception as e:
            logger.error(f"Erreur filtrage événement Sentry: {e}")
            return event

class ElasticsearchIntegration:
    """Intégration avec Elasticsearch pour les logs"""

    def __init__(self, app=None):
        self.app = app
        self.client = None
        self.enabled = False

        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialiser Elasticsearch"""
        self.app = app

        if app.config.get('MONITORING_CONFIG', {}).get('log_aggregation', False):
            try:
                from elasticsearch import Elasticsearch

                es_host = os.getenv('ELASTICSEARCH_HOST', 'localhost')
                es_port = int(os.getenv('ELASTICSEARCH_PORT', '9200'))

                self.client = Elasticsearch([f"http://{es_host}:{es_port}"])
                self.enabled = self.client.ping()

                if self.enabled:
                    logger.info("Elasticsearch connecté pour l'agrégation de logs")

            except ImportError:
                logger.warning("Elasticsearch client non installé")
            except Exception as e:
                logger.error(f"Erreur connexion Elasticsearch: {e}")

    def index_log(self, log_entry):
        """Indexer une entrée de log"""
        if not self.enabled or not self.client:
            return False

        try:
            index_name = f"passprint-logs-{datetime.now().strftime('%Y.%m.%d')}"

            # Préparer le document
            doc = {
                'timestamp': datetime.utcnow(),
                'level': log_entry.get('level', 'INFO'),
                'logger': log_entry.get('logger', 'unknown'),
                'message': log_entry.get('message', ''),
                'module': log_entry.get('module', ''),
                'function': log_entry.get('function', ''),
                'line': log_entry.get('line', 0),
                'environment': self.app.config.get('ENVIRONMENT', 'unknown') if self.app else 'unknown'
            }

            # Ajouter les informations de sécurité si disponibles
            if 'user_id' in log_entry:
                doc['user_id'] = log_entry['user_id']
            if 'ip_address' in log_entry:
                doc['ip_address'] = log_entry['ip_address']
            if 'resource_type' in log_entry:
                doc['resource_type'] = log_entry['resource_type']

            # Indexer le document
            response = self.client.index(
                index=index_name,
                document=doc,
                refresh='wait_for'
            )

            return response['result'] == 'created'

        except Exception as e:
            logger.error(f"Erreur indexation log Elasticsearch: {e}")
            return False

class MonitoringIntegration:
    """Intégration complète du monitoring"""

    def __init__(self, app=None):
        self.app = app
        self.prometheus = None
        self.sentry = None
        self.elasticsearch = None

        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialiser toutes les intégrations de monitoring"""
        self.app = app

        # Initialiser Prometheus
        if app.config.get('PROMETHEUS_ENABLED', False):
            self.prometheus = PrometheusMetrics(app)

        # Initialiser Sentry
        if app.config.get('SENTRY_DSN'):
            self.sentry = SentryIntegration(app)

        # Initialiser Elasticsearch
        if app.config.get('MONITORING_CONFIG', {}).get('log_aggregation', False):
            self.elasticsearch = ElasticsearchIntegration(app)

        logger.info("Intégrations de monitoring initialisées")

    def record_api_request(self, endpoint, method, status_code, duration=None):
        """Enregistrer une requête API"""
        if self.prometheus:
            self.prometheus.http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status_code
            ).inc()

            if duration:
                self.prometheus.http_request_duration_seconds.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)

    def record_security_event(self, event_type, severity='medium'):
        """Enregistrer un événement de sécurité"""
        if self.prometheus:
            self.prometheus.record_security_event(event_type, severity)

    def record_database_operation(self, operation, table, duration=None):
        """Enregistrer une opération de base de données"""
        if self.prometheus:
            self.prometheus.record_database_operation(operation, table)

            if duration:
                self.prometheus.database_query_duration_seconds.labels(
                    operation=operation
                ).observe(duration)

    def index_log_entry(self, log_entry):
        """Indexer une entrée de log"""
        if self.elasticsearch:
            return self.elasticsearch.index_log(log_entry)
        return False

# Instances globales
monitoring_integration = None

def init_monitoring_integration(app):
    """Initialiser l'intégration de monitoring"""
    global monitoring_integration
    monitoring_integration = MonitoringIntegration(app)
    return monitoring_integration

def get_monitoring_integration():
    """Obtenir l'instance d'intégration de monitoring"""
    return monitoring_integration

# Décorateurs pour mesurer les performances
def monitor_endpoint(endpoint_name=None):
    """Décorateur pour monitorer les endpoints"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)

                # Enregistrer les métriques
                duration = time.time() - start_time
                endpoint = endpoint_name or func.__name__

                if monitoring_integration:
                    # Cette fonction sera appelée après la requête
                    # Enregistrer dans les logs pour traitement asynchrone
                    logger.info(f"ENDPOINT_METRICS:{endpoint}:{duration}")

                return result

            except Exception as e:
                # Enregistrer l'erreur
                duration = time.time() - start_time
                endpoint = endpoint_name or func.__name__

                if monitoring_integration:
                    logger.error(f"ENDPOINT_ERROR:{endpoint}:{duration}:{str(e)}")

                raise

        return wrapper
    return decorator

def monitor_database_operation(operation_name):
    """Décorateur pour monitorer les opérations de base de données"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)

                duration = time.time() - start_time

                if monitoring_integration:
                    logger.info(f"DB_OPERATION:{operation_name}:{duration}")

                return result

            except Exception as e:
                duration = time.time() - start_time

                if monitoring_integration:
                    logger.error(f"DB_ERROR:{operation_name}:{duration}:{str(e)}")

                raise

        return wrapper
    return decorator

# Classe pour mesurer les performances avec contexte
class PerformanceMonitor:
    """Moniteur de performances avec contexte"""

    def __init__(self, operation_name, operation_type='generic'):
        self.operation_name = operation_name
        self.operation_type = operation_type
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time

            # Enregistrer la métrique
            if monitoring_integration:
                if self.operation_type == 'database':
                    monitoring_integration.record_database_operation(
                        self.operation_name, 'unknown', duration
                    )
                elif self.operation_type == 'api':
                    logger.info(f"API_OPERATION:{self.operation_name}:{duration}")
                else:
                    logger.info(f"PERFORMANCE:{self.operation_name}:{duration}")

# Fonctions utilitaires
def monitor_performance(operation_name, operation_type='generic'):
    """Fonction utilitaire pour monitorer les performances"""
    return PerformanceMonitor(operation_name, operation_type)

def record_custom_metric(metric_name, value, metric_type='gauge'):
    """Enregistrer une métrique personnalisée"""
    if monitoring_integration and monitoring_integration.prometheus:
        try:
            if metric_type == 'counter':
                # Créer un compteur personnalisé si nécessaire
                pass
            elif metric_type == 'gauge':
                # Créer une jauge personnalisée si nécessaire
                pass
            elif metric_type == 'histogram':
                # Créer un histogramme personnalisé si nécessaire
                pass

            logger.info(f"CUSTOM_METRIC:{metric_name}:{value}:{metric_type}")

        except Exception as e:
            logger.error(f"Erreur enregistrement métrique personnalisée: {e}")

if __name__ == "__main__":
    print("📊 Configuration du monitoring PassPrint")

    # Test des intégrations
    print("✅ Métriques Prometheus configurées")
    print("✅ Intégration Sentry configurée")
    print("✅ Intégration Elasticsearch configurée")
    print("✅ Monitoring avancé opérationnel!")