#!/usr/bin/env python3
"""
Script de minification des assets CSS et JS pour PassPrint
Utilise rcssmin et rjsmin pour optimiser les performances
"""
import os
import rcssmin
import rjsmin

def minify_css(input_file, output_file):
    """Minifie un fichier CSS"""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            css_content = f.read()

        # Minifier le CSS
        minified_css = rcssmin.cssmin(css_content)

        # Écrire le fichier minifié
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(minified_css)

        # Calculer la réduction
        original_size = len(css_content.encode('utf-8'))
        minified_size = len(minified_css.encode('utf-8'))
        reduction = ((original_size - minified_size) / original_size) * 100

        print(f"  [OK] CSS minifie: {output_file}")
        print(f"    Reduction: {reduction:.1f}%")
        return True

    except Exception as e:
        print(f"  [ERREUR] Minification CSS: {e}")
        return False

def minify_js(input_file, output_file):
    """Minifie un fichier JavaScript"""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            js_content = f.read()

        # Minifier le JavaScript
        minified_js = rjsmin.jsmin(js_content)

        # Écrire le fichier minifié
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(minified_js)

        # Calculer la réduction
        original_size = len(js_content.encode('utf-8'))
        minified_size = len(minified_js.encode('utf-8'))
        reduction = ((original_size - minified_size) / original_size) * 100

        print(f"  [OK] JS minifie: {output_file}")
        print(f"    Reduction: {reduction:.1f}%")
        return True

    except Exception as e:
        print(f"  [ERREUR] Minification JS: {e}")
        return False

def update_html_links(html_file, css_file, js_file):
    """Met à jour les liens dans le fichier HTML"""
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remplacer les liens CSS
        css_pattern = r'href="css/style\.css"'
        css_replacement = f'href="{css_file}"'
        content = content.replace('href="css/style.css"', css_replacement)

        # Remplacer les liens JS
        js_pattern = r'src="js/script\.js"'
        js_replacement = f'src="{js_file}"'
        content = content.replace('src="js/script.js"', js_replacement)

        # Écrire le fichier mis à jour
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  [OK] HTML mis a jour: {html_file}")
        return True

    except Exception as e:
        print(f"  [ERREUR] Mise a jour HTML: {e}")
        return False

def main():
    """Fonction principale"""
    print("Minification des assets PassPrint")
    print("=" * 35)

    # Chemins des fichiers
    css_input = 'css/style.css'
    css_output = 'css/style.min.css'
    js_input = 'js/script.js'
    js_output = 'js/script.min.js'
    html_file = 'index.html'

    # Vérifier que les fichiers existent
    if not os.path.exists(css_input):
        print(f"  [ERREUR] Fichier CSS non trouve: {css_input}")
        return

    if not os.path.exists(js_input):
        print(f"  [ERREUR] Fichier JS non trouve: {js_input}")
        return

    # Minifier le CSS
    print("Minification CSS...")
    css_success = minify_css(css_input, css_output)

    # Minifier le JavaScript
    print("\nMinification JavaScript...")
    js_success = minify_js(js_input, js_output)

    # Mettre à jour les liens HTML
    print("\nMise a jour des liens HTML...")
    html_success = update_html_links(html_file, css_output, js_output)

    # Résumé
    print("\nResultats:")
    print(f"- CSS minifie: {'OK' if css_success else 'ERREUR'}")
    print(f"- JS minifie: {'OK' if js_success else 'ERREUR'}")
    print(f"- HTML mis a jour: {'OK' if html_success else 'ERREUR'}")

    if css_success and js_success and html_success:
        print("\nMinification reussie !")
        print("Fichiers crees:")
        print(f"- {css_output}")
        print(f"- {js_output}")
        print(f"- {html_file} (liens mis a jour)")
    else:
        print("\nDes erreurs sont survenues lors de la minification.")

if __name__ == "__main__":
    main()