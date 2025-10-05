#!/usr/bin/env python3
"""
Dashboard Admin Professionnel pour PassPrint
Interface d'administration complète avec métriques temps réel
"""
import os
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from flask import Blueprint, render_template_string, request, jsonify, g
from models import db, User, Product, Order, OrderItem, Quote, Cart, File, NewsletterSubscriber, AuditLog, BackupLog
from config import get_config

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Template HTML professionnel pour le dashboard admin
ADMIN_DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Admin - PassPrint</title>

    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- DataTables -->
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.4/css/dataTables.bootstrap5.min.css">
    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.4/js/dataTables.bootstrap5.min.js"></script>

    <style>
        :root {
            --primary-color: #2D1B69;
            --secondary-color: #FF6B35;
            --success-color: #28a745;
            --warning-color: #ffc107;
            --danger-color: #dc3545;
            --light-color: #f8f9fa;
            --dark-color: #343a40;
        }

        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
        }

        .navbar-brand {
            background: linear-gradient(135deg, #FFD700 0%, #FF6B35 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            font-size: 1.5rem;
        }

        .sidebar {
            background: rgba(45, 27, 105, 0.95);
            backdrop-filter: blur(20px);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
            min-height: 100vh;
            position: fixed;
            left: 0;
            top: 0;
            width: 280px;
            z-index: 1000;
            transition: all 0.3s ease;
        }

        .sidebar.collapsed {
            margin-left: -280px;
        }

        .sidebar-header {
            padding: 2rem 1.5rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            text-align: center;
        }

        .sidebar-menu {
            list-style: none;
            padding: 0;
            margin: 0;
        }

        .sidebar-menu li {
            margin: 0;
        }

        .sidebar-menu a {
            display: flex;
            align-items: center;
            padding: 1rem 1.5rem;
            color: rgba(255, 255, 255, 0.8);
            text-decoration: none;
            transition: all 0.3s ease;
            border-left: 3px solid transparent;
        }

        .sidebar-menu a:hover,
        .sidebar-menu a.active {
            background: rgba(255, 107, 53, 0.1);
            border-left-color: #FF6B35;
            color: #FF6B35;
        }

        .sidebar-menu i {
            margin-right: 0.75rem;
            width: 20px;
            text-align: center;
        }

        .main-content {
            margin-left: 280px;
            padding: 2rem;
            transition: margin-left 0.3s ease;
        }

        .main-content.expanded {
            margin-left: 0;
        }

        .stats-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease;
        }

        .stats-card:hover {
            transform: translateY(-5px);
        }

        .stats-icon {
            width: 60px;
            height: 60px;
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            margin-bottom: 1rem;
        }

        .stats-value {
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
        }

        .stats-label {
            color: #666;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .chart-container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 15px;
            padding: 1.5rem;
            margin: 2rem 0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }

        .table-container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 15px;
            padding: 1.5rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }

        .btn-action {
            padding: 0.5rem 1rem;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 0.85rem;
        }

        .btn-primary {
            background: linear-gradient(135deg, #2D1B69 0%, #FF6B35 100%);
            color: white;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(45, 27, 105, 0.3);
        }

        .status-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }

        .status-pending { background: #fff3cd; color: #856404; }
        .status-confirmed { background: #d1ecf1; color: #0c5460; }
        .status-processing { background: #fff3cd; color: #856404; }
        .status-shipped { background: #d4edda; color: #155724; }
        .status-delivered { background: #d4edda; color: #155724; }
        .status-cancelled { background: #f8d7da; color: #721c24; }

        .alert-item {
            background: rgba(255, 255, 255, 0.9);
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
            border-left: 4px solid;
            display: flex;
            justify-content: between;
            align-items: center;
        }

        .alert-critical { border-color: #dc3545; }
        .alert-warning { border-color: #ffc107; }
        .alert-info { border-color: #17a2b8; }

        .metric-trend {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .trend-up { color: #28a745; }
        .trend-down { color: #dc3545; }
        .trend-stable { color: #6c757d; }

        .loading {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 200px;
        }

        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #FF6B35;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        @media (max-width: 768px) {
            .sidebar {
                margin-left: -280px;
            }

            .sidebar.show {
                margin-left: 0;
            }

            .main-content {
                margin-left: 0;
            }

            .stats-card {
                margin-bottom: 1rem;
            }
        }
    </style>
</head>
<body>
<!-- Login Modal -->
<div class="modal fade" id="loginModal" tabindex="-1" data-bs-backdrop="static" data-bs-keyboard="false">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content" style="background: rgba(255,255,255,0.95); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.2);">
            <div class="modal-header" style="border-bottom: 1px solid rgba(0,0,0,0.1);">
                <h5 class="modal-title" style="color: #2D1B69; font-weight: 600;">
                    <i class="fas fa-sign-in-alt me-2"></i>Connexion Admin
                </h5>
            </div>
            <div class="modal-body">
                <form id="loginForm">
                    <div class="mb-3">
                        <label for="loginEmail" class="form-label" style="color: #2D1B69; font-weight: 500;">Email</label>
                        <input type="email" class="form-control" id="loginEmail" required style="border-radius: 10px; border: 1px solid rgba(45, 27, 105, 0.2);">
                    </div>
                    <div class="mb-3">
                        <label for="loginPassword" class="form-label" style="color: #2D1B69; font-weight: 500;">Mot de passe</label>
                        <input type="password" class="form-control" id="loginPassword" required style="border-radius: 10px; border: 1px solid rgba(45, 27, 105, 0.2);">
                    </div>
                    <div class="mb-3 form-check">
                        <input type="checkbox" class="form-check-input" id="rememberMe">
                        <label class="form-check-label" for="rememberMe" style="color: #666;">Se souvenir de moi</label>
                    </div>
                    <div id="loginError" class="alert alert-danger" style="display: none; border-radius: 10px;"></div>
                </form>
            </div>
            <div class="modal-footer" style="border-top: 1px solid rgba(0,0,0,0.1);">
                <button type="button" class="btn btn-outline-primary" onclick="showSignupModal()" style="border-radius: 25px;">Créer un compte</button>
                <button type="button" class="btn btn-primary" onclick="login()" style="border-radius: 25px; background: linear-gradient(135deg, #2D1B69 0%, #FF6B35 100%); border: none;">Se connecter</button>
            </div>
        </div>
    </div>
</div>

<!-- Signup Modal -->
<div class="modal fade" id="signupModal" tabindex="-1" data-bs-backdrop="static" data-bs-keyboard="false">
    <div class="modal-dialog modal-dialog-centered modal-lg">
        <div class="modal-content" style="background: rgba(255,255,255,0.95); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.2);">
            <div class="modal-header" style="border-bottom: 1px solid rgba(0,0,0,0.1);">
                <h5 class="modal-title" style="color: #2D1B69; font-weight: 600;">
                    <i class="fas fa-user-plus me-2"></i>Créer un compte Admin
                </h5>
                <button type="button" class="btn-close" onclick="showLoginModal()"></button>
            </div>
            <div class="modal-body">
                <form id="signupForm">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="signupFirstName" class="form-label" style="color: #2D1B69; font-weight: 500;">Prénom</label>
                                <input type="text" class="form-control" id="signupFirstName" required style="border-radius: 10px; border: 1px solid rgba(45, 27, 105, 0.2);">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="signupLastName" class="form-label" style="color: #2D1B69; font-weight: 500;">Nom</label>
                                <input type="text" class="form-control" id="signupLastName" required style="border-radius: 10px; border: 1px solid rgba(45, 27, 105, 0.2);">
                            </div>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label for="signupEmail" class="form-label" style="color: #2D1B69; font-weight: 500;">Email</label>
                        <input type="email" class="form-control" id="signupEmail" required style="border-radius: 10px; border: 1px solid rgba(45, 27, 105, 0.2);">
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="signupPassword" class="form-label" style="color: #2D1B69; font-weight: 500;">Mot de passe</label>
                                <input type="password" class="form-control" id="signupPassword" required style="border-radius: 10px; border: 1px solid rgba(45, 27, 105, 0.2);" minlength="8">
                                <div class="form-text" style="font-size: 0.8rem; color: #666;">Minimum 8 caractères</div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="signupConfirmPassword" class="form-label" style="color: #2D1B69; font-weight: 500;">Confirmer le mot de passe</label>
                                <input type="password" class="form-control" id="signupConfirmPassword" required style="border-radius: 10px; border: 1px solid rgba(45, 27, 105, 0.2);" minlength="8">
                            </div>
                        </div>
                    </div>
                    <div class="mb-3">
                        <label for="signupPhone" class="form-label" style="color: #2D1B69; font-weight: 500;">Téléphone</label>
                        <input type="tel" class="form-control" id="signupPhone" style="border-radius: 10px; border: 1px solid rgba(45, 27, 105, 0.2);">
                    </div>
                    <div class="mb-3">
                        <label for="signupCompany" class="form-label" style="color: #2D1B69; font-weight: 500;">Entreprise (optionnel)</label>
                        <input type="text" class="form-control" id="signupCompany" style="border-radius: 10px; border: 1px solid rgba(45, 27, 105, 0.2);">
                    </div>
                    <div class="mb-3 form-check">
                        <input type="checkbox" class="form-check-input" id="acceptTerms" required>
                        <label class="form-check-label" for="acceptTerms" style="color: #666; font-size: 0.9rem;">
                            J'accepte les <a href="#" style="color: #FF6B35;">conditions d'utilisation</a> et la <a href="#" style="color: #FF6B35;">politique de confidentialité</a>
                        </label>
                    </div>
                    <div id="signupError" class="alert alert-danger" style="display: none; border-radius: 10px;"></div>
                    <div id="signupSuccess" class="alert alert-success" style="display: none; border-radius: 10px;"></div>
                </form>
            </div>
            <div class="modal-footer" style="border-top: 1px solid rgba(0,0,0,0.1);">
                <button type="button" class="btn btn-outline-secondary" onclick="showLoginModal()" style="border-radius: 25px;">Retour à la connexion</button>
                <button type="button" class="btn btn-success" onclick="signup()" style="border-radius: 25px; background: linear-gradient(135deg, #28a745 0%, #20c997 100%); border: none;">Créer le compte</button>
            </div>
        </div>
    </div>
</div>

<!-- Auth Overlay -->
<div id="authOverlay" class="position-fixed top-0 start-0 w-100 h-100" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); z-index: 9998; display: flex; align-items: center; justify-content: center;">
    <div class="text-center text-white">
        <div class="spinner-border text-light mb-3" role="status" style="width: 3rem; height: 3rem;">
            <span class="visually-hidden">Chargement...</span>
        </div>
        <h3>Vérification de l'authentification...</h3>
        <p>Redirection vers le panneau d'administration</p>
    </div>
</div>

<!-- Sidebar -->
<nav class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <h3 style="color: #FFD700; margin: 0;">PassPrint Admin</h3>
            <p style="color: rgba(255,255,255,0.7); font-size: 0.9rem;">Panneau de Contrôle</p>
        </div>
        <ul class="sidebar-menu">
            <li><a href="#" class="active" data-page="overview"><i class="fas fa-tachometer-alt"></i>Vue d'ensemble</a></li>
            <li><a href="#" data-page="orders"><i class="fas fa-shopping-cart"></i>Commandes</a></li>
            <li><a href="#" data-page="products"><i class="fas fa-box"></i>Produits</a></li>
            <li><a href="#" data-page="users"><i class="fas fa-users"></i>Utilisateurs</a></li>
            <li><a href="#" data-page="quotes"><i class="fas fa-file-invoice"></i>Devis</a></li>
            <li><a href="#" data-page="analytics"><i class="fas fa-chart-bar"></i>Analytiques</a></li>
            <li><a href="#" data-page="monitoring"><i class="fas fa-heartbeat"></i>Monitoring</a></li>
            <li><a href="#" data-page="security"><i class="fas fa-shield-alt"></i>Sécurité</a></li>
            <li><a href="#" data-page="backups"><i class="fas fa-database"></i>Sauvegardes</a></li>
            <li><a href="#" data-page="settings"><i class="fas fa-cog"></i>Paramètres</a></li>
        </ul>
    </nav>

    <!-- Main Content -->
    <div class="main-content" id="mainContent">
        <!-- Header -->
        <nav class="navbar navbar-expand-lg navbar-light mb-4" style="background: rgba(255,255,255,0.95); backdrop-filter: blur(20px); border-radius: 15px; padding: 1rem;">
            <div class="container-fluid">
                <button class="btn btn-outline-primary" id="sidebarToggle">
                    <i class="fas fa-bars"></i>
                </button>

                <div class="d-flex align-items-center ms-auto">
                    <div class="dropdown me-3">
                        <button class="btn btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown">
                            <i class="fas fa-bell"></i> Alertes
                        </button>
                        <ul class="dropdown-menu" id="alertsDropdown">
                            <li><a class="dropdown-item" href="#">Aucune alerte</a></li>
                        </ul>
                    </div>

                    <div class="dropdown">
                        <button class="btn btn-outline-primary dropdown-toggle" type="button" data-bs-toggle="dropdown">
                            <i class="fas fa-user"></i> Admin
                        </button>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item" href="#" onclick="showProfile()"><i class="fas fa-user"></i> Profil</a></li>
                            <li><a class="dropdown-item" href="#" onclick="showSettings()"><i class="fas fa-cog"></i> Paramètres</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item" href="#" onclick="logout()"><i class="fas fa-sign-out-alt"></i> Déconnexion</a></li>
                        </ul>
                    </div>
                </div>
            </div>
        </nav>

        <!-- Page Content -->
        <div id="pageContent">
            <!-- Overview Page -->
            <div id="overviewPage" class="page-content">
                <div class="row mb-4">
                    <div class="col-12">
                        <h1 style="color: white;">Vue d'ensemble</h1>
                        <p style="color: rgba(255,255,255,0.8);">Dernière mise à jour: <span id="lastUpdate">Chargement...</span></p>
                    </div>
                </div>

                <!-- Stats Cards -->
                <div class="row mb-4" id="statsCards">
                    <div class="col-lg-3 col-md-6 mb-4">
                        <div class="stats-card">
                            <div class="stats-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                                <i class="fas fa-users" style="color: white;"></i>
                            </div>
                            <div class="stats-value" id="totalUsers">-</div>
                            <div class="stats-label">Utilisateurs Totaux</div>
                            <div class="metric-trend">
                                <span id="usersTrend" class="trend-stable">↔</span>
                                <small id="usersTrendValue">-</small>
                            </div>
                        </div>
                    </div>

                    <div class="col-lg-3 col-md-6 mb-4">
                        <div class="stats-card">
                            <div class="stats-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                                <i class="fas fa-shopping-cart" style="color: white;"></i>
                            </div>
                            <div class="stats-value" id="totalOrders">-</div>
                            <div class="stats-label">Commandes</div>
                            <div class="metric-trend">
                                <span id="ordersTrend" class="trend-stable">↔</span>
                                <small id="ordersTrendValue">-</small>
                            </div>
                        </div>
                    </div>

                    <div class="col-lg-3 col-md-6 mb-4">
                        <div class="stats-card">
                            <div class="stats-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                                <i class="fas fa-box" style="color: white;"></i>
                            </div>
                            <div class="stats-value" id="totalProducts">-</div>
                            <div class="stats-label">Produits</div>
                            <div class="metric-trend">
                                <span id="productsTrend" class="trend-stable">↔</span>
                                <small id="productsTrendValue">-</small>
                            </div>
                        </div>
                    </div>

                    <div class="col-lg-3 col-md-6 mb-4">
                        <div class="stats-card">
                            <div class="stats-icon" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
                                <i class="fas fa-dollar-sign" style="color: white;"></i>
                            </div>
                            <div class="stats-value" id="monthlyRevenue">-</div>
                            <div class="stats-label">Revenus du Mois</div>
                            <div class="metric-trend">
                                <span id="revenueTrend" class="trend-stable">↔</span>
                                <small id="revenueTrendValue">-</small>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Charts Row -->
                <div class="row mb-4">
                    <div class="col-lg-8">
                        <div class="chart-container">
                            <h3 style="color: #2D1B69; margin-bottom: 1.5rem;">Ventes Mensuelles</h3>
                            <canvas id="salesChart" height="300"></canvas>
                        </div>
                    </div>
                    <div class="col-lg-4">
                        <div class="chart-container">
                            <h3 style="color: #2D1B69; margin-bottom: 1.5rem;">Statuts des Commandes</h3>
                            <canvas id="ordersChart" height="300"></canvas>
                        </div>
                    </div>
                </div>

                <!-- Recent Orders and Alerts -->
                <div class="row">
                    <div class="col-lg-8">
                        <div class="table-container">
                            <h3 style="color: #2D1B69; margin-bottom: 1.5rem;">Commandes Récentes</h3>
                            <div class="table-responsive">
                                <table class="table table-hover" id="recentOrdersTable">
                                    <thead>
                                        <tr>
                                            <th>Commande</th>
                                            <th>Client</th>
                                            <th>Montant</th>
                                            <th>Statut</th>
                                            <th>Date</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody id="recentOrdersBody">
                                        <tr>
                                            <td colspan="6" class="text-center">Chargement...</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                    <div class="col-lg-4">
                        <div class="chart-container">
                            <h3 style="color: #2D1B69; margin-bottom: 1.5rem;">Alertes Système</h3>
                            <div id="alertsContainer">
                                <div class="alert-item alert-info">
                                    <div>
                                        <strong>Système opérationnel</strong><br>
                                        <small>Tous les services fonctionnent normalement</small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Orders Page -->
            <div id="ordersPage" class="page-content" style="display: none;">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h1 style="color: white;">Gestion des Commandes</h1>
                    <div>
                        <select class="form-select" id="ordersFilter" style="width: auto;">
                            <option value="">Tous les statuts</option>
                            <option value="pending">En attente</option>
                            <option value="confirmed">Confirmée</option>
                            <option value="processing">En cours</option>
                            <option value="shipped">Expédiée</option>
                            <option value="delivered">Livrée</option>
                            <option value="cancelled">Annulée</option>
                        </select>
                    </div>
                </div>

                <div class="table-container">
                    <div class="table-responsive">
                        <table class="table table-hover" id="ordersTable">
                            <thead>
                                <tr>
                                    <th>Commande</th>
                                    <th>Client</th>
                                    <th>Montant</th>
                                    <th>Statut</th>
                                    <th>Date</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="ordersTableBody">
                                <tr>
                                    <td colspan="6" class="text-center">Chargement...</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Products Page -->
            <div id="productsPage" class="page-content" style="display: none;">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h1 style="color: white;">Gestion des Produits</h1>
                    <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addProductModal">
                        <i class="fas fa-plus"></i> Ajouter un Produit
                    </button>
                </div>

                <div class="table-container">
                    <div class="table-responsive">
                        <table class="table table-hover" id="productsTable">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Nom</th>
                                    <th>Catégorie</th>
                                    <th>Prix</th>
                                    <th>Stock</th>
                                    <th>Statut</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="productsTableBody">
                                <tr>
                                    <td colspan="7" class="text-center">Chargement...</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Users Page -->
            <div id="usersPage" class="page-content" style="display: none;">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h1 style="color: white;">Gestion des Utilisateurs</h1>
                </div>

                <div class="table-container">
                    <div class="table-responsive">
                        <table class="table table-hover" id="usersTable">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Nom</th>
                                    <th>Email</th>
                                    <th>Téléphone</th>
                                    <th>Entreprise</th>
                                    <th>Admin</th>
                                    <th>Date d'inscription</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="usersTableBody">
                                <tr>
                                    <td colspan="8" class="text-center">Chargement...</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Analytics Page -->
            <div id="analyticsPage" class="page-content" style="display: none;">
                <h1 style="color: white; margin-bottom: 2rem;">Analytiques Avancées</h1>

                <div class="row mb-4">
                    <div class="col-lg-6">
                        <div class="chart-container">
                            <h3 style="color: #2D1B69;">Top Produits</h3>
                            <canvas id="topProductsChart" height="300"></canvas>
                        </div>
                    </div>
                    <div class="col-lg-6">
                        <div class="chart-container">
                            <h3 style="color: #2D1B69;">Répartition par Catégorie</h3>
                            <canvas id="categoryChart" height="300"></canvas>
                        </div>
                    </div>
                </div>

                <div class="chart-container">
                    <h3 style="color: #2D1B69;">Évolution des Ventes</h3>
                    <canvas id="revenueChart" height="400"></canvas>
                </div>
            </div>

            <!-- Monitoring Page -->
            <div id="monitoringPage" class="page-content" style="display: none;">
                <h1 style="color: white; margin-bottom: 2rem;">Monitoring Système</h1>

                <div class="row mb-4">
                    <div class="col-lg-6">
                        <div class="chart-container">
                            <h3 style="color: #2D1B69;">Utilisation CPU</h3>
                            <canvas id="cpuChart" height="300"></canvas>
                        </div>
                    </div>
                    <div class="col-lg-6">
                        <div class="chart-container">
                            <h3 style="color: #2D1B69;">Utilisation Mémoire</h3>
                            <canvas id="memoryChart" height="300"></canvas>
                        </div>
                    </div>
                </div>

                <div class="row">
                    <div class="col-lg-6">
                        <div class="chart-container">
                            <h3 style="color: #2D1B69;">Temps de Réponse</h3>
                            <canvas id="responseTimeChart" height="300"></canvas>
                        </div>
                    </div>
                    <div class="col-lg-6">
                        <div class="chart-container">
                            <h3 style="color: #2D1B69;">Score de Sécurité</h3>
                            <canvas id="securityChart" height="300"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Security Page -->
            <div id="securityPage" class="page-content" style="display: none;">
                <h1 style="color: white; margin-bottom: 2rem;">Centre de Sécurité</h1>

                <div class="row mb-4">
                    <div class="col-lg-6">
                        <div class="chart-container">
                            <h3 style="color: #2D1B69;">Événements de Sécurité (24h)</h3>
                            <canvas id="securityEventsChart" height="300"></canvas>
                        </div>
                    </div>
                    <div class="col-lg-6">
                        <div class="chart-container">
                            <h3 style="color: #2D1B69;">Tentatives de Connexion</h3>
                            <canvas id="loginAttemptsChart" height="300"></canvas>
                        </div>
                    </div>
                </div>

                <div class="table-container">
                    <h3 style="color: #2D1B69; margin-bottom: 1.5rem;">Logs de Sécurité Récents</h3>
                    <div class="table-responsive">
                        <table class="table table-hover" id="securityLogsTable">
                            <thead>
                                <tr>
                                    <th>Timestamp</th>
                                    <th>Action</th>
                                    <th>Détails</th>
                                    <th>IP</th>
                                    <th>Statut</th>
                                </tr>
                            </thead>
                            <tbody id="securityLogsBody">
                                <tr>
                                    <td colspan="5" class="text-center">Chargement...</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Backups Page -->
            <div id="backupsPage" class="page-content" style="display: none;">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h1 style="color: white;">Gestion des Sauvegardes</h1>
                    <div>
                        <button class="btn btn-success" onclick="createFullBackup()">
                            <i class="fas fa-plus"></i> Nouvelle Sauvegarde
                        </button>
                        <button class="btn btn-warning" onclick="testBackupIntegrity()">
                            <i class="fas fa-check"></i> Tester l'Intégrité
                        </button>
                    </div>
                </div>

                <div class="row mb-4">
                    <div class="col-lg-4">
                        <div class="stats-card">
                            <div class="stats-icon" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%);">
                                <i class="fas fa-database" style="color: white;"></i>
                            </div>
                            <div class="stats-value" id="backupCount">-</div>
                            <div class="stats-label">Sauvegardes</div>
                        </div>
                    </div>
                    <div class="col-lg-4">
                        <div class="stats-card">
                            <div class="stats-icon" style="background: linear-gradient(135deg, #17a2b8 0%, #007bff 100%);">
                                <i class="fas fa-hdd" style="color: white;"></i>
                            </div>
                            <div class="stats-value" id="totalBackupSize">-</div>
                            <div class="stats-label">Espace Utilisé</div>
                        </div>
                    </div>
                    <div class="col-lg-4">
                        <div class="stats-card">
                            <div class="stats-icon" style="background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);">
                                <i class="fas fa-clock" style="color: white;"></i>
                            </div>
                            <div class="stats-value" id="lastBackup">-</div>
                            <div class="stats-label">Dernière Sauvegarde</div>
                        </div>
                    </div>
                </div>

                <div class="table-container">
                    <div class="table-responsive">
                        <table class="table table-hover" id="backupsTable">
                            <thead>
                                <tr>
                                    <th>Type</th>
                                    <th>Fichier</th>
                                    <th>Taille</th>
                                    <th>Statut</th>
                                    <th>Date</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="backupsTableBody">
                                <tr>
                                    <td colspan="6" class="text-center">Chargement...</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Settings Page -->
            <div id="settingsPage" class="page-content" style="display: none;">
                <h1 style="color: white; margin-bottom: 2rem;">Paramètres Système</h1>

                <div class="row">
                    <div class="col-lg-6">
                        <div class="chart-container">
                            <h3 style="color: #2D1B69;">Configuration Générale</h3>
                            <form id="settingsForm">
                                <div class="mb-3">
                                    <label class="form-label">Nom de l'application</label>
                                    <input type="text" class="form-control" value="PassPrint" readonly>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Version</label>
                                    <input type="text" class="form-control" value="2.0.0" readonly>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Environnement</label>
                                    <input type="text" class="form-control" value="Production" readonly>
                                </div>
                            </form>
                        </div>
                    </div>
                    <div class="col-lg-6">
                        <div class="chart-container">
                            <h3 style="color: #2D1B69;">Actions Système</h3>
                            <div class="d-grid gap-2">
                                <button class="btn btn-primary" onclick="clearAllCaches()">
                                    <i class="fas fa-broom"></i> Vider tous les Caches
                                </button>
                                <button class="btn btn-warning" onclick="restartServices()">
                                    <i class="fas fa-redo"></i> Redémarrer les Services
                                </button>
                                <button class="btn btn-info" onclick="generateSystemReport()">
                                    <i class="fas fa-file-alt"></i> Générer un Rapport
                                </button>
                                <button class="btn btn-danger" onclick="emergencyMaintenance()">
                                    <i class="fas fa-exclamation-triangle"></i> Maintenance d'Urgence
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Add Product Modal -->
    <div class="modal fade" id="addProductModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Ajouter un Produit</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="addProductForm">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Nom du produit *</label>
                                    <input type="text" class="form-control" name="name" required>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Prix *</label>
                                    <input type="number" class="form-control" name="price" step="0.01" required>
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Catégorie *</label>
                                    <select class="form-select" name="category" required>
                                        <option value="">Choisir une catégorie</option>
                                        <option value="print">Impression</option>
                                        <option value="supplies">Fournitures</option>
                                        <option value="usb">Clés USB</option>
                                        <option value="other">Autres</option>
                                    </select>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label class="form-label">Quantité en stock</label>
                                    <input type="number" class="form-control" name="stock_quantity" value="0">
                                </div>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Description</label>
                            <textarea class="form-control" name="description" rows="3"></textarea>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">URL de l'image</label>
                            <input type="url" class="form-control" name="image_url">
                        </div>
                        <div class="mb-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="is_active" checked>
                                <label class="form-check-label">Produit actif</label>
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
        const API_BASE = '/api';
        const REFRESH_INTERVAL = 30000; // 30 secondes

        // Variables globales
        let currentPage = 'overview';
        let charts = {};
        let refreshTimer;
        let isAuthenticated = false;
        let currentUser = null;

        // Initialisation
        document.addEventListener('DOMContentLoaded', function() {
            checkAuthentication();
        });

        // Fonctions d'authentification
        async function checkAuthentication() {
            try {
                const token = localStorage.getItem('admin_token');
                if (!token) {
                    showLoginModal();
                    return;
                }

                const response = await fetch(`${API_BASE}/auth/verify`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.user && data.user.is_admin) {
                        isAuthenticated = true;
                        currentUser = data.user;
                        hideAuthOverlay();
                        initializeDashboard();
                        setupEventListeners();
                        loadDashboardData();
                        startAutoRefresh();
                        updateUserInfo();
                    } else {
                        showLoginModal();
                    }
                } else {
                    localStorage.removeItem('admin_token');
                    showLoginModal();
                }
            } catch (error) {
                console.error('Erreur vérification auth:', error);
                showLoginModal();
            }
        }

        function showLoginModal() {
            document.getElementById('authOverlay').style.display = 'none';
            const loginModal = new bootstrap.Modal(document.getElementById('loginModal'), {
                backdrop: 'static',
                keyboard: false
            });
            loginModal.show();
        }

        function showSignupModal() {
            bootstrap.Modal.getInstance(document.getElementById('loginModal')).hide();
            const signupModal = new bootstrap.Modal(document.getElementById('signupModal'), {
                backdrop: 'static',
                keyboard: false
            });
            signupModal.show();
        }

        function hideAuthOverlay() {
            document.getElementById('authOverlay').style.display = 'none';
        }

        async function login() {
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
            const rememberMe = document.getElementById('rememberMe').checked;

            if (!email || !password) {
                showLoginError('Veuillez remplir tous les champs');
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/auth/login`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ email, password })
                });

                const data = await response.json();

                if (response.ok && data.user && data.user.is_admin) {
                    localStorage.setItem('admin_token', data.token);
                    isAuthenticated = true;
                    currentUser = data.user;

                    bootstrap.Modal.getInstance(document.getElementById('loginModal')).hide();
                    hideAuthOverlay();
                    initializeDashboard();
                    setupEventListeners();
                    loadDashboardData();
                    startAutoRefresh();
                    updateUserInfo();

                    showAlert('Connexion réussie!', 'success');
                } else {
                    showLoginError(data.error || 'Email ou mot de passe incorrect');
                }
            } catch (error) {
                showLoginError('Erreur de connexion réseau');
            }
        }

        async function signup() {
            const firstName = document.getElementById('signupFirstName').value;
            const lastName = document.getElementById('signupLastName').value;
            const email = document.getElementById('signupEmail').value;
            const password = document.getElementById('signupPassword').value;
            const confirmPassword = document.getElementById('signupConfirmPassword').value;
            const phone = document.getElementById('signupPhone').value;
            const company = document.getElementById('signupCompany').value;
            const acceptTerms = document.getElementById('acceptTerms').checked;

            // Validation
            if (!firstName || !lastName || !email || !password) {
                showSignupError('Veuillez remplir tous les champs obligatoires');
                return;
            }

            if (password !== confirmPassword) {
                showSignupError('Les mots de passe ne correspondent pas');
                return;
            }

            if (password.length < 8) {
                showSignupError('Le mot de passe doit contenir au moins 8 caractères');
                return;
            }

            if (!acceptTerms) {
                showSignupError('Veuillez accepter les conditions d\'utilisation');
                return;
            }

            try {
                const response = await fetch(`${API_BASE}/auth/register`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        first_name: firstName,
                        last_name: lastName,
                        email,
                        password,
                        phone,
                        company
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    showSignupSuccess('Compte créé avec succès! Vous pouvez maintenant vous connecter.');
                    setTimeout(() => {
                        showLoginModal();
                    }, 2000);
                } else {
                    showSignupError(data.error || 'Erreur lors de la création du compte');
                }
            } catch (error) {
                showSignupError('Erreur de connexion réseau');
            }
        }

        function showLoginError(message) {
            const errorDiv = document.getElementById('loginError');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }

        function showSignupError(message) {
            const errorDiv = document.getElementById('signupError');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            document.getElementById('signupSuccess').style.display = 'none';
        }

        function showSignupSuccess(message) {
            const successDiv = document.getElementById('signupSuccess');
            successDiv.textContent = message;
            successDiv.style.display = 'block';
            document.getElementById('signupError').style.display = 'none';
        }

        function updateUserInfo() {
            if (currentUser) {
                const userName = `${currentUser.first_name} ${currentUser.last_name}`;
                document.querySelector('.dropdown-toggle .fa-user').nextSibling.textContent = userName;
            }
        }

        function logout() {
            localStorage.removeItem('admin_token');
            isAuthenticated = false;
            currentUser = null;
            location.reload();
        }

        // Gestionnaire d'événements pour les formulaires
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                const activeModal = document.querySelector('.modal.show');
                if (activeModal) {
                    const modalId = activeModal.id;
                    if (modalId === 'loginModal') {
                        login();
                    } else if (modalId === 'signupModal') {
                        signup();
                    }
                }
            }
        });

        function initializeDashboard() {
            // Initialiser les graphiques
            initializeCharts();

            // Configurer DataTables
            if (typeof $.fn.DataTable !== 'undefined') {
                $('#ordersTable, #productsTable, #usersTable, #securityLogsTable, #backupsTable').DataTable({
                    language: {
                        url: '//cdn.datatables.net/plug-ins/1.13.4/i18n/fr-FR.json'
                    },
                    pageLength: 25,
                    responsive: true
                });
            }
        }

        function setupEventListeners() {
            // Navigation sidebar
            document.querySelectorAll('.sidebar-menu a').forEach(link => {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    const page = this.getAttribute('data-page');
                    showPage(page);
                });
            });

            // Toggle sidebar
            document.getElementById('sidebarToggle').addEventListener('click', function() {
                document.getElementById('sidebar').classList.toggle('show');
                document.getElementById('mainContent').classList.toggle('expanded');
            });

            // Orders filter
            document.getElementById('ordersFilter').addEventListener('change', function() {
                loadOrders();
            });
        }

        function showPage(pageName) {
            // Masquer toutes les pages
            document.querySelectorAll('.page-content').forEach(page => {
                page.style.display = 'none';
            });

            // Afficher la page demandée
            document.getElementById(pageName + 'Page').style.display = 'block';
            currentPage = pageName;

            // Mettre à jour la navigation
            document.querySelectorAll('.sidebar-menu a').forEach(link => {
                link.classList.remove('active');
            });
            document.querySelector(`[data-page="${pageName}"]`).classList.add('active');

            // Charger les données de la page
            loadPageData(pageName);
        }

        async function loadDashboardData() {
            try {
                const response = await fetch(`${API_BASE}/admin/dashboard`);
                const data = await response.json();

                if (response.ok) {
                    updateStatsCards(data.stats);
                    updateRecentOrders(data.recent_orders);
                    updateCharts(data);
                    updateLastUpdate();
                } else {
                    console.error('Erreur chargement dashboard:', data.error);
                }
            } catch (error) {
                console.error('Erreur réseau:', error);
            }
        }

        function updateStatsCards(stats) {
            document.getElementById('totalUsers').textContent = stats.total_users || 0;
            document.getElementById('totalOrders').textContent = stats.total_orders || 0;
            document.getElementById('totalProducts').textContent = stats.total_products || 0;
            document.getElementById('monthlyRevenue').textContent = formatPrice(stats.monthly_revenue || 0);
        }

        function updateRecentOrders(orders) {
            const tbody = document.getElementById('recentOrdersBody');

            if (!orders || orders.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center">Aucune commande récente</td></tr>';
                return;
            }

            tbody.innerHTML = orders.map(order => `
                <tr>
                    <td><strong>${order.order_number}</strong></td>
                    <td>${order.customer_id || 'N/A'}</td>
                    <td>${formatPrice(order.total_amount)}</td>
                    <td><span class="status-badge status-${order.status}">${getStatusLabel(order.status)}</span></td>
                    <td>${new Date(order.created_at).toLocaleDateString('fr-FR')}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" onclick="viewOrder('${order.order_number}')">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-warning" onclick="editOrder('${order.order_number}')">
                            <i class="fas fa-edit"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        }

        function updateLastUpdate() {
            document.getElementById('lastUpdate').textContent = new Date().toLocaleString('fr-FR');
        }

        function formatPrice(price) {
            return new Intl.NumberFormat('fr-FR').format(price) + ' FCFA';
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

        function initializeCharts() {
            // Graphique des ventes mensuelles
            const salesCtx = document.getElementById('salesChart').getContext('2d');
            charts.salesChart = new Chart(salesCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Ventes (FCFA)',
                        data: [],
                        borderColor: '#2D1B69',
                        backgroundColor: 'rgba(45, 27, 105, 0.1)',
                        fill: true
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
                                    return formatPrice(value);
                                }
                            }
                        }
                    }
                }
            });

            // Graphique des statuts de commandes
            const ordersCtx = document.getElementById('ordersChart').getContext('2d');
            charts.ordersChart = new Chart(ordersCtx, {
                type: 'doughnut',
                data: {
                    labels: [],
                    datasets: [{
                        data: [],
                        backgroundColor: [
                            '#ffc107', '#17a2b8', '#28a745', '#dc3545', '#6f42c1', '#fd7e14'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }

        function updateCharts(data) {
            // Mettre à jour le graphique des ventes
            if (data.monthly_sales && charts.salesChart) {
                charts.salesChart.data.labels = data.monthly_sales.map(item => item.month);
                charts.salesChart.data.datasets[0].data = data.monthly_sales.map(item => item.revenue);
                charts.salesChart.update();
            }

            // Mettre à jour le graphique des statuts
            if (data.status_counts && charts.ordersChart) {
                const statusLabels = Object.keys(data.status_counts);
                const statusData = Object.values(data.status_counts);

                charts.ordersChart.data.labels = statusLabels.map(label => getStatusLabel(label));
                charts.ordersChart.data.datasets[0].data = statusData;
                charts.ordersChart.update();
            }
        }

        function loadPageData(pageName) {
            switch(pageName) {
                case 'orders':
                    loadOrders();
                    break;
                case 'products':
                    loadProducts();
                    break;
                case 'users':
                    loadUsers();
                    break;
                case 'analytics':
                    loadAnalytics();
                    break;
                case 'monitoring':
                    loadMonitoring();
                    break;
                case 'security':
                    loadSecurityLogs();
                    break;
                case 'backups':
                    loadBackups();
                    break;
            }
        }

        async function loadOrders() {
            try {
                const statusFilter = document.getElementById('ordersFilter').value;
                let url = `${API_BASE}/admin/orders`;
                if (statusFilter) {
                    url += `?status=${statusFilter}`;
                }

                const response = await fetch(url);
                const data = await response.json();

                if (response.ok) {
                    updateOrdersTable(data.orders);
                } else {
                    console.error('Erreur chargement commandes:', data.error);
                }
            } catch (error) {
                console.error('Erreur réseau:', error);
            }
        }

        function updateOrdersTable(orders) {
            const tbody = document.getElementById('ordersTableBody');

            if (!orders || orders.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center">Aucune commande trouvée</td></tr>';
                return;
            }

            tbody.innerHTML = orders.map(order => `
                <tr>
                    <td><strong>${order.order_number}</strong></td>
                    <td>${order.customer_id || 'N/A'}</td>
                    <td>${formatPrice(order.total_amount)}</td>
                    <td><span class="status-badge status-${order.status}">${getStatusLabel(order.status)}</span></td>
                    <td>${new Date(order.created_at).toLocaleDateString('fr-FR')}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" onclick="viewOrder('${order.order_number}')">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-warning" onclick="editOrder('${order.order_number}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="cancelOrder('${order.order_number}')">
                            <i class="fas fa-times"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        }

        async function loadProducts() {
            try {
                const response = await fetch(`${API_BASE}/products`);
                const products = await response.json();

                updateProductsTable(products);
            } catch (error) {
                console.error('Erreur chargement produits:', error);
            }
        }

        function updateProductsTable(products) {
            const tbody = document.getElementById('productsTableBody');

            if (!products || products.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="text-center">Aucun produit trouvé</td></tr>';
                return;
            }

            tbody.innerHTML = products.map(product => `
                <tr>
                    <td>${product.id}</td>
                    <td><strong>${product.name}</strong></td>
                    <td><span class="badge bg-secondary">${product.category}</span></td>
                    <td>${formatPrice(product.price)}</td>
                    <td>${product.stock_quantity || 0}</td>
                    <td>
                        <span class="status-badge ${product.is_active ? 'status-delivered' : 'status-cancelled'}">
                            ${product.is_active ? 'Actif' : 'Inactif'}
                        </span>
                    </td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" onclick="editProduct(${product.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="toggleProductStatus(${product.id})">
                            <i class="fas fa-toggle-${product.is_active ? 'off' : 'on'}"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        }

        async function loadUsers() {
            try {
                const response = await fetch(`${API_BASE}/admin/users`);
                const data = await response.json();

                if (response.ok) {
                    updateUsersTable(data.users);
                } else {
                    console.error('Erreur chargement utilisateurs:', data.error);
                }
            } catch (error) {
                console.error('Erreur réseau:', error);
            }
        }

        function updateUsersTable(users) {
            const tbody = document.getElementById('usersTableBody');

            if (!users || users.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" class="text-center">Aucun utilisateur trouvé</td></tr>';
                return;
            }

            tbody.innerHTML = users.map(user => `
                <tr>
                    <td>${user.id}</td>
                    <td><strong>${user.first_name} ${user.last_name}</strong></td>
                    <td>${user.email}</td>
                    <td>${user.phone || 'N/A'}</td>
                    <td>${user.company || 'N/A'}</td>
                    <td>
                        <span class="status-badge ${user.is_admin ? 'status-delivered' : 'status-pending'}">
                            ${user.is_admin ? 'Admin' : 'Utilisateur'}
                        </span>
                    </td>
                    <td>${new Date(user.created_at).toLocaleDateString('fr-FR')}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" onclick="editUser(${user.id})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-warning" onclick="resetUserPassword(${user.id})">
                            <i class="fas fa-key"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        }

        async function loadAnalytics() {
            try {
                const response = await fetch(`${API_BASE}/admin/analytics`);
                const data = await response.json();

                if (response.ok) {
                    updateAnalyticsCharts(data);
                } else {
                    console.error('Erreur chargement analytiques:', data.error);
                }
            } catch (error) {
                console.error('Erreur réseau:', error);
            }
        }

        function updateAnalyticsCharts(data) {
            // Mettre à jour le graphique des top produits
            if (data.top_products && charts.topProductsChart) {
                charts.topProductsChart.data.labels = data.top_products.map(item => item.product.name);
                charts.topProductsChart.data.datasets[0].data = data.top_products.map(item => item.total_sold);
                charts.topProductsChart.update();
            }

            // Mettre à jour le graphique des revenus
            if (data.monthly_sales && charts.revenueChart) {
                charts.revenueChart.data.labels = data.monthly_sales.map(item => item.month);
                charts.revenueChart.data.datasets[0].data = data.monthly_sales.map(item => item.revenue);
                charts.revenueChart.update();
            }
        }

        async function loadMonitoring() {
            try {
                const response = await fetch(`${API_BASE}/monitoring/metrics`);
                const data = await response.json();

                if (response.ok) {
                    updateMonitoringCharts(data.metrics);
                } else {
                    console.error('Erreur chargement monitoring:', data.error);
                }
            } catch (error) {
                console.error('Erreur réseau:', error);
            }
        }

        function updateMonitoringCharts(metrics) {
            // Mettre à jour les graphiques de monitoring
            if (metrics.system) {
                updateSystemCharts(metrics.system);
            }
        }

        function updateSystemCharts(systemMetrics) {
            // Mettre à jour les graphiques système
            console.log('Mise à jour graphiques système:', systemMetrics);
        }

        async function loadSecurityLogs() {
            try {
                // Simulation des logs de sécurité
                const mockSecurityLogs = [
                    {
                        created_at: new Date().toISOString(),
                        action: 'login_success',
                        details: 'Connexion réussie',
                        ip_address: '192.168.1.100',
                        status: 'success'
                    },
                    {
                        created_at: new Date(Date.now() - 3600000).toISOString(),
                        action: 'failed_login',
                        details: 'Tentative de connexion échouée',
                        ip_address: '192.168.1.101',
                        status: 'failure'
                    }
                ];

                updateSecurityLogsTable(mockSecurityLogs);
            } catch (error) {
                console.error('Erreur chargement logs sécurité:', error);
            }
        }

        function updateSecurityLogsTable(logs) {
            const tbody = document.getElementById('securityLogsBody');

            if (!logs || logs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center">Aucun log de sécurité</td></tr>';
                return;
            }

            tbody.innerHTML = logs.map(log => `
                <tr>
                    <td>${new Date(log.created_at).toLocaleString('fr-FR')}</td>
                    <td>${log.action}</td>
                    <td>${log.details}</td>
                    <td>${log.ip_address || 'N/A'}</td>
                    <td><span class="status-badge ${log.status === 'success' ? 'status-delivered' : 'status-cancelled'}">${log.status}</span></td>
                </tr>
            `).join('');
        }

        async function loadBackups() {
            try {
                // Simulation des sauvegardes
                const mockBackups = [
                    {
                        backup_type: 'database',
                        file_path: '/backups/passprint_db_20250104.sql.gz',
                        file_size: 52428800,
                        status: 'success',
                        created_at: new Date().toISOString()
                    },
                    {
                        backup_type: 'files',
                        file_path: '/backups/passprint_files_20250104.tar.gz',
                        file_size: 104857600,
                        status: 'success',
                        created_at: new Date(Date.now() - 86400000).toISOString()
                    }
                ];

                updateBackupsTable(mockBackups);
                updateBackupStats(mockBackups);
            } catch (error) {
                console.error('Erreur chargement sauvegardes:', error);
            }
        }

        function updateBackupsTable(backups) {
            const tbody = document.getElementById('backupsTableBody');

            if (!backups || backups.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center">Aucune sauvegarde trouvée</td></tr>';
                return;
            }

            tbody.innerHTML = backups.map(backup => `
                <tr>
                    <td><span class="badge bg-secondary">${backup.backup_type}</span></td>
                    <td>${backup.file_path.split('/').pop()}</td>
                    <td>${formatFileSize(backup.file_size)}</td>
                    <td><span class="status-badge ${backup.status === 'success' ? 'status-delivered' : 'status-cancelled'}">${backup.status}</span></td>
                    <td>${new Date(backup.created_at).toLocaleDateString('fr-FR')}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" onclick="restoreBackup('${backup.file_path}')">
                            <i class="fas fa-undo"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-info" onclick="downloadBackup('${backup.file_path}')">
                            <i class="fas fa-download"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteBackup('${backup.file_path}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        }

        function updateBackupStats(backups) {
            document.getElementById('backupCount').textContent = backups.length;
            const totalSize = backups.reduce((sum, backup) => sum + backup.file_size, 0);
            document.getElementById('totalBackupSize').textContent = formatFileSize(totalSize);

            if (backups.length > 0) {
                const lastBackup = backups.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))[0];
                document.getElementById('lastBackup').textContent = new Date(lastBackup.created_at).toLocaleDateString('fr-FR');
            }
        }

        function formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }

        function startAutoRefresh() {
            refreshTimer = setInterval(() => {
                if (currentPage === 'overview') {
                    loadDashboardData();
                }
            }, REFRESH_INTERVAL);
        }

        function stopAutoRefresh() {
            if (refreshTimer) {
                clearInterval(refreshTimer);
            }
        }

        // Actions
        async function saveProduct() {
            const form = document.getElementById('addProductForm');
            const formData = new FormData(form);
            const productData = {};

            formData.forEach((value, key) => {
                if (key === 'price' || key === 'stock_quantity') {
                    productData[key] = parseFloat(value) || 0;
                } else if (key === 'is_active') {
                    productData[key] = true;
                } else {
                    productData[key] = value;
                }
            });

            try {
                const response = await fetch(`${API_BASE}/admin/products`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(productData)
                });

                if (response.ok) {
                    bootstrap.Modal.getInstance(document.getElementById('addProductModal')).hide();
                    loadProducts();
                    showAlert('Produit créé avec succès!', 'success');
                } else {
                    const error = await response.json();
                    showAlert(error.error || 'Erreur lors de la création du produit', 'danger');
                }
            } catch (error) {
                showAlert('Erreur réseau', 'danger');
            }
        }

        function showAlert(message, type) {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
            alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
            alertDiv.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;

            document.body.appendChild(alertDiv);

            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        }

        // Placeholder functions for actions
        function viewOrder(orderNumber) {
            showAlert(`Visualisation de la commande ${orderNumber}`, 'info');
        }

        function editOrder(orderNumber) {
            showAlert(`Modification de la commande ${orderNumber}`, 'info');
        }

        function cancelOrder(orderNumber) {
            if (confirm('Êtes-vous sûr de vouloir annuler cette commande?')) {
                showAlert(`Commande ${orderNumber} annulée`, 'warning');
            }
        }

        function editProduct(productId) {
            showAlert(`Modification du produit ${productId}`, 'info');
        }

        function toggleProductStatus(productId) {
            showAlert(`Changement de statut du produit ${productId}`, 'info');
        }

        function editUser(userId) {
            showAlert(`Modification de l'utilisateur ${userId}`, 'info');
        }

        function resetUserPassword(userId) {
            showAlert(`Réinitialisation du mot de passe utilisateur ${userId}`, 'info');
        }

        function createFullBackup() {
            showAlert('Création d\'une sauvegarde complète...', 'info');
        }

        function testBackupIntegrity() {
            showAlert('Test d\'intégrité des sauvegardes...', 'info');
        }

        function restoreBackup(backupPath) {
            if (confirm('Êtes-vous sûr de vouloir restaurer cette sauvegarde?')) {
                showAlert(`Restauration de ${backupPath}...`, 'warning');
            }
        }

        function downloadBackup(backupPath) {
            showAlert(`Téléchargement de ${backupPath}...`, 'info');
        }

        function deleteBackup(backupPath) {
            if (confirm('Êtes-vous sûr de vouloir supprimer cette sauvegarde?')) {
                showAlert(`Suppression de ${backupPath}...`, 'danger');
            }
        }

        function clearAllCaches() {
            if (confirm('Êtes-vous sûr de vouloir vider tous les caches?')) {
                showAlert('Vider tous les caches...', 'warning');
            }
        }

        function restartServices() {
            if (confirm('Êtes-vous sûr de vouloir redémarrer les services?')) {
                showAlert('Redémarrage des services...', 'warning');
            }
        }

        function generateSystemReport() {
            showAlert('Génération du rapport système...', 'info');
        }

        function emergencyMaintenance() {
            if (confirm('Êtes-vous sûr de vouloir activer la maintenance d\'urgence?')) {
                showAlert('Maintenance d\'urgence activée', 'danger');
            }
        }

        function showProfile() {
            showAlert('Fonctionnalité de profil à venir', 'info');
        }

        function showSettings() {
            showAlert('Fonctionnalité de paramètres à venir', 'info');
        }

        // Cleanup on page unload
        window.addEventListener('beforeunload', function() {
            stopAutoRefresh();
        });
    </script>
</body>
</html>
"""

# Blueprint pour le dashboard admin
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
def admin_dashboard():
    """Servir le dashboard admin professionnel"""
    return render_template_string(ADMIN_DASHBOARD_TEMPLATE)

# Fonction pour enregistrer le blueprint
def register_admin_dashboard(app):
    """Enregistrer le dashboard admin dans l'application"""
    app.register_blueprint(admin_bp, url_prefix='/admin')
    return app

if __name__ == "__main__":
    print("🚀 Dashboard Admin Professionnel PassPrint")
    print("Accès: http://localhost:5000/admin/dashboard")