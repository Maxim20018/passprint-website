#!/usr/bin/env python3
"""
Script simplifié de génération des favicons pour PassPrint
Utilise Pillow uniquement pour créer des favicons basiques
"""
import os
from PIL import Image, ImageDraw, ImageFont
import math

def create_simple_logo(size):
    """Crée un logo simple pour favicon"""
    # Créer une image carrée
    img = Image.new('RGBA', (size, size), (255, 107, 53, 255))  # Couleur principale #FF6B35
    draw = ImageDraw.Draw(img)

    # Ajouter un cercle blanc au centre
    center = size // 2
    radius = int(size * 0.35)
    draw.ellipse(
        [(center - radius, center - radius), (center + radius, center + radius)],
        fill=(255, 255, 255, 255)
    )

    # Ajouter un petit carré noir (représentant l'impression)
    square_size = int(size * 0.15)
    square_pos = int(size * 0.25)
    draw.rectangle(
        [square_pos, square_pos, square_pos + square_size, square_pos + square_size],
        fill=(0, 0, 0, 255)
    )

    return img

def create_favicon_ico(sizes, output_path):
    """Crée un fichier .ico multi-résolutions"""
    try:
        images = []
        for size in sizes:
            img = create_simple_logo(size)
            images.append(img)

        # Sauvegarder comme .ico
        if images:
            images[0].save(
                output_path,
                format='ICO',
                sizes=[(img.size[0], img.size[1]) for img in images],
                append_images=images[1:]
            )
            print(f"  [OK] ICO cree: {output_path}")
            return True

    except Exception as e:
        print(f"  [ERREUR] Creation ICO: {e}")
        return False

def generate_favicons():
    """Génère tous les favicons nécessaires"""
    images_dir = 'images'
    if not os.path.exists(images_dir):
        print(f"Dossier {images_dir} non trouve")
        return

    print("Generation des favicons PassPrint (version simplifiee)")
    print("=" * 50)

    # 1. Générer favicon.ico (multi-résolutions)
    ico_sizes = [16, 32, 48]
    ico_path = os.path.join(images_dir, "favicon.ico")
    if create_favicon_ico(ico_sizes, ico_path):
        print("  [OK] favicon.ico genere avec tailles 16x16, 32x32, 48x48")

    # 2. Générer favicon-32x32.png
    png32 = create_simple_logo(32)
    png32_path = os.path.join(images_dir, "favicon-32x32.png")
    png32.save(png32_path, 'PNG')
    print(f"  [OK] PNG cree: {png32_path} (32x32)")

    # 3. Générer favicon-16x16.png
    png16 = create_simple_logo(16)
    png16_path = os.path.join(images_dir, "favicon-16x16.png")
    png16.save(png16_path, 'PNG')
    print(f"  [OK] PNG cree: {png16_path} (16x16)")

    # 4. Générer apple-touch-icon.png (180x180)
    apple_icon = create_simple_logo(180)
    apple_path = os.path.join(images_dir, "apple-touch-icon.png")
    apple_icon.save(apple_path, 'PNG')
    print(f"  [OK] PNG cree: {apple_path} (180x180)")

    print("\nGeneration terminee!")
    print("Fichiers crees:")
    print("- favicon.ico (16x16, 32x32, 48x48)")
    print("- favicon-32x32.png")
    print("- favicon-16x16.png")
    print("- apple-touch-icon.png (180x180)")
    print("\nNote: Favicons simplifies crees avec Pillow")
    print("Pour des favicons plus sophistiques, utiliser RealFaviconGenerator.net")

if __name__ == "__main__":
    generate_favicons()