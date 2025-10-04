#!/usr/bin/env python3
"""
Serveur PassPrint Fonctionnel - Version Garantie de Marcher
"""
from flask import Flask, send_from_directory, jsonify
import os

app = Flask(__name__)

@app.route('/')
def index():
    """Page d'accueil"""
    return send_from_directory('.', 'index.html')

@app.route('/admin.html')
def admin():
    """Dashboard administration"""
    return send_from_directory('.', 'admin.html')

@app.route('/dashboard.html')
def dashboard():
    """Dashboard moderne"""
    return send_from_directory('.', 'dashboard.html')

@app.route('/test-admin.html')
def test_admin():
    """Test dashboard"""
    return send_from_directory('.', 'test_admin.html')

@app.route('/index_dashboard.html')
def index_dashboard():
    """Page d'accueil du dashboard"""
    return send_from_directory('.', 'index_dashboard.html')

@app.route('/api/health')
def health():
    """Santé de l'API"""
    return jsonify({
        'status': 'API fonctionnelle',
        'message': 'Serveur PassPrint actif',
        'version': '1.0.0'
    })

@app.route('/favicon.ico')
def favicon():
    """Servir le favicon"""
    return send_from_directory('.', 'favicon.ico')

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

@app.route('/<path:filename>')
def serve_file(filename):
    """Servir les fichiers statiques"""
    return send_from_directory('.', filename)

if __name__ == '__main__':
    print("Serveur PassPrint - Version Fonctionnelle")
    print("=" * 50)
    print("Site Web: http://localhost:5000")
    print("Dashboard: http://localhost:5000/dashboard.html")
    print("Admin: http://localhost:5000/admin.html")
    print("API: http://localhost:5000/api/health")
    print("=" * 50)
    print("Le serveur est maintenant actif et fonctionnel!")

    app.run(host='0.0.0.0', port=5000, debug=True)