#!/usr/bin/env python3
"""
Script pour mettre à jour le HTML avec les images WebP et fallbacks
"""
import os
import re

def update_html_with_webp(html_content):
    """Met à jour le contenu HTML pour utiliser WebP avec fallbacks"""

    def replace_img_tag(match):
        img_tag = match.group(0)

        # Extraire src et alt
        src_match = re.search(r'src="([^"]*)"', img_tag)
        alt_match = re.search(r'alt="([^"]*)"', img_tag)

        if not src_match:
            return img_tag

        src = src_match.group(1)
        alt = alt_match.group(1) if alt_match else ""

        # Vérifier si c'est une image locale (pas une URL externe)
        if src.startswith('http') or src.startswith('//'):
            return img_tag

        # Extraire le nom de fichier sans extension
        filename = os.path.basename(src)
        name_without_ext = os.path.splitext(filename)[0]

        # Créer le chemin WebP
        webp_src = f"images/webp/{name_without_ext}.webp"

        # Créer la balise picture
        picture_tag = f'''<picture>
  <source srcset="{webp_src}" type="image/webp">
  <img src="{src}" alt="{alt}" loading="lazy">
</picture>'''

        return picture_tag

    # Pattern pour trouver les balises img
    img_pattern = r'<img[^>]+>'
    updated_content = re.sub(img_pattern, replace_img_tag, html_content)

    return updated_content

def process_html_files():
    """Traite tous les fichiers HTML du projet"""
    html_files = ['index.html']  # Ajouter d'autres fichiers HTML si nécessaire

    for html_file in html_files:
        if not os.path.exists(html_file):
            print(f"Fichier {html_file} non trouve")
            continue

        print(f"Traitement: {html_file}")

        # Lire le contenu
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Mettre à jour le contenu
        updated_content = update_html_with_webp(content)

        # Écrire le contenu mis à jour
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        print(f"  [OK] Mis a jour: {html_file}")

if __name__ == "__main__":
    print("Mise a jour HTML avec WebP")
    print("=" * 30)
    process_html_files()
    print("\nMise a jour terminee!")