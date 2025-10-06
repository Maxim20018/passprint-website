#!/usr/bin/env python3
"""
Script de correction d'encodage pour les fichiers HTML PassPrint
Corrige les caractères mal encodés et vérifie UTF-8
"""
import os
import glob
import re

def fix_encoding(content):
    """Corrige les caractères mal encodés UTF-8"""
    # Dictionnaire des corrections d'encodage
    corrections = {
        'Ã ': 'à',  # a accent grave
        'Ã©': 'é',  # e accent aigu
        'Ã¨': 'è',  # e accent grave
        'Ã ': 'à',  # a accent grave (variante)
        'Ã´': 'ô',  # o accent circonflexe
        'Ã»': 'û',  # u accent circonflexe
        'Ã§': 'ç',  # c cedille
        'â€': '—',  # tiret long
        'â€™': "'",  # apostrophe
        'â€œ': '"',  # guillemet double gauche
        'â€': '"',  # guillemet double droite
        'â€¢': '•',  # puce
        'â€“': '–',  # tiret moyen
        'â€”': '—',  # tiret long
    }

    # Appliquer toutes les corrections
    for wrong, correct in corrections.items():
        content = content.replace(wrong, correct)

    return content

def ensure_utf8_meta(content):
    """S'assure que la balise meta charset UTF-8 est présente"""
    # Vérifier si <meta charset="UTF-8"> existe déjà
    if '<meta charset="UTF-8">' in content or '<meta charset="utf-8">' in content:
        return content

    # Chercher la balise <head>
    head_match = re.search(r'<head[^>]*>', content, re.IGNORECASE)
    if head_match:
        head_tag = head_match.group()
        insert_pos = head_match.end()

        # Insérer la balise meta charset juste après <head>
        meta_tag = '\n    <meta charset="UTF-8">'
        content = content[:insert_pos] + meta_tag + content[insert_pos:]

    return content

def process_html_file(filepath):
    """Traite un fichier HTML individuel"""
    try:
        print(f"Traitement: {filepath}")

        # Lire le fichier
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        original_content = content

        # Corriger l'encodage
        content = fix_encoding(content)

        # S'assurer que UTF-8 est présent
        content = ensure_utf8_meta(content)

        # Écrire seulement si des changements ont été faits
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  [MODIFIE] {filepath}")
            return True
        else:
            print(f"  [OK] {filepath} (aucune modification)")
            return False

    except Exception as e:
        print(f"  [ERREUR] {filepath}: {e}")
        return False

def find_html_files():
    """Trouve tous les fichiers HTML dans le projet"""
    html_files = []

    # Liste des fichiers HTML connus
    known_files = [
        'index.html',
        'admin.html',
        'dashboard.html',
        'index_dashboard.html',
        'monitoring_dashboard.html',
        'test_admin.html',
        'pages/about.html',
        'pages/account.html',
        'pages/blog.html',
        'pages/contact.html',
        'pages/faq.html',
        'pages/privacy.html',
        'pages/services.html',
        'pages/terms.html'
    ]

    for file_path in known_files:
        if os.path.exists(file_path):
            html_files.append(file_path)

    return html_files

def main():
    """Fonction principale"""
    print("Correction d'encodage HTML PassPrint")
    print("=" * 40)

    # Trouver tous les fichiers HTML
    html_files = find_html_files()
    print(f"Fichiers HTML trouves: {len(html_files)}")

    # Traiter chaque fichier
    modified_count = 0
    for html_file in html_files:
        if process_html_file(html_file):
            modified_count += 1

    print("\nResultats:")
    print(f"- Fichiers traites: {len(html_files)}")
    print(f"- Fichiers modifies: {modified_count}")

    if modified_count > 0:
        print("\nCorrections appliquees:")
        print("- Caracteres mal encodes corriges")
        print("- Balises <meta charset=\"UTF-8\"> ajoutees si necessaire")
    else:
        print("\nAucune modification necessaire - tous les fichiers sont corrects")

if __name__ == "__main__":
    main()