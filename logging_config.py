#!/usr/bin/env python3
"""
Configuration complète du système de logging pour PassPrint
Supporte la rotation, les niveaux multiples, et l'export externe
"""
import os
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
import json
import sys

class JSONFormatter(logging.Formatter):
    """Formatter JSON pour les logs structurés"""

    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'process': record.process
        }

        # Ajouter les informations de sécurité si disponibles
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
        if hasattr(record, 'user_agent'):
            log_entry['user_agent'] = record.user_agent
        if hasattr(record, 'resource_type'):
            log_entry['resource_type'] = record.resource_type
        if hasattr(record, 'resource_id'):
            log_entry['resource_id'] = record.resource_id

        # Ajouter les métriques de performance si disponibles
        if hasattr(record, 'duration'):
            log_entry['duration_ms'] = record.duration
        if hasattr(record, 'memory_usage'):
            log_entry['memory_mb'] = record.memory_usage
        if hasattr(record, 'cpu_usage'):
            log_entry['cpu_percent'] = record.cpu_usage

        # Ajouter les informations d'erreur si disponibles
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)

class SecurityFormatter(logging.Formatter):
    """Formatter spécialisé pour les événements de sécurité"""

    def format(self, record):
        return json.dumps({
            'timestamp': datetime.utcnow().isoformat(),
            'level': 'SECURITY',
            'event_type': getattr(record, 'event_type', 'security_event'),
            'user_id': getattr(record, 'user_id', None),
            'action': getattr(record, 'action', 'unknown'),
            'details': record.getMessage(),
            'ip_address': getattr(record, 'ip_address', None),
            'user_agent': getattr(record, 'user_agent', None),
            'resource_type': getattr(record, 'resource_type', None),
            'resource_id': getattr(record, 'resource_id', None),
            'status': getattr(record, 'status', 'unknown'),
            'severity': getattr(record, 'severity', 'medium')
        }, ensure_ascii=False)

def setup_logging(app=None):
    """Configurer le système de logging complet"""

    # Créer le dossier des logs
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    # Configuration de base
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'json': {
                '()': JSONFormatter,
            },
            'security': {
                '()': SecurityFormatter,
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'detailed',
                'stream': sys.stdout
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'json',
                'filename': log_dir / 'app.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 10,
                'encoding': 'utf-8'
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'json',
                'filename': log_dir / 'error.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 20,
                'encoding': 'utf-8'
            },
            'security_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'security',
                'filename': log_dir / 'security.log',
                'maxBytes': 52428800,  # 50MB
                'backupCount': 5,
                'encoding': 'utf-8'
            },
            'audit_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'json',
                'filename': log_dir / 'audit.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 30,
                'encoding': 'utf-8'
            }
        },
        'loggers': {
            'app': {
                'level': 'INFO',
                'handlers': ['console', 'file', 'error_file'],
                'propagate': False
            },
            'security': {
                'level': 'INFO',
                'handlers': ['security_file', 'audit_file'],
                'propagate': False
            },
            'database': {
                'level': 'WARNING',
                'handlers': ['file', 'error_file'],
                'propagate': False
            },
            'payment': {
                'level': 'INFO',
                'handlers': ['file', 'audit_file'],
                'propagate': False
            },
            'api': {
                'level': 'INFO',
                'handlers': ['file'],
                'propagate': False
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['console', 'file']
        }
    }

    # Ajuster selon l'environnement
    if app and hasattr(app, 'config'):
        flask_env = app.config.get('ENVIRONMENT', 'development')

        if flask_env == 'production':
            # En production, moins de logs console
            config['handlers']['console']['level'] = 'WARNING'
            config['root']['level'] = 'INFO'
            config['loggers']['app']['level'] = 'INFO'

            # Ajouter un handler pour les logs externes si configuré
            external_log_url = os.getenv('EXTERNAL_LOG_URL')
            if external_log_url:
                config['handlers']['external'] = {
                    'class': 'logging.handlers.HTTPHandler',
                    'host': external_log_url,
                    'url': '/logs',
                    'method': 'POST',
                    'level': 'ERROR',
                    'formatter': 'json'
                }
                config['loggers']['app']['handlers'].append('external')
                config['loggers']['security']['handlers'].append('external')

        elif flask_env == 'development':
            # En développement, plus de logs console
            config['handlers']['console']['level'] = 'DEBUG'
            config['root']['level'] = 'DEBUG'

    # Appliquer la configuration
    import logging.config
    logging.config.dictConfig(config)

    # Créer les loggers principaux
    logger = logging.getLogger('app')
    security_logger = logging.getLogger('security')

    return logger, security_logger

class LoggerMixin:
    """Mixin pour ajouter le logging aux classes"""

    @property
    def logger(self):
        class_name = self.__class__.__name__
        return logging.getLogger(f'app.{class_name.lower()}')

def log_security_event(action: str, details: str, user_id: str = None,
                      ip_address: str = None, user_agent: str = None,
                      resource_type: str = None, resource_id: str = None,
                      status: str = 'success', severity: str = 'medium'):
    """Fonction utilitaire pour logger les événements de sécurité"""
    security_logger = logging.getLogger('security')

    # Créer un objet log avec les attributs personnalisés
    class SecurityLogRecord(logging.LogRecord):
        def __init__(self, action, details, user_id, ip_address, user_agent,
                     resource_type, resource_id, status, severity):
            super().__init__(
                name='security', level=logging.INFO, pathname='', lineno=0,
                msg=details, args=(), exc_info=None
            )
            self.action = action
            self.user_id = user_id
            self.ip_address = ip_address
            self.user_agent = user_agent
            self.resource_type = resource_type
            self.resource_id = resource_id
            self.status = status
            self.severity = severity

    # Créer et logger l'enregistrement
    record = SecurityLogRecord(action, details, user_id, ip_address, user_agent,
                              resource_type, resource_id, status, severity)
    security_logger.handle(record)

def log_api_request(endpoint: str, method: str, status_code: int, duration: float = None,
                   user_id: str = None, ip_address: str = None):
    """Logger une requête API"""
    logger = logging.getLogger('api')

    class APIRequestRecord(logging.LogRecord):
        def __init__(self, endpoint, method, status_code, duration, user_id, ip_address):
            super().__init__(
                name='api', level=logging.INFO, pathname='', lineno=0,
                msg=f'{method} {endpoint} - {status_code}', args=(), exc_info=None
            )
            self.endpoint = endpoint
            self.method = method
            self.status_code = status_code
            self.duration = duration
            self.user_id = user_id
            self.ip_address = ip_address

    record = APIRequestRecord(endpoint, method, status_code, duration, user_id, ip_address)
    logger.handle(record)

def log_database_operation(operation: str, table: str, duration: float = None,
                          records_affected: int = None, error: str = None):
    """Logger une opération de base de données"""
    logger = logging.getLogger('database')

    class DatabaseLogRecord(logging.LogRecord):
        def __init__(self, operation, table, duration, records_affected, error):
            level = logging.ERROR if error else logging.INFO
            super().__init__(
                name='database', level=level, pathname='', lineno=0,
                msg=f'{operation} on {table}', args=(), exc_info=None
            )
            self.operation = operation
            self.table = table
            self.duration = duration
            self.records_affected = records_affected
            self.error = error

    record = DatabaseLogRecord(operation, table, duration, records_affected, error)
    logger.handle(record)

# Classe de contexte pour mesurer les performances
class PerformanceLogger:
    """Context manager pour mesurer et logger les performances"""

    def __init__(self, operation: str, logger_name: str = 'app'):
        self.operation = operation
        self.logger = logging.getLogger(logger_name)
        self.start_time = None
        self.start_memory = None

    def __enter__(self):
        self.start_time = time.time()

        # Mesurer la mémoire si psutil est disponible
        try:
            import psutil
            process = psutil.Process()
            self.start_memory = process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            pass

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time

        # Créer l'enregistrement de log
        class PerformanceLogRecord(logging.LogRecord):
            def __init__(self, operation, duration, memory_usage, exc_type):
                level = logging.ERROR if exc_type else logging.INFO
                super().__init__(
                    name='app', level=level, pathname='', lineno=0,
                    msg=f'{operation} completed in {duration:.3f}s', args=(), exc_info=(exc_type, exc_val, exc_tb)
                )
                self.operation = operation
                self.duration = duration * 1000  # Convertir en millisecondes
                self.memory_usage = memory_usage
                self.error = exc_type is not None

        record = PerformanceLogRecord(self.operation, duration, self.start_memory, exc_type)
        self.logger.handle(record)

# Fonction utilitaire pour créer des loggers personnalisés
def get_logger(name: str, level: str = 'INFO'):
    """Obtenir un logger configuré"""
    logger = logging.getLogger(f'app.{name}')
    logger.setLevel(getattr(logging, level.upper()))
    return logger

# Configuration pour les tests
def setup_test_logging():
    """Configuration minimale pour les tests"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )

    # Désactiver les handlers existants
    for logger_name in ['app', 'security', 'database', 'payment', 'api']:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True

if __name__ == "__main__":
    print("📝 Configuration du logging PassPrint")
    logger, security_logger = setup_logging()

    # Test des loggers
    logger.info("Test du logger principal")
    security_logger.info("Test du logger de sécurité")

    print("✅ Configuration du logging terminée")