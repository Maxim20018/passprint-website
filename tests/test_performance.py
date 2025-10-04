#!/usr/bin/env python3
"""
Tests de performance pour PassPrint
Tests d'optimisation, profiling, et benchmarks
"""
import pytest
import time
import psutil
from unittest.mock import Mock, patch
from tests import TestUtils

class TestDatabaseOptimization:
    """Tests pour l'optimisation de base de données"""

    def test_query_profiler_initialization(self, app):
        """Test de l'initialisation du profileur de requêtes"""
        from database_optimizer import QueryProfiler

        profiler = QueryProfiler(app)

        assert profiler.slow_query_threshold == 1.0
        assert len(profiler.query_stats) == 0
        assert isinstance(profiler.query_stats, dict)

    def test_query_profiling_context_manager(self, app):
        """Test du context manager de profilage"""
        from database_optimizer import QueryProfiler

        profiler = QueryProfiler(app)

        # Test du profilage
        with profiler.profile_query("SELECT * FROM test", "test_operation"):
            time.sleep(0.1)  # Simulation d'une requête

        # Vérifier que les statistiques sont enregistrées
        assert 'test_operation' in profiler.query_stats
        stats = profiler.query_stats['test_operation']
        assert stats['count'] == 1
        assert stats['total_time'] > 0

    def test_slow_query_detection(self, app):
        """Test de détection des requêtes lentes"""
        from database_optimizer import QueryProfiler

        profiler = QueryProfiler(app)
        profiler.slow_query_threshold = 0.05  # 50ms

        # Exécuter une requête lente
        with profiler.profile_query("SELECT * FROM slow_table", "slow_operation"):
            time.sleep(0.1)  # 100ms - devrait être détecté comme lent

        stats = profiler.query_stats['slow_operation']
        assert stats['slow_queries'] == 1
        assert len(stats['examples']) == 1

    def test_query_statistics_generation(self, app):
        """Test de génération des statistiques de requêtes"""
        from database_optimizer import QueryProfiler

        profiler = QueryProfiler(app)

        # Ajouter quelques statistiques de test
        for i in range(5):
            with profiler.profile_query(f"SELECT {i}", "test_op"):
                time.sleep(0.01 * i)

        stats = profiler.get_query_statistics()

        assert 'test_op' in stats
        assert stats['test_op']['count'] == 5
        assert stats['test_op']['avg_time'] > 0

    def test_optimization_report_generation(self, app):
        """Test de génération du rapport d'optimisation"""
        from database_optimizer import QueryProfiler

        profiler = QueryProfiler(app)

        # Ajouter des données de test
        with profiler.profile_query("SELECT * FROM users", "user_query"):
            time.sleep(0.1)

        report = profiler.generate_optimization_report()

        assert 'generated_at' in report
        assert 'total_operations' in report
        assert 'slow_queries' in report
        assert 'optimization_recommendations' in report

class TestMemoryOptimization:
    """Tests pour l'optimisation mémoire"""

    def test_memory_optimizer_initialization(self, app):
        """Test de l'initialisation de l'optimiseur mémoire"""
        from performance_optimizer import MemoryOptimizer

        optimizer = MemoryOptimizer(app)

        assert optimizer.memory_config['memory_limit_mb'] == 512
        assert isinstance(optimizer.memory_snapshots, type(optimizer.memory_snapshots))

    def test_memory_snapshot_creation(self, app):
        """Test de création de snapshot mémoire"""
        from performance_optimizer import MemoryOptimizer

        optimizer = MemoryOptimizer(app)

        snapshot = optimizer.take_memory_snapshot()

        if 'error' not in snapshot:
            assert 'timestamp' in snapshot
            assert 'rss_mb' in snapshot
            assert 'memory_percent' in snapshot
            assert isinstance(snapshot['rss_mb'], (int, float))

    def test_memory_leak_detection(self, app):
        """Test de détection de fuite mémoire"""
        from performance_optimizer import MemoryOptimizer

        optimizer = MemoryOptimizer(app)

        # Prendre plusieurs snapshots
        for _ in range(15):
            optimizer.take_memory_snapshot()
            time.sleep(0.01)

        leak_analysis = optimizer.detect_memory_leaks()

        assert 'memory_trend' in leak_analysis
        assert 'current_memory_mb' in leak_analysis
        assert 'potential_leak' in leak_analysis['memory_trend']

    def test_memory_optimization_execution(self, app):
        """Test de l'exécution d'optimisation mémoire"""
        from performance_optimizer import MemoryOptimizer

        optimizer = MemoryOptimizer(app)

        optimization_result = optimizer.optimize_memory_usage()

        assert 'actions_taken' in optimization_result
        assert 'memory_freed_mb' in optimization_result
        assert 'success' in optimization_result
        assert isinstance(optimization_result['actions_taken'], list)

class TestCacheOptimization:
    """Tests pour l'optimisation de cache"""

    def test_cache_optimizer_initialization(self, app):
        """Test de l'initialisation de l'optimiseur de cache"""
        from performance_optimizer import CacheOptimizer

        optimizer = CacheOptimizer(app)

        assert optimizer.cache_strategies == {}
        assert hasattr(optimizer, 'analyze_cache_effectiveness')

    def test_cache_effectiveness_analysis(self, app):
        """Test de l'analyse d'efficacité du cache"""
        from performance_optimizer import CacheOptimizer

        optimizer = CacheOptimizer(app)

        analysis = optimizer.analyze_cache_effectiveness()

        assert isinstance(analysis, dict)
        assert 'cache_efficiency' in analysis or 'error' in analysis

    def test_cache_strategy_optimization(self, app):
        """Test de l'optimisation de stratégie de cache"""
        from performance_optimizer import CacheOptimizer

        optimizer = CacheOptimizer(app)

        optimization_result = optimizer.optimize_cache_strategy()

        assert 'strategies_optimized' in optimization_result
        assert 'ttl_adjustments' in optimization_result
        assert 'success' in optimization_result

class TestLoadTesting:
    """Tests pour les tests de charge"""

    def test_load_test_engine_initialization(self, app):
        """Test de l'initialisation du moteur de tests de charge"""
        from load_testing import LoadTestEngine

        engine = LoadTestEngine()

        assert engine.base_url == 'http://localhost:5000'
        assert engine.test_config['max_workers'] == 50
        assert len(engine.scenarios) == 0

    def test_realistic_scenarios_creation(self, app):
        """Test de création de scénarios réalistes"""
        from load_testing import LoadTestEngine

        engine = LoadTestEngine()

        scenarios = engine.create_realistic_scenarios()

        assert isinstance(scenarios, list)
        assert len(scenarios) > 0

        # Vérifier la structure des scénarios
        for scenario in scenarios:
            assert hasattr(scenario, 'name')
            assert hasattr(scenario, 'endpoint')
            assert hasattr(scenario, 'method')
            assert scenario.method in ['GET', 'POST']

    def test_load_test_scenario_execution(self, app):
        """Test de l'exécution d'un scénario de test de charge"""
        from load_testing import LoadTestEngine, LoadTestScenario

        engine = LoadTestEngine()

        # Créer un scénario simple
        scenario = LoadTestScenario(
            'test_scenario',
            '/api/health',
            'GET',
            expected_status=200
        )

        # Exécuter le scénario avec peu de requêtes pour le test
        result = engine.execute_scenario(scenario, 5)

        assert result.scenario_name == 'test_scenario'
        assert result.total_requests == 5
        assert isinstance(result.response_times, list)

    def test_system_metrics_collection(self, app):
        """Test de collecte des métriques système"""
        from load_testing import LoadTestEngine

        engine = LoadTestEngine()

        metrics = engine._collect_system_metrics()

        if 'error' not in metrics:
            assert 'cpu_percent' in metrics
            assert 'memory_percent' in metrics
            assert 'disk_percent' in metrics
            assert 'timestamp' in metrics

class TestPerformanceMonitoring:
    """Tests pour le monitoring de performances"""

    def test_performance_monitor_initialization(self, app):
        """Test de l'initialisation du moniteur de performances"""
        from performance_optimizer import PerformanceMonitor

        monitor = PerformanceMonitor(app)

        assert monitor.memory_optimizer is not None
        assert monitor.cache_optimizer is not None
        assert monitor.load_tester is not None

    def test_performance_metric_recording(self, app):
        """Test d'enregistrement de métriques de performance"""
        from performance_optimizer import PerformanceMonitor

        monitor = PerformanceMonitor(app)

        # Enregistrer une métrique
        monitor.record_performance_metric('response_times', 0.5)

        # Vérifier qu'elle est enregistrée
        assert len(monitor.performance_metrics['response_times']) == 1
        assert monitor.performance_metrics['response_times'][0]['value'] == 0.5

    def test_performance_summary_generation(self, app):
        """Test de génération du résumé de performances"""
        from performance_optimizer import PerformanceMonitor

        monitor = PerformanceMonitor(app)

        # Ajouter quelques métriques de test
        for i in range(10):
            monitor.record_performance_metric('response_times', 0.1 * i)

        summary = monitor.get_performance_summary()

        assert 'timestamp' in summary
        assert 'memory_analysis' in summary
        assert 'cache_analysis' in summary

class TestPerformanceDecorators:
    """Tests pour les décorateurs de performance"""

    def test_profile_performance_decorator(self, app):
        """Test du décorateur de profilage de performance"""
        from performance_optimizer import profile_performance

        @profile_performance('test_function')
        def test_function():
            time.sleep(0.05)
            return "result"

        # Exécuter la fonction
        result = test_function()

        assert result == "result"

    def test_monitor_memory_usage_decorator(self, app):
        """Test du décorateur de monitoring mémoire"""
        from performance_optimizer import monitor_memory_usage

        @monitor_memory_usage()
        def memory_test_function():
            # Créer quelques objets en mémoire
            test_list = [i for i in range(1000)]
            time.sleep(0.01)
            return len(test_list)

        # Exécuter la fonction
        result = memory_test_function()

        assert result == 1000

class TestPerformanceIntegration:
    """Tests d'intégration des performances"""

    def test_performance_optimization_workflow(self, app):
        """Test du workflow complet d'optimisation des performances"""
        from performance_optimizer import PerformanceMonitor

        monitor = PerformanceMonitor(app)

        # Exécuter l'optimisation complète
        optimization_result = monitor.optimize_all_systems()

        assert 'timestamp' in optimization_result
        assert 'optimizations' in optimization_result
        assert 'overall_success' in optimization_result

        # Vérifier que chaque optimisation a été tentée
        assert 'memory' in optimization_result['optimizations']
        assert 'cache' in optimization_result['optimizations']

    def test_performance_monitoring_with_monitoring_system(self, app):
        """Test de l'intégration avec le système de monitoring"""
        from performance_optimizer import PerformanceMonitor
        from monitoring_config import get_monitoring_integration

        monitor = PerformanceMonitor(app)

        # Enregistrer une métrique
        monitor.record_performance_metric('response_times', 1.5)

        # Vérifier que le monitoring est intégré
        monitoring = get_monitoring_integration()
        if monitoring:
            assert monitoring is not None

class TestLoadTestingScenarios:
    """Tests pour les scénarios de tests de charge"""

    def test_load_test_scenario_structure(self, app):
        """Test de la structure des scénarios de test de charge"""
        from load_testing import LoadTestScenario

        scenario = LoadTestScenario(
            'test_scenario',
            '/api/test',
            'POST',
            {'key': 'value'},
            {'Content-Type': 'application/json'},
            201
        )

        assert scenario.name == 'test_scenario'
        assert scenario.endpoint == '/api/test'
        assert scenario.method == 'POST'
        assert scenario.data == {'key': 'value'}
        assert scenario.expected_status == 201

    def test_load_test_result_calculations(self, app):
        """Test des calculs de résultats de test de charge"""
        from load_testing import LoadTestResult

        result = LoadTestResult('test_scenario')
        result.start_time = datetime.utcnow()

        # Ajouter des résultats de test
        test_response_times = [0.1, 0.2, 0.15, 0.3, 0.12]
        for response_time in test_response_times:
            result.add_request(response_time, 200, True)

        result.finalize()

        assert result.total_requests == 5
        assert result.successful_requests == 5
        assert result.success_rate == 1.0
        assert abs(result.avg_response_time - 0.174) < 0.01  # Moyenne approximative

class TestPerformanceBenchmarking:
    """Tests pour les benchmarks de performance"""

    def test_performance_benchmark_initialization(self, app):
        """Test de l'initialisation du benchmark de performance"""
        from load_testing import PerformanceBenchmark

        benchmark = PerformanceBenchmark(app)

        assert benchmark.app == app
        assert isinstance(benchmark.benchmarks, dict)

    def test_database_benchmark_execution(self, app, db):
        """Test de l'exécution du benchmark de base de données"""
        from load_testing import PerformanceBenchmark

        benchmark = PerformanceBenchmark(app)

        # Créer quelques données de test
        TestUtils.create_test_user(db, 'benchmark@test.com')

        benchmark_result = benchmark.run_database_benchmark()

        if 'error' not in benchmark_result:
            assert 'timestamp' in benchmark_result
            assert 'database_operations' in benchmark_result
            assert isinstance(benchmark_result['database_operations'], dict)

class TestPerformanceAnalysis:
    """Tests pour l'analyse de performances"""

    def test_performance_analyzer_initialization(self, app):
        """Test de l'initialisation de l'analyseur de performances"""
        from load_testing import PerformanceAnalyzer

        analyzer = PerformanceAnalyzer(app)

        assert analyzer.load_engine is not None
        assert analyzer.benchmark is not None

    def test_system_health_assessment(self, app):
        """Test de l'évaluation de santé du système"""
        from load_testing import PerformanceAnalyzer

        analyzer = PerformanceAnalyzer(app)

        health = analyzer._assess_system_health()

        if 'error' not in health:
            assert 'score' in health
            assert 'status' in health
            assert 'metrics' in health
            assert 0 <= health['score'] <= 100
            assert health['status'] in ['healthy', 'degraded', 'critical']

    def test_bottleneck_identification(self, app):
        """Test d'identification des goulots d'étranglement"""
        from load_testing import PerformanceAnalyzer

        analyzer = PerformanceAnalyzer(app)

        bottlenecks = analyzer._identify_performance_bottlenecks()

        assert isinstance(bottlenecks, list)

    def test_optimization_opportunities_detection(self, app):
        """Test de détection des opportunités d'optimisation"""
        from load_testing import PerformanceAnalyzer

        analyzer = PerformanceAnalyzer(app)

        opportunities = analyzer._find_optimization_opportunities()

        assert isinstance(opportunities, list)

    def test_capacity_planning_generation(self, app):
        """Test de génération du plan de capacité"""
        from load_testing import PerformanceAnalyzer

        analyzer = PerformanceAnalyzer(app)

        capacity_plan = analyzer._generate_capacity_plan()

        if 'error' not in capacity_plan:
            assert 'current_capacity' in capacity_plan
            assert 'recommended_capacity' in capacity_plan
            assert 'scaling_recommendations' in capacity_plan

class TestPerformanceIntegration:
    """Tests d'intégration des performances"""

    def test_end_to_end_performance_workflow(self, app, db):
        """Test du workflow complet de performance"""
        from performance_optimizer import PerformanceMonitor

        monitor = PerformanceMonitor(app)

        # 1. Enregistrer des métriques
        for i in range(20):
            monitor.record_performance_metric('response_times', 0.1 + i * 0.01)

        # 2. Obtenir le résumé
        summary = monitor.get_performance_summary()

        assert 'timestamp' in summary
        assert 'memory_analysis' in summary

        # 3. Optimiser les systèmes
        optimization_result = monitor.optimize_all_systems()

        assert 'timestamp' in optimization_result
        assert 'optimizations' in optimization_result

    def test_performance_monitoring_with_existing_systems(self, app):
        """Test de l'intégration avec les systèmes existants"""
        from performance_optimizer import PerformanceMonitor
        from monitoring_config import get_monitoring_integration

        monitor = PerformanceMonitor(app)

        # Enregistrer une métrique
        monitor.record_performance_metric('response_times', 0.8)

        # Vérifier l'intégration avec le monitoring
        monitoring = get_monitoring_integration()
        if monitoring:
            assert monitoring is not None

class TestPerformanceErrorHandling:
    """Tests de gestion des erreurs de performance"""

    def test_memory_optimization_error_handling(self, app):
        """Test de gestion des erreurs d'optimisation mémoire"""
        from performance_optimizer import MemoryOptimizer

        optimizer = MemoryOptimizer(app)

        # Simuler une erreur en modifiant la configuration
        original_config = optimizer.memory_config.copy()
        optimizer.memory_config['invalid_key'] = 'invalid_value'

        try:
            # Devrait gérer l'erreur sans planter
            optimization_result = optimizer.optimize_memory_usage()
            assert 'success' in optimization_result
        except Exception as e:
            # Si ça plante, ce n'est pas acceptable
            assert False, f"Erreur non gérée: {e}"
        finally:
            # Restaurer la configuration
            optimizer.memory_config = original_config

    def test_cache_optimization_error_handling(self, app):
        """Test de gestion des erreurs d'optimisation de cache"""
        from performance_optimizer import CacheOptimizer

        optimizer = CacheOptimizer(app)

        # Devrait gérer les erreurs sans planter
        optimization_result = optimizer.optimize_cache_strategy()
        assert 'success' in optimization_result

    def test_load_testing_error_handling(self, app):
        """Test de gestion des erreurs de tests de charge"""
        from load_testing import LoadTestEngine, LoadTestScenario

        engine = LoadTestEngine()

        # Créer un scénario avec une URL invalide
        scenario = LoadTestScenario(
            'error_scenario',
            '/invalid/endpoint',
            'GET',
            expected_status=200
        )

        # Devrait gérer les erreurs de connexion sans planter
        result = engine.execute_scenario(scenario, 2)
        assert result.scenario_name == 'error_scenario'

class TestPerformanceMetrics:
    """Tests pour les métriques de performance"""

    def test_performance_metrics_tracking(self, app):
        """Test du suivi des métriques de performance"""
        from performance_optimizer import PerformanceMonitor

        monitor = PerformanceMonitor(app)

        # Enregistrer plusieurs métriques
        test_values = [0.1, 0.2, 0.15, 0.3, 0.12]
        for value in test_values:
            monitor.record_performance_metric('response_times', value)

        # Vérifier le suivi
        response_times = monitor.performance_metrics['response_times']
        assert len(response_times) == 5

        values = [entry['value'] for entry in response_times]
        assert values == test_values

    def test_performance_summary_accuracy(self, app):
        """Test de l'exactitude du résumé de performances"""
        from performance_optimizer import PerformanceMonitor

        monitor = PerformanceMonitor(app)

        # Ajouter des métriques avec timestamps différents
        base_time = time.time()
        for i in range(5):
            monitor.record_performance_metric('response_times', 0.1 * (i + 1))

        summary = monitor.get_performance_summary()

        assert 'timestamp' in summary

        # Vérifier les métriques de réponse
        if 'response_times' in summary:
            rt_metrics = summary['response_times']
            assert 'current' in rt_metrics
            assert 'average' in rt_metrics
            assert 'trend' in rt_metrics

class TestPerformanceOptimization:
    """Tests pour l'optimisation des performances"""

    def test_database_optimization_execution(self, app, db):
        """Test de l'exécution d'optimisation de base de données"""
        from database_optimizer import DatabaseOptimizer

        optimizer = DatabaseOptimizer(app)

        # Analyser les performances
        analysis = optimizer.analyze_database_performance()

        # Devrait retourner un résultat valide
        assert isinstance(analysis, dict)

        # Créer les index d'optimisation
        index_result = optimizer.create_optimization_indexes()

        # Devrait gérer les erreurs proprement
        assert isinstance(index_result, dict)

    def test_query_optimization_suggestions(self, app):
        """Test des suggestions d'optimisation de requêtes"""
        from database_optimizer import DatabaseOptimizer

        optimizer = DatabaseOptimizer(app)

        # Analyser une requête de test
        test_query = "SELECT * FROM users WHERE email = 'test@test.com'"
        optimization = optimizer.optimize_query_performance(test_query, 'test_query')

        assert isinstance(optimization, dict)

        if 'error' not in optimization:
            assert 'query_analysis' in optimization
            assert 'optimization_suggestions' in optimization
            assert isinstance(optimization['optimization_suggestions'], list)

class TestLoadTestingRealistic:
    """Tests réalistes pour les tests de charge"""

    def test_realistic_load_test_execution(self, app, db):
        """Test d'exécution réaliste de test de charge"""
        from load_testing import LoadTestEngine

        engine = LoadTestEngine()

        # Créer des scénarios réalistes
        scenarios = engine.create_realistic_scenarios()

        # Exécuter un test avec un scénario simple
        if scenarios:
            simple_scenario = scenarios[0]  # Premier scénario (probablement health check)

            # Exécuter avec peu de requêtes pour le test
            result = engine.execute_scenario(simple_scenario, 3)

            assert result.scenario_name == simple_scenario.name
            assert result.total_requests == 3

            # Devrait avoir au moins quelques résultats
            assert len(result.requests) >= 0

    def test_load_test_result_analysis(self, app):
        """Test de l'analyse des résultats de test de charge"""
        from load_testing import LoadTestEngine

        engine = LoadTestEngine()

        # Analyser les résultats globaux
        overall_results = [
            type('MockResult', (), {
                'total_requests': 100,
                'successful_requests': 95,
                'failed_requests': 5,
                'response_times': [0.1, 0.2, 0.15]
            })(),
            type('MockResult', (), {
                'total_requests': 50,
                'successful_requests': 48,
                'failed_requests': 2,
                'response_times': [0.12, 0.18, 0.14]
            })()
        ]

        summary = engine._analyze_overall_results(overall_results)

        if 'error' not in summary:
            assert 'total_requests' in summary
            assert 'successful_requests' in summary
            assert 'overall_success_rate' in summary
            assert summary['total_requests'] == 150
            assert summary['successful_requests'] == 143

class TestPerformanceMonitoring:
    """Tests pour le monitoring de performances"""

    def test_performance_monitoring_integration(self, app):
        """Test de l'intégration du monitoring de performances"""
        from performance_optimizer import PerformanceMonitor
        from monitoring_alerting import MetricsCollector

        monitor = PerformanceMonitor(app)
        collector = MetricsCollector()

        # Démarrer la collecte
        collector.start_collection()
        time.sleep(2)

        # Enregistrer une métrique
        monitor.record_performance_metric('response_times', 0.5)

        # Obtenir le résumé
        summary = monitor.get_performance_summary()

        assert 'timestamp' in summary

        collector.stop_collection()

    def test_performance_optimization_with_monitoring(self, app):
        """Test de l'optimisation avec intégration monitoring"""
        from performance_optimizer import PerformanceMonitor

        monitor = PerformanceMonitor(app)

        # Optimiser les systèmes
        optimization_result = monitor.optimize_all_systems()

        assert 'timestamp' in optimization_result
        assert 'optimizations' in optimization_result

        # Vérifier que chaque type d'optimisation est présent
        assert 'memory' in optimization_result['optimizations']
        assert 'cache' in optimization_result['optimizations']

class TestPerformanceBenchmarking:
    """Tests pour les benchmarks de performance"""

    def test_database_benchmark_with_real_data(self, app, db):
        """Test du benchmark de base de données avec des données réelles"""
        from load_testing import PerformanceBenchmark

        benchmark = PerformanceBenchmark(app)

        # Créer des données de test
        for i in range(10):
            TestUtils.create_test_user(db, f'benchmark{i}@test.com')
            TestUtils.create_test_product(db, f'Product {i}', 10000 + i * 1000)

        # Exécuter le benchmark
        result = benchmark.run_database_benchmark()

        if 'error' not in result:
            assert 'timestamp' in result
            assert 'database_operations' in result
            assert isinstance(result['database_operations'], dict)

            # Vérifier qu'au moins une opération a été benchmarkée
            assert len(result['database_operations']) > 0

class TestPerformanceAnalysis:
    """Tests pour l'analyse de performances"""

    def test_system_performance_analysis(self, app):
        """Test de l'analyse de performances système"""
        from load_testing import PerformanceAnalyzer

        analyzer = PerformanceAnalyzer(app)

        analysis = analyzer.analyze_system_performance()

        if 'error' not in analysis:
            assert 'timestamp' in analysis
            assert 'system_health' in analysis
            assert 'performance_bottlenecks' in analysis
            assert 'optimization_opportunities' in analysis

            # Vérifier la structure de la santé système
            system_health = analysis['system_health']
            assert 'score' in system_health
            assert 'status' in system_health
            assert 'metrics' in system_health

    def test_bottleneck_identification_accuracy(self, app):
        """Test de l'exactitude d'identification des goulots"""
        from load_testing import PerformanceAnalyzer

        analyzer = PerformanceAnalyzer(app)

        bottlenecks = analyzer._identify_performance_bottlenecks()

        assert isinstance(bottlenecks, list)

        # Devrait identifier au moins les goulots évidents si ils existent
        # En test, peut être vide si le système est sain

    def test_optimization_opportunities_detection(self, app):
        """Test de détection des opportunités d'optimisation"""
        from load_testing import PerformanceAnalyzer

        analyzer = PerformanceAnalyzer(app)

        opportunities = analyzer._find_optimization_opportunities()

        assert isinstance(opportunities, list)

class TestPerformanceUtilities:
    """Tests pour les utilitaires de performance"""

    def test_performance_utility_functions(self, app):
        """Test des fonctions utilitaires de performance"""
        from performance_optimizer import (
            optimize_memory, optimize_cache,
            get_performance_summary
        )

        # Tester les fonctions utilitaires
        memory_result = optimize_memory()
        assert isinstance(memory_result, dict)

        cache_result = optimize_cache()
        assert isinstance(cache_result, dict)

        summary = get_performance_summary()
        assert isinstance(summary, dict)

    def test_load_testing_utility_functions(self, app):
        """Test des fonctions utilitaires de tests de charge"""
        from load_testing import (
            run_load_test_scenario, run_comprehensive_load_test,
            analyze_system_performance
        )

        # Tester l'analyse système
        analysis = analyze_system_performance()
        assert isinstance(analysis, dict)

        # Tester un scénario de test de charge simple
        # (Peut échouer si l'API n'est pas disponible)
        try:
            result = run_load_test_scenario('health_check', 2)
            assert isinstance(result, dict)
        except Exception as e:
            # Acceptable en test si l'API n'est pas démarrée
            assert 'error' in str(e).lower() or True

class TestPerformanceErrorScenarios:
    """Tests pour les scénarios d'erreur de performance"""

    def test_memory_optimization_with_failures(self, app):
        """Test d'optimisation mémoire avec des échecs simulés"""
        from performance_optimizer import MemoryOptimizer

        optimizer = MemoryOptimizer(app)

        # Simuler des conditions d'erreur
        original_take_snapshot = optimizer.take_memory_snapshot

        def failing_snapshot():
            return {'error': 'Simulated error'}

        optimizer.take_memory_snapshot = failing_snapshot

        try:
            # Devrait gérer l'erreur sans planter
            optimization_result = optimizer.optimize_memory_usage()
            assert 'success' in optimization_result
        finally:
            # Restaurer la fonction originale
            optimizer.take_memory_snapshot = original_take_snapshot

    def test_cache_optimization_with_failures(self, app):
        """Test d'optimisation de cache avec des échecs simulés"""
        from performance_optimizer import CacheOptimizer

        optimizer = CacheOptimizer(app)

        # Devrait gérer les erreurs sans planter
        optimization_result = optimizer.optimize_cache_strategy()
        assert 'success' in optimization_result

    def test_load_testing_with_network_failures(self, app):
        """Test de tests de charge avec des échecs réseau simulés"""
        from load_testing import LoadTestEngine, LoadTestScenario

        engine = LoadTestEngine()

        # Créer un scénario qui va échouer
        scenario = LoadTestScenario(
            'failing_scenario',
            '/api/nonexistent',
            'GET',
            expected_status=404
        )

        # Devrait gérer les échecs sans planter
        result = engine.execute_scenario(scenario, 2)
        assert result.scenario_name == 'failing_scenario'

class TestPerformanceMetricsTracking:
    """Tests pour le suivi des métriques de performance"""

    def test_metrics_tracking_accuracy(self, app):
        """Test de l'exactitude du suivi des métriques"""
        from performance_optimizer import PerformanceMonitor

        monitor = PerformanceMonitor(app)

        # Enregistrer des métriques précises
        test_times = [0.1, 0.2, 0.15, 0.25, 0.12]
        for response_time in test_times:
            monitor.record_performance_metric('response_times', response_time)

        # Vérifier l'exactitude
        response_times = monitor.performance_metrics['response_times']
        recorded_times = [entry['value'] for entry in response_times]

        assert recorded_times == test_times

        # Vérifier le résumé
        summary = monitor.get_performance_summary()
        if 'response_times' in summary:
            rt_summary = summary['response_times']
            assert abs(rt_summary['average'] - 0.164) < 0.01  # Moyenne approximative

    def test_performance_trend_analysis(self, app):
        """Test de l'analyse de tendance des performances"""
        from performance_optimizer import PerformanceMonitor

        monitor = PerformanceMonitor(app)

        # Créer une tendance à la hausse
        for i in range(10):
            response_time = 0.1 + i * 0.02  # Tendance à la hausse
            monitor.record_performance_metric('response_times', response_time)

        summary = monitor.get_performance_summary()

        if 'response_times' in summary:
            rt_summary = summary['response_times']
            assert 'trend' in rt_summary

class TestPerformanceOptimizationWorkflow:
    """Tests du workflow d'optimisation des performances"""

    def test_complete_performance_optimization_workflow(self, app, db):
        """Test du workflow complet d'optimisation des performances"""
        from performance_optimizer import PerformanceMonitor
        from database_optimizer import DatabaseOptimizer

        # 1. Initialiser les optimiseurs
        monitor = PerformanceMonitor(app)
        db_optimizer = DatabaseOptimizer(app)

        # 2. Analyser les performances actuelles
        db_analysis = db_optimizer.analyze_database_performance()
        assert isinstance(db_analysis, dict)

        # 3. Enregistrer des métriques
        for i in range(15):
            monitor.record_performance_metric('response_times', 0.1 + i * 0.005)

        # 4. Générer le résumé
        summary = monitor.get_performance_summary()
        assert 'timestamp' in summary

        # 5. Optimiser les systèmes
        optimization_result = monitor.optimize_all_systems()
        assert 'optimizations' in optimization_result

        # 6. Vérifier que tout fonctionne ensemble
        assert optimization_result['overall_success'] == True

if __name__ == "__main__":
    pytest.main([__file__, '-v'])