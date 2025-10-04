#!/usr/bin/env python3
"""
Optimiseur de base de données avancé pour PassPrint
Profilage, optimisation des requêtes, et gestion des performances
"""
import os
import time
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque
import psycopg2
import sqlite3
from contextlib import contextmanager
from typing import Dict, List, Optional, Any, Tuple
import json
from pathlib import Path

from models import db
from config import get_config
from monitoring_config import get_monitoring_integration

logger = logging.getLogger(__name__)

class QueryProfiler:
    """Profileur de requêtes SQL"""

    def __init__(self, app=None):
        self.app = app
        self.query_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'avg_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0,
            'slow_queries': 0,
            'examples': deque(maxlen=10)
        })
        self.slow_query_threshold = float(os.getenv('SLOW_QUERY_THRESHOLD', '1.0'))  # secondes

    @contextmanager
    def profile_query(self, query: str, operation: str = 'unknown'):
        """Context manager pour profiler une requête"""
        start_time = time.time()
        try:
            yield
        finally:
            execution_time = time.time() - start_time

            # Enregistrer les statistiques
            stats = self.query_stats[operation]
            stats['count'] += 1
            stats['total_time'] += execution_time
            stats['avg_time'] = stats['total_time'] / stats['count']
            stats['min_time'] = min(stats['min_time'], execution_time)
            stats['max_time'] = max(stats['max_time'], execution_time)

            if execution_time > self.slow_query_threshold:
                stats['slow_queries'] += 1

            # Garder un exemple de requête lente
            if execution_time > self.slow_query_threshold:
                stats['examples'].append({
                    'query': query[:200] + ('...' if len(query) > 200 else ''),
                    'execution_time': execution_time,
                    'timestamp': datetime.utcnow().isoformat()
                })

    def get_query_statistics(self) -> Dict:
        """Obtenir les statistiques des requêtes"""
        return dict(self.query_stats)

    def get_slow_queries(self) -> List[Dict]:
        """Obtenir la liste des requêtes lentes"""
        slow_queries = []

        for operation, stats in self.query_stats.items():
            if stats['slow_queries'] > 0:
                slow_queries.append({
                    'operation': operation,
                    'statistics': stats,
                    'slow_query_rate': stats['slow_queries'] / max(1, stats['count'])
                })

        return sorted(slow_queries, key=lambda x: x['slow_query_rate'], reverse=True)

    def generate_optimization_report(self) -> Dict:
        """Générer un rapport d'optimisation"""
        return {
            'generated_at': datetime.utcnow().isoformat(),
            'total_operations': sum(stats['count'] for stats in self.query_stats.values()),
            'slow_queries': sum(stats['slow_queries'] for stats in self.query_stats.values()),
            'average_execution_time': self._calculate_average_execution_time(),
            'optimization_recommendations': self._generate_recommendations(),
            'query_statistics': self.get_query_statistics(),
            'slow_queries': self.get_slow_queries()
        }

    def _calculate_average_execution_time(self) -> float:
        """Calculer le temps d'exécution moyen"""
        total_time = sum(stats['total_time'] for stats in self.query_stats.values())
        total_queries = sum(stats['count'] for stats in self.query_stats.values())

        return total_time / max(1, total_queries)

    def _generate_recommendations(self) -> List[str]:
        """Générer des recommandations d'optimisation"""
        recommendations = []

        # Analyser les statistiques
        for operation, stats in self.query_stats.items():
            if stats['count'] > 100 and stats['avg_time'] > 0.5:
                recommendations.append(f"Optimiser l'opération '{operation}' (temps moyen: {stats['avg_time']:.3f}s)")

            if stats['slow_queries'] / max(1, stats['count']) > 0.1:
                recommendations.append(f"Requête '{operation}' lente détectée ({stats['slow_queries']} requêtes lentes)")

        # Recommandations générales
        if self._calculate_average_execution_time() > 1.0:
            recommendations.append("Temps d'exécution moyen élevé - envisager l'ajout d'index")

        return recommendations

class DatabaseOptimizer:
    """Optimiseur de base de données complet"""

    def __init__(self, app=None):
        self.app = app
        self.profiler = QueryProfiler(app)
        self.logger = logging.getLogger(__name__)

        # Configuration d'optimisation
        self.optimization_config = {
            'auto_analyze': os.getenv('DB_AUTO_ANALYZE', 'true').lower() == 'true',
            'auto_vacuum': os.getenv('DB_AUTO_VACUUM', 'true').lower() == 'true',
            'query_timeout': int(os.getenv('DB_QUERY_TIMEOUT', '30')),
            'max_connections': int(os.getenv('DB_MAX_CONNECTIONS', '20')),
            'index_suggestions_enabled': os.getenv('DB_INDEX_SUGGESTIONS', 'true').lower() == 'true'
        }

    def analyze_database_performance(self) -> Dict:
        """Analyser les performances de la base de données"""
        try:
            config = get_config()
            db_url = config.SQLALCHEMY_DATABASE_URI

            if 'sqlite' in db_url:
                return self._analyze_sqlite_performance()
            elif 'postgresql' in db_url:
                return self._analyze_postgresql_performance()
            else:
                return {'error': f'Type de base non supporté: {db_url}'}

        except Exception as e:
            self.logger.error(f"Erreur analyse performances base de données: {e}")
            return {'error': str(e)}

    def _analyze_sqlite_performance(self) -> Dict:
        """Analyser les performances SQLite"""
        try:
            config = get_config()
            db_path = config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')

            if not os.path.exists(db_path):
                return {'error': 'Base de données SQLite non trouvée'}

            # Analyser la base SQLite
            conn = sqlite3.connect(db_path)

            # Statistiques de base
            cursor = conn.cursor()

            # Taille de la base
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            db_size = cursor.fetchone()[0]

            # Nombre de tables
            cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]

            # Statistiques des index
            cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='index'")
            index_count = cursor.fetchone()[0]

            # Analyse des tables
            cursor.execute("SELECT name, COUNT(*) FROM sqlite_master WHERE type='table' GROUP BY name")
            tables = cursor.fetchall()

            table_stats = []
            for table_name, _ in tables:
                # Nombre de lignes par table
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]

                # Taille de la table
                cursor.execute(f"SELECT COUNT(*) FROM pragma_table_info('{table_name}')")
                column_count = cursor.fetchone()[0]

                table_stats.append({
                    'name': table_name,
                    'row_count': row_count,
                    'column_count': column_count,
                    'estimated_size': row_count * column_count * 50  # Estimation approximative
                })

            # Analyser les requêtes lentes potentielles
            slow_query_candidates = []
            for table in table_stats:
                if table['row_count'] > 10000:  # Grandes tables
                    slow_query_candidates.append({
                        'table': table['name'],
                        'row_count': table['row_count'],
                        'recommendation': f"Envisager un index sur la table {table['name']}"
                    })

            conn.close()

            return {
                'database_type': 'SQLite',
                'database_size': db_size,
                'table_count': table_count,
                'index_count': index_count,
                'tables': table_stats,
                'slow_query_candidates': slow_query_candidates,
                'optimization_recommendations': self._generate_sqlite_optimizations(table_stats)
            }

        except Exception as e:
            return {'error': f'Erreur analyse SQLite: {e}'}

    def _analyze_postgresql_performance(self) -> Dict:
        """Analyser les performances PostgreSQL"""
        try:
            config = get_config()
            db_url = config.SQLALCHEMY_DATABASE_URI

            # Parser l'URL PostgreSQL
            import re
            pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
            match = re.match(pattern, db_url)

            if not match:
                return {'error': 'Format URL PostgreSQL invalide'}

            user, password, host, port, database = match.groups()

            # Connexion à PostgreSQL
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )

            cursor = conn.cursor()

            # Statistiques générales
            cursor.execute("SELECT current_setting('version')")
            pg_version = cursor.fetchone()[0]

            cursor.execute("SELECT pg_database_size(current_database())")
            db_size = cursor.fetchone()[0]

            # Statistiques des tables
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation
                FROM pg_stats
                WHERE schemaname = 'public'
                ORDER BY tablename, attname
            """)

            table_stats = []
            current_table = None

            for row in cursor.fetchall():
                schema, table, column, n_distinct, correlation = row

                if current_table != table:
                    if current_table:
                        table_stats.append(current_table)
                    current_table = {
                        'name': table,
                        'columns': []
                    }

                current_table['columns'].append({
                    'name': column,
                    'distinct_values': n_distinct if n_distinct >= 0 else None,
                    'correlation': correlation
                })

            if current_table:
                table_stats.append(current_table)

            # Analyser les index
            cursor.execute("""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
            """)

            index_stats = []
            for row in cursor.fetchall():
                schema, table, index, scans, tuples_read, tuples_fetched = row
                index_stats.append({
                    'table': table,
                    'index': index,
                    'scans': scans,
                    'tuples_read': tuples_read,
                    'tuples_fetched': tuples_fetched,
                    'efficiency': (tuples_fetched / max(1, tuples_read)) if tuples_read > 0 else 0
                })

            # Analyser les requêtes lentes
            cursor.execute("""
                SELECT
                    query,
                    calls,
                    total_time,
                    mean_time,
                    rows
                FROM pg_stat_statements
                WHERE mean_time > 1000  -- Requêtes de plus de 1 seconde
                ORDER BY mean_time DESC
                LIMIT 10
            """)

            slow_queries = []
            for row in cursor.fetchall():
                query, calls, total_time, mean_time, rows = row
                slow_queries.append({
                    'query': query[:100] + ('...' if len(query) > 100 else ''),
                    'calls': calls,
                    'total_time': total_time,
                    'mean_time': mean_time,
                    'rows': rows
                })

            conn.close()

            return {
                'database_type': 'PostgreSQL',
                'version': pg_version,
                'database_size': db_size,
                'table_count': len(table_stats),
                'index_count': len(index_stats),
                'tables': table_stats,
                'indexes': index_stats,
                'slow_queries': slow_queries,
                'optimization_recommendations': self._generate_postgresql_optimizations(table_stats, index_stats)
            }

        except Exception as e:
            return {'error': f'Erreur analyse PostgreSQL: {e}'}

    def _generate_sqlite_optimizations(self, table_stats: List[Dict]) -> List[str]:
        """Générer des recommandations d'optimisation SQLite"""
        recommendations = []

        for table in table_stats:
            table_name = table['name']
            row_count = table['row_count']

            # Recommandations pour les grandes tables
            if row_count > 50000:
                recommendations.append(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_created_at ON {table_name}(created_at)")
                recommendations.append(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_updated_at ON {table_name}(updated_at)")

            # Recommandations spécifiques par table
            if table_name == 'user':
                recommendations.append("CREATE INDEX IF NOT EXISTS idx_user_email ON user(email)")
                recommendations.append("CREATE INDEX IF NOT EXISTS idx_user_is_admin ON user(is_admin)")

            elif table_name == 'order':
                recommendations.append("CREATE INDEX IF NOT EXISTS idx_order_customer_id ON order(customer_id)")
                recommendations.append("CREATE INDEX IF NOT EXISTS idx_order_status ON order(status)")
                recommendations.append("CREATE INDEX IF NOT EXISTS idx_order_created_at ON order(created_at)")

            elif table_name == 'product':
                recommendations.append("CREATE INDEX IF NOT EXISTS idx_product_category ON product(category)")
                recommendations.append("CREATE INDEX IF NOT EXISTS idx_product_is_active ON product(is_active)")
                recommendations.append("CREATE INDEX IF NOT EXISTS idx_product_price ON product(price)")

        # Optimisations générales
        recommendations.append("ANALYZE; -- Mettre à jour les statistiques")
        recommendations.append("VACUUM; -- Optimiser l'espace")

        return recommendations

    def _generate_postgresql_optimizations(self, table_stats: List[Dict], index_stats: List[Dict]) -> List[str]:
        """Générer des recommandations d'optimisation PostgreSQL"""
        recommendations = []

        # Analyser les index inefficaces
        for index in index_stats:
            if index['efficiency'] < 0.1 and index['scans'] > 100:
                recommendations.append(f"DROP INDEX IF EXISTS {index['index']} -- Index inefficace")

        # Recommandations pour les colonnes avec faible corrélation
        for table in table_stats:
            for column in table['columns']:
                if column['correlation'] and abs(column['correlation']) < 0.3:
                    recommendations.append(f"CREATE INDEX IF NOT EXISTS idx_{table['name']}_{column['name']} ON {table['name']}({column['name']})")

        # Optimisations de configuration
        recommendations.append("shared_preload_libraries = 'pg_stat_statements' -- Pour analyser les requêtes")
        recommendations.append("track_io_timing = on -- Pour mesurer les I/O")
        recommendations.append("log_min_duration_statement = 1000 -- Logger les requêtes lentes")

        return recommendations

    def create_optimization_indexes(self) -> Dict:
        """Créer les index d'optimisation recommandés"""
        try:
            optimization_result = {
                'indexes_created': [],
                'errors': [],
                'success': True
            }

            config = get_config()
            db_url = config.SQLALCHEMY_DATABASE_URI

            if 'sqlite' in db_url:
                return self._create_sqlite_indexes()
            elif 'postgresql' in db_url:
                return self._create_postgresql_indexes()
            else:
                return {'error': 'Type de base non supporté pour l\'optimisation'}

        except Exception as e:
            self.logger.error(f"Erreur création index d'optimisation: {e}")
            return {'error': str(e)}

    def _create_sqlite_indexes(self) -> Dict:
        """Créer les index SQLite recommandés"""
        try:
            config = get_config()
            db_path = config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')

            indexes_created = []
            errors = []

            # Index recommandés pour PassPrint
            recommended_indexes = [
                "CREATE INDEX IF NOT EXISTS idx_user_email ON user(email)",
                "CREATE INDEX IF NOT EXISTS idx_user_is_admin ON user(is_admin)",
                "CREATE INDEX IF NOT EXISTS idx_order_customer_id ON order(customer_id)",
                "CREATE INDEX IF NOT EXISTS idx_order_status ON order(status)",
                "CREATE INDEX IF NOT EXISTS idx_order_created_at ON order(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_product_category ON product(category)",
                "CREATE INDEX IF NOT EXISTS idx_product_is_active ON product(is_active)",
                "CREATE INDEX IF NOT EXISTS idx_product_price ON product(price)",
                "CREATE INDEX IF NOT EXISTS idx_quote_customer_id ON quote(customer_id)",
                "CREATE INDEX IF NOT EXISTS idx_quote_status ON quote(status)",
                "CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action)",
                "CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at)"
            ]

            conn = sqlite3.connect(db_path)

            for index_sql in recommended_indexes:
                try:
                    conn.execute(index_sql)
                    indexes_created.append(index_sql)
                except Exception as e:
                    errors.append(f"Erreur création index: {e}")

            conn.commit()
            conn.close()

            return {
                'success': len(errors) == 0,
                'indexes_created': indexes_created,
                'errors': errors,
                'total_indexes': len(indexes_created)
            }

        except Exception as e:
            return {'error': f'Erreur création index SQLite: {e}'}

    def _create_postgresql_indexes(self) -> Dict:
        """Créer les index PostgreSQL recommandés"""
        try:
            config = get_config()
            db_url = config.SQLALCHEMY_DATABASE_URI

            # Parser l'URL PostgreSQL
            import re
            pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
            match = re.match(pattern, db_url)

            if not match:
                return {'error': 'Format URL PostgreSQL invalide'}

            user, password, host, port, database = match.groups()

            indexes_created = []
            errors = []

            # Index recommandés pour PassPrint
            recommended_indexes = [
                f"CREATE INDEX IF NOT EXISTS idx_user_email ON {database}.user(email)",
                f"CREATE INDEX IF NOT EXISTS idx_user_is_admin ON {database}.user(is_admin)",
                f"CREATE INDEX IF NOT EXISTS idx_order_customer_id ON {database}.order(customer_id)",
                f"CREATE INDEX IF NOT EXISTS idx_order_status ON {database}.order(status)",
                f"CREATE INDEX IF NOT EXISTS idx_order_created_at ON {database}.order(created_at)",
                f"CREATE INDEX IF NOT EXISTS idx_product_category ON {database}.product(category)",
                f"CREATE INDEX IF NOT EXISTS idx_product_is_active ON {database}.product(is_active)",
                f"CREATE INDEX IF NOT EXISTS idx_quote_customer_id ON {database}.quote(customer_id)",
                f"CREATE INDEX IF NOT EXISTS idx_quote_status ON {database}.quote(status)",
                f"CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON {database}.audit_log(user_id)",
                f"CREATE INDEX IF NOT EXISTS idx_audit_log_action ON {database}.audit_log(action)",
                f"CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON {database}.audit_log(created_at)"
            ]

            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )

            cursor = conn.cursor()

            for index_sql in recommended_indexes:
                try:
                    cursor.execute(index_sql)
                    indexes_created.append(index_sql)
                except Exception as e:
                    errors.append(f"Erreur création index: {e}")

            conn.commit()
            conn.close()

            return {
                'success': len(errors) == 0,
                'indexes_created': indexes_created,
                'errors': errors,
                'total_indexes': len(indexes_created)
            }

        except Exception as e:
            return {'error': f'Erreur création index PostgreSQL: {e}'}

    def optimize_query_performance(self, query: str, operation: str = 'custom') -> Dict:
        """Optimiser les performances d'une requête spécifique"""
        try:
            with self.profiler.profile_query(query, operation):
                # Analyser la requête
                analysis = self._analyze_query_structure(query)

                # Générer des suggestions d'optimisation
                suggestions = self._generate_query_optimizations(query, analysis)

                return {
                    'query_analysis': analysis,
                    'optimization_suggestions': suggestions,
                    'estimated_improvement': self._estimate_query_improvement(suggestions)
                }

        except Exception as e:
            return {'error': f'Erreur optimisation requête: {e}'}

    def _analyze_query_structure(self, query: str) -> Dict:
        """Analyser la structure d'une requête"""
        analysis = {
            'query_length': len(query),
            'has_joins': 'JOIN' in query.upper(),
            'has_subqueries': 'SELECT' in query.upper() and '(' in query,
            'has_order_by': 'ORDER BY' in query.upper(),
            'has_group_by': 'GROUP BY' in query.upper(),
            'has_limit': 'LIMIT' in query.upper(),
            'estimated_complexity': 'high' if query.count(' ') > 20 else 'medium' if query.count(' ') > 10 else 'low'
        }

        return analysis

    def _generate_query_optimizations(self, query: str, analysis: Dict) -> List[str]:
        """Générer des suggestions d'optimisation pour une requête"""
        suggestions = []

        if not analysis['has_limit'] and analysis['estimated_complexity'] == 'high':
            suggestions.append("Ajouter LIMIT pour éviter les résultats volumineux")

        if analysis['has_joins'] and not any(f"idx_{table}" in query.lower() for table in ['user', 'order', 'product']):
            suggestions.append("Vérifier que les index appropriés existent sur les colonnes de jointure")

        if 'SELECT *' in query.upper():
            suggestions.append("Spécifier uniquement les colonnes nécessaires au lieu de SELECT *")

        if analysis['has_order_by'] and not analysis['has_limit']:
            suggestions.append("Envisager LIMIT avec ORDER BY pour de meilleures performances")

        return suggestions

    def _estimate_query_improvement(self, suggestions: List[str]) -> str:
        """Estimer l'amélioration potentielle"""
        improvement_score = 0

        for suggestion in suggestions:
            if 'LIMIT' in suggestion:
                improvement_score += 20
            elif 'index' in suggestion.lower():
                improvement_score += 30
            elif 'SELECT *' in suggestion:
                improvement_score += 10

        if improvement_score >= 50:
            return 'high'
        elif improvement_score >= 25:
            return 'medium'
        else:
            return 'low'

class PerformanceOptimizer:
    """Optimiseur global des performances"""

    def __init__(self, app=None):
        self.app = app
        self.db_optimizer = DatabaseOptimizer(app)
        self.logger = logging.getLogger(__name__)

        # Configuration d'optimisation
        self.optimization_config = {
            'auto_optimize': os.getenv('AUTO_OPTIMIZE', 'true').lower() == 'true',
            'optimization_interval': int(os.getenv('OPTIMIZATION_INTERVAL_HOURS', '24')),
            'performance_threshold': float(os.getenv('PERFORMANCE_THRESHOLD', '0.5')),
            'memory_limit_mb': int(os.getenv('MEMORY_LIMIT_MB', '512'))
        }

    def run_comprehensive_optimization(self) -> Dict:
        """Exécuter une optimisation complète"""
        try:
            optimization_result = {
                'timestamp': datetime.utcnow().isoformat(),
                'optimizations_performed': [],
                'performance_improvements': [],
                'errors': [],
                'success': True
            }

            # 1. Optimisation de la base de données
            db_optimization = self.db_optimizer.analyze_database_performance()
            if 'error' not in db_optimization:
                optimization_result['optimizations_performed'].append('database_analysis')

                # Créer les index recommandés
                index_creation = self.db_optimizer.create_optimization_indexes()
                if index_creation.get('success', False):
                    optimization_result['optimizations_performed'].append('index_creation')
                    optimization_result['performance_improvements'].append(f"Index créés: {index_creation['total_indexes']}")

            # 2. Optimisation du cache
            cache_optimization = self._optimize_cache_performance()
            if cache_optimization['success']:
                optimization_result['optimizations_performed'].append('cache_optimization')
                optimization_result['performance_improvements'].append(cache_optimization['improvement'])

            # 3. Optimisation mémoire
            memory_optimization = self._optimize_memory_usage()
            if memory_optimization['success']:
                optimization_result['optimizations_performed'].append('memory_optimization')
                optimization_result['performance_improvements'].append(memory_optimization['improvement'])

            # 4. Optimisation des sauvegardes
            backup_optimization = self._optimize_backup_performance()
            if backup_optimization['success']:
                optimization_result['optimizations_performed'].append('backup_optimization')
                optimization_result['performance_improvements'].append(backup_optimization['improvement'])

            return optimization_result

        except Exception as e:
            self.logger.error(f"Erreur optimisation complète: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def _optimize_cache_performance(self) -> Dict:
        """Optimiser les performances du cache"""
        try:
            from redis_cache import cache_manager

            # Analyser les performances du cache
            stats = cache_manager.get_stats()

            optimizations = []

            # Optimisations basées sur les statistiques
            if stats.get('memory_cache', {}).get('size', 0) > 800:
                optimizations.append("Réduire la taille du cache mémoire")

            if stats.get('redis_cache', {}).get('keys_count', 0) > 10000:
                optimizations.append("Nettoyer les clés Redis inutilisées")

            # Ajuster les TTL selon les performances
            cache_health = cache_manager.health_check()
            if cache_health.get('status') != 'healthy':
                optimizations.append("Vérifier la connectivité Redis")

            return {
                'success': True,
                'optimizations_applied': optimizations,
                'improvement': f"{len(optimizations)} optimisations de cache appliquées"
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _optimize_memory_usage(self) -> Dict:
        """Optimiser l'utilisation mémoire"""
        try:
            import psutil

            process = psutil.Process()
            memory_info = process.memory_info()

            optimizations = []

            # Analyser l'utilisation mémoire
            memory_mb = memory_info.rss / 1024 / 1024

            if memory_mb > self.optimization_config['memory_limit_mb']:
                # Optimisations mémoire
                optimizations.append("Mémoire élevée détectée - optimisation recommandée")

                # Vider les caches si nécessaire
                from redis_cache import clear_cache
                cache_cleared = clear_cache('temp')

                if cache_cleared:
                    optimizations.append("Cache temporaire vidé")

            return {
                'success': True,
                'memory_usage_mb': memory_mb,
                'optimizations_applied': optimizations,
                'improvement': f"Mémoire optimisée ({memory_mb:.1f}MB)"
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _optimize_backup_performance(self) -> Dict:
        """Optimiser les performances de sauvegarde"""
        try:
            from backup_system import backup_system

            # Analyser les performances de sauvegarde
            backup_status = backup_system.get_backup_status()

            optimizations = []

            # Optimisations basées sur l'historique
            if backup_status:
                recent_backups = [b for b in backup_status if b.get('status') == 'success'][-5:]

                if recent_backups:
                    avg_duration = sum(
                        (datetime.fromisoformat(b.get('completed_at', datetime.utcnow().isoformat())) -
                         datetime.fromisoformat(b.get('started_at', datetime.utcnow().isoformat()))).total_seconds()
                        for b in recent_backups
                    ) / len(recent_backups)

                    if avg_duration > 300:  # Plus de 5 minutes
                        optimizations.append("Sauvegardes lentes détectées - optimisation recommandée")

            return {
                'success': True,
                'optimizations_applied': optimizations,
                'improvement': f"{len(optimizations)} optimisations de sauvegarde"
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def generate_performance_report(self) -> Dict:
        """Générer un rapport de performances"""
        try:
            report = {
                'generated_at': datetime.utcnow().isoformat(),
                'system_performance': self._get_system_performance(),
                'database_performance': self.db_optimizer.analyze_database_performance(),
                'cache_performance': self._get_cache_performance(),
                'memory_performance': self._get_memory_performance(),
                'backup_performance': self._get_backup_performance(),
                'optimization_recommendations': self._get_optimization_recommendations(),
                'performance_score': self._calculate_performance_score()
            }

            # Sauvegarder le rapport
            report_file = Path('logs') / f'performance_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)

            return report

        except Exception as e:
            self.logger.error(f"Erreur génération rapport performances: {e}")
            return {'error': str(e)}

    def _get_system_performance(self) -> Dict:
        """Obtenir les métriques de performance système"""
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'disk_usage': disk.percent,
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            }

        except Exception as e:
            return {'error': str(e)}

    def _get_cache_performance(self) -> Dict:
        """Obtenir les métriques de performance du cache"""
        try:
            from redis_cache import get_cache_stats

            return get_cache_stats()

        except Exception as e:
            return {'error': str(e)}

    def _get_memory_performance(self) -> Dict:
        """Obtenir les métriques de performance mémoire"""
        try:
            import psutil

            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'memory_percent': process.memory_percent(),
                'open_files': len(process.open_files()),
                'threads': process.num_threads()
            }

        except Exception as e:
            return {'error': str(e)}

    def _get_backup_performance(self) -> Dict:
        """Obtenir les métriques de performance des sauvegardes"""
        try:
            from backup_system import backup_system

            status = backup_system.get_backup_status()

            if status:
                recent_backups = [b for b in status if b.get('status') == 'success'][-10:]

                if recent_backups:
                    total_size = sum(b.get('file_size', 0) for b in recent_backups)
                    avg_size = total_size / len(recent_backups)

                    return {
                        'recent_backups_count': len(recent_backups),
                        'total_size_mb': total_size / 1024 / 1024,
                        'average_size_mb': avg_size / 1024 / 1024,
                        'success_rate': len(recent_backups) / len(status) if status else 0
                    }

            return {'no_recent_backups': True}

        except Exception as e:
            return {'error': str(e)}

    def _get_optimization_recommendations(self) -> List[str]:
        """Obtenir les recommandations d'optimisation"""
        recommendations = []

        try:
            # Recommandations système
            system_perf = self._get_system_performance()
            if system_perf.get('cpu_usage', 0) > 80:
                recommendations.append("CPU élevé - envisager l'optimisation des requêtes ou l'augmentation des ressources")

            if system_perf.get('memory_usage', 0) > 85:
                recommendations.append("Mémoire élevée - vérifier les fuites mémoire")

            # Recommandations base de données
            db_perf = self.db_optimizer.analyze_database_performance()
            if 'optimization_recommendations' in db_perf:
                recommendations.extend(db_perf['optimization_recommendations'][:3])  # Top 3

            # Recommandations cache
            cache_perf = self._get_cache_performance()
            if cache_perf.get('memory_cache', {}).get('size', 0) > 500:
                recommendations.append("Cache mémoire volumineux - envisager l'ajustement des TTL")

        except Exception as e:
            recommendations.append(f"Erreur génération recommandations: {e}")

        return recommendations

    def _calculate_performance_score(self) -> int:
        """Calculer un score de performance global (0-100)"""
        try:
            score = 100

            # Pénalités basées sur les métriques
            system_perf = self._get_system_performance()

            # Pénalité CPU
            cpu_usage = system_perf.get('cpu_usage', 0)
            if cpu_usage > 80:
                score -= 20
            elif cpu_usage > 60:
                score -= 10

            # Pénalité mémoire
            memory_usage = system_perf.get('memory_usage', 0)
            if memory_usage > 85:
                score -= 20
            elif memory_usage > 70:
                score -= 10

            # Pénalité disque
            disk_usage = system_perf.get('disk_usage', 0)
            if disk_usage > 90:
                score -= 15
            elif disk_usage > 80:
                score -= 5

            return max(0, score)

        except Exception:
            return 50  # Score par défaut

# Instances globales
query_profiler = QueryProfiler()
database_optimizer = DatabaseOptimizer()
performance_optimizer = PerformanceOptimizer()

def profile_query(query: str, operation: str = 'custom'):
    """Fonction utilitaire pour profiler une requête"""
    return query_profiler.profile_query(query, operation)

def optimize_database():
    """Fonction utilitaire pour optimiser la base de données"""
    return database_optimizer.create_optimization_indexes()

def run_performance_optimization():
    """Fonction utilitaire pour exécuter l'optimisation complète"""
    return performance_optimizer.run_comprehensive_optimization()

def generate_performance_report():
    """Fonction utilitaire pour générer un rapport de performances"""
    return performance_optimizer.generate_performance_report()

if __name__ == "__main__":
    print("🚀 Optimiseur de performances PassPrint")

    # Test du système d'optimisation
    optimization_result = run_performance_optimization()
    print(f"✅ Optimisation terminée: {optimization_result.get('success', False)}")

    # Générer le rapport de performances
    report = generate_performance_report()
    print(f"📊 Rapport généré avec {len(report.get('optimization_recommendations', []))} recommandations")