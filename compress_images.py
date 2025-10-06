#!/usr/bin/env python3
"""
Script de compression d'images pour PassPrint
Convertit les images en WebP et compresse les originaux
"""
import os
from PIL import Image
import glob

def compress_image(input_path, output_path, quality=80):
    """Compresse une image avec la qualité spécifiée"""
    try:
        with Image.open(input_path) as img:
            # Convertir en RGB si nécessaire (pour les PNG avec transparence)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Créer un fond blanc
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Sauvegarder avec compression
            img.save(output_path, 'JPEG', quality=quality, optimize=True)
            return True
    except Exception as e:
        print(f"Erreur compression {input_path}: {e}")
        return False

def convert_to_webp(input_path, output_path, quality=80):
    """Convertit une image en WebP"""
    try:
        with Image.open(input_path) as img:
            # Convertir en RGB si nécessaire
            if img.mode in ('RGBA', 'LA', 'P'):
                if img.mode == 'P':
                    img = img.convert('RGBA')
                # Pour WebP, on peut garder la transparence
                if img.mode == 'RGBA':
                    img.save(output_path, 'WebP', quality=quality, lossless=False)
                else:
                    img = img.convert('RGB')
                    img.save(output_path, 'WebP', quality=quality, lossless=False)
            else:
                img.save(output_path, 'WebP', quality=quality, lossless=False)
            return True
    except Exception as e:
        print(f"Erreur conversion WebP {input_path}: {e}")
        return False

def process_images():
    """Traite toutes les images du dossier images/"""
    images_dir = 'images'
    if not os.path.exists(images_dir):
        print(f"Dossier {images_dir} non trouvé")
        return

    # Créer dossier pour les WebP
    webp_dir = os.path.join(images_dir, 'webp')
    os.makedirs(webp_dir, exist_ok=True)

    # Extensions à traiter
    extensions = ['*.jpg', '*.jpeg', '*.png']
    processed = 0
    compressed = 0

    for ext in extensions:
        for img_path in glob.glob(os.path.join(images_dir, ext)):
            filename = os.path.basename(img_path)
            name_without_ext = os.path.splitext(filename)[0]

            print(f"Traitement: {filename}")

            # Compresser l'original
            compressed_path = os.path.join(images_dir, f"{name_without_ext}_compressed.jpg")
            if compress_image(img_path, compressed_path, quality=80):
                # Remplacer l'original par la version compressée
                os.replace(compressed_path, img_path)
                compressed += 1
                print(f"  [OK] Compresse: {filename}")

            # Créer version WebP
            webp_path = os.path.join(webp_dir, f"{name_without_ext}.webp")
            if convert_to_webp(img_path, webp_path, quality=80):
                print(f"  [OK] WebP cree: {name_without_ext}.webp")

            processed += 1

    print(f"\nTraitement terminé:")
    print(f"- Images traitées: {processed}")
    print(f"- Images compressées: {compressed}")
    print(f"- Versions WebP créées: {processed}")

if __name__ == "__main__":
    print("Compression des images PassPrint")
    print("=" * 40)
    process_images()
    print("\nCompression terminee!")