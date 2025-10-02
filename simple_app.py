#!/usr/bin/env python3
"""
Application Flask simplifiée pour PassPrint
Version de démarrage rapide
"""
from flask import Flask, jsonify, send_from_directory, request
import os
import json
from datetime import datetime

app = Flask(__name__)

# Données de test pour le dashboard
test_data = {
    'stats': {
        'total_users': 156,
        'total_orders': 89,
        'total_products': 12,
        'monthly_revenue': 1250000,
        'pending_orders': 5,
        'out_of_stock': 2
    },
    'recent_orders': [
        {
            'order_number': 'PP202501011201',
            'total_amount': 45000,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'customer_id': 1,
            'items': []
        },
        {
            'order_number': 'PP202501011158',
            'total_amount': 32000,
            'status': 'confirmed',
            'created_at': datetime.utcnow().isoformat(),
            'customer_id': 2,
            'items': []
        }
    ],
    'monthly_sales': [
        {'month': '2024-12', 'revenue': 850000},
        {'month': '2025-01', 'revenue': 1250000}
    ]
}

@app.route('/')
def index():
    """Page d'accueil"""
    return send_from_directory('.', 'index.html')

@app.route('/admin.html')
def admin():
    """Dashboard administration"""
    return send_from_directory('.', 'admin.html')

@app.route('/test-admin.html')
def test_admin():
    """Test dashboard administration"""
    return send_from_directory('.', 'test_admin.html')

@app.route('/dashboard.html')
def dashboard():
    """Dashboard administration principal"""
    return send_from_directory('.', 'dashboard.html')

@app.route('/admin-dashboard')
def admin_dashboard():
    """Dashboard d'administration avec backend intégré"""
    try:
        # Import and run the admin dashboard
        import subprocess
        import sys

        # Start admin dashboard in background if not running
        try:
            import requests
            requests.get('http://localhost:5000/api/admin/dashboard-data', timeout=1)
        except:
            # Start admin dashboard server
            subprocess.Popen([sys.executable, 'admin_dashboard.py'])

        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Redirection Dashboard...</title>
            <meta http-equiv="refresh" content="2;url=http://localhost:5000/admin-dashboard">
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #2D1B69 0%, #FF6B35 100%); color: white; }
                .spinner { border: 4px solid rgba(255,255,255,0.3); border-radius: 50%; border-top: 4px solid white; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto; }
                @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            </style>
        </head>
        <body>
            <h2>🚀 Démarrage du Dashboard d'Administration...</h2>
            <div class="spinner"></div>
            <p>Redirection automatique en cours...</p>
            <p><a href="http://localhost:5000/admin-dashboard" style="color: #FFD700;">Cliquez ici si la redirection ne fonctionne pas</a></p>
        </body>
        </html>
        """
    except Exception as e:
        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Erreur Dashboard</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f8f9fa;">
            <h2>Erreur lors du démarrage du dashboard</h2>
            <p>{str(e)}</p>
            <p><a href="dashboard.html">Accéder au dashboard simple</a></p>
        </body>
        </html>
        """

# API Routes pour le dashboard
@app.route('/api/admin/dashboard')
def admin_dashboard():
    """Tableau de bord administrateur"""
    return jsonify(test_data)

@app.route('/api/admin/orders')
def admin_orders():
    """Gestion des commandes"""
    return jsonify({
        'orders': test_data['recent_orders'],
        'pagination': {
            'page': 1,
            'per_page': 20,
            'total': 2,
            'pages': 1
        }
    })

@app.route('/api/admin/products', methods=['GET', 'POST'])
def admin_products():
    """Gestion des produits"""
    if request.method == 'POST':
        return jsonify({'message': 'Produit créé avec succès'}), 201
    return jsonify([])

@app.route('/api/admin/users')
def admin_users():
    """Gestion des utilisateurs"""
    return jsonify({
        'users': [
            {
                'id': 1,
                'first_name': 'Admin',
                'last_name': 'PassPrint',
                'email': 'admin@passprint.com',
                'phone': '696465609',
                'company': 'PassPrint',
                'created_at': datetime.utcnow().isoformat()
            }
        ],
        'pagination': {
            'page': 1,
            'per_page': 20,
            'total': 1,
            'pages': 1
        }
    })

@app.route('/api/admin/analytics')
def admin_analytics():
    """Analytics"""
    return jsonify({
        'monthly_sales': test_data['monthly_sales'],
        'top_products': [],
        'status_counts': {'pending': 1, 'confirmed': 1}
    })

@app.route('/api/health')
def health():
    """Santé de l'API"""
    return jsonify({
        'status': 'API simplifiée active',
        'message': 'Application en cours d\'initialisation'
    })

@app.route('/<path:filename>')
def serve_static(filename):
    """Servir les fichiers statiques"""
    return send_from_directory('.', filename)

if __name__ == '__main__':
    print("Demarrage de PassPrint (version simplifiee)...")
    print("Site web: http://localhost:5000")
    print("Admin: http://localhost:5000/admin.html")
    print("=" * 50)

    app.run(host='0.0.0.0', port=5000, debug=True)