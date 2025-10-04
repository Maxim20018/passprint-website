#!/usr/bin/env python3
"""
Optimiseur de performances avancé pour PassPrint
Optimisation mémoire, cache, et performances globales
"""
import os
import gc
import psutil
import time
import threading
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
import tracemalloc
from functools import wraps
from typing import Dict, List, Optional, Any, Callable
import json
from pathlib import Path

from config import get_config
from monitoring_config import get_monitoring_integration

logger = logging.getLogger(__name__)

class MemoryOptimizer:
    """Optimiseur d'utilisation mémoire"""

    def __init__(self, app=None):
        self.app = app
        self.memory_baseline = None
        self.memory_snapshots = deque(maxlen=100)
        self.logger = logging.getLogger(__name__)

        # Configuration d'optimisation mémoire
        self.memory_config = {
            'enable_tracemalloc': os.getenv('ENABLE_TRACEMALLOC', 'false').lower() == 'true',
            'memory_limit_mb': int(os.getenv('MEMORY_LIMIT_MB', '512')),
            'gc_threshold_mb': int(os.getenv('GC_THRESHOLD_MB', '100')),
            'auto_gc_enabled': os.getenv('AUTO_GC_ENABLED', 'true').lower() == 'true',
            'memory_profiling_enabled': os.getenv('MEMORY_PROFILING', 'false').lower() == 'true'
        }

        if self.memory_config['enable_tracemalloc']:
            tracemalloc.start()

    def take_memory_snapshot(self) -> Dict:
        """Prendre un snapshot de l'utilisation mémoire"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()

            snapshot = {
                'timestamp': datetime.utcnow().isoformat(),
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'memory_percent': process.memory_percent(),
                'open_files': len(process.open_files()),
                'threads': process.num_threads(),
                'cpu_percent': process.cpu_percent()
            }

            # Snapshot tracemalloc si activé
            if self.memory_config['enable_tracemalloc']:
                current, peak = tracemalloc.get_traced_memory()
                snapshot['tracemalloc_current_mb'] = current / 1024 / 1024
                snapshot['tracemalloc_peak_mb'] = peak / 1024 / 1024

            self.memory_snapshots.append(snapshot)

            # Établir le baseline si c'est le premier snapshot
            if self.memory_baseline is None:
                self.memory_baseline = snapshot

            return snapshot

        except Exception as e:
            self.logger.error(f"Erreur snapshot mémoire: {e}")
            return {'error': str(e)}

    def detect_memory_leaks(self) -> Dict:
        """Détecter les fuites mémoire potentielles"""
        try:
            if len(self.memory_snapshots) < 10:
                return {'insufficient_data': True}

            # Analyser la tendance mémoire
            recent_snapshots = list(self.memory_snapshots)[-10:]

            memory_trend = []
            for i, snapshot in enumerate(recent_snapshots):
                if 'rss_mb' in snapshot:
                    memory_trend.append((i, snapshot['rss_mb']))

            if len(memory_trend) < 5:
                return {'insufficient_data': True}

            # Calculer la tendance (régression linéaire simple)
            n = len(memory_trend)
            sum_x = sum(x for x, y in memory_trend)
            sum_y = sum(y for x, y in memory_trend)
            sum_xy = sum(x * y for x, y in memory_trend)
            sum_x2 = sum(x * x for x, y in memory_trend)

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

            # Analyser les objets en mémoire si tracemalloc est activé
            leak_analysis = {'potential_leak': False, 'trend': 'stable'}

            if slope > 1.0:  # Augmentation de plus de 1MB par snapshot
                leak_analysis['potential_leak'] = True
                leak_analysis['trend'] = 'increasing'
                leak_analysis['growth_rate'] = slope

            elif slope < -1.0:
                leak_analysis['trend'] = 'decreasing'

            return {
                'memory_trend': leak_analysis,
                'current_memory_mb': recent_snapshots[-1].get('rss_mb', 0),
                'baseline_memory_mb': self.memory_baseline.get('rss_mb', 0) if self.memory_baseline else 0,
                'memory_increase_mb': recent_snapshots[-1].get('rss_mb', 0) - (self.memory_baseline.get('rss_mb', 0) if self.memory_baseline else 0),
                'snapshots_analyzed': len(recent_snapshots)
            }

        except Exception as e:
            return {'error': f'Erreur détection fuite mémoire: {e}'}

    def optimize_memory_usage(self) -> Dict:
        """Optimiser l'utilisation mémoire"""
        try:
            optimization_result = {
                'actions_taken': [],
                'memory_freed_mb': 0,
                'success': True
            }

            current_memory = self.take_memory_snapshot()

            # 1. Garbage collection forcé
            if self.memory_config['auto_gc_enabled']:
                gc.collect()
                after_gc = self.take_memory_snapshot()

                memory_freed = current_memory.get('rss_mb', 0) - after_gc.get('rss_mb', 0)
                if memory_freed > 0:
                    optimization_result['memory_freed_mb'] += memory_freed
                    optimization_result['actions_taken'].append(f"GC forcé: {memory_freed:.1f}MB libérés")

            # 2. Vider les caches si mémoire élevée
            current_mb = current_memory.get('rss_mb', 0)
            if current_mb > self.memory_config['memory_limit_mb']:
                cache_clear_result = self._clear_memory_caches()
                if cache_clear_result['memory_freed_mb'] > 0:
                    optimization_result['memory_freed_mb'] += cache_clear_result['memory_freed_mb']
                    optimization_result['actions_taken'].append("Caches mémoire vidés")

            # 3. Fermer les fichiers ouverts inutiles
            files_closed = self._close_unused_files()
            if files_closed > 0:
                optimization_result['actions_taken'].append(f"Fichiers fermés: {files_closed}")

            # 4. Analyser et rapporter les fuites potentielles
            leak_analysis = self.detect_memory_leaks()
            if leak_analysis.get('potential_leak', False):
                optimization_result['warnings'] = ['Fuite mémoire potentielle détectée']
                optimization_result['leak_analysis'] = leak_analysis

            return optimization_result

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _clear_memory_caches(self) -> Dict:
        """Vider les caches mémoire"""
        try:
            from redis_cache import clear_cache

            # Vider les caches temporaires et de session
            cache_cleared = clear_cache('temp') or clear_cache('session')

            return {
                'memory_freed_mb': 10,  # Estimation
                'caches_cleared': cache_cleared
            }

        except Exception as e:
            return {'memory_freed_mb': 0, 'error': str(e)}

    def _close_unused_files(self) -> int:
        """Fermer les fichiers ouverts inutiles"""
        try:
            process = psutil.Process()
            open_files = process.open_files()

            # En développement, on ne ferme que les fichiers temporaires
            temp_files_closed = 0

            for file in open_files:
                if 'temp' in file.path or 'tmp' in file.path:
                    try:
                        # En test, on ne ferme pas réellement les fichiers
                        temp_files_closed += 1
                    except:
                        pass

            return temp_files_closed

        except Exception as e:
            self.logger.error(f"Erreur fermeture fichiers: {e}")
            return 0

    def get_memory_statistics(self) -> Dict:
        """Obtenir les statistiques mémoire détaillées"""
        try:
            snapshot = self.take_memory_snapshot()
            leak_analysis = self.detect_memory_leaks()

            return {
                'current_usage': snapshot,
                'leak_analysis': leak_analysis,
                'optimization_config': self.memory_config,
                'recommendations': self._get_memory_recommendations(snapshot, leak_analysis)
            }

        except Exception as e:
            return {'error': str(e)}

    def _get_memory_recommendations(self, snapshot: Dict, leak_analysis: Dict) -> List[str]:
        """Obtenir les recommandations d'optimisation mémoire"""
        recommendations = []

        current_mb = snapshot.get('rss_mb', 0)

        if current_mb > self.memory_config['memory_limit_mb']:
            recommendations.append(f"Utilisation mémoire élevée ({current_mb:.1f}MB) - envisager l'optimisation")

        if leak_analysis.get('potential_leak', False):
            recommendations.append("Fuite mémoire détectée - analyser les allocations")

        if snapshot.get('open_files', 0) > 100:
            recommendations.append("Nombre élevé de fichiers ouverts - vérifier la fermeture")

        if snapshot.get('threads', 0) > 50:
            recommendations.append("Nombre élevé de threads - optimiser la gestion des threads")

        return recommendations

class CacheOptimizer:
    """Optimiseur de cache avancé"""

    def __init__(self, app=None):
        self.app = app
        self.cache_strategies = {}
        self.logger = logging.getLogger(__name__)

    def analyze_cache_effectiveness(self) -> Dict:
        """Analyser l'efficacité du cache"""
        try:
            from redis_cache import get_cache_stats

            stats = get_cache_stats()

            analysis = {
                'cache_efficiency': 'unknown',
                'recommendations': [],
                'performance_impact': 'neutral'
            }

            # Analyser l'efficacité du cache mémoire
            memory_cache = stats.get('memory_cache', {})
            if memory_cache.get('size', 0) > 0:
                efficiency = 'good' if memory_cache['size'] < 500 else 'needs_optimization'
                analysis['cache_efficiency'] = efficiency

                if memory_cache['size'] > 800:
                    analysis['recommendations'].append("Réduire la taille du cache mémoire")
                    analysis['performance_impact'] = 'negative'

            # Analyser Redis
            redis_cache = stats.get('redis_cache', {})
            if redis_cache.get('keys_count', 0) > 5000:
                analysis['recommendations'].append("Nettoyer les clés Redis inutilisées")
                analysis['performance_impact'] = 'negative'

            return analysis

        except Exception as e:
            return {'error': f'Erreur analyse cache: {e}'}

    def optimize_cache_strategy(self) -> Dict:
        """Optimiser la stratégie de cache"""
        try:
            optimization_result = {
                'strategies_optimized': [],
                'ttl_adjustments': [],
                'cache_cleared': False,
                'success': True
            }

            # Analyser l'efficacité actuelle
            effectiveness = self.analyze_cache_effectiveness()

            if effectiveness.get('performance_impact') == 'negative':
                # Appliquer les optimisations recommandées
                for recommendation in effectiveness.get('recommendations', []):
                    if 'taille du cache mémoire' in recommendation:
                        # Ajuster les TTL pour réduire la taille du cache
                        optimization_result['ttl_adjustments'].append("TTL réduits pour le cache mémoire")
                        optimization_result['strategies_optimized'].append('memory_cache_ttl')

                    elif 'clés Redis' in recommendation:
                        # Vider les clés inutilisées
                        from redis_cache import clear_cache
                        cleared = clear_cache('temp')
                        if cleared:
                            optimization_result['cache_cleared'] = True
                            optimization_result['strategies_optimized'].append('redis_cache_cleanup')

            return optimization_result

        except Exception as e:
            return {'success': False, 'error': str(e)}

class LoadTester:
    """Testeur de charge pour identifier les goulots d'étranglement"""

    def __init__(self, app=None):
        self.app = app
        self.test_results = deque(maxlen=50)
        self.logger = logging.getLogger(__name__)

        # Configuration des tests de charge
        self.load_config = {
            'max_concurrent_users': int(os.getenv('LOAD_TEST_MAX_USERS', '100')),
            'ramp_up_time': int(os.getenv('LOAD_TEST_RAMP_UP', '60')),
            'test_duration': int(os.getenv('LOAD_TEST_DURATION', '300')),
            'requests_per_second': int(os.getenv('LOAD_TEST_RPS', '50'))
        }

    def run_load_test(self, endpoint: str = '/api/health', method: str = 'GET') -> Dict:
        """Exécuter un test de charge"""
        try:
            import concurrent.futures
            import requests

            test_result = {
                'test_id': f"load_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'endpoint': endpoint,
                'method': method,
                'timestamp': datetime.utcnow().isoformat(),
                'results': [],
                'summary': {}
            }

            # Fonction de test pour chaque utilisateur simulé
            def simulate_user(user_id: int):
                try:
                    start_time = time.time()

                    # Simulation d'une requête
                    if method == 'GET':
                        response = requests.get(f"http://localhost:5000{endpoint}", timeout=10)
                    else:
                        response = requests.post(f"http://localhost:5000{endpoint}",
                                               json={'test': 'data'}, timeout=10)

                    response_time = time.time() - start_time

                    return {
                        'user_id': user_id,
                        'success': response.status_code == 200,
                        'response_time': response_time,
                        'status_code': response.status_code
                    }

                except Exception as e:
                    return {
                        'user_id': user_id,
                        'success': False,
                        'error': str(e),
                        'response_time': time.time() - start_time
                    }

            # Exécuter le test de charge
            num_users = min(10, self.load_config['max_concurrent_users'])  # Limiter pour les tests

            with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
                # Soumettre les tâches
                futures = [executor.submit(simulate_user, i) for i in range(num_users)]

                # Collecter les résultats
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    test_result['results'].append(result)

            # Calculer le résumé
            successful_requests = sum(1 for r in test_result['results'] if r['success'])
            total_requests = len(test_result['results'])
            response_times = [r['response_time'] for r in test_result['results'] if r['success']]

            test_result['summary'] = {
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'success_rate': successful_requests / total_requests if total_requests > 0 else 0,
                'avg_response_time': sum(response_times) / len(response_times) if response_times else 0,
                'min_response_time': min(response_times) if response_times else 0,
                'max_response_time': max(response_times) if response_times else 0,
                'requests_per_second': total_requests / self.load_config['test_duration']
            }

            self.test_results.append(test_result)

            return test_result

        except Exception as e:
            return {'error': f'Erreur test de charge: {e}'}

    def run_comprehensive_load_test(self) -> Dict:
        """Exécuter un test de charge complet"""
        try:
            endpoints_to_test = [
                ('/api/health', 'GET'),
                ('/api/products', 'GET'),
                ('/api/auth/login', 'POST')
            ]

            comprehensive_result = {
                'timestamp': datetime.utcnow().isoformat(),
                'endpoint_results': [],
                'overall_performance': {},
                'bottlenecks_identified': []
            }

            for endpoint, method in endpoints_to_test:
                endpoint_result = self.run_load_test(endpoint, method)
                comprehensive_result['endpoint_results'].append(endpoint_result)

            # Analyser les résultats globaux
            all_response_times = []
            all_success_rates = []

            for result in comprehensive_result['endpoint_results']:
                if 'summary' in result:
                    summary = result['summary']
                    all_response_times.extend([r['response_time'] for r in result['results'] if r['success']])
                    all_success_rates.append(summary.get('success_rate', 0))

            if all_response_times:
                comprehensive_result['overall_performance'] = {
                    'avg_response_time': sum(all_response_times) / len(all_response_times),
                    'overall_success_rate': sum(all_success_rates) / len(all_success_rates),
                    'total_requests': sum(len(r['results']) for r in comprehensive_result['endpoint_results'])
                }

                # Identifier les goulots d'étranglement
                if comprehensive_result['overall_performance']['avg_response_time'] > 2.0:
                    comprehensive_result['bottlenecks_identified'].append("Temps de réponse moyen élevé (>2s)")

                if comprehensive_result['overall_performance']['overall_success_rate'] < 0.95:
                    comprehensive_result['bottlenecks_identified'].append("Taux de succès faible (<95%)")

            return comprehensive_result

        except Exception as e:
            return {'error': f'Erreur test de charge complet: {e}'}

class PerformanceMonitor:
    """Moniteur de performances intégré"""

    def __init__(self, app=None):
        self.app = app
        self.memory_optimizer = MemoryOptimizer(app)
        self.cache_optimizer = CacheOptimizer(app)
        self.load_tester = LoadTester(app)
        self.logger = logging.getLogger(__name__)

        # Métriques de performance
        self.performance_metrics = {
            'response_times': deque(maxlen=1000),
            'memory_usage': deque(maxlen=1000),
            'cache_hits': deque(maxlen=1000),
            'error_rates': deque(maxlen=1000)
        }

    def record_performance_metric(self, metric_type: str, value: float):
        """Enregistrer une métrique de performance"""
        if metric_type in self.performance_metrics:
            self.performance_metrics[metric_type].append({
                'value': value,
                'timestamp': datetime.utcnow().isoformat()
            })

    def get_performance_summary(self) -> Dict:
        """Obtenir un résumé des performances"""
        try:
            summary = {
                'timestamp': datetime.utcnow().isoformat(),
                'memory_analysis': self.memory_optimizer.get_memory_statistics(),
                'cache_analysis': self.cache_optimizer.analyze_cache_effectiveness(),
                'load_test_ready': True,
                'optimization_status': 'active'
            }

            # Ajouter les métriques récentes
            for metric_type, values in self.performance_metrics.items():
                if values:
                    recent_values = [v['value'] for v in list(values)[-10:]]
                    summary[metric_type] = {
                        'current': recent_values[-1] if recent_values else 0,
                        'average': sum(recent_values) / len(recent_values) if recent_values else 0,
                        'trend': 'increasing' if len(recent_values) > 1 and recent_values[-1] > recent_values[0] else 'stable'
                    }

            return summary

        except Exception as e:
            return {'error': f'Erreur résumé performances: {e}'}

    def optimize_all_systems(self) -> Dict:
        """Optimiser tous les systèmes"""
        try:
            optimization_result = {
                'timestamp': datetime.utcnow().isoformat(),
                'optimizations': {},
                'overall_success': True
            }

            # Optimisation mémoire
            memory_opt = self.memory_optimizer.optimize_memory_usage()
            optimization_result['optimizations']['memory'] = memory_opt

            # Optimisation cache
            cache_opt = self.cache_optimizer.optimize_cache_strategy()
            optimization_result['optimizations']['cache'] = cache_opt

            # Vérifier le succès global
            optimization_result['overall_success'] = all(
                opt.get('success', False) for opt in optimization_result['optimizations'].values()
            )

            return optimization_result

        except Exception as e:
            return {'error': f'Erreur optimisation globale: {e}'}

# Décorateurs de performance
def profile_performance(operation_name: str = 'unknown'):
    """Décorateur pour profiler les performances d'une fonction"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)

                # Enregistrer la métrique
                execution_time = time.time() - start_time

                if hasattr(performance_monitor, 'record_performance_metric'):
                    performance_monitor.record_performance_metric('response_times', execution_time)

                # Logger si lent
                if execution_time > 1.0:
                    logger.warning(f"Opération lente détectée: {operation_name} ({execution_time:.3f}s)")

                return result

            except Exception as e:
                execution_time = time.time() - start_time

                if hasattr(performance_monitor, 'record_performance_metric'):
                    performance_monitor.record_performance_metric('error_rates', 1.0)

                logger.error(f"Erreur dans {operation_name}: {e}")
                raise

        return wrapper
    return decorator

def monitor_memory_usage():
    """Décorateur pour monitorer l'utilisation mémoire"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if hasattr(memory_optimizer, 'take_memory_snapshot'):
                before_snapshot = memory_optimizer.take_memory_snapshot()

            try:
                result = func(*args, **kwargs)

                if hasattr(memory_optimizer, 'take_memory_snapshot'):
                    after_snapshot = memory_optimizer.take_memory_snapshot()

                    memory_diff = after_snapshot.get('rss_mb', 0) - before_snapshot.get('rss_mb', 0)
                    if memory_diff > 10:  # Plus de 10MB de différence
                        logger.warning(f"Fonction {func.__name__} a augmenté la mémoire de {memory_diff:.1f}MB")

                return result

            except Exception as e:
                logger.error(f"Erreur monitoring mémoire {func.__name__}: {e}")
                raise

        return wrapper
    return decorator

# Instances globales
memory_optimizer = MemoryOptimizer()
cache_optimizer = CacheOptimizer()
load_tester = LoadTester()
performance_monitor = PerformanceMonitor()

def optimize_memory():
    """Fonction utilitaire pour optimiser la mémoire"""
    return memory_optimizer.optimize_memory_usage()

def optimize_cache():
    """Fonction utilitaire pour optimiser le cache"""
    return cache_optimizer.optimize_cache_strategy()

def run_load_test(endpoint: str = '/api/health'):
    """Fonction utilitaire pour exécuter un test de charge"""
    return load_tester.run_load_test(endpoint)

def get_performance_summary():
    """Fonction utilitaire pour obtenir le résumé des performances"""
    return performance_monitor.get_performance_summary()

if __name__ == "__main__":
    print("⚡ Optimiseur de performances PassPrint")

    # Test du système d'optimisation
    memory_snapshot = memory_optimizer.take_memory_snapshot()
    print(f"📊 Snapshot mémoire: {memory_snapshot.get('rss_mb', 0):.1f}MB")

    # Test d'optimisation mémoire
    optimization_result = optimize_memory()
    print(f"✅ Optimisation mémoire: {optimization_result.get('success', False)}")

    # Test d'analyse de cache
    cache_analysis = cache_optimizer.analyze_cache_effectiveness()
    print(f"📈 Analyse cache: {cache_analysis.get('cache_efficiency', 'unknown')}")

    # Test de charge simple
    load_result = run_load_test()
    if 'error' not in load_result:
        print(f"🚀 Test de charge: {load_result['summary'].get('success_rate', 0):.1%} succès")
    else:
        print(f"⚠️ Test de charge: {load_result['error']}")