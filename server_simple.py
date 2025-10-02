#!/usr/bin/env python3
"""
Serveur PassPrint ultra-simple
Version garantie de fonctionner
"""
from flask import Flask, send_from_directory

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/admin.html')
def admin():
    return send_from_directory('.', 'admin.html')

@app.route('/dashboard.html')
def dashboard():
    return send_from_directory('.', 'dashboard.html')

@app.route('/test-admin.html')
def test_admin():
    return send_from_directory('.', 'test_admin.html')

@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('.', filename)

if __name__ == '__main__':
    print("Serveur PassPrint demarre...")
    print("Site web: http://localhost:5000")
    print("Dashboard: http://localhost:5000/dashboard.html")
    print("Admin: http://localhost:5000/admin.html")
    print("=" * 50)

    app.run(host='0.0.0.0', port=5000, debug=True)