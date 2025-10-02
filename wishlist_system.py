#!/usr/bin/env python3
"""
Système de wishlist pour PassPrint
Permet aux utilisateurs de sauvegarder et comparer des produits
"""
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid

@dataclass
class WishlistItem:
    """Élément de wishlist"""
    product_id: str
    product_name: str
    product_price: float
    product_image: str
    product_category: str
    date_added: datetime
    notes: str = ""
    priority: int = 1  # 1-5, 5 étant la plus haute priorité

class WishlistSystem:
    """Système de gestion des wishlists"""

    def __init__(self):
        self.wishlists = {}  # user_id -> list of items
        self.comparisons = {}  # comparison_id -> list of products

    def add_to_wishlist(self, user_id: str, product_data: Dict) -> Dict:
        """
        Ajouter un produit à la wishlist

        Args:
            user_id: ID de l'utilisateur
            product_data: Données du produit

        Returns:
            Résultat de l'ajout
        """
        try:
            if user_id not in self.wishlists:
                self.wishlists[user_id] = []

            # Vérifier si le produit existe déjà
            existing_item = None
            for item in self.wishlists[user_id]:
                if item.product_id == product_data['product_id']:
                    existing_item = item
                    break

            if existing_item:
                return {
                    'success': False,
                    'message': 'Produit déjà dans la wishlist',
                    'item': existing_item
                }

            # Créer nouvel élément
            new_item = WishlistItem(
                product_id=product_data['product_id'],
                product_name=product_data['name'],
                product_price=product_data['price'],
                product_image=product_data.get('image_url', ''),
                product_category=product_data.get('category', ''),
                date_added=datetime.utcnow(),
                notes=product_data.get('notes', ''),
                priority=product_data.get('priority', 1)
            )

            self.wishlists[user_id].append(new_item)

            return {
                'success': True,
                'message': 'Produit ajouté à la wishlist',
                'item': new_item
            }

        except Exception as e:
            return {'error': f'Erreur ajout wishlist: {str(e)}'}

    def remove_from_wishlist(self, user_id: str, product_id: str) -> Dict:
        """
        Retirer un produit de la wishlist

        Args:
            user_id: ID de l'utilisateur
            product_id: ID du produit à retirer

        Returns:
            Résultat de la suppression
        """
        try:
            if user_id not in self.wishlists:
                return {'error': 'Wishlist vide'}

            # Trouver et supprimer l'élément
            for i, item in enumerate(self.wishlists[user_id]):
                if item.product_id == product_id:
                    removed_item = self.wishlists[user_id].pop(i)
                    return {
                        'success': True,
                        'message': 'Produit retiré de la wishlist',
                        'item': removed_item
                    }

            return {'error': 'Produit non trouvé dans la wishlist'}

        except Exception as e:
            return {'error': f'Erreur suppression wishlist: {str(e)}'}

    def get_wishlist(self, user_id: str) -> Dict:
        """
        Récupérer la wishlist d'un utilisateur

        Args:
            user_id: ID de l'utilisateur

        Returns:
            Wishlist de l'utilisateur
        """
        try:
            if user_id not in self.wishlists:
                return {'items': [], 'total': 0}

            items = self.wishlists[user_id]

            # Trier par priorité et date d'ajout
            sorted_items = sorted(items, key=lambda x: (-x.priority, x.date_added))

            return {
                'items': [
                    {
                        'product_id': item.product_id,
                        'product_name': item.product_name,
                        'product_price': item.product_price,
                        'product_image': item.product_image,
                        'product_category': item.product_category,
                        'date_added': item.date_added.isoformat(),
                        'notes': item.notes,
                        'priority': item.priority
                    }
                    for item in sorted_items
                ],
                'total': len(items)
            }

        except Exception as e:
            return {'error': f'Erreur récupération wishlist: {str(e)}'}

    def update_wishlist_item(self, user_id: str, product_id: str, updates: Dict) -> Dict:
        """
        Mettre à jour un élément de la wishlist

        Args:
            user_id: ID de l'utilisateur
            product_id: ID du produit
            updates: Mises à jour à appliquer

        Returns:
            Résultat de la mise à jour
        """
        try:
            if user_id not in self.wishlists:
                return {'error': 'Wishlist vide'}

            # Trouver l'élément
            for item in self.wishlists[user_id]:
                if item.product_id == product_id:
                    # Appliquer les mises à jour
                    for key, value in updates.items():
                        if hasattr(item, key):
                            setattr(item, key, value)

                    return {
                        'success': True,
                        'message': 'Élément wishlist mis à jour',
                        'item': {
                            'product_id': item.product_id,
                            'product_name': item.product_name,
                            'notes': item.notes,
                            'priority': item.priority
                        }
                    }

            return {'error': 'Produit non trouvé dans la wishlist'}

        except Exception as e:
            return {'error': f'Erreur mise à jour wishlist: {str(e)}'}

    def create_comparison(self, product_ids: List[str]) -> Dict:
        """
        Créer une comparaison de produits

        Args:
            product_ids: Liste des IDs de produits à comparer

        Returns:
            ID de la comparaison créée
        """
        try:
            comparison_id = str(uuid.uuid4())

            self.comparisons[comparison_id] = {
                'id': comparison_id,
                'product_ids': product_ids,
                'created_at': datetime.utcnow(),
                'status': 'active'
            }

            return {
                'success': True,
                'comparison_id': comparison_id,
                'message': 'Comparaison créée avec succès'
            }

        except Exception as e:
            return {'error': f'Erreur création comparaison: {str(e)}'}

    def get_comparison(self, comparison_id: str) -> Dict:
        """
        Récupérer une comparaison

        Args:
            comparison_id: ID de la comparaison

        Returns:
            Détails de la comparaison
        """
        try:
            if comparison_id not in self.comparisons:
                return {'error': 'Comparaison non trouvée'}

            comparison = self.comparisons[comparison_id]

            return {
                'id': comparison['id'],
                'product_ids': comparison['product_ids'],
                'created_at': comparison['created_at'].isoformat(),
                'status': comparison['status']
            }

        except Exception as e:
            return {'error': f'Erreur récupération comparaison: {str(e)}'}

    def get_comparison_features(self, product_ids: List[str]) -> Dict:
        """
        Obtenir les caractéristiques pour comparaison

        Args:
            product_ids: Liste des IDs de produits

        Returns:
            Caractéristiques pour comparaison
        """
        try:
            # Données de démonstration pour la comparaison
            products_data = {
                'PROD001': {
                    'name': 'Banderole Premium',
                    'price': 25000,
                    'quality': 5,
                    'durability': 5,
                    'delivery_time': 3,
                    'warranty': 12,
                    'features': ['Résistante UV', 'Installation facile', 'Garantie 1 an']
                },
                'PROD002': {
                    'name': 'Banderole Standard',
                    'price': 15000,
                    'quality': 3,
                    'durability': 3,
                    'delivery_time': 5,
                    'warranty': 6,
                    'features': ['Économique', 'Installation simple']
                }
            }

            comparison_data = []
            for product_id in product_ids:
                if product_id in products_data:
                    comparison_data.append(products_data[product_id])

            return {
                'products': comparison_data,
                'criteria': ['Prix', 'Qualité', 'Durabilité', 'Délai livraison', 'Garantie']
            }

        except Exception as e:
            return {'error': f'Erreur comparaison: {str(e)}'}

    def clear_wishlist(self, user_id: str) -> Dict:
        """
        Vider la wishlist d'un utilisateur

        Args:
            user_id: ID de l'utilisateur

        Returns:
            Résultat de la suppression
        """
        try:
            if user_id in self.wishlists:
                item_count = len(self.wishlists[user_id])
                self.wishlists[user_id] = []

                return {
                    'success': True,
                    'message': f'Wishlist vidée ({item_count} éléments supprimés)'
                }

            return {'error': 'Wishlist déjà vide'}

        except Exception as e:
            return {'error': f'Erreur vidage wishlist: {str(e)}'}

    def get_wishlist_stats(self, user_id: str) -> Dict:
        """
        Obtenir les statistiques de la wishlist

        Args:
            user_id: ID de l'utilisateur

        Returns:
            Statistiques de la wishlist
        """
        try:
            if user_id not in self.wishlists:
                return {'total_items': 0, 'total_value': 0, 'categories': {}}

            items = self.wishlists[user_id]

            total_value = sum(item.product_price for item in items)
            categories = {}
            for item in items:
                category = item.product_category
                if category not in categories:
                    categories[category] = 0
                categories[category] += 1

            return {
                'total_items': len(items),
                'total_value': round(total_value, 2),
                'categories': categories,
                'avg_priority': round(sum(item.priority for item in items) / len(items), 1) if items else 0
            }

        except Exception as e:
            return {'error': f'Erreur statistiques wishlist: {str(e)}'}

# Instance globale du système de wishlist
wishlist_system = WishlistSystem()

def add_product_to_wishlist(user_id: str, product_data: Dict) -> Dict:
    """
    Ajouter un produit à la wishlist

    Args:
        user_id: ID de l'utilisateur
        product_data: Données du produit

    Returns:
        Résultat de l'ajout
    """
    return wishlist_system.add_to_wishlist(user_id, product_data)

def get_user_wishlist(user_id: str) -> Dict:
    """
    Récupérer la wishlist d'un utilisateur

    Args:
        user_id: ID de l'utilisateur

    Returns:
        Wishlist de l'utilisateur
    """
    return wishlist_system.get_wishlist(user_id)

def compare_products(product_ids: List[str]) -> Dict:
    """
    Comparer des produits

    Args:
        product_ids: Liste des IDs de produits

    Returns:
        Comparaison des produits
    """
    return wishlist_system.get_comparison_features(product_ids)

if __name__ == "__main__":
    # Test du système de wishlist
    test_user = "user123"
    test_product = {
        'product_id': 'PROD001',
        'name': 'Banderole Premium',
        'price': 25000,
        'image_url': 'images/banderole.jpg',
        'category': 'print'
    }

    result = wishlist_system.add_to_wishlist(test_user, test_product)
    print("Test ajout wishlist:")
    print(json.dumps(result, indent=2, default=str, ensure_ascii=False))