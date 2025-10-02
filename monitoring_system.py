#!/usr/bin/env python3
"""
Système de monitoring pour PassPrint
Surveille les performances et l'état du système
"""
import psutil
import time
from datetime import datetime
import threading

class MonitoringSystem:
    """Système de monitoring"""

    def __init__(self):
        self.metrics = {
            'cpu_usage': [],
            'memory_usage': [],
            'disk_usage': [],
            'network_io': [],
            'response_times': []
        }
        self.monitoring = True

    def get_system_metrics(self):
        """Récupérer les métriques système"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'network_bytes_sent': psutil.net_io_counters().bytes_sent,
            'network_bytes_recv': psutil.net_io_counters().bytes_recv,
            'timestamp': datetime.utcnow().isoformat()
        }

    def start_monitoring(self):
        """Démarrer le monitoring"""
        def monitor():
            while self.monitoring:
                metrics = self.get_system_metrics()
                for key, value in metrics.items():
                    if key != 'timestamp':
                        self.metrics[f'{key}'].append(value)
                        # Garder seulement les 100 dernières valeurs
                        if len(self.metrics[f'{key}']) > 100:
                            self.metrics[f'{key}'] = self.metrics[f'{key}'][-100:]

                time.sleep(5)  # Monitoring toutes les 5 secondes

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

    def get_metrics_summary(self):
        """Résumé des métriques"""
        return {
            'current': self.get_system_metrics(),
            'averages': {
                key: sum(values) / len(values) if values else 0
                for key, values in self.metrics.items()
            },
            'peaks': {
                key: max(values) if values else 0
                for key, values in self.metrics.items()
            }
        }

# Instance globale du monitoring
monitoring_system = MonitoringSystem()

def get_system_metrics():
    """Obtenir les métriques système"""
    return monitoring_system.get_system_metrics()

def get_monitoring_summary():
    """Obtenir le résumé du monitoring"""
    return monitoring_system.get_metrics_summary()

if __name__ == "__main__":
    print("Système de monitoring opérationnel!")