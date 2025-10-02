#!/usr/bin/env python3
"""
Gestionnaire CDN pour PassPrint
Optimise la distribution des fichiers statiques
"""
import os
import hashlib
import time

class CDNManager:
    """Gestionnaire CDN"""

    def __init__(self):
        self.static_files = {}
        self.cache_busters = {}

    def add_static_file(self, filepath: str):
        """Ajouter un fichier statique"""
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                content = f.read()
                file_hash = hashlib.md5(content).hexdigest()[:8]
                self.static_files[filepath] = {
                    'hash': file_hash,
                    'size': len(content),
                    'last_modified': os.path.getmtime(filepath)
                }
                return file_hash
        return None

    def get_cache_busted_url(self, filepath: str) -> str:
        """Obtenir l'URL avec cache buster"""
        file_hash = self.add_static_file(filepath)
        if file_hash:
            return f"{filepath}?v={file_hash}"
        return filepath

# Instance globale du CDN manager
cdn_manager = CDNManager()

def get_cache_busted_url(filepath: str) -> str:
    """Obtenir l'URL avec cache buster"""
    return cdn_manager.get_cache_busted_url(filepath)

if __name__ == "__main__":
    print("Gestionnaire CDN opérationnel!")