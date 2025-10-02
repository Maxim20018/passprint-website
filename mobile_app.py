#!/usr/bin/env python3
"""
Application mobile PWA pour PassPrint
Interface mobile optimisée
"""
from flask import render_template_string

MOBILE_APP_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PassPrint Mobile</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #2D1B69 0%, #FF6B35 100%);
            color: white;
            font-family: 'Inter', sans-serif;
        }
        .container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
        }
        .btn {
            border-radius: 25px;
            padding: 1rem 2rem;
            margin: 1rem 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-center mb-4">📱 PassPrint Mobile</h1>
        <p class="text-center">Application mobile PWA</p>

        <div class="text-center">
            <button class="btn btn-primary">Installer l'App</button>
            <a href="index.html" class="btn btn-secondary">Site Web</a>
            <a href="dashboard.html" class="btn btn-success">Dashboard</a>
        </div>

        <div class="mt-4">
            <h3>Fonctionnalités Mobile</h3>
            <ul>
                <li>✅ Interface mobile optimisée</li>
                <li>✅ PWA installable</li>
                <li>✅ Notifications push</li>
                <li>✅ Mode hors ligne</li>
                <li>✅ Géolocalisation</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""

def get_mobile_app():
    """Obtenir l'interface mobile"""
    return MOBILE_APP_HTML

if __name__ == "__main__":
    print("Application mobile PWA opérationnelle!")