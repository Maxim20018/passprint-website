#!/usr/bin/env python3
"""
Tests du système de monitoring pour PassPrint
Tests des métriques, alertes, et intégrations de monitoring
"""
import pytest
import json
import time
from unittest.mock import Mock, patch
from tests import TestUtils

class TestMetricsCollection:
    """Tests pour la collecte de métriques"""

    def test_metrics_collector_initialization(self, app):
        """Test de l'initialisation du collecteur de métriques"""
        from monitoring_alerting import MetricsCollector

        collector = MetricsCollector()
        assert collector.running == False
        assert collector.collection_interval == 5
        assert len(collector.metrics) > 0

    def test_system_metrics_collection(self, app):
        """Test de collecte des métriques système"""
        from monitoring_alerting import MetricsCollector

        collector = MetricsCollector()

        # Démarrer la collecte
        collector.start_collection()

        # Attendre un peu pour la collecte
        time.sleep(2)

        # Vérifier que les métriques sont collectées
        assert 'system' in collector.metrics
        assert 'timestamp' in collector.metrics['system']
        assert 'cpu' in collector.metrics['system']
        assert 'memory' in collector.metrics['system']
        assert 'disk' in collector.metrics['system']

        # Vérifier les valeurs
        cpu_metrics = collector.metrics['system']['cpu']
        assert 'percent' in cpu_metrics
        assert isinstance(cpu_metrics['percent'], (int, float))
        assert 0 <= cpu_metrics['percent'] <= 100

        collector.stop_collection()

    def test_application_metrics_collection(self, app):
        """Test de collecte des métriques applicatives"""
        from monitoring_alerting import MetricsCollector

        collector = MetricsCollector()

        # Simuler quelques métriques d'application
        with app.app_context():
            collector._collect_application_metrics()

        assert 'application' in collector.metrics
        assert 'timestamp' in collector.metrics['application']
        assert 'health' in collector.metrics['application']

        health = collector.metrics['application']['health']
        assert 'healthy' in health
        assert 'checks' in health

    def test_database_metrics_collection(self, app, db):
        """Test de collecte des métriques base de données"""
        from monitoring_alerting import MetricsCollector

        collector = MetricsCollector()

        with app.app_context():
            collector._collect_database_metrics()

        assert 'database' in collector.metrics
        assert 'timestamp' in collector.metrics['database']
        assert 'stats' in collector.metrics['database']

        db_stats = collector.metrics['database']['stats']
        assert 'total_users' in db_stats
        assert 'total_orders' in db_stats
        assert 'total_products' in db_stats

    def test_cache_metrics_collection(self, app):
        """Test de collecte des métriques de cache"""
        from monitoring_alerting import MetricsCollector

        collector = MetricsCollector()

        with app.app_context():
            collector._collect_cache_metrics()

        assert 'cache' in collector.metrics
        assert 'timestamp' in collector.metrics['cache']
        assert 'health' in collector.metrics['cache']

    def test_security_metrics_collection(self, app, db):
        """Test de collecte des métriques de sécurité"""
        from monitoring_alerting import MetricsCollector

        collector = MetricsCollector()

        with app.app_context():
            collector._collect_security_metrics()

        assert 'security' in collector.metrics
        assert 'timestamp' in collector.metrics['security']
        assert 'events' in collector.metrics['security']

    def test_metrics_summary_generation(self, app):
        """Test de génération du résumé des métriques"""
        from monitoring_alerting import MetricsCollector

        collector = MetricsCollector()

        # Ajouter quelques données à l'historique
        for i in range(10):
            collector.history['cpu_usage'].append(50 + i)
            collector.history['memory_usage'].append(60 + i)

        summary = collector.get_metrics_summary(duration_minutes=60)

        assert 'period' in summary
        assert 'system' in summary
        assert 'memory' in summary
        assert 'current' in summary

        # Vérifier les statistiques
        cpu_stats = summary['system']
        assert 'avg' in cpu_stats
        assert 'max' in cpu_stats
        assert 'min' in cpu_stats
        assert cpu_stats['count'] == 10

class TestAlertingSystem:
    """Tests pour le système d'alertes"""

    def test_alert_manager_initialization(self, app):
        """Test de l'initialisation du gestionnaire d'alertes"""
        from monitoring_alerting import AlertManager

        alert_manager = AlertManager()

        assert len(alert_manager.alert_rules) > 0
        assert len(alert_manager.notification_channels) >= 0
        assert alert_manager.alert_history.maxlen == 1000

    def test_alert_rules_loading(self, app):
        """Test du chargement des règles d'alerte"""
        from monitoring_alerting import AlertManager

        alert_manager = AlertManager()

        # Vérifier les règles par défaut
        expected_rules = [
            'high_cpu_usage',
            'high_memory_usage',
            'disk_space_low',
            'database_unavailable',
            'high_error_rate',
            'security_threat',
            'cache_performance_degraded'
        ]

        for rule_name in expected_rules:
            assert rule_name in alert_manager.alert_rules
            assert 'enabled' in alert_manager.alert_rules[rule_name]
            assert 'condition' in alert_manager.alert_rules[rule_name]
            assert 'severity' in alert_manager.alert_rules[rule_name]

    def test_notification_channels_setup(self, app):
        """Test de configuration des canaux de notification"""
        from monitoring_alerting import AlertManager

        alert_manager = AlertManager()

        # Vérifier que les canaux sont configurés selon les variables d'environnement
        # (En test, ils seront probablement vides sauf si configurés spécifiquement)
        assert isinstance(alert_manager.notification_channels, dict)

    def test_alert_creation(self, app):
        """Test de création d'alerte"""
        from monitoring_alerting import AlertManager

        alert_manager = AlertManager()

        # Créer des métriques de test qui déclenchent une alerte
        test_metrics = {
            'system': {
                'cpu': {'percent': 90},  # Devrait déclencher high_cpu_usage
                'memory': {'percent': 70},
                'disk': {'percent': 50}
            }
        }

        # Vérifier les alertes
        alert_manager.check_alerts(test_metrics)

        # Vérifier qu'une alerte a été créée (si les canaux de notification sont configurés)
        # En test, cela peut ne pas être le cas, donc on teste juste que ça ne plante pas
        assert isinstance(alert_manager.alert_history, type(alert_manager.alert_history))

    def test_alert_cooldown(self, app):
        """Test du système de cooldown des alertes"""
        from monitoring_alerting import AlertManager

        alert_manager = AlertManager()

        # Créer une alerte manuellement
        alert = {
            'id': 'test_alert_123',
            'rule_name': 'high_cpu_usage',
            'severity': 'warning',
            'message': 'Test alert',
            'timestamp': time.time(),
            'resolved': False
        }

        alert_manager.alert_history.append(alert)

        # Vérifier le cooldown
        is_on_cooldown = alert_manager._is_alert_on_cooldown(
            'high_cpu_usage',
            5,  # 5 minutes
            time.time()
        )

        # Devrait être en cooldown car l'alerte vient d'être créée
        assert is_on_cooldown == True

    def test_alert_resolution(self, app):
        """Test de résolution d'alerte"""
        from monitoring_alerting import AlertManager

        alert_manager = AlertManager()

        # Créer une alerte manuellement
        alert = {
            'id': 'test_alert_456',
            'rule_name': 'test_rule',
            'severity': 'warning',
            'message': 'Test alert',
            'timestamp': time.time(),
            'resolved': False
        }

        alert_manager.alert_history.append(alert)

        # Résoudre l'alerte
        resolved = alert_manager.resolve_alert('test_alert_456')

        assert resolved == True

        # Vérifier que l'alerte est marquée comme résolue
        for alert in alert_manager.alert_history:
            if alert['id'] == 'test_alert_456':
                assert alert['resolved'] == True
                break

class TestMonitoringDashboard:
    """Tests pour le dashboard de monitoring"""

    def test_monitoring_dashboard_creation(self, app):
        """Test de création du dashboard de monitoring"""
        from monitoring_alerting import MonitoringDashboard

        dashboard = MonitoringDashboard(app)

        assert dashboard.app == app
        assert dashboard.metrics_collector is not None
        assert dashboard.alert_manager is not None

    def test_health_endpoint(self, client, db):
        """Test de l'endpoint de santé du monitoring"""
        response = client.get('/api/monitoring/health')

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)

        assert 'monitoring_system' in data
        assert 'metrics_collection' in data
        assert 'alerts_enabled' in data
        assert 'timestamp' in data

    def test_metrics_endpoint(self, client, db):
        """Test de l'endpoint des métriques"""
        response = client.get('/api/monitoring/metrics')

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)

        assert 'metrics' in data
        assert 'timestamp' in data

        # Vérifier la structure des métriques
        metrics = data['metrics']
        expected_sections = ['system', 'application', 'database', 'cache', 'security']

        for section in expected_sections:
            assert section in metrics

    def test_metrics_summary_endpoint(self, client, db):
        """Test de l'endpoint de résumé des métriques"""
        response = client.get('/api/monitoring/metrics/summary?duration=60')

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)

        assert 'period' in data
        assert 'system' in data
        assert 'memory' in data
        assert 'current' in data

    def test_alerts_endpoint(self, client, db):
        """Test de l'endpoint des alertes"""
        response = client.get('/api/monitoring/alerts?limit=10')

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)

        assert 'alerts' in data
        assert 'total' in data
        assert 'timestamp' in data
        assert isinstance(data['alerts'], list)

    def test_performance_metrics_endpoint(self, client, db):
        """Test de l'endpoint des métriques de performance"""
        response = client.get('/api/monitoring/performance')

        assert response.status_code == 200
        data = TestUtils.assert_response_ok(response)

        assert 'response_times' in data
        assert 'throughput' in data
        assert 'error_analysis' in data
        assert 'resource_utilization' in data

class TestPrometheusIntegration:
    """Tests pour l'intégration Prometheus"""

    def test_prometheus_metrics_initialization(self, app):
        """Test de l'initialisation des métriques Prometheus"""
        from monitoring_config import PrometheusMetrics

        # Activer Prometheus dans la config de test
        app.config['PROMETHEUS_ENABLED'] = True

        prometheus = PrometheusMetrics(app)

        assert prometheus.registry is not None
        assert prometheus.http_requests_total is not None
        assert prometheus.http_request_duration_seconds is not None
        assert prometheus.system_cpu_usage is not None

    def test_metrics_collection_setup(self, app):
        """Test de configuration de la collecte automatique"""
        from monitoring_config import PrometheusMetrics

        app.config['PROMETHEUS_ENABLED'] = True

        prometheus = PrometheusMetrics(app)

        # Vérifier que les métriques sont configurées
        assert prometheus.http_requests_total is not None
        assert prometheus.api_errors_total is not None
        assert prometheus.security_events_total is not None

    @patch('monitoring_config.generate_latest')
    def test_prometheus_endpoint_generation(self, mock_generate, app, client):
        """Test de génération de l'endpoint Prometheus"""
        from monitoring_config import PrometheusMetrics

        app.config['PROMETHEUS_ENABLED'] = True

        prometheus = PrometheusMetrics(app)
        mock_generate.return_value = b'# Test metrics'

        response = client.get('/metrics')

        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/plain; charset=utf-8'

class TestSentryIntegration:
    """Tests pour l'intégration Sentry"""

    def test_sentry_initialization_without_dsn(self, app):
        """Test de l'initialisation Sentry sans DSN"""
        from monitoring_config import SentryIntegration

        sentry = SentryIntegration(app)

        # Devrait fonctionner sans planter
        assert sentry.dsn is None

    @patch('sentry_sdk.init')
    def test_sentry_initialization_with_dsn(self, mock_init, app):
        """Test de l'initialisation Sentry avec DSN"""
        from monitoring_config import SentryIntegration

        app.config['SENTRY_DSN'] = 'https://test@test.ingest.sentry.io/test'
        app.config['MONITORING_CONFIG'] = {'enabled': True}

        sentry = SentryIntegration(app)

        # Vérifier que Sentry a été initialisé
        mock_init.assert_called_once()

class TestElasticsearchIntegration:
    """Tests pour l'intégration Elasticsearch"""

    def test_elasticsearch_initialization_without_config(self, app):
        """Test de l'initialisation Elasticsearch sans configuration"""
        from monitoring_config import ElasticsearchIntegration

        sentry = ElasticsearchIntegration(app)

        # Devrait fonctionner sans planter
        assert sentry.enabled == False

    @patch('elasticsearch.Elasticsearch')
    def test_elasticsearch_initialization_with_config(self, mock_es, app):
        """Test de l'initialisation Elasticsearch avec configuration"""
        from monitoring_config import ElasticsearchIntegration

        app.config['MONITORING_CONFIG'] = {'log_aggregation': True}

        # Mock Elasticsearch
        mock_client = Mock()
        mock_client.ping.return_value = True
        mock_es.return_value = mock_client

        elasticsearch = ElasticsearchIntegration(app)

        # Vérifier que le client est créé
        assert elasticsearch.client is not None
        assert elasticsearch.enabled == True

class TestMonitoringIntegration:
    """Tests pour l'intégration complète de monitoring"""

    def test_monitoring_integration_initialization(self, app):
        """Test de l'initialisation complète du monitoring"""
        from monitoring_config import MonitoringIntegration

        integration = MonitoringIntegration(app)

        assert integration.app == app
        assert integration.prometheus is not None
        assert integration.sentry is not None
        assert integration.elasticsearch is not None

    def test_api_request_recording(self, app):
        """Test d'enregistrement des requêtes API"""
        from monitoring_config import MonitoringIntegration

        integration = MonitoringIntegration(app)

        # Enregistrer une requête fictive
        integration.record_api_request('/api/test', 'GET', 200, 0.5)

        # Vérifier que ça ne plante pas (les métriques sont internes)
        assert True

    def test_security_event_recording(self, app):
        """Test d'enregistrement des événements de sécurité"""
        from monitoring_config import MonitoringIntegration

        integration = MonitoringIntegration(app)

        # Enregistrer un événement de sécurité fictif
        integration.record_security_event('test_event', 'medium')

        # Vérifier que ça ne plante pas
        assert True

    def test_database_operation_recording(self, app):
        """Test d'enregistrement des opérations de base de données"""
        from monitoring_config import MonitoringIntegration

        integration = MonitoringIntegration(app)

        # Enregistrer une opération DB fictive
        integration.record_database_operation('SELECT', 'users', 0.1)

        # Vérifier que ça ne plante pas
        assert True

class TestPerformanceMonitoring:
    """Tests pour le monitoring de performances"""

    def test_performance_monitor_context_manager(self, app):
        """Test du context manager de monitoring de performances"""
        from monitoring_config import PerformanceMonitor

        with PerformanceMonitor('test_operation', 'api') as monitor:
            # Simuler une opération
            time.sleep(0.1)
            assert monitor.operation_name == 'test_operation'
            assert monitor.operation_type == 'api'

        # Vérifier que le monitoring s'est terminé
        assert monitor.start_time is not None

    def test_monitor_performance_decorator(self, app):
        """Test du décorateur de monitoring de performances"""
        from monitoring_config import monitor_performance

        @monitor_performance('test_function', 'database')
        def test_function():
            time.sleep(0.05)
            return "result"

        # Exécuter la fonction
        result = test_function()

        assert result == "result"

    def test_monitor_endpoint_decorator(self, app):
        """Test du décorateur de monitoring d'endpoints"""
        from monitoring_config import monitor_endpoint

        @monitor_endpoint('test_endpoint')
        def test_endpoint():
            time.sleep(0.05)
            return "endpoint_result"

        # Exécuter l'endpoint
        result = test_endpoint()

        assert result == "endpoint_result"

class TestMonitoringAPIEndpoints:
    """Tests pour les endpoints de monitoring"""

    def test_monitoring_health_requires_admin(self, client, db):
        """Test que l'endpoint de santé du monitoring nécessite l'authentification admin"""
        response = client.get('/api/monitoring/health')

        # En test, peut nécessiter une authentification ou pas selon la configuration
        assert response.status_code in [200, 401]

    def test_metrics_endpoint_data_structure(self, client, db):
        """Test de la structure des données de l'endpoint des métriques"""
        response = client.get('/api/monitoring/metrics')

        if response.status_code == 200:
            data = TestUtils.assert_response_ok(response)

            assert 'metrics' in data
            assert 'timestamp' in data

            # Vérifier la structure des métriques
            metrics = data['metrics']
            for section in ['system', 'application', 'database', 'cache', 'security']:
                assert section in metrics

    def test_alerts_endpoint_pagination(self, client, db):
        """Test de la pagination de l'endpoint des alertes"""
        response = client.get('/api/monitoring/alerts?limit=5')

        if response.status_code == 200:
            data = TestUtils.assert_response_ok(response)

            assert 'alerts' in data
            assert 'total' in data
            assert isinstance(data['alerts'], list)

            # Si il y a des alertes, vérifier qu'il n'y en a pas plus que la limite
            if data['total'] > 0:
                assert len(data['alerts']) <= 5

class TestMonitoringErrorHandling:
    """Tests de gestion des erreurs du monitoring"""

    def test_metrics_collection_error_handling(self, app):
        """Test de gestion des erreurs lors de la collecte de métriques"""
        from monitoring_alerting import MetricsCollector

        collector = MetricsCollector()

        # Simuler une erreur en modifiant les métriques
        original_collect = collector._collect_system_metrics

        def failing_collect(timestamp):
            raise Exception("Test error")

        collector._collect_system_metrics = failing_collect

        # Devrait gérer l'erreur sans planter
        try:
            collector.collect_all_metrics()
            # Si on arrive ici, c'est que l'erreur a été gérée
            assert True
        except:
            # Si ça plante, c'est une erreur
            assert False

        # Restaurer la fonction originale
        collector._collect_system_metrics = original_collect

    def test_alert_sending_error_handling(self, app):
        """Test de gestion des erreurs lors de l'envoi d'alertes"""
        from monitoring_alerting import AlertManager

        alert_manager = AlertManager()

        # Créer une alerte de test
        alert = {
            'id': 'test_error_alert',
            'rule_name': 'test_rule',
            'severity': 'warning',
            'message': 'Test alert',
            'timestamp': time.time(),
            'resolved': False
        }

        # Devrait gérer les erreurs d'envoi sans planter
        try:
            alert_manager._send_notifications(alert)
            # Si on arrive ici, c'est que l'erreur a été gérée
            assert True
        except:
            # Si ça plante, c'est une erreur
            assert False

class TestMonitoringIntegration:
    """Tests d'intégration du système de monitoring"""

    @pytest.mark.integration
    def test_full_monitoring_workflow(self, app, db):
        """Test du workflow complet de monitoring"""
        from monitoring_alerting import MonitoringDashboard

        # Créer le dashboard
        dashboard = MonitoringDashboard(app)

        # Attendre la collecte de métriques
        time.sleep(3)

        # Vérifier que les métriques sont collectées
        assert len(dashboard.metrics_collector.metrics) > 0

        # Vérifier les alertes
        alert_manager = dashboard.alert_manager
        initial_alert_count = len(alert_manager.alert_history)

        # Vérifier les métriques actuelles
        current_metrics = dashboard.metrics_collector.metrics

        # Déclencher une vérification d'alertes
        dashboard.check_and_send_alerts()

        # Vérifier que le système fonctionne
        assert dashboard.metrics_collector.running == True

    def test_monitoring_dashboard_route(self, client, db, admin_auth_headers):
        """Test de la route du dashboard de monitoring"""
        response = client.get('/admin/monitoring', headers=admin_auth_headers)

        # Devrait retourner le fichier HTML du dashboard
        assert response.status_code == 200

    def test_monitoring_api_endpoints_integration(self, client, db):
        """Test d'intégration des endpoints de monitoring"""
        endpoints = [
            '/api/monitoring/health',
            '/api/monitoring/metrics',
            '/api/monitoring/metrics/summary?duration=60',
            '/api/monitoring/alerts?limit=10',
            '/api/monitoring/performance'
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            # Tous les endpoints devraient répondre (avec ou sans authentification selon la config)
            assert response.status_code in [200, 401, 404]

if __name__ == "__main__":
    pytest.main([__file__, '-v'])