#!/usr/bin/env python3
"""
Framework de tests de charge pour PassPrint
Tests de performance et identification des goulots d'étranglement
"""
import os
import time
import json
import logging
import requests
import threading
from datetime import datetime, timedelta
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Any, Callable
import statistics
import psutil
from pathlib import Path

logger = logging.getLogger(__name__)

class LoadTestScenario:
    """Scénario de test de charge"""

    def __init__(self, name: str, endpoint: str, method: str = 'GET', data: dict = None,
                 headers: dict = None, expected_status: int = 200):
        self.name = name
        self.endpoint = endpoint
        self.method = method
        self.data = data or {}
        self.headers = headers or {}
        self.expected_status = expected_status

class LoadTestResult:
    """Résultat d'un test de charge"""

    def __init__(self, scenario_name: str):
        self.scenario_name = scenario_name
        self.start_time = None
        self.end_time = None
        self.requests = []
        self.errors = []
        self.response_times = []

    def add_request(self, response_time: float, status_code: int, success: bool, error: str = None):
        """Ajouter une requête au résultat"""
        self.requests.append({
            'response_time': response_time,
            'status_code': status_code,
            'success': success,
            'timestamp': datetime.utcnow().isoformat()
        })

        if success:
            self.response_times.append(response_time)
        else:
            self.errors.append({
                'error': error,
                'timestamp': datetime.utcnow().isoformat()
            })

    def finalize(self):
        """Finaliser le résultat du test"""
        self.end_time = datetime.utcnow()

        if self.requests:
            self.duration = (self.end_time - self.start_time).total_seconds()
            self.total_requests = len(self.requests)
            self.successful_requests = len(self.response_times)
            self.failed_requests = len(self.errors)
            self.success_rate = self.successful_requests / self.total_requests if self.total_requests > 0 else 0

            if self.response_times:
                self.avg_response_time = statistics.mean(self.response_times)
                self.median_response_time = statistics.median(self.response_times)
                self.min_response_time = min(self.response_times)
                self.max_response_time = max(self.response_times)
                self.p95_response_time = statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) >= 20 else max(self.response_times)
                self.p99_response_time = statistics.quantiles(self.response_times, n=100)[98] if len(self.response_times) >= 100 else max(self.response_times)
            else:
                self.avg_response_time = 0
                self.median_response_time = 0
                self.min_response_time = 0
                self.max_response_time = 0
                self.p95_response_time = 0
                self.p99_response_time = 0

            self.requests_per_second = self.total_requests / max(1, self.duration)

class LoadTestEngine:
    """Moteur de tests de charge"""

    def __init__(self, base_url: str = 'http://localhost:5000'):
        self.base_url = base_url
        self.scenarios = []
        self.results = []
        self.logger = logging.getLogger(__name__)

        # Configuration des tests
        self.test_config = {
            'max_workers': int(os.getenv('LOAD_TEST_WORKERS', '50')),
            'timeout': int(os.getenv('LOAD_TEST_TIMEOUT', '30')),
            'ramp_up_time': int(os.getenv('LOAD_TEST_RAMP_UP', '60')),
            'test_duration': int(os.getenv('LOAD_TEST_DURATION', '300')),
            'monitor_system': os.getenv('LOAD_TEST_MONITOR_SYSTEM', 'true').lower() == 'true'
        }

    def add_scenario(self, scenario: LoadTestScenario):
        """Ajouter un scénario de test"""
        self.scenarios.append(scenario)

    def create_realistic_scenarios(self) -> List[LoadTestScenario]:
        """Créer des scénarios réalistes pour PassPrint"""
        scenarios = [
            LoadTestScenario(
                'health_check',
                '/api/health',
                'GET',
                expected_status=200
            ),
            LoadTestScenario(
                'products_list',
                '/api/products',
                'GET',
                expected_status=200
            ),
            LoadTestScenario(
                'user_registration',
                '/api/auth/register',
                'POST',
                {
                    'email': 'loadtest{}@example.com',
                    'password': 'SecurePassword123!',
                    'first_name': 'Load',
                    'last_name': 'Test'
                },
                {'Content-Type': 'application/json'},
                expected_status=201
            ),
            LoadTestScenario(
                'user_login',
                '/api/auth/login',
                'POST',
                {
                    'email': 'loadtest@example.com',
                    'password': 'SecurePassword123!'
                },
                {'Content-Type': 'application/json'},
                expected_status=200
            ),
            LoadTestScenario(
                'cart_operations',
                '/api/cart',
                'POST',
                {
                    'product_id': 1,
                    'quantity': 1
                },
                {'Content-Type': 'application/json'},
                expected_status=200
            ),
            LoadTestScenario(
                'quote_creation',
                '/api/quotes',
                'POST',
                {
                    'project_name': 'Load Test Project',
                    'project_description': 'Test de charge',
                    'format': 'A4',
                    'quantity': 100
                },
                {'Content-Type': 'application/json'},
                expected_status=201
            )
        ]

        return scenarios

    def execute_scenario(self, scenario: LoadTestScenario, num_requests: int = 100) -> LoadTestResult:
        """Exécuter un scénario de test"""
        result = LoadTestResult(scenario.name)
        result.start_time = datetime.utcnow()

        def make_request(request_id: int):
            try:
                start_time = time.time()

                # Préparer les données avec l'ID de requête
                data = scenario.data.copy()
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, str) and '{}' in str(value):
                            data[key] = str(value).format(request_id)

                # Préparer les headers
                headers = scenario.headers.copy()
                headers['User-Agent'] = f'PassPrint-LoadTest/{request_id}'

                # Effectuer la requête
                if scenario.method == 'GET':
                    response = requests.get(
                        f"{self.base_url}{scenario.endpoint}",
                        headers=headers,
                        timeout=self.test_config['timeout']
                    )
                elif scenario.method == 'POST':
                    response = requests.post(
                        f"{self.base_url}{scenario.endpoint}",
                        json=data,
                        headers=headers,
                        timeout=self.test_config['timeout']
                    )
                else:
                    raise ValueError(f"Méthode non supportée: {scenario.method}")

                response_time = time.time() - start_time
                success = response.status_code == scenario.expected_status

                result.add_request(
                    response_time=response_time,
                    status_code=response.status_code,
                    success=success,
                    error=None if success else f"Status {response.status_code}"
                )

            except Exception as e:
                response_time = time.time() - start_time
                result.add_request(
                    response_time=response_time,
                    status_code=0,
                    success=False,
                    error=str(e)
                )

        # Exécuter les requêtes
        with ThreadPoolExecutor(max_workers=self.test_config['max_workers']) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_requests)]

            # Attendre la fin de toutes les requêtes
            for future in as_completed(futures):
                try:
                    future.result()  # Récupérer le résultat ou l'exception
                except Exception as e:
                    self.logger.error(f"Erreur exécution requête: {e}")

        result.finalize()
        return result

    def run_comprehensive_load_test(self) -> Dict:
        """Exécuter un test de charge complet"""
        try:
            # Créer les scénarios réalistes
            if not self.scenarios:
                self.scenarios = self.create_realistic_scenarios()

            comprehensive_result = {
                'test_id': f"comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'timestamp': datetime.utcnow().isoformat(),
                'configuration': self.test_config,
                'scenario_results': [],
                'system_metrics': {},
                'overall_summary': {},
                'bottlenecks': []
            }

            # Métriques système avant le test
            initial_metrics = self._collect_system_metrics()
            comprehensive_result['system_metrics']['initial'] = initial_metrics

            # Exécuter chaque scénario
            for scenario in self.scenarios:
                self.logger.info(f"Exécution scénario: {scenario.name}")

                # Déterminer le nombre de requêtes selon le scénario
                num_requests = self._get_scenario_request_count(scenario)

                scenario_result = self.execute_scenario(scenario, num_requests)
                comprehensive_result['scenario_results'].append(scenario_result.__dict__)

            # Métriques système après le test
            final_metrics = self._collect_system_metrics()
            comprehensive_result['system_metrics']['final'] = final_metrics

            # Analyser les résultats
            comprehensive_result['overall_summary'] = self._analyze_overall_results(comprehensive_result['scenario_results'])
            comprehensive_result['bottlenecks'] = self._identify_bottlenecks(comprehensive_result)

            # Sauvegarder les résultats
            self._save_test_results(comprehensive_result)

            return comprehensive_result

        except Exception as e:
            self.logger.error(f"Erreur test de charge complet: {e}")
            return {'error': str(e)}

    def _collect_system_metrics(self) -> Dict:
        """Collecter les métriques système"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_mb': memory.used / 1024 / 1024,
                'disk_percent': disk.percent,
                'disk_used_gb': disk.used / 1024 / 1024 / 1024,
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {'error': str(e)}

    def _get_scenario_request_count(self, scenario: LoadTestScenario) -> int:
        """Déterminer le nombre de requêtes pour un scénario"""
        # Ajuster selon le type de scénario
        if 'health' in scenario.name:
            return 1000  # Tests de santé peuvent être nombreux
        elif 'registration' in scenario.name or 'login' in scenario.name:
            return 100   # Tests d'authentification limités
        elif 'products' in scenario.name:
            return 500   # Tests de lecture de données
        else:
            return 200   # Autres scénarios

    def _analyze_overall_results(self, scenario_results: List[Dict]) -> Dict:
        """Analyser les résultats globaux"""
        try:
            all_response_times = []
            total_requests = 0
            total_successful = 0
            total_failed = 0

            for result in scenario_results:
                if hasattr(result, 'response_times'):
                    all_response_times.extend(result.response_times)
                total_requests += result.total_requests
                total_successful += result.successful_requests
                total_failed += result.failed_requests

            if all_response_times:
                return {
                    'total_requests': total_requests,
                    'successful_requests': total_successful,
                    'failed_requests': total_failed,
                    'overall_success_rate': total_successful / total_requests if total_requests > 0 else 0,
                    'avg_response_time': statistics.mean(all_response_times),
                    'median_response_time': statistics.median(all_response_times),
                    'min_response_time': min(all_response_times),
                    'max_response_time': max(all_response_times),
                    'p95_response_time': statistics.quantiles(all_response_times, n=20)[18] if len(all_response_times) >= 20 else max(all_response_times),
                    'total_scenarios': len(scenario_results)
                }

            return {
                'total_requests': total_requests,
                'successful_requests': total_successful,
                'failed_requests': total_failed,
                'overall_success_rate': 0,
                'total_scenarios': len(scenario_results)
            }

        except Exception as e:
            return {'error': f'Erreur analyse résultats: {e}'}

    def _identify_bottlenecks(self, comprehensive_result: Dict) -> List[str]:
        """Identifier les goulots d'étranglement"""
        bottlenecks = []

        try:
            summary = comprehensive_result.get('overall_summary', {})

            # Analyser les métriques de performance
            if summary.get('avg_response_time', 0) > 2.0:
                bottlenecks.append("Temps de réponse moyen élevé (>2s)")

            if summary.get('overall_success_rate', 1.0) < 0.95:
                bottlenecks.append("Taux de succès faible (<95%)")

            # Analyser les métriques système
            system_metrics = comprehensive_result.get('system_metrics', {})

            if system_metrics.get('initial', {}).get('cpu_percent', 0) > 80:
                bottlenecks.append("CPU élevé avant le test")

            final_cpu = system_metrics.get('final', {}).get('cpu_percent', 0)
            initial_cpu = system_metrics.get('initial', {}).get('cpu_percent', 0)

            if final_cpu > initial_cpu + 20:
                bottlenecks.append("Augmentation significative de l'utilisation CPU")

            # Analyser par scénario
            for scenario_result in comprehensive_result.get('scenario_results', []):
                if scenario_result.get('avg_response_time', 0) > 5.0:
                    bottlenecks.append(f"Scénario lent: {scenario_result.get('scenario_name', 'unknown')}")

                if scenario_result.get('success_rate', 1.0) < 0.90:
                    bottlenecks.append(f"Scénario avec faible taux de succès: {scenario_result.get('scenario_name', 'unknown')}")

        except Exception as e:
            bottlenecks.append(f"Erreur identification goulots: {e}")

        return bottlenecks

    def _save_test_results(self, results: Dict):
        """Sauvegarder les résultats du test"""
        try:
            results_dir = Path('load_test_results')
            results_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"load_test_{results['test_id']}_{timestamp}.json"

            with open(results_dir / filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)

            self.logger.info(f"Résultats sauvegardés: {filename}")

        except Exception as e:
            self.logger.error(f"Erreur sauvegarde résultats: {e}")

class PerformanceBenchmark:
    """Benchmark de performances"""

    def __init__(self, app=None):
        self.app = app
        self.benchmarks = {}
        self.logger = logging.getLogger(__name__)

    def run_database_benchmark(self) -> Dict:
        """Exécuter un benchmark de base de données"""
        try:
            benchmark_result = {
                'timestamp': datetime.utcnow().isoformat(),
                'database_operations': {},
                'query_optimization': {},
                'index_effectiveness': {}
            }

            # Benchmark des opérations CRUD de base
            operations = [
                ('user_select', "SELECT * FROM user WHERE id = 1"),
                ('user_insert', "INSERT INTO user (email, password_hash, first_name, last_name) VALUES ('test@test.com', 'hash', 'Test', 'User')"),
                ('product_select', "SELECT * FROM product WHERE category = 'print'"),
                ('order_select', "SELECT * FROM order WHERE customer_id = 1"),
                ('complex_join', "SELECT u.email, COUNT(o.id) as order_count FROM user u LEFT JOIN order o ON u.id = o.customer_id GROUP BY u.id")
            ]

            for op_name, query in operations:
                times = []

                # Exécuter plusieurs fois pour obtenir une moyenne
                for _ in range(10):
                    start_time = time.time()

                    # Exécuter la requête selon le type de base
                    config = get_config()
                    db_url = config.SQLALCHEMY_DATABASE_URI

                    if 'sqlite' in db_url:
                        import sqlite3
                        conn = sqlite3.connect(db_url.replace('sqlite:///', ''))
                        cursor = conn.cursor()
                        cursor.execute(query)
                        cursor.fetchall()
                        conn.close()

                    elif 'postgresql' in db_url:
                        import psycopg2
                        # Parser l'URL PostgreSQL
                        pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
                        match = re.match(pattern, db_url)
                        if match:
                            user, password, host, port, database = match.groups()
                            conn = psycopg2.connect(
                                host=host, port=port, user=user,
                                password=password, database=database
                            )
                            cursor = conn.cursor()
                            cursor.execute(query)
                            cursor.fetchall()
                            conn.close()

                    execution_time = time.time() - start_time
                    times.append(execution_time)

                benchmark_result['database_operations'][op_name] = {
                    'avg_time': statistics.mean(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'executions': len(times)
                }

            return benchmark_result

        except Exception as e:
            return {'error': f'Erreur benchmark base de données: {e}'}

    def run_api_benchmark(self) -> Dict:
        """Exécuter un benchmark des API"""
        try:
            benchmark_result = {
                'timestamp': datetime.utcnow().isoformat(),
                'api_endpoints': {},
                'cache_effectiveness': {},
                'memory_usage': {}
            }

            # Endpoints à benchmarker
            endpoints = [
                ('health', '/api/health', 'GET'),
                ('products', '/api/products', 'GET'),
                ('product_detail', '/api/products/1', 'GET')
            ]

            for name, endpoint, method in endpoints:
                times = []

                # Benchmark sans cache
                for _ in range(5):
                    start_time = time.time()

                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)

                    execution_time = time.time() - start_time
                    times.append(execution_time)

                benchmark_result['api_endpoints'][name] = {
                    'avg_time': statistics.mean(times),
                    'status_code': response.status_code if 'response' in locals() else 0,
                    'executions': len(times)
                }

            return benchmark_result

        except Exception as e:
            return {'error': f'Erreur benchmark API: {e}'}

class PerformanceAnalyzer:
    """Analyseur de performances"""

    def __init__(self, app=None):
        self.app = app
        self.load_engine = LoadTestEngine()
        self.benchmark = PerformanceBenchmark(app)
        self.logger = logging.getLogger(__name__)

    def analyze_system_performance(self) -> Dict:
        """Analyser les performances globales du système"""
        try:
            analysis = {
                'timestamp': datetime.utcnow().isoformat(),
                'system_health': self._assess_system_health(),
                'performance_bottlenecks': self._identify_performance_bottlenecks(),
                'optimization_opportunities': self._find_optimization_opportunities(),
                'capacity_planning': self._generate_capacity_plan(),
                'recommendations': self._generate_performance_recommendations()
            }

            return analysis

        except Exception as e:
            return {'error': f'Erreur analyse performances: {e}'}

    def _assess_system_health(self) -> Dict:
        """Évaluer la santé du système"""
        try:
            # Métriques système actuelles
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            health_score = 100

            # Pénalités selon l'utilisation
            if cpu_percent > 80:
                health_score -= 30
            elif cpu_percent > 60:
                health_score -= 15

            if memory.percent > 85:
                health_score -= 25
            elif memory.percent > 70:
                health_score -= 10

            if disk.percent > 90:
                health_score -= 20
            elif disk.percent > 80:
                health_score -= 5

            return {
                'score': max(0, health_score),
                'status': 'healthy' if health_score >= 70 else 'degraded' if health_score >= 40 else 'critical',
                'metrics': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'disk_percent': disk.percent
                }
            }

        except Exception as e:
            return {'error': str(e)}

    def _identify_performance_bottlenecks(self) -> List[str]:
        """Identifier les goulots d'étranglement de performance"""
        bottlenecks = []

        try:
            # Analyser les métriques système
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            if cpu_percent > 80:
                bottlenecks.append("Goulot d'étranglement CPU détecté")

            if memory.percent > 85:
                bottlenecks.append("Goulot d'étranglement mémoire détecté")

            # Analyser les processus
            process = psutil.Process()
            if process.cpu_percent() > 50:
                bottlenecks.append("Processus principal utilise beaucoup de CPU")

            # Analyser les connexions réseau
            network = psutil.net_io_counters()
            if network.bytes_sent + network.bytes_recv > 100 * 1024 * 1024:  # 100MB
                bottlenecks.append("Utilisation réseau élevée")

        except Exception as e:
            bottlenecks.append(f"Erreur analyse goulots: {e}")

        return bottlenecks

    def _find_optimization_opportunities(self) -> List[str]:
        """Trouver les opportunités d'optimisation"""
        opportunities = []

        try:
            # Analyser la base de données
            db_analysis = database_optimizer.analyze_database_performance()
            if 'optimization_recommendations' in db_analysis:
                opportunities.extend(db_analysis['optimization_recommendations'][:3])

            # Analyser le cache
            cache_analysis = cache_optimizer.analyze_cache_effectiveness()
            if cache_analysis.get('performance_impact') == 'negative':
                opportunities.append("Optimiser la stratégie de cache")

            # Analyser la mémoire
            memory_stats = memory_optimizer.get_memory_statistics()
            if memory_stats.get('leak_analysis', {}).get('potential_leak', False):
                opportunities.append("Analyser les fuites mémoire potentielles")

        except Exception as e:
            opportunities.append(f"Erreur recherche opportunités: {e}")

        return opportunities

    def _generate_capacity_plan(self) -> Dict:
        """Générer un plan de capacité"""
        try:
            current_load = self._assess_current_load()

            # Projections basées sur la charge actuelle
            projections = {
                'current_capacity': current_load,
                'recommended_capacity': {
                    'cpu_cores': max(2, current_load['cpu_usage'] * 2),
                    'memory_gb': max(2, current_load['memory_usage_gb'] * 1.5),
                    'disk_gb': max(50, current_load['disk_usage_gb'] * 2)
                },
                'scaling_recommendations': self._get_scaling_recommendations(current_load)
            }

            return projections

        except Exception as e:
            return {'error': str(e)}

    def _assess_current_load(self) -> Dict:
        """Évaluer la charge actuelle"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            return {
                'cpu_usage': cpu_percent / 100,
                'memory_usage_gb': memory.used / 1024 / 1024 / 1024,
                'disk_usage_gb': psutil.disk_usage('/').used / 1024 / 1024 / 1024,
                'load_level': 'low' if cpu_percent < 30 else 'medium' if cpu_percent < 70 else 'high'
            }

        except Exception as e:
            return {'error': str(e)}

    def _get_scaling_recommendations(self, current_load: Dict) -> List[str]:
        """Obtenir les recommandations de mise à l'échelle"""
        recommendations = []

        if current_load.get('load_level') == 'high':
            recommendations.append("Envisager la mise à l'échelle horizontale (plus de serveurs)")
            recommendations.append("Optimiser les requêtes de base de données")

        if current_load.get('memory_usage_gb', 0) > 8:
            recommendations.append("Envisager plus de mémoire RAM")

        if current_load.get('disk_usage_gb', 0) > 500:
            recommendations.append("Envisager plus d'espace disque ou un stockage externe")

        return recommendations

    def _generate_performance_recommendations(self) -> List[str]:
        """Générer des recommandations de performance"""
        recommendations = []

        try:
            # Recommandations générales
            system_health = self._assess_system_health()

            if system_health.get('status') != 'healthy':
                recommendations.append("Santé système dégradée - optimisation nécessaire")

            # Recommandations spécifiques
            bottlenecks = self._identify_performance_bottlenecks()
            if bottlenecks:
                recommendations.extend(bottlenecks[:3])  # Top 3

            opportunities = self._find_optimization_opportunities()
            if opportunities:
                recommendations.extend(opportunities[:3])  # Top 3

        except Exception as e:
            recommendations.append(f"Erreur génération recommandations: {e}")

        return recommendations

# Instances globales
load_test_engine = LoadTestEngine()
performance_benchmark = PerformanceBenchmark()
performance_analyzer = PerformanceAnalyzer()

def run_load_test_scenario(scenario_name: str, num_requests: int = 100) -> Dict:
    """Fonction utilitaire pour exécuter un scénario de test de charge"""
    if not load_test_engine.scenarios:
        load_test_engine.scenarios = load_test_engine.create_realistic_scenarios()

    scenario = next((s for s in load_test_engine.scenarios if s.name == scenario_name), None)
    if not scenario:
        return {'error': f'Scénario non trouvé: {scenario_name}'}

    result = load_test_engine.execute_scenario(scenario, num_requests)
    return result.__dict__

def run_comprehensive_load_test() -> Dict:
    """Fonction utilitaire pour exécuter un test de charge complet"""
    return load_test_engine.run_comprehensive_load_test()

def run_database_benchmark() -> Dict:
    """Fonction utilitaire pour exécuter un benchmark de base de données"""
    return performance_benchmark.run_database_benchmark()

def run_api_benchmark() -> Dict:
    """Fonction utilitaire pour exécuter un benchmark d'API"""
    return performance_benchmark.run_api_benchmark()

def analyze_system_performance() -> Dict:
    """Fonction utilitaire pour analyser les performances du système"""
    return performance_analyzer.analyze_system_performance()

if __name__ == "__main__":
    print("🚀 Framework de tests de charge PassPrint")

    # Test du système de charge
    load_engine = LoadTestEngine()

    # Créer les scénarios réalistes
    scenarios = load_engine.create_realistic_scenarios()
    print(f"✅ {len(scenarios)} scénarios créés")

    # Exécuter un test rapide
    if scenarios:
        test_result = load_engine.execute_scenario(scenarios[0], 10)
        print(f"📊 Test rapide: {test_result.success_rate:.1%} succès, {test_result.avg_response_time:.3f}s moyen")

    # Analyser les performances
    analysis = analyze_system_performance()
    if 'error' not in analysis:
        health = analysis.get('system_health', {})
        print(f"🏥 Santé système: {health.get('status', 'unknown')} (score: {health.get('score', 0)}/100)")

        bottlenecks = analysis.get('performance_bottlenecks', [])
        if bottlenecks:
            print(f"⚠️ Goulots détectés: {len(bottlenecks)}")
            for bottleneck in bottlenecks[:3]:
                print(f"  - {bottleneck}")
    else:
        print(f"❌ Erreur analyse: {analysis['error']}")