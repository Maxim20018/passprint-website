#!/usr/bin/env python3
"""
Load balancer pour PassPrint
Répartit la charge entre plusieurs serveurs
"""
import random
import requests
from typing import List

class LoadBalancer:
    """Load balancer simple"""

    def __init__(self, servers: List[str]):
        self.servers = servers
        self.current_index = 0

    def get_server(self) -> str:
        """Obtenir un serveur (round-robin)"""
        server = self.servers[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.servers)
        return server

    def get_healthy_server(self) -> str:
        """Obtenir un serveur sain"""
        for _ in range(len(self.servers)):
            server = self.get_server()
            if self._check_health(server):
                return server
        return self.servers[0]  # Fallback

    def _check_health(self, server: str) -> bool:
        """Vérifier la santé d'un serveur"""
        try:
            response = requests.get(f"http://{server}/api/health", timeout=1)
            return response.status_code == 200
        except:
            return False

# Configuration load balancer
load_balancer = LoadBalancer([
    'localhost:5000',
    'localhost:5001',
    'localhost:5002'
])

def get_server():
    """Obtenir un serveur disponible"""
    return load_balancer.get_healthy_server()

if __name__ == "__main__":
    print("Load balancer opérationnel!")