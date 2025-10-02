#!/usr/bin/env python3
"""
Serveur de test PassPrint - Version simple sans emojis
"""
from flask import Flask, send_from_directory, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/dashboard.html')
def dashboard():
    return send_from_directory('.', 'dashboard.html')

@app.route('/admin.html')
def admin():
    return send_from_directory('.', 'admin.html')

@app.route('/test-admin.html')
def test_admin():
    return send_from_directory('.', 'test-admin.html')

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'OK',
        'message': 'Serveur PassPrint fonctionne',
        'version': '1.0.0'
    })

@app.route('/api/dashboard')
def dashboard_data():
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
    return send_from_directory('.', filename)

if __name__ == '__main__':
    print("Serveur PassPrint demarre...")
    print("Site web: http://localhost:5000")
    print("Dashboard: http://localhost:5000/dashboard.html")
    print("API: http://localhost:5000/api/health")
    print("=" * 50)

    app.run(host='0.0.0.0', port=5000, debug=True)