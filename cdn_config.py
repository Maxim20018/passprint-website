#!/usr/bin/env python3
"""
Configuration CDN pour PassPrint
Gestion des assets statiques avec CloudFlare et autres CDN
"""
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CDNManager:
    """Gestionnaire de CDN pour PassPrint"""

    def __init__(self, app=None):
        self.app = app
        self.cdn_providers = {
            'cloudflare': {
                'enabled': os.getenv('CLOUDFLARE_ENABLED', 'false').lower() == 'true',
                'zone_id': os.getenv('CLOUDFLARE_ZONE_ID'),
                'api_token': os.getenv('CLOUDFLARE_API_TOKEN'),
                'account_id': os.getenv('CLOUDFLARE_ACCOUNT_ID')
            },
            'aws': {
                'enabled': os.getenv('AWS_CDN_ENABLED', 'false').lower() == 'true',
                'access_key': os.getenv('AWS_ACCESS_KEY_ID'),
                'secret_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
                'region': os.getenv('AWS_REGION', 'us-east-1'),
                'distribution_id': os.getenv('AWS_DISTRIBUTION_ID')
            },
            'local': {
                'enabled': True,  # Toujours disponible comme fallback
                'base_url': os.getenv('CDN_BASE_URL', '/static/'),
                'cache_headers': {
                    'js': 'public, max-age=31536000, immutable',  # 1 an
                    'css': 'public, max-age=31536000, immutable',  # 1 an
                    'images': 'public, max-age=2592000',  # 30 jours
                    'fonts': 'public, max-age=31536000, immutable'  # 1 an
                }
            }
        }

        # Configuration des assets
        self.asset_config = {
            'version': os.getenv('ASSET_VERSION', '1.0.0'),
            'static_dir': Path('static'),
            'uploads_dir': Path('uploads'),
            'cache_busting': os.getenv('CACHE_BUSTING', 'true').lower() == 'true',
            'compression': os.getenv('COMPRESSION_ENABLED', 'true').lower() == 'true'
        }

    def get_asset_url(self, asset_path: str, asset_type: str = 'static') -> str:
        """Obtenir l'URL d'un asset avec gestion CDN"""
        if asset_type == 'static':
            return self._get_static_asset_url(asset_path)
        elif asset_type == 'upload':
            return self._get_upload_asset_url(asset_path)
        else:
            return asset_path

    def _get_static_asset_url(self, asset_path: str) -> str:
        """Obtenir l'URL d'un asset statique"""
        # Nettoyer le chemin
        clean_path = asset_path.strip('/')

        # Vérifier si le fichier existe
        full_path = self.asset_config['static_dir'] / clean_path
        if not full_path.exists():
            logger.warning(f"Asset statique non trouvé: {full_path}")
            return asset_path

        # Générer l'URL avec cache busting si activé
        if self.asset_config['cache_busting']:
            # Utiliser le hash du fichier pour le cache busting
            file_hash = self._get_file_hash(full_path)
            versioned_path = f"{clean_path}?v={file_hash[:8]}"
        else:
            versioned_path = clean_path

        # Choisir le provider CDN
        if self.cdn_providers['cloudflare']['enabled']:
            base_url = os.getenv('CLOUDFLARE_CDN_URL', 'https://cdn.passprint.com')
            return f"{base_url}/{versioned_path}"
        elif self.cdn_providers['aws']['enabled']:
            base_url = os.getenv('AWS_CDN_URL', 'https://passprint.cloudfront.net')
            return f"{base_url}/{versioned_path}"
        else:
            # Utiliser le serveur local
            return f"{self.cdn_providers['local']['base_url']}{versioned_path}"

    def _get_upload_asset_url(self, asset_path: str) -> str:
        """Obtenir l'URL d'un fichier uploadé"""
        clean_path = asset_path.strip('/')

        # Pour les uploads, utiliser principalement le serveur local pour la sécurité
        if self.cdn_providers['cloudflare']['enabled']:
            base_url = os.getenv('CLOUDFLARE_IMAGES_URL', 'https://images.passprint.com')
            return f"{base_url}/{clean_path}"
        else:
            return f"/uploads/{clean_path}"

    def _get_file_hash(self, file_path: Path) -> str:
        """Calculer le hash d'un fichier pour le cache busting"""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            return file_hash
        except Exception as e:
            logger.error(f"Erreur calcul hash fichier {file_path}: {e}")
            return datetime.now().strftime('%Y%m%d%H%M%S')

    def purge_cdn_cache(self, file_paths: list = None, tags: list = None) -> dict:
        """Purger le cache CDN"""
        results = {}

        # CloudFlare
        if self.cdn_providers['cloudflare']['enabled']:
            results['cloudflare'] = self._purge_cloudflare_cache(file_paths, tags)

        # AWS CloudFront
        if self.cdn_providers['aws']['enabled']:
            results['aws'] = self._purge_aws_cache(file_paths)

        return results

    def _purge_cloudflare_cache(self, file_paths: list = None, tags: list = None) -> dict:
        """Purger le cache CloudFlare"""
        try:
            import requests

            url = f"https://api.cloudflare.com/client/v4/zones/{self.cdn_providers['cloudflare']['zone_id']}/purge_cache"

            headers = {
                'Authorization': f'Bearer {self.cdn_providers["cloudflare"]["api_token"]}',
                'Content-Type': 'application/json'
            }

            data = {'purge_everything': False}

            if file_paths:
                data['files'] = [f"https://passprint.com/{path}" for path in file_paths]

            if tags:
                data['tags'] = tags

            response = requests.post(url, headers=headers, json=data, timeout=30)

            if response.status_code == 200:
                return {'status': 'success', 'response': response.json()}
            else:
                return {'status': 'error', 'response': response.text}

        except Exception as e:
            logger.error(f"Erreur purge CloudFlare: {e}")
            return {'status': 'error', 'error': str(e)}

    def _purge_aws_cache(self, file_paths: list = None) -> dict:
        """Purger le cache AWS CloudFront"""
        try:
            import boto3

            client = boto3.client(
                'cloudfront',
                aws_access_key_id=self.cdn_providers['aws']['access_key'],
                aws_secret_access_key=self.cdn_providers['aws']['secret_key'],
                region_name=self.cdn_providers['aws']['region']
            )

            # Créer les paths pour l'invalidation
            paths = ['/*']  # Invalider tout par défaut

            if file_paths:
                paths = file_paths

            response = client.create_invalidation(
                DistributionId=self.cdn_providers['aws']['distribution_id'],
                InvalidationBatch={
                    'Paths': {
                        'Quantity': len(paths),
                        'Items': paths
                    },
                    'CallerReference': f'passprint-{datetime.now().strftime("%Y%m%d%H%M%S")}'
                }
            )

            return {'status': 'success', 'invalidation_id': response['Invalidation']['Id']}

        except Exception as e:
            logger.error(f"Erreur purge AWS: {e}")
            return {'status': 'error', 'error': str(e)}

    def optimize_images(self, image_paths: list) -> dict:
        """Optimiser les images pour le CDN"""
        results = {}

        for image_path in image_paths:
            try:
                full_path = Path(image_path)
                if not full_path.exists():
                    continue

                # Optimisation selon le type d'image
                if image_path.lower().endswith(('.jpg', '.jpeg')):
                    results[image_path] = self._optimize_jpeg(full_path)
                elif image_path.lower().endswith('.png'):
                    results[image_path] = self._optimize_png(full_path)
                elif image_path.lower().endswith('.webp'):
                    results[image_path] = self._optimize_webp(full_path)

            except Exception as e:
                logger.error(f"Erreur optimisation image {image_path}: {e}")
                results[image_path] = {'status': 'error', 'error': str(e)}

        return results

    def _optimize_jpeg(self, image_path: Path) -> dict:
        """Optimiser une image JPEG"""
        try:
            from PIL import Image

            with Image.open(image_path) as img:
                # Convertir en RGB si nécessaire
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Optimiser et sauvegarder
                img.save(
                    image_path,
                    'JPEG',
                    quality=85,
                    optimize=True,
                    progressive=True
                )

            return {
                'status': 'success',
                'original_size': image_path.stat().st_size,
                'format': 'JPEG'
            }

        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def _optimize_png(self, image_path: Path) -> dict:
        """Optimiser une image PNG"""
        try:
            from PIL import Image

            with Image.open(image_path) as img:
                # Optimiser et sauvegarder
                img.save(image_path, 'PNG', optimize=True)

            return {
                'status': 'success',
                'original_size': image_path.stat().st_size,
                'format': 'PNG'
            }

        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def _optimize_webp(self, image_path: Path) -> dict:
        """Optimiser une image WebP"""
        try:
            from PIL import Image

            with Image.open(image_path) as img:
                # Convertir en RGB si nécessaire
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Sauvegarder en WebP avec optimisation
                webp_path = image_path.with_suffix('.webp')
                img.save(webp_path, 'WEBP', quality=85)

            return {
                'status': 'success',
                'original_size': image_path.stat().st_size,
                'webp_size': webp_path.stat().st_size,
                'format': 'WebP'
            }

        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def generate_manifest(self) -> dict:
        """Générer le manifest des assets pour le cache busting"""
        manifest = {
            'version': self.asset_config['version'],
            'generated_at': datetime.utcnow().isoformat(),
            'assets': {}
        }

        try:
            # Parcourir les fichiers statiques
            static_dir = self.asset_config['static_dir']
            if static_dir.exists():
                for asset_file in static_dir.rglob('*'):
                    if asset_file.is_file() and not asset_file.name.startswith('.'):
                        relative_path = asset_file.relative_to(static_dir)
                        file_hash = self._get_file_hash(asset_file)

                        manifest['assets'][str(relative_path)] = {
                            'hash': file_hash,
                            'size': asset_file.stat().st_size,
                            'modified': asset_file.stat().st_mtime,
                            'url': self.get_asset_url(str(relative_path))
                        }

            # Sauvegarder le manifest
            manifest_path = static_dir / 'manifest.json'
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)

            return manifest

        except Exception as e:
            logger.error(f"Erreur génération manifest: {e}")
            return {'error': str(e)}

    def get_cache_headers(self, file_path: str) -> dict:
        """Obtenir les headers de cache appropriés pour un fichier"""
        extension = Path(file_path).suffix.lower().lstrip('.')

        # Configuration des headers par type de fichier
        cache_config = {
            'js': {
                'Cache-Control': 'public, max-age=31536000, immutable',
                'Content-Encoding': 'gzip' if self.asset_config['compression'] else None
            },
            'css': {
                'Cache-Control': 'public, max-age=31536000, immutable',
                'Content-Encoding': 'gzip' if self.asset_config['compression'] else None
            },
            'jpg': {'Cache-Control': 'public, max-age=2592000'},
            'jpeg': {'Cache-Control': 'public, max-age=2592000'},
            'png': {'Cache-Control': 'public, max-age=2592000'},
            'gif': {'Cache-Control': 'public, max-age=2592000'},
            'svg': {'Cache-Control': 'public, max-age=31536000'},
            'woff': {'Cache-Control': 'public, max-age=31536000'},
            'woff2': {'Cache-Control': 'public, max-age=31536000'},
            'html': {'Cache-Control': 'public, max-age=3600, must-revalidate'},
            'pdf': {'Cache-Control': 'public, max-age=86400'}
        }

        return cache_config.get(extension, {'Cache-Control': 'public, max-age=3600'})

# Instance globale du CDN manager
cdn_manager = CDNManager()

def get_asset_url(asset_path: str, asset_type: str = 'static') -> str:
    """Fonction utilitaire pour obtenir l'URL d'un asset"""
    return cdn_manager.get_asset_url(asset_path, asset_type)

def purge_cdn_cache(file_paths: list = None, tags: list = None) -> dict:
    """Fonction utilitaire pour purger le cache CDN"""
    return cdn_manager.purge_cdn_cache(file_paths, tags)

def optimize_images(image_paths: list) -> dict:
    """Fonction utilitaire pour optimiser les images"""
    return cdn_manager.optimize_images(image_paths)

def generate_asset_manifest() -> dict:
    """Fonction utilitaire pour générer le manifest des assets"""
    return cdn_manager.generate_manifest()

def get_cache_headers(file_path: str) -> dict:
    """Fonction utilitaire pour obtenir les headers de cache"""
    return cdn_manager.get_cache_headers(file_path)

if __name__ == "__main__":
    print("🌐 Gestionnaire CDN PassPrint configuré")

    # Test du système CDN
    test_url = get_asset_url('css/style.css')
    print(f"URL d'asset: {test_url}")

    # Générer le manifest
    manifest = generate_asset_manifest()
    print(f"Manifest généré avec {len(manifest.get('assets', {}))} assets")