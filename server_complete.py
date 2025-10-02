#!/usr/bin/env python3
"""
Serveur PassPrint Complet - Version qui fonctionne
Sert tous les fichiers correctement
"""
from flask import Flask, send_from_directory, jsonify, render_template_string
import os

app = Flask(__name__)

# Template HTML de test
TEST_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PassPrint - Site Web d'Imprimerie</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body {
            background: linear-gradient(135deg, #2D1B69 0%, #FF6B35 100%);
            color: white;
            font-family: 'Inter', sans-serif;
        }
        .hero {
            padding: 4rem 0;
            text-align: center;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            margin: 2rem 0;
        }
        .btn {
            border-radius: 25px;
            padding: 1rem 2rem;
            margin: 1rem;
        }
        .service-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 2rem;
            border-radius: 15px;
            margin: 1rem 0;
            transition: all 0.3s ease;
        }
        .service-card:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.15);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1 class="display-4">
                <i class="fas fa-print text-warning me-3"></i>
                PassPrint
            </h1>
            <p class="lead">Imprimerie Professionnelle à Douala</p>
            <p>Services d'impression premium, banderoles, stickers, panneaux, clés USB</p>

            <div class="d-flex justify-content-center gap-3 flex-wrap">
                <a href="index.html" class="btn btn-warning">
                    <i class="fas fa-home me-2"></i>Accueil
                </a>
                <a href="pages/services.html" class="btn btn-success">
                    <i class="fas fa-cogs me-2"></i>Nos Services
                </a>
                <a href="pages/contact.html" class="btn btn-info">
                    <i class="fas fa-phone me-2"></i>Contact
                </a>
                <a href="dashboard.html" class="btn btn-primary">
                    <i class="fas fa-tachometer-alt me-2"></i>Dashboard
                </a>
            </div>
        </div>

        <div class="row">
            <div class="col-md-6">
                <div class="service-card">
                    <h3><i class="fas fa-flag text-warning me-2"></i>Banderoles Publicitaires</h3>
                    <p>Grand format professionnel pour vos événements et campagnes publicitaires.</p>
                    <p><strong>Prix:</strong> 25,000 FCFA/m²</p>
                </div>
            </div>
            <div class="col-md-6">
                <div class="service-card">
                    <h3><i class="fas fa-sticky-note text-warning me-2"></i>Stickers Personnalisés</h3>
                    <p>Autocollants vinyle avec découpe sur mesure pour votre communication.</p>
                    <p><strong>Prix:</strong> 15,000 FCFA/100 pièces</p>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-6">
                <div class="service-card">
                    <h3><i class="fas fa-cube text-warning me-2"></i>Panneaux Rigides</h3>
                    <p>Supports rigides premium pour signalétique intérieure et extérieure.</p>
                    <p><strong>Prix:</strong> 45,000 FCFA/m²</p>
                </div>
            </div>
            <div class="col-md-6">
                <div class="service-card">
                    <h3><i class="fas fa-usb text-warning me-2"></i>Clés USB Corporate</h3>
                    <p>Supports de stockage personnalisables avec votre logo.</p>
                    <p><strong>Prix:</strong> 8,500 FCFA/32GB</p>
                </div>
            </div>
        </div>

        <div class="text-center mt-5">
            <h2>Contactez-nous</h2>
            <div class="row">
                <div class="col-md-4">
                    <i class="fas fa-phone fa-2x text-warning mb-2"></i>
                    <p>696 465 609<br>677 863 752</p>
                </div>
                <div class="col-md-4">
                    <i class="fas fa-envelope fa-2x text-warning mb-2"></i>
                    <p>passprint@yahoo.com</p>
                </div>
                <div class="col-md-4">
                    <i class="fas fa-map-marker-alt fa-2x text-warning mb-2"></i>
                    <p>Douala, Cameroun<br>Angerapheal</p>
                </div>
            </div>
        </div>

        <div class="text-center mt-5">
            <h3>🚀 Fonctionnalités Disponibles</h3>
            <div class="row mt-4">
                <div class="col-md-4">
                    <div class="service-card">
                        <h4>✅ Site Web Complet</h4>
                        <p>Interface professionnelle responsive</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="service-card">
                        <h4>✅ Dashboard Admin</h4>
                        <p>Gestion complète de l'entreprise</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="service-card">
                        <h4>✅ API Backend</h4>
                        <p>Services web professionnels</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

@app.route('/')
def index():
    """Page d'accueil principale"""
    try:
        # Essayer de servir le fichier index.html existant
        if os.path.exists('index.html'):
            with open('index.html', 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # Retourner le template de test
            return TEST_HTML
    except Exception as e:
        return TEST_HTML

@app.route('/index.html')
def index_file():
    """Servir le fichier index.html"""
    try:
        return send_from_directory('.', 'index.html')
    except FileNotFoundError:
        return TEST_HTML

@app.route('/dashboard.html')
def dashboard():
    """Dashboard d'administration"""
    try:
        return send_from_directory('.', 'dashboard.html')
    except FileNotFoundError:
        return "Dashboard non trouvé", 404

@app.route('/admin.html')
def admin():
    """Interface d'administration"""
    try:
        return send_from_directory('.', 'admin.html')
    except FileNotFoundError:
        return "Admin non trouvé", 404

@app.route('/api/health')
def health():
    """Santé de l'API"""
    return jsonify({
        'status': 'OK',
        'message': 'Serveur PassPrint fonctionne',
        'version': '1.0.0',
        'files_available': {
            'index_html': os.path.exists('index.html'),
            'dashboard_html': os.path.exists('dashboard.html'),
            'admin_html': os.path.exists('admin.html'),
            'css_dir': os.path.exists('css'),
            'js_dir': os.path.exists('js'),
            'images_dir': os.path.exists('images')
        }
    })

@app.route('/api/dashboard')
def dashboard_data():
    """Données du dashboard"""
    return jsonify({
        'stats': {
            'total_users': 156,
            'total_orders': 89,
            'total_products': 12,
            'monthly_revenue': 1250000
        },
        'recent_orders': [
            {
                'order_number': 'PP202501011201',
                'total_amount': 45000,
                'status': 'pending',
                'created_at': '2025-01-01T12:01:00Z'
            }
        ]
    })

@app.route('/css/<path:filename>')
def serve_css(filename):
    """Servir les fichiers CSS"""
    return send_from_directory('css', filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    """Servir les fichiers JavaScript"""
    return send_from_directory('js', filename)

@app.route('/images/<path:filename>')
def serve_images(filename):
    """Servir les images"""
    return send_from_directory('images', filename)

@app.route('/videos/<path:filename>')
def serve_videos(filename):
    """Servir les vidéos"""
    return send_from_directory('videos', filename)

@app.route('/pages/<path:filename>')
def serve_pages(filename):
    """Servir les pages"""
    return send_from_directory('pages', filename)

@app.route('/<path:filename>')
def serve_file(filename):
    """Servir les autres fichiers"""
    try:
        return send_from_directory('.', filename)
    except FileNotFoundError:
        return f"Fichier {filename} non trouvé", 404

if __name__ == '__main__':
    print("🚀 Serveur PassPrint Complet")
    print("=" * 50)
    print("✅ Site Web: http://localhost:5000")
    print("✅ Dashboard: http://localhost:5000/dashboard.html")
    print("✅ Admin: http://localhost:5000/admin.html")
    print("✅ API: http://localhost:5000/api/health")
    print("=" * 50)
    print("🎯 Le serveur sert maintenant tous les fichiers correctement!")

    app.run(host='0.0.0.0', port=5000, debug=True)