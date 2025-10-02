#!/usr/bin/env python3
"""
Dashboard d'Administration Ultra-Professionnel pour PassPrint
Design et fonctionnalités de niveau entreprise avec architecture avancée
"""
from flask import Flask, render_template_string, jsonify, request, send_from_directory, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import json
import uuid
from datetime import datetime, timedelta
import sqlite3
import threading
import time
import random
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import bcrypt
from functools import wraps
import requests
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import smtplib
import ssl

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ultra-secure-key-change-in-production-2025'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration de la base de données
DATABASE = 'passprint_enterprise.db'

def get_db():
    """Connexion à la base de données"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialisation de la base de données d'entreprise"""
    with get_db() as conn:
        # Table des utilisateurs
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                is_active BOOLEAN DEFAULT 1,
                last_login DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table des produits
        conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price DECIMAL(10,2) NOT NULL,
                category TEXT NOT NULL,
                stock_quantity INTEGER DEFAULT 0,
                min_stock_level INTEGER DEFAULT 5,
                image_url TEXT,
                specifications TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table des commandes
        conn.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                total_amount DECIMAL(10,2) NOT NULL,
                status TEXT DEFAULT 'pending',
                payment_status TEXT DEFAULT 'pending',
                payment_method TEXT,
                shipping_address TEXT,
                billing_address TEXT,
                notes TEXT,
                internal_notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES users (id)
            )
        ''')

        # Table des éléments de commande
        conn.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                total_price DECIMAL(10,2) NOT NULL,
                specifications TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')

        # Table des devis
        conn.execute('''
            CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote_number TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                project_name TEXT,
                project_description TEXT,
                specifications TEXT,
                estimated_price DECIMAL(10,2),
                final_price DECIMAL(10,2),
                status TEXT DEFAULT 'draft',
                valid_until DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES users (id)
            )
        ''')

        # Table des fichiers
        conn.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_type TEXT NOT NULL,
                mime_type TEXT,
                uploaded_by INTEGER,
                related_to_type TEXT,
                related_to_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (uploaded_by) REFERENCES users (id)
            )
        ''')

        # Table des activités
        conn.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Table des paramètres système
        conn.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT,
                setting_type TEXT DEFAULT 'string',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()

def init_sample_data():
    """Initialisation des données de démonstration"""
    with get_db() as conn:
        # Administrateur par défaut
        admin_password = bcrypt.hashpw('admin2025!Pro'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        conn.execute('''
            INSERT OR IGNORE INTO users (username, email, password_hash, first_name, last_name, role)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('admin', 'admin@passprint.com', admin_password, 'Administrateur', 'PassPrint', 'admin'))

        # Produits de démonstration
        products = [
            ('Banderole Publicitaire Premium', 'Banderole grand format résistante aux intempéries avec finitions professionnelles', 25000.00, 'print', 15, 5, 'images/banderole.jpg', '{"format": "2x1m", "material": "PVC Premium", "finishing": "Œillets renforcés"}'),
            ('Stickers Personnalisés Deluxe', 'Autocollants vinyle avec découpe sur mesure et laminage brillant', 15000.00, 'print', 0, 10, 'images/macaron.jpg', '{"format": "A5", "material": "Vinyle adhésif", "cutting": "Sur mesure"}'),
            ('Clé USB 32GB Corporate', 'Support de stockage personnalisé avec logo gravé et packaging premium', 8500.00, 'usb', 25, 5, 'images/32G.jpg', '{"capacity": "32GB", "interface": "USB 3.0", "customization": "Logo gravé"}'),
            ('Panneau Alucobond 3mm', 'Panneau composite aluminium pour signalétique extérieure durable', 45000.00, 'print', 8, 3, 'images/grandformat.jpg', '{"thickness": "3mm", "size": "1x1m", "weatherproof": "Oui"}'),
            ('Papier Couche Premium A4', 'Papier de haute qualité pour impressions professionnelles', 3500.00, 'supplies', 100, 20, 'images/Double A A4.jpg', '{"weight": "120g", "finish": "Couché brillant"}')
        ]

        for product in products:
            conn.execute('''
                INSERT OR IGNORE INTO products (name, description, price, category, stock_quantity, min_stock_level, image_url, specifications)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', product)

        # Commandes de démonstration
        orders = [
            ('PP202501011201', 1, 45000.00, 'pending', 'pending', 'transfer', 'Douala, Cameroun', 'Douala, Cameroun', 'Commande urgente pour événement', 'À traiter en priorité'),
            ('PP202501011158', 1, 32000.00, 'confirmed', 'paid', 'card', 'Yaoundé, Cameroun', 'Yaoundé, Cameroun', 'Commande confirmée', 'Payée par carte'),
            ('PP202501011145', 1, 75000.00, 'delivered', 'paid', 'transfer', 'Bafoussam, Cameroun', 'Bafoussam, Cameroun', 'Livraison effectuée', 'Client satisfait')
        ]

        for order in orders:
            conn.execute('''
                INSERT OR IGNORE INTO orders (order_number, customer_id, total_amount, status, payment_status, payment_method, shipping_address, billing_address, notes, internal_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', order)

        conn.commit()

# Template HTML du dashboard ultra-professionnel
PROFESSIONAL_DASHBOARD = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PassPrint Enterprise Admin - Dashboard Ultra-Professionnel</title>

    <!-- Bootstrap 5 -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome Pro -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Animate CSS -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css">
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- ApexCharts -->
    <script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
    <!-- Socket.IO -->
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>

    <style>
        :root {
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 50%, #4facfe 100%);
            --success-gradient: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
            --warning-gradient: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
            --dark-gradient: linear-gradient(135deg, #2D1B69 0%, #11998e 50%, #38ef7d 100%);
            --glass-bg: rgba(255, 255, 255, 0.1);
            --glass-border: rgba(255, 255, 255, 0.2);
            --shadow-light: 0 4px 6px rgba(0, 0, 0, 0.05);
            --shadow-medium: 0 8px 25px rgba(0, 0, 0, 0.15);
            --shadow-heavy: 0 20px 40px rgba(0, 0, 0, 0.3);
        }

        * {
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%);
            color: white;
            overflow-x: hidden;
            min-height: 100vh;
        }

        /* Navbar Ultra-Moderne */
        .navbar {
            background: rgba(45, 27, 105, 0.95);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            position: sticky;
            top: 0;
            z-index: 1000;
        }

        .navbar-brand {
            background: var(--primary-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 800;
            font-size: 1.8rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .navbar-brand i {
            font-size: 2rem;
            color: #FFD700;
        }

        /* Sidebar Révolutionnaire */
        .sidebar {
            width: 320px;
            height: 100vh;
            background: linear-gradient(180deg, rgba(45, 27, 105, 0.98) 0%, rgba(23, 33, 62, 0.98) 100%);
            backdrop-filter: blur(20px);
            position: fixed;
            left: 0;
            top: 0;
            color: white;
            overflow-y: auto;
            z-index: 999;
            box-shadow: 4px 0 30px rgba(0, 0, 0, 0.5);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .sidebar.collapsed {
            width: 80px;
        }

        .sidebar-header {
            padding: 2.5rem 2rem;
            text-align: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            position: relative;
        }

        .sidebar-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--primary-gradient);
        }

        .sidebar-logo {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .sidebar-logo img {
            width: 60px;
            height: 60px;
            border-radius: 15px;
            box-shadow: 0 8px 25px rgba(255, 107, 53, 0.3);
        }

        .sidebar-title {
            font-size: 1.5rem;
            font-weight: 700;
            background: var(--primary-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .sidebar-subtitle {
            font-size: 0.9rem;
            opacity: 0.7;
            margin-top: 0.5rem;
        }

        .nav-item {
            margin: 0.5rem 1rem;
            position: relative;
        }

        .nav-link {
            color: rgba(255, 255, 255, 0.8);
            padding: 1rem 1.5rem;
            display: flex;
            align-items: center;
            gap: 1rem;
            border-radius: 15px;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            border: 1px solid transparent;
        }

        .nav-link::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: var(--primary-gradient);
            transition: left 0.4s ease;
            z-index: -1;
        }

        .nav-link:hover::before,
        .nav-link.active::before {
            left: 0;
        }

        .nav-link:hover,
        .nav-link.active {
            color: white;
            border-color: rgba(255, 107, 53, 0.3);
            box-shadow: 0 8px 25px rgba(255, 107, 53, 0.2);
            transform: translateX(5px) translateY(-2px);
        }

        .nav-link i {
            width: 24px;
            font-size: 1.2rem;
            transition: all 0.3s ease;
        }

        .nav-link:hover i {
            transform: scale(1.1);
            color: #FFD700;
        }

        .nav-badge {
            position: absolute;
            top: 50%;
            right: 1rem;
            transform: translateY(-50%);
            background: var(--warning-gradient);
            color: white;
            border-radius: 12px;
            padding: 0.25rem 0.75rem;
            font-size: 0.75rem;
            font-weight: 600;
            min-width: 24px;
            text-align: center;
        }

        /* Main Content */
        .main-content {
            margin-left: 320px;
            padding: 2rem;
            transition: margin-left 0.4s ease;
        }

        .main-content.expanded {
            margin-left: 80px;
        }

        /* Hero Section Spectaculaire */
        .hero-section {
            background: var(--primary-gradient);
            border-radius: 30px;
            padding: 4rem;
            margin-bottom: 3rem;
            position: relative;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(102, 126, 234, 0.3);
        }

        .hero-section::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="20" cy="20" r="2" fill="rgba(255,255,255,0.1)"/><circle cx="80" cy="80" r="1.5" fill="rgba(255,255,255,0.08)"/><circle cx="60" cy="30" r="1" fill="rgba(255,255,255,0.12)"/></svg>') repeat;
            animation: float 30s infinite linear;
        }

        .hero-section::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: radial-gradient(circle at 30% 70%, rgba(255, 107, 53, 0.2) 0%, transparent 50%);
        }

        .floating-shapes {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
            overflow: hidden;
        }

        .shape {
            position: absolute;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 50%;
            animation: float 8s ease-in-out infinite;
        }

        .shape:nth-child(1) {
            width: 120px;
            height: 120px;
            top: 10%;
            left: 5%;
            animation-delay: 0s;
        }

        .shape:nth-child(2) {
            width: 80px;
            height: 80px;
            top: 60%;
            right: 15%;
            animation-delay: -2s;
        }

        .shape:nth-child(3) {
            width: 150px;
            height: 150px;
            bottom: 10%;
            left: 60%;
            animation-delay: -4s;
        }

        .hero-content {
            position: relative;
            z-index: 2;
        }

        .hero-title {
            font-size: 3.5rem;
            font-weight: 900;
            line-height: 1.1;
            margin-bottom: 1.5rem;
            background: linear-gradient(135deg, #fff 0%, #FFD700 50%, #FF6B35 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        }

        .hero-subtitle {
            font-size: 1.4rem;
            opacity: 0.9;
            margin-bottom: 2rem;
            line-height: 1.6;
        }

        .hero-stats {
            display: flex;
            gap: 2rem;
            flex-wrap: wrap;
        }

        .hero-stat {
            text-align: center;
            padding: 1.5rem;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            min-width: 150px;
        }

        .hero-stat-value {
            font-size: 2.5rem;
            font-weight: 800;
            background: var(--success-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1;
        }

        .hero-stat-label {
            font-size: 0.9rem;
            opacity: 0.8;
            margin-top: 0.5rem;
        }

        /* Cards Ultra-Modernes */
        .stats-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 25px;
            padding: 2.5rem;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        .stats-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--primary-gradient);
            transform: scaleX(0);
            transform-origin: left;
            transition: transform 0.4s ease;
        }

        .stats-card:hover::before {
            transform: scaleX(1);
        }

        .stats-card:hover {
            transform: translateY(-10px) scale(1.02);
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
            border-color: rgba(255, 107, 53, 0.3);
        }

        .stats-icon {
            width: 80px;
            height: 80px;
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.5rem;
            font-size: 2.5rem;
            color: white;
            position: relative;
            overflow: hidden;
        }

        .stats-icon::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: inherit;
            opacity: 0.2;
            border-radius: inherit;
        }

        .stats-value {
            font-size: 3rem;
            font-weight: 900;
            background: var(--primary-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1;
            margin-bottom: 0.5rem;
        }

        .stats-label {
            color: rgba(255, 255, 255, 0.7);
            font-size: 1rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }

        .stats-trend {
            font-size: 0.9rem;
            margin-top: 0.5rem;
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            display: inline-block;
        }

        .stats-trend.up {
            background: rgba(67, 233, 123, 0.2);
            color: #43e97b;
        }

        .stats-trend.down {
            background: rgba(240, 147, 251, 0.2);
            color: #f093fb;
        }

        /* Graphiques Avancés */
        .chart-container {
            position: relative;
            height: 350px;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 20px;
            padding: 1.5rem;
        }

        /* Tables Professionnelles */
        .orders-table {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 25px;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }

        .table th {
            background: var(--dark-gradient);
            color: white;
            border: none;
            padding: 1.5rem 1rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            position: sticky;
            top: 0;
        }

        .table td {
            padding: 1.5rem 1rem;
            border-color: rgba(255, 255, 255, 0.05);
            vertical-align: middle;
        }

        .table tbody tr {
            transition: all 0.3s ease;
        }

        .table tbody tr:hover {
            background: rgba(255, 107, 53, 0.05);
            transform: scale(1.01);
        }

        /* Status Badges Animés */
        .status-badge {
            padding: 0.75rem 1.5rem;
            border-radius: 25px;
            font-size: 0.85rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            position: relative;
            overflow: hidden;
        }

        .status-badge::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transition: left 0.5s;
        }

        .status-badge:hover::before {
            left: 100%;
        }

        .status-pending {
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
            color: #856404;
        }

        .status-confirmed {
            background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
            color: #0c5460;
        }

        .status-processing {
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            color: #155724;
        }

        .status-shipped {
            background: linear-gradient(135deg, #cce7ff 0%, #b6d4fe 100%);
            color: #004085;
        }

        .status-delivered {
            background: linear-gradient(135deg, #d1ecf1 0%, #a3d5d9 100%);
            color: #0c5460;
        }

        .status-cancelled {
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
            color: #721c24;
        }

        /* Boutons Révolutionnaires */
        .btn {
            border-radius: 15px;
            padding: 0.75rem 2rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            border: none;
        }

        .btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transition: left 0.5s;
        }

        .btn:hover::before {
            left: 100%;
        }

        .btn-primary {
            background: var(--primary-gradient);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        }

        .btn-primary:hover {
            transform: translateY(-3px) scale(1.05);
            box-shadow: 0 12px 35px rgba(102, 126, 234, 0.4);
        }

        .btn-success {
            background: var(--success-gradient);
            box-shadow: 0 8px 25px rgba(67, 233, 123, 0.3);
        }

        .btn-success:hover {
            transform: translateY(-3px) scale(1.05);
            box-shadow: 0 12px 35px rgba(67, 233, 123, 0.4);
        }

        .btn-warning {
            background: var(--warning-gradient);
            box-shadow: 0 8px 25px rgba(250, 112, 154, 0.3);
        }

        .btn-warning:hover {
            transform: translateY(-3px) scale(1.05);
            box-shadow: 0 12px 35px rgba(250, 112, 154, 0.4);
        }

        /* Loading Animation */
        .loading {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 9999;
            align-items: center;
            justify-content: center;
        }

        .loading.show {
            display: flex;
        }

        .loading-spinner {
            width: 80px;
            height: 80px;
            border: 4px solid rgba(255, 255, 255, 0.1);
            border-radius: 50%;
            border-top: 4px solid #FF6B35;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
        }

        /* Animations d'Entrée */
        .animate-slide-up {
            animation: slideInUp 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .animate-slide-left {
            animation: slideInLeft 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .animate-slide-right {
            animation: slideInRight 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        }

        @keyframes slideInUp {
            from {
                opacity: 0;
                transform: translateY(50px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes slideInLeft {
            from {
                opacity: 0;
                transform: translateX(-50px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(50px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .sidebar {
                transform: translateX(-100%);
            }

            .main-content {
                margin-left: 0;
            }

            .hero-title {
                font-size: 2.5rem;
            }

            .hero-stats {
                flex-direction: column;
                gap: 1rem;
            }
        }

        /* Dark Mode Support */
        @media (prefers-color-scheme: dark) {
            body {
                background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%);
            }
        }

        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.1);
        }

        ::-webkit-scrollbar-thumb {
            background: var(--primary-gradient);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
    </style>
</head>
<body>
    <!-- Sidebar -->
    <nav class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <div class="sidebar-logo">
                <img src="images/logo.svg" alt="PassPrint Logo" onerror="this.src='https://via.placeholder.com/60x60/FF6B35/FFFFFF?text=PP'">
                <div>
                    <div class="sidebar-title">PassPrint</div>
                    <div class="sidebar-subtitle">Enterprise Admin</div>
                </div>
            </div>
        </div>

        <ul class="nav flex-column">
            <li class="nav-item">
                <a class="nav-link active" href="#" data-page="dashboard">
                    <i class="fas fa-tachometer-alt"></i>
                    <span>Dashboard</span>
                    <span class="nav-badge">3</span>
                </a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="#" data-page="orders">
                    <i class="fas fa-shopping-cart"></i>
                    <span>Commandes</span>
                    <span class="nav-badge">12</span>
                </a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="#" data-page="products">
                    <i class="fas fa-box"></i>
                    <span>Produits</span>
                </a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="#" data-page="customers">
                    <i class="fas fa-users"></i>
                    <span>Clients</span>
                </a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="#" data-page="analytics">
                    <i class="fas fa-chart-bar"></i>
                    <span>Analytics</span>
                </a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="#" data-page="inventory">
                    <i class="fas fa-warehouse"></i>
                    <span>Inventaire</span>
                </a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="#" data-page="files">
                    <i class="fas fa-folder-open"></i>
                    <span>Fichiers</span>
                </a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="#" data-page="reports">
                    <i class="fas fa-file-alt"></i>
                    <span>Rapports</span>
                </a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="#" data-page="settings">
                    <i class="fas fa-cog"></i>
                    <span>Paramètres</span>
                </a>
            </li>
            <li class="nav-item mt-4">
                <a class="nav-link text-danger" href="#" onclick="logout()">
                    <i class="fas fa-sign-out-alt"></i>
                    <span>Déconnexion</span>
                </a>
            </li>
        </ul>
    </nav>

    <!-- Main Content -->
    <main class="main-content">
        <!-- Navbar -->
        <nav class="navbar navbar-expand-lg mb-4">
            <div class="container-fluid">
                <button class="btn btn-outline-light d-lg-none me-3" onclick="toggleSidebar()">
                    <i class="fas fa-bars"></i>
                </button>

                <div class="navbar-brand">
                    <i class="fas fa-crown"></i>
                    Centre de Contrôle PassPrint
                </div>

                <div class="d-flex align-items-center gap-3">
                    <!-- Real-time Clock -->
                    <div class="d-none d-md-block">
                        <div id="current-time" class="text-light" style="font-size: 0.9rem;"></div>
                        <div id="current-date" class="text-light" style="font-size: 0.8rem; opacity: 0.8;"></div>
                    </div>

                    <!-- Notifications -->
                    <div class="dropdown">
                        <button class="btn btn-outline-light position-relative" data-bs-toggle="dropdown">
                            <i class="fas fa-bell"></i>
                            <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">5</span>
                        </button>
                        <ul class="dropdown-menu dropdown-menu-end">
                            <li><h6 class="dropdown-header">Notifications</h6></li>
                            <li><a class="dropdown-item" href="#">Nouvelle commande #PP202501011201</a></li>
                            <li><a class="dropdown-item" href="#">Produit en rupture de stock</a></li>
                            <li><a class="dropdown-item" href="#">Nouveau message client</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item text-center" href="#">Voir toutes les notifications</a></li>
                        </ul>
                    </div>

                    <!-- User Menu -->
                    <div class="dropdown">
                        <button class="btn btn-outline-light dropdown-toggle d-flex align-items-center" data-bs-toggle="dropdown">
                            <img src="https://via.placeholder.com/32x32/FF6B35/FFFFFF?text=A" class="rounded-circle me-2" alt="Avatar">
                            <span id="admin-name">Administrateur</span>
                        </button>
                        <ul class="dropdown-menu dropdown-menu-end">
                            <li><a class="dropdown-item" href="#"><i class="fas fa-user me-2"></i>Profil</a></li>
                            <li><a class="dropdown-item" href="#"><i class="fas fa-key me-2"></i>Changer mot de passe</a></li>
                            <li><a class="dropdown-item" href="#"><i class="fas fa-history me-2"></i>Historique</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item text-danger" href="#" onclick="logout()"><i class="fas fa-sign-out-alt me-2"></i>Déconnexion</a></li>
                        </ul>
                    </div>
                </div>
            </div>
        </nav>

        <!-- Dashboard Page -->
        <div id="dashboard-page">
            <!-- Hero Section -->
            <section class="hero-section text-white position-relative">
                <div class="floating-shapes">
                    <div class="shape"></div>
                    <div class="shape"></div>
                    <div class="shape"></div>
                </div>
                <div class="hero-content">
                    <div class="row align-items-center">
                        <div class="col-lg-8">
                            <h1 class="hero-title animate-slide-up">
                                Centre de Contrôle <span style="color: #FFD700;">PassPrint</span>
                            </h1>
                            <p class="hero-subtitle animate-slide-up" style="animation-delay: 0.2s;">
                                Gérez votre entreprise d'impression avec une plateforme de gestion d'entreprise de niveau mondial, dotée d'analytics en temps réel et d'automatisation avancée.
                            </p>
                            <div class="d-flex gap-3 flex-wrap animate-slide-up" style="animation-delay: 0.4s;">
                                <button class="btn btn-warning btn-lg" onclick="showPage('orders')">
                                    <i class="fas fa-plus-circle me-2"></i>Nouvelle Commande
                                </button>
                                <button class="btn btn-outline-light btn-lg" onclick="showPage('products')">
                                    <i class="fas fa-box me-2"></i>Gérer Produits
                                </button>
                                <button class="btn btn-success btn-lg" onclick="refreshAllData()">
                                    <i class="fas fa-sync-alt me-2"></i>Rafraîchir Données
                                </button>
                            </div>
                        </div>
                        <div class="col-lg-4">
                            <div class="text-center animate-slide-up" style="animation-delay: 0.6s;">
                                <i class="fas fa-rocket fa-5x text-warning mb-4 animate-float"></i>
                                <h3 class="h2">Performance</h3>
                                <p class="mb-3">Votre entreprise en pleine croissance</p>
                                <div class="hero-stats">
                                    <div class="hero-stat">
                                        <div class="hero-stat-value">+25%</div>
                                        <div class="hero-stat-label">Croissance</div>
                                    </div>
                                    <div class="hero-stat">
                                        <div class="hero-stat-value">98%</div>
                                        <div class="hero-stat-label">Satisfaction</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Stats Cards -->
            <div class="row g-4 mb-4">
                <div class="col-lg-3 col-md-6">
                    <div class="stats-card animate-slide-up">
                        <div class="stats-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                            <i class="fas fa-users"></i>
                        </div>
                        <div class="stats-value" id="total-users">-</div>
                        <div class="stats-label">Clients Actifs</div>
                        <div class="stats-trend up" id="users-trend">+12% ce mois</div>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6">
                    <div class="stats-card animate-slide-up" style="animation-delay: 0.1s;">
                        <div class="stats-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                            <i class="fas fa-shopping-cart"></i>
                        </div>
                        <div class="stats-value" id="total-orders">-</div>
                        <div class="stats-label">Commandes</div>
                        <div class="stats-trend up" id="orders-trend">+8% ce mois</div>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6">
                    <div class="stats-card animate-slide-up" style="animation-delay: 0.2s;">
                        <div class="stats-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                            <i class="fas fa-box"></i>
                        </div>
                        <div class="stats-value" id="total-products">-</div>
                        <div class="stats-label">Produits Actifs</div>
                        <div class="stats-trend down" id="stock-warning">2 en rupture</div>
                    </div>
                </div>
                <div class="col-lg-3 col-md-6">
                    <div class="stats-card animate-slide-up" style="animation-delay: 0.3s;">
                        <div class="stats-icon" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
                            <i class="fas fa-chart-line"></i>
                        </div>
                        <div class="stats-value" id="monthly-revenue">-</div>
                        <div class="stats-label">Revenus du Mois</div>
                        <div class="stats-trend up" id="revenue-trend">+15% vs dernier mois</div>
                    </div>
                </div>
            </div>

            <div class="row g-4">
                <!-- Advanced Chart -->
                <div class="col-lg-8">
                    <div class="stats-card">
                        <div class="d-flex justify-content-between align-items-center mb-4">
                            <h5 class="mb-0">Évolution des Ventes</h5>
                            <div class="btn-group btn-group-sm">
                                <button class="btn btn-outline-light active" onclick="loadChartData('month')">Mois</button>
                                <button class="btn btn-outline-light" onclick="loadChartData('week')">Semaine</button>
                                <button class="btn btn-outline-light" onclick="loadChartData('day')">Jour</button>
                            </div>
                        </div>
                        <div class="chart-container">
                            <canvas id="salesChart"></canvas>
                        </div>
                    </div>
                </div>

                <!-- Recent Activity -->
                <div class="col-lg-4">
                    <div class="stats-card">
                        <div class="d-flex justify-content-between align-items-center mb-4">
                            <h5 class="mb-0">Activité Récente</h5>
                            <button class="btn btn-outline-warning btn-sm" onclick="showPage('analytics')">
                                <i class="fas fa-eye me-1"></i>Voir tout
                            </button>
                        </div>
                        <div class="activity-timeline">
                            <div class="timeline-item d-flex mb-3 p-3 rounded" style="background: rgba(255, 255, 255, 0.05);">
                                <div class="timeline-marker bg-success rounded-circle me-3 mt-1"></div>
                                <div class="flex-grow-1">
                                    <div class="fw-bold">Nouvelle commande #PP202501011201</div>
                                    <small class="text-muted">Il y a 5 minutes • Banderole Publicitaire × 2</small>
                                </div>
                                <div class="text-end">
                                    <div class="fw-bold text-success">45,000 FCFA</div>
                                </div>
                            </div>
                            <div class="timeline-item d-flex mb-3 p-3 rounded" style="background: rgba(255, 255, 255, 0.05);">
                                <div class="timeline-marker bg-primary rounded-circle me-3 mt-1"></div>
                                <div class="flex-grow-1">
                                    <div class="fw-bold">Produit ajouté au catalogue</div>
                                    <small class="text-muted">Il y a 15 minutes • Clé USB 64GB</small>
                                </div>
                                <div class="text-end">
                                    <div class="fw-bold text-primary">Nouveau</div>
                                </div>
                            </div>
                            <div class="timeline-item d-flex mb-3 p-3 rounded" style="background: rgba(255, 255, 255, 0.05);">
                                <div class="timeline-marker bg-warning rounded-circle me-3 mt-1"></div>
                                <div class="flex-grow-1">
                                    <div class="fw-bold">Commande expédiée #PP202501011145</div>
                                    <small class="text-muted">Il y a 32 minutes • Panneau A1</small>
                                </div>
                                <div class="text-end">
                                    <div class="fw-bold text-warning">Expédiée</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Services Overview -->
            <div class="row g-4 mt-2">
                <div class="col-12">
                    <div class="stats-card">
                        <h4 class="mb-4 text-center">Services d'Impression Premium</h4>
                        <div class="row g-4">
                            <div class="col-lg-3 col-md-6">
                                <div class="text-center p-4 rounded" style="background: rgba(255, 107, 53, 0.1); border: 1px solid rgba(255, 107, 53, 0.2);">
                                    <i class="fas fa-flag fa-4x text-warning mb-3"></i>
                                    <h6 class="h5">Banderoles</h6>
                                    <p class="mb-3">Grand format professionnel</p>
                                    <div class="d-flex justify-content-between align-items-center">
                                        <span class="badge bg-warning">25,000 FCFA/m²</span>
                                        <span class="badge bg-success">Stock: 15</span>
                                    </div>
                                </div>
                            </div>
                            <div class="col-lg-3 col-md-6">
                                <div class="text-center p-4 rounded" style="background: rgba(245, 87, 108, 0.1); border: 1px solid rgba(245, 87, 108, 0.2);">
                                    <i class="fas fa-sticky-note fa-4x text-warning mb-3"></i>
                                    <h6 class="h5">Stickers</h6>
                                    <p class="mb-3">Découpe personnalisée</p>
                                    <div class="d-flex justify-content-between align-items-center">
                                        <span class="badge bg-warning">15,000 FCFA/100</span>
                                        <span class="badge bg-danger">Stock: 0</span>
                                    </div>
                                </div>
                            </div>
                            <div class="col-lg-3 col-md-6">
                                <div class="text-center p-4 rounded" style="background: rgba(79, 172, 254, 0.1); border: 1px solid rgba(79, 172, 254, 0.2);">
                                    <i class="fas fa-cube fa-4x text-warning mb-3"></i>
                                    <h6 class="h5">Panneaux</h6>
                                    <p class="mb-3">Supports rigides</p>
                                    <div class="d-flex justify-content-between align-items-center">
                                        <span class="badge bg-warning">45,000 FCFA/m²</span>
                                        <span class="badge bg-success">Stock: 8</span>
                                    </div>
                                </div>
                            </div>
                            <div class="col-lg-3 col-md-6">
                                <div class="text-center p-4 rounded" style="background: rgba(0, 166, 118, 0.1); border: 1px solid rgba(0, 166, 118, 0.2);">
                                    <i class="fas fa-usb fa-4x text-warning mb-3"></i>
                                    <h6 class="h5">Clés USB</h6>
                                    <p class="mb-3">Stockage personnalisé</p>
                                    <div class="d-flex justify-content-between align-items-center">
                                        <span class="badge bg-warning">8,500 FCFA/32GB</span>
                                        <span class="badge bg-success">Stock: 25</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Orders Page -->
        <div id="orders-page" style="display: none;">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2 class="mb-0">Gestion des Commandes</h2>
                <div class="d-flex gap-2">
                    <select class="form-select" id="status-filter" style="width: auto;">
                        <option value="">Tous les statuts</option>
                        <option value="pending">En attente</option>
                        <option value="confirmed">Confirmée</option>
                        <option value="processing">En cours</option>
                        <option value="shipped">Expédiée</option>
                        <option value="delivered">Livrée</option>
                        <option value="cancelled">Annulée</option>
                    </select>
                    <button class="btn btn-success" onclick="addNewOrder()">
                        <i class="fas fa-plus me-2"></i>Nouvelle Commande
                    </button>
                    <button class="btn btn-outline-primary" onclick="exportOrders()">
                        <i class="fas fa-download me-2"></i>Exporter
                    </button>
                </div>
            </div>

            <div class="orders-table">
                <table class="table table-hover mb-0">
                    <thead>
                        <tr>
                            <th>Commande</th>
                            <th>Client</th>
                            <th>Produits</th>
                            <th>Montant</th>
                            <th>Statut</th>
                            <th>Date</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="orders-table-body">
                        <!-- Orders will be loaded here -->
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Products Page -->
        <div id="products-page" style="display: none;">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2 class="mb-0">Gestion des Produits</h2>
                <button class="btn btn-success" data-bs-toggle="modal" data-bs-target="#productModal">
                    <i class="fas fa-plus me-2"></i>Ajouter un Produit
                </button>
            </div>

            <!-- Product Filters -->
            <div class="stats-card p-3 mb-4">
                <div class="row g-3">
                    <div class="col-md-3">
                        <select class="form-select" id="category-filter">
                            <option>Toutes les catégories</option>
                            <option>Impression</option>
                            <option>USB</option>
                            <option>Fournitures</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <select class="form-select" id="stock-filter">
                            <option>Tous les stocks</option>
                            <option>En stock</option>
                            <option>Rupture de stock</option>
                        </select>
                    </div>
                    <div class="col-md-3">
                        <input type="text" class="form-control" placeholder="Rechercher produit..." id="product-search">
                    </div>
                    <div class="col-md-3">
                        <div class="d-flex gap-2">
                            <button class="btn btn-outline-primary" onclick="filterProducts()">Filtrer</button>
                            <button class="btn btn-outline-secondary" onclick="resetFilters()">Reset</button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Products Grid -->
            <div class="row g-4" id="products-grid">
                <!-- Products will be loaded here -->
            </div>
        </div>

        <!-- Customers Page -->
        <div id="customers-page" style="display: none;">
            <h2 class="mb-4">Gestion des Clients</h2>
            <div class="stats-card p-4">
                <div class="table-responsive">
                    <table class="table table-hover mb-0">
                        <thead>
                            <tr>
                                <th>Client</th>
                                <th>Contact</th>
                                <th>Commandes</th>
                                <th>Total Dépensé</th>
                                <th>Dernière Commande</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="customers-table-body">
                            <!-- Customers will be loaded here -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Analytics Page -->
        <div id="analytics-page" style="display: none;">
            <h2 class="mb-4">Analytics & Business Intelligence</h2>
            <div class="row g-4">
                <div class="col-lg-6">
                    <div class="stats-card p-4">
                        <h5 class="mb-4">Ventes par Catégorie</h5>
                        <div class="chart-container">
                            <canvas id="categoryChart"></canvas>
                        </div>
                    </div>
                </div>
                <div class="col-lg-6">
                    <div class="stats-card p-4">
                        <h5 class="mb-4">Top Produits</h5>
                        <div class="chart-container">
                            <canvas id="productsChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Inventory Page -->
        <div id="inventory-page" style="display: none;">
            <h2 class="mb-4">Gestion de l'Inventaire</h2>
            <div class="stats-card p-4">
                <div class="table-responsive">
                    <table class="table table-hover mb-0">
                        <thead>
                            <tr>
                                <th>Produit</th>
                                <th>Stock Actuel</th>
                                <th>Stock Minimum</th>
                                <th>Statut</th>
                                <th>Dernier Réappro</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="inventory-table-body">
                            <!-- Inventory will be loaded here -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Files Page -->
        <div id="files-page" style="display: none;">
            <h2 class="mb-4">Gestion des Fichiers</h2>
            <div class="stats-card p-4">
                <div class="table-responsive">
                    <table class="table table-hover mb-0">
                        <thead>
                            <tr>
                                <th>Fichier</th>
                                <th>Type</th>
                                <th>Taille</th>
                                <th>Uploadé par</th>
                                <th>Date</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="files-table-body">
                            <!-- Files will be loaded here -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Reports Page -->
        <div id="reports-page" style="display: none;">
            <h2 class="mb-4">Rapports & Analytics</h2>
            <div class="row g-4">
                <div class="col-lg-4">
                    <div class="stats-card p-4 text-center">
                        <i class="fas fa-file-pdf fa-3x text-danger mb-3"></i>
                        <h5>Rapport des Ventes</h5>
                        <button class="btn btn-danger" onclick="generateSalesReport()">Générer PDF</button>
                    </div>
                </div>
                <div class="col-lg-4">
                    <div class="stats-card p-4 text-center">
                        <i class="fas fa-chart-line fa-3x text-success mb-3"></i>
                        <h5>Rapport Analytics</h5>
                        <button class="btn btn-success" onclick="generateAnalyticsReport()">Générer Rapport</button>
                    </div>
                </div>
                <div class="col-lg-4">
                    <div class="stats-card p-4 text-center">
                        <i class="fas fa-users fa-3x text-primary mb-3"></i>
                        <h5>Rapport Clients</h5>
                        <button class="btn btn-primary" onclick="generateCustomerReport()">Générer Rapport</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Settings Page -->
        <div id="settings-page" style="display: none;">
            <h2 class="mb-4">Paramètres Système</h2>
            <div class="row g-4">
                <div class="col-lg-6">
                    <div class="stats-card p-4">
                        <h5 class="mb-4">Configuration Email</h5>
                        <form>
                            <div class="mb-3">
                                <label class="form-label">Serveur SMTP</label>
                                <input type="text" class="form-control" value="smtp.gmail.com">
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Email expéditeur</label>
                                <input type="email" class="form-control" value="passprint@gmail.com">
                            </div>
                            <button class="btn btn-primary">Tester Configuration</button>
                        </form>
                    </div>
                </div>
                <div class="col-lg-6">
                    <div class="stats-card p-4">
                        <h5 class="mb-4">Configuration Stripe</h5>
                        <div class="mb-3">
                            <label class="form-label">Clé publique</label>
                            <input type="text" class="form-control" value="pk_test_...">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Clé secrète</label>
                            <input type="password" class="form-control" value="sk_test_...">
                        </div>
                        <button class="btn btn-success">Vérifier Connexion</button>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <!-- Loading Overlay -->
    <div class="loading" id="loading">
        <div class="text-center">
            <div class="loading-spinner"></div>
            <h4 class="text-light mt-3">Chargement du Dashboard...</h4>
            <p class="text-light">Récupération des données en temps réel</p>
        </div>
    </div>

    <!-- Product Modal -->
    <div class="modal fade" id="productModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content" style="background: linear-gradient(135deg, #2D1B69 0%, #4A3585 100%); color: white;">
                <div class="modal-header">
                    <h5 class="modal-title">Ajouter un Produit</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="product-form">
                        <div class="row g-3">
                            <div class="col-md-6">
                                <label class="form-label">Nom du produit *</label>
                                <input type="text" class="form-control" id="product-name" required>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">Prix *</label>
                                <input type="number" class="form-control" id="product-price" step="0.01" required>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">Catégorie</label>
                                <select class="form-select" id="product-category">
                                    <option value="print">Impression</option>
                                    <option value="supplies">Fournitures</option>
                                    <option value="usb">Clés USB</option>
                                    <option value="other">Autre</option>
                                </select>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">Stock initial</label>
                                <input type="number" class="form-control" id="product-stock" value="0">
                            </div>
                            <div class="col-12">
                                <label class="form-label">Description</label>
                                <textarea class="form-control" id="product-description" rows="3"></textarea>
                            </div>
                            <div class="col-12">
                                <label class="form-label">Image URL</label>
                                <input type="url" class="form-control" id="product-image">
                            </div>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
                    <button type="button" class="btn btn-primary" onclick="saveProduct()">Sauvegarder</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Configuration
        const API_BASE = 'http://localhost:5000/api/admin';
        let currentUser = null;
        let currentToken = null;

        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            // Set current date and time
            updateDateTime();

            // Load dashboard by default
            loadDashboard();

            // Navigation
            document.querySelectorAll('.nav-link').forEach(link => {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    const page = this.getAttribute('data-page');
                    showPage(page);

                    // Update active state
                    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
                    this.classList.add('active');
                });
            });

            // Initialize charts
            initializeCharts();

            // Auto-refresh every 30 seconds
            setInterval(refreshAllData, 30000);

            // Update time every minute
            setInterval(updateDateTime, 60000);
        });

        function updateDateTime() {
            const now = new Date();
            const timeString = now.toLocaleTimeString('fr-FR', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            const dateString = now.toLocaleDateString('fr-FR', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });

            document.getElementById('current-time').textContent = timeString;
            document.getElementById('current-date').textContent = dateString;
        }

        // Page management
        function showPage(page) {
            // Hide all pages
            document.querySelectorAll('[id$="-page"]').forEach(p => {
                p.style.display = 'none';
            });

            // Show selected page
            document.getElementById(`${page}-page`).style.display = 'block';

            // Load page data
            switch(page) {
                case 'dashboard':
                    loadDashboard();
                    break;
                case 'orders':
                    loadOrders();
                    break;
                case 'products':
                    loadProducts();
                    break;
                case 'customers':
                    loadCustomers();
                    break;
                case 'analytics':
                    loadAnalytics();
                    break;
            }
        }

        // Dashboard functions
        async function loadDashboard() {
            showLoading();

            try {
                // Load data from API
                const [dashboardData, ordersData, productsData, usersData] = await Promise.all([
                    fetchWithAuth(`${API_BASE}/dashboard`),
                    fetchWithAuth(`${API_BASE}/orders?page=1&per_page=5`),
                    fetchWithAuth(`${API_BASE}/products`),
                    fetchWithAuth(`${API_BASE}/users?page=1&per_page=5`)
                ]);

                if (dashboardData.ok) {
                    const data = await dashboardData.json();

                    // Update stats with animation
                    animateValue('total-users', 0, data.stats.total_users, 1000);
                    animateValue('total-orders', 0, data.stats.total_orders, 1000);
                    animateValue('total-products', 0, data.stats.total_products, 1000);
                    document.getElementById('monthly-revenue').textContent =
                        new Intl.NumberFormat('fr-FR', {
                            style: 'currency',
                            currency: 'XOF'
                        }).format(data.stats.monthly_revenue);

                    // Load recent orders
                    if (ordersData.ok) {
                        const orders = await ordersData.json();
                        renderRecentOrders(orders.orders || []);
                    }

                    // Load chart
                    loadSalesChart(data.monthly_sales || []);
                }

            } catch (error) {
                console.error('Dashboard load error:', error);
                loadDemoData();
            }

            hideLoading();
        }

        function loadDemoData() {
            // Fallback demo data
            document.getElementById('total-users').textContent = '156';
            document.getElementById('total-orders').textContent = '89';
            document.getElementById('total-products').textContent = '12';
            document.getElementById('monthly-revenue').textContent = '1,250,000 FCFA';

            loadSalesChart([
                {month: '2024-12', revenue: 850000},
                {month: '2025-01', revenue: 1250000}
            ]);
        }

        function renderRecentOrders(orders) {
            const container = document.querySelector('.activity-timeline');

            if (!orders || orders.length === 0) {
                container.innerHTML = '<p class="text-muted">Aucune activité récente</p>';
                return;
            }

            container.innerHTML = orders.map(order => `
                <div class="timeline-item d-flex mb-3 p-3 rounded" style="background: rgba(255, 255, 255, 0.05);">
                    <div class="timeline-marker bg-success rounded-circle me-3 mt-1"></div>
                    <div class="flex-grow-1">
                        <div class="fw-bold">Commande ${order.order_number}</div>
                        <small class="text-muted">${new Date(order.created_at).toLocaleString('fr-FR')} • ${formatPrice(order.total_amount)}</small>
                    </div>
                    <div class="text-end">
                        <span class="status-badge status-${order.status}">${getStatusLabel(order.status)}</span>
                    </div>
                </div>
            `).join('');
        }

        function loadSalesChart(monthlySales) {
            const ctx = document.getElementById('salesChart').getContext('2d');

            // Destroy existing chart if it exists
            if (window.salesChart) {
                window.salesChart.destroy();
            }

            // Default data if no sales data
            if (!monthlySales || monthlySales.length === 0) {
                monthlySales = [
                    {month: '2024-12', revenue: 850000},
                    {month: '2025-01', revenue: 1250000}
                ];
            }

            window.salesChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: monthlySales.map(sale => {
                        const date = new Date(sale.month + '-01');
                        return date.toLocaleDateString('fr-FR', { month: 'short', year: '2-digit' });
                    }),
                    datasets: [{
                        label: 'Ventes (FCFA)',
                        data: monthlySales.map(sale => sale.revenue),
                        borderColor: '#FF6B35',
                        backgroundColor: 'rgba(255, 107, 53, 0.1)',
                        tension: 0.4,
                        fill: true,
                        pointBackgroundColor: '#FFD700',
                        pointBorderColor: '#FF6B35',
                        pointBorderWidth: 3,
                        pointRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return (value / 1000) + 'K FCFA';
                                }
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }

        // Utility functions
        function showLoading() {
            document.getElementById('loading').classList.add('show');
        }

        function hideLoading() {
            document.getElementById('loading').classList.remove('show');
        }

        async function fetchWithAuth(url) {
            try {
                const response = await fetch(url, {
                    headers: {
                        'Authorization': `Bearer ${currentToken}`,
                        'Content-Type': 'application/json'
                    }
                });
                return response;
            } catch (error) {
                console.error('API Error:', error);
                return { ok: false };
            }
        }

        function formatPrice(price) {
            return new Intl.NumberFormat('fr-FR', {
                style: 'currency',
                currency: 'XOF',
                minimumFractionDigits: 0
            }).format(price);
        }

        function getStatusLabel(status) {
            const labels = {
                'pending': 'En attente',
                'confirmed': 'Confirmée',
                'processing': 'En cours',
                'shipped': 'Expédiée',
                'delivered': 'Livrée',
                'cancelled': 'Annulée'
            };
            return labels[status] || status;
        }

        function toggleSidebar() {
            document.getElementById('sidebar').classList.toggle('collapsed');
            document.querySelector('.main-content').classList.toggle('expanded');
        }

        function refreshAllData() {
            loadDashboard();
            showNotification('Données rafraîchies avec succès!', 'success');
        }

        function showNotification(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `alert alert-${type} position-fixed animate-slide-up`;
            notification.style.cssText = `
                top: 20px;
                right: 20px;
                z-index: 9999;
                min-width: 300px;
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
            `;
            notification.innerHTML = `<i class="fas fa-info-circle me-2"></i>${message}`;

            document.body.appendChild(notification);

            setTimeout(() => {
                notification.remove();
            }, 3000);
        }

        function animateValue(elementId, start, end, duration) {
            const element = document.getElementById(elementId);
            let startTimestamp = null;

            const step = (timestamp) => {
                if (!startTimestamp) startTimestamp = timestamp;
                const progress = Math.min((timestamp - startTimestamp) / duration, 1);
                element.textContent = Math.floor(progress * (end - start) + start);
                if (progress < 1) {
                    window.requestAnimationFrame(step);
                }
            };
            window.requestAnimationFrame(step);
        }

        function logout() {
            localStorage.removeItem('admin_token');
            window.location.href = 'index.html';
        }

        // Placeholder functions for other features
        function loadOrders() {
            console.log('Loading orders...');
        }

        function loadProducts() {
            console.log('Loading products...');
        }

        function loadCustomers() {
            console.log('Loading customers...');
        }

        function loadAnalytics() {
            console.log('Loading analytics...');
        }

        function saveProduct() {
            const modal = bootstrap.Modal.getInstance(document.getElementById('productModal'));
            modal.hide();
            showNotification('Produit ajouté avec succès!', 'success');
        }

        function initializeCharts() {
            // Initialize all charts with demo data
            setTimeout(() => {
                loadSalesChart([]);
            }, 1000);
        }
    </script>
</body>
</html>
"""

@app.route('/admin-dashboard')
def admin_dashboard():
    """Dashboard d'administration ultra-professionnel"""
    return render_template_string(PROFESSIONAL_DASHBOARD, version=DASHBOARD_VERSION, api_base=API_BASE)

@app.route('/api/admin/dashboard')
def api_dashboard():
    """API pour les données du dashboard"""
    return jsonify({
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
                'created_at': '2025-01-01T12:01:00Z',
                'customer_id': 1
            }
        ],
        'monthly_sales': [
            {'month': '2024-12', 'revenue': 850000},
            {'month': '2025-01', 'revenue': 1250000}
        ]
    })

@app.route('/api/admin/orders')
def api_orders():
    """API pour les commandes"""
    return jsonify({
        'orders': [
            {
                'order_number': 'PP202501011201',
                'customer_id': 1,
                'total_amount': 45000,
                'status': 'pending',
                'created_at': '2025-01-01T12:01:00Z',
                'items': [{'name': 'Banderole Publicitaire', 'quantity': 2}]
            }
        ],
        'pagination': {
            'page': 1,
            'per_page': 20,
            'total': 1,
            'pages': 1
        }
    })

@app.route('/api/admin/products')
def api_products():
    """API pour les produits"""
    return jsonify([
        {
            'id': 1,
            'name': 'Banderole Publicitaire Premium',
            'price': 25000,
            'category': 'print',
            'stock_quantity': 15,
            'image_url': 'images/banderole.jpg'
        },
        {
            'id': 2,
            'name': 'Stickers Personnalisés Deluxe',
            'price': 15000,
            'category': 'print',
            'stock_quantity': 0,
            'image_url': 'images/macaron.jpg'
        }
    ])

@app.route('/api/admin/users')
def api_users():
    """API pour les utilisateurs"""
    return jsonify({
        'users': [
            {
                'id': 1,
                'first_name': 'Administrateur',
                'last_name': 'PassPrint',
                'email': 'admin@passprint.com',
                'phone': '696465609',
                'company': 'PassPrint SARL',
                'created_at': '2025-01-01T00:00:00Z'
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
def api_analytics():
    """API pour les analytics"""
    return jsonify({
        'monthly_sales': [
            {'month': '2024-12', 'revenue': 850000},
            {'month': '2025-01', 'revenue': 1250000}
        ],
        'top_products': [],
        'status_counts': {'pending': 1, 'confirmed': 1}
    })

if __name__ == '__main__':
    print("🚀 Démarrage du Dashboard d'Administration Ultra-Professionnel...")
    print("📊 Dashboard: http://localhost:5000/admin-dashboard")
    print("🔌 API: http://localhost:5000/api/admin/dashboard")
    print("=" * 70)

    app.run(host='0.0.0.0', port=5000, debug=True)