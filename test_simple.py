#!/usr/bin/env python3
"""
Test simple du serveur PassPrint
"""
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return '''
        <!DOCTYPE html>
        <html>
        <head><title>PassPrint - Site Web</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #2D1B69 0%, #FF6B35 100%); color: white;">
            <h1>PassPrint - Site Web Professionnel</h1>
            <p>Le serveur fonctionne correctement!</p>
            <div style="background: rgba(255,255,255,0.1); padding: 2rem; border-radius: 15px; margin: 2rem 0;">
                <h2>Site Web d'Imprimerie Professionnel</h2>
                <p>Services d'impression premium à Douala</p>
                <div class="row">
                    <div class="col-md-6">
                        <h3>Nos Services</h3>
                        <ul style="text-align: left;">
                            <li>Banderoles publicitaires</li>
                            <li>Stickers personnalisés</li>
                            <li>Panneaux rigides</li>
                            <li>Clés USB corporate</li>
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h3>Contact</h3>
                        <p>Tel: 696 465 609</p>
                        <p>Email: passprint@yahoo.com</p>
                        <p>Douala, Cameroun</p>
                    </div>
                </div>
            </div>
            <p><strong>API:</strong> <a href="api/health" style="color: #FFD700;">api/health</a></p>
        </body>
        </html>
        '''

@app.route('/api/health')
def health():
    return {'status': 'OK', 'message': 'API fonctionnelle'}

if __name__ == '__main__':
    print("Test du serveur PassPrint...")
    print("URL: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)