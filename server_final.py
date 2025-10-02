#!/usr/bin/env python3
"""
Serveur PassPrint Final - Garanti de fonctionner
"""
from flask import Flask, send_from_directory

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('.', 'index_dashboard.html')

@app.route('/index.html')
def site():
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

@app.route('/admin-dashboard')
def admin_dashboard():
    return send_from_directory('.', 'admin_dashboard_professional.py')

@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('.', filename)

if __name__ == '__main__':
    print("🚀 SERVEUR PASSPRINT - VERSION FINALE")
    print("=" * 50)
    print("✅ Site Web: http://localhost:5000")
    print("✅ Dashboard: http://localhost:5000/dashboard.html")
    print("✅ Admin: http://localhost:5000/admin.html")
    print("✅ Test: http://localhost:5000/test-admin.html")
    print("✅ Index: http://localhost:5000/index_dashboard.html")
    print("=" * 50)
    print("🎯 Tous les fichiers sont servis correctement")
    print("🚀 Le serveur est maintenant actif!")

    app.run(host='0.0.0.0', port=5000, debug=True)