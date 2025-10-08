#!/usr/bin/env python3
"""
Script de génération des favicons pour PassPrint
Génère tous les formats nécessaires à partir du logo.svg
"""
import os
import cairosvg
from PIL import Image
import io

def svg_to_png(svg_path, png_path, size):
    """Convertit SVG en PNG à la taille spécifiée"""
    try:
        # Convertir SVG en PNG avec cairosvg
        cairosvg.svg2png(
            url=svg_path,
            write_to=png_path,
            output_width=size,
            output_height=size,
            scale=1.0
        )
        print(f"  [OK] PNG cree: {png_path} ({size}x{size})")
        return True
    except Exception as e:
        print(f"  [ERREUR] Conversion SVG: {e}")
        return False

def create_favicon_ico(sizes, output_path):
    """Crée un fichier .ico multi-résolutions"""
    try:
        images = []
        for size in sizes:
            png_path = f"temp_favicon_{size}.png"
            if svg_to_png("images/logo.svg", png_path, size):
                img = Image.open(png_path)
                # Convertir en mode RGBA si nécessaire
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                images.append(img)
            else:
                return False

        # Sauvegarder comme .ico
        if images:
            images[0].save(
                output_path,
                format='ICO',
                sizes=[(img.size[0], img.size[1]) for img in images],
                append_images=images[1:]
            )
            print(f"  [OK] ICO cree: {output_path}")

        # Nettoyer les fichiers temporaires
        for size in sizes:
            temp_file = f"temp_favicon_{size}.png"
            if os.path.exists(temp_file):
                os.remove(temp_file)

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

    print("Generation des favicons PassPrint")
    print("=" * 35)

    # Vérifier que le logo.svg existe
    svg_path = os.path.join(images_dir, "logo.svg")
    if not os.path.exists(svg_path):
        print(f"Logo SVG non trouve: {svg_path}")
        return

    print(f"Source: {svg_path}")

    # 1. Générer favicon.ico (multi-résolutions)
    ico_sizes = [16, 32, 48]
    ico_path = os.path.join(images_dir, "favicon.ico")
    if create_favicon_ico(ico_sizes, ico_path):
        print("  [OK] favicon.ico genere avec tailles 16x16, 32x32, 48x48")

    # 2. Générer favicon-32x32.png
    png32_path = os.path.join(images_dir, "favicon-32x32.png")
    svg_to_png(svg_path, png32_path, 32)

    # 3. Générer favicon-16x16.png
    png16_path = os.path.join(images_dir, "favicon-16x16.png")
    svg_to_png(svg_path, png16_path, 16)

    # 4. Générer apple-touch-icon.png (180x180)
    apple_path = os.path.join(images_dir, "apple-touch-icon.png")
    svg_to_png(svg_path, apple_path, 180)

    print("\nGeneration terminee!")
    print("Fichiers crees:")
    print("- favicon.ico (16x16, 32x32, 48x48)")
    print("- favicon-32x32.png")
    print("- favicon-16x16.png")
    print("- apple-touch-icon.png (180x180)")

if __name__ == "__main__":
    generate_favicons()