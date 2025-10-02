#!/usr/bin/env python3
"""
Système de gestion des stocks temps réel pour PassPrint
Gère les niveaux de stock et les alertes automatiques
"""
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import sqlite3
import threading
import time

@dataclass
class StockAlert:
    """Alerte de stock"""
    product_id: int
    product_name: str
    current_stock: int
    min_stock: int
    alert_type: str  # 'low_stock', 'out_of_stock', 'overstock'
    created_at: datetime
    is_read: bool = False

class StockManager:
    """Gestionnaire de stocks temps réel"""

    def __init__(self):
        self.db_path = 'passprint.db'
        self.alerts = []
        self.stock_history = {}
        self.alert_callbacks = []

        # Démarrer le monitoring
        self.monitoring_thread = threading.Thread(target=self._monitor_stocks, daemon=True)
        self.monitoring_thread.start()

    def get_connection(self):
        """Obtenir une connexion à la base de données"""
        return sqlite3.connect(self.db_path)

    def update_stock(self, product_id: int, new_quantity: int, reason: str = 'manual') -> Dict:
        """
        Mettre à jour le stock d'un produit

        Args:
            product_id: ID du produit
            new_quantity: Nouvelle quantité
            reason: Raison de la mise à jour

        Returns:
            Résultat de la mise à jour
        """
        try:
            with self.get_connection() as conn:
                # Récupérer les infos actuelles
                cursor = conn.execute('SELECT name, stock_quantity, min_stock_level FROM products WHERE id = ?', (product_id,))
                product = cursor.fetchone()

                if not product:
                    return {'error': 'Produit non trouvé'}

                old_quantity = product[1]

                # Mettre à jour le stock
                conn.execute('''
                    UPDATE products
                    SET stock_quantity = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (new_quantity, product_id))

                # Enregistrer dans l'historique
                conn.execute('''
                    INSERT INTO stock_history (product_id, old_quantity, new_quantity, reason, created_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (product_id, old_quantity, new_quantity, reason))

                conn.commit()

                # Vérifier les alertes
                self._check_stock_alerts(product_id, product[0], new_quantity, product[2])

                return {
                    'success': True,
                    'product_id': product_id,
                    'old_quantity': old_quantity,
                    'new_quantity': new_quantity,
                    'reason': reason
                }

        except Exception as e:
            return {'error': f'Erreur mise à jour stock: {str(e)}'}

    def get_stock_levels(self) -> Dict:
        """
        Récupérer tous les niveaux de stock

        Returns:
            Niveaux de stock avec alertes
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT id, name, stock_quantity, min_stock_level
                    FROM products
                    WHERE is_active = 1
                    ORDER BY stock_quantity ASC
                ''')

                products = cursor.fetchall()

                stock_data = {
                    'products': [],
                    'summary': {
                        'total_products': 0,
                        'in_stock': 0,
                        'low_stock': 0,
                        'out_of_stock': 0,
                        'total_value': 0
                    },
                    'alerts': []
                }

                for product in products:
                    product_id, name, quantity, min_stock = product

                    # Déterminer le statut
                    if quantity <= 0:
                        status = 'out_of_stock'
                        stock_data['summary']['out_of_stock'] += 1
                    elif quantity <= min_stock:
                        status = 'low_stock'
                        stock_data['summary']['low_stock'] += 1
                    else:
                        status = 'in_stock'
                        stock_data['summary']['in_stock'] += 1

                    # Récupérer le prix pour calculer la valeur
                    price_cursor = conn.execute('SELECT price FROM products WHERE id = ?', (product_id,))
                    price = price_cursor.fetchone()[0] if price_cursor.fetchone() else 0

                    product_info = {
                        'id': product_id,
                        'name': name,
                        'quantity': quantity,
                        'min_stock': min_stock,
                        'status': status,
                        'value': quantity * price
                    }

                    stock_data['products'].append(product_info)
                    stock_data['summary']['total_value'] += product_info['value']

                stock_data['summary']['total_products'] = len(products)

                # Ajouter les alertes récentes
                stock_data['alerts'] = [
                    {
                        'product_id': alert.product_id,
                        'product_name': alert.product_name,
                        'current_stock': alert.current_stock,
                        'alert_type': alert.alert_type,
                        'created_at': alert.created_at.isoformat()
                    }
                    for alert in self.alerts[-10:]  # 10 dernières alertes
                ]

                return stock_data

        except Exception as e:
            return {'error': f'Erreur récupération stocks: {str(e)}'}

    def _check_stock_alerts(self, product_id: int, product_name: str, current_stock: int, min_stock: int):
        """
        Vérifier et créer les alertes de stock

        Args:
            product_id: ID du produit
            product_name: Nom du produit
            current_stock: Stock actuel
            min_stock: Stock minimum
        """
        try:
            # Alerte rupture de stock
            if current_stock <= 0:
                alert = StockAlert(
                    product_id=product_id,
                    product_name=product_name,
                    current_stock=current_stock,
                    min_stock=min_stock,
                    alert_type='out_of_stock',
                    created_at=datetime.utcnow()
                )
                self.alerts.append(alert)

            # Alerte stock faible
            elif current_stock <= min_stock:
                alert = StockAlert(
                    product_id=product_id,
                    product_name=product_name,
                    current_stock=current_stock,
                    min_stock=min_stock,
                    alert_type='low_stock',
                    created_at=datetime.utcnow()
                )
                self.alerts.append(alert)

            # Nettoyer les vieilles alertes (plus de 24h)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            self.alerts = [alert for alert in self.alerts if alert.created_at > cutoff_time]

        except Exception as e:
            print(f"Erreur vérification alertes: {e}")

    def _monitor_stocks(self):
        """
        Surveiller les stocks en arrière-plan (thread)
        """
        while True:
            try:
                # Vérifier les stocks toutes les 5 minutes
                stock_data = self.get_stock_levels()

                if 'error' not in stock_data:
                    # Vérifier les alertes pour chaque produit
                    for product in stock_data['products']:
                        self._check_stock_alerts(
                            product['id'],
                            product['name'],
                            product['quantity'],
                            product['min_stock']
                        )

                time.sleep(300)  # 5 minutes

            except Exception as e:
                print(f"Erreur monitoring stocks: {e}")
                time.sleep(300)

    def get_stock_alerts(self) -> List[Dict]:
        """
        Récupérer les alertes de stock

        Returns:
            Liste des alertes de stock
        """
        try:
            return [
                {
                    'product_id': alert.product_id,
                    'product_name': alert.product_name,
                    'current_stock': alert.current_stock,
                    'min_stock': alert.min_stock,
                    'alert_type': alert.alert_type,
                    'created_at': alert.created_at.isoformat(),
                    'is_read': alert.is_read
                }
                for alert in self.alerts
            ]
        except Exception as e:
            return []

    def mark_alert_read(self, product_id: int) -> Dict:
        """
        Marquer une alerte comme lue

        Args:
            product_id: ID du produit

        Returns:
            Résultat du marquage
        """
        try:
            for alert in self.alerts:
                if alert.product_id == product_id:
                    alert.is_read = True
                    return {'success': True, 'message': 'Alerte marquée comme lue'}

            return {'error': 'Alerte non trouvée'}

        except Exception as e:
            return {'error': f'Erreur marquage alerte: {str(e)}'}

    def get_stock_history(self, product_id: int, days: int = 30) -> Dict:
        """
        Récupérer l'historique des stocks

        Args:
            product_id: ID du produit
            days: Nombre de jours à récupérer

        Returns:
            Historique des stocks
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT old_quantity, new_quantity, reason, created_at
                    FROM stock_history
                    WHERE product_id = ? AND created_at >= date('now', '-' || ? || ' days')
                    ORDER BY created_at DESC
                ''', (product_id, days))

                history = cursor.fetchall()

                return {
                    'product_id': product_id,
                    'history': [
                        {
                            'old_quantity': row[0],
                            'new_quantity': row[1],
                            'reason': row[2],
                            'created_at': row[3]
                        }
                        for row in history
                    ]
                }

        except Exception as e:
            return {'error': f'Erreur historique stocks: {str(e)}'}

    def predict_stock_needs(self, product_id: int, days_ahead: int = 30) -> Dict:
        """
        Prédire les besoins en stock

        Args:
            product_id: ID du produit
            days_ahead: Nombre de jours à prédire

        Returns:
            Prédiction des besoins en stock
        """
        try:
            # Récupérer l'historique des ventes
            history = self.get_stock_history(product_id, 90)  # 90 jours d'historique

            if 'error' in history:
                return history

            if not history['history']:
                return {'error': 'Historique insuffisant pour la prédiction'}

            # Calcul simple de tendance
            total_consumed = sum(
                max(0, h['old_quantity'] - h['new_quantity'])
                for h in history['history']
                if h['reason'] in ['sale', 'order']
            )

            avg_daily_consumption = total_consumed / 90  # Consommation moyenne par jour
            predicted_consumption = avg_daily_consumption * days_ahead

            # Récupérer le stock actuel
            with self.get_connection() as conn:
                cursor = conn.execute('SELECT stock_quantity, min_stock_level FROM products WHERE id = ?', (product_id,))
                product = cursor.fetchone()

                if not product:
                    return {'error': 'Produit non trouvé'}

                current_stock = product[0]
                min_stock = product[1]

                predicted_stock = current_stock - predicted_consumption
                needs_restock = predicted_stock < min_stock

                return {
                    'product_id': product_id,
                    'current_stock': current_stock,
                    'predicted_consumption': round(predicted_consumption, 2),
                    'predicted_stock': round(predicted_stock, 2),
                    'needs_restock': needs_restock,
                    'recommended_order': max(0, min_stock - predicted_stock + 10),  # +10 de sécurité
                    'confidence': 'medium'  # Niveau de confiance de la prédiction
                }

        except Exception as e:
            return {'error': f'Erreur prédiction stocks: {str(e)}'}

# Instance globale du gestionnaire de stocks
stock_manager = StockManager()

def update_product_stock(product_id: int, quantity: int, reason: str = 'manual') -> Dict:
    """
    Mettre à jour le stock d'un produit

    Args:
        product_id: ID du produit
        quantity: Nouvelle quantité
        reason: Raison de la mise à jour

    Returns:
        Résultat de la mise à jour
    """
    return stock_manager.update_stock(product_id, quantity, reason)

def get_all_stock_levels() -> Dict:
    """
    Récupérer tous les niveaux de stock

    Returns:
        Niveaux de stock avec alertes
    """
    return stock_manager.get_stock_levels()

def get_stock_alerts() -> List[Dict]:
    """
    Récupérer les alertes de stock

    Returns:
        Liste des alertes de stock
    """
    return stock_manager.get_stock_alerts()

if __name__ == "__main__":
    # Test du gestionnaire de stocks
    print("Test du système de gestion des stocks...")

    # Test mise à jour stock
    result = stock_manager.update_stock(1, 5, 'test')
    print(f"Mise à jour stock: {result}")

    # Test récupération stocks
    stocks = stock_manager.get_stock_levels()
    print(f"Niveaux de stock: {len(stocks.get('products', []))} produits")

    print("Système de gestion des stocks opérationnel!")