#!/usr/bin/env python3
"""
Comparateur de produits pour PassPrint
Permet de comparer les caractéristiques des produits
"""
import json

class ProductComparator:
    """Système de comparaison de produits"""

    def __init__(self):
        self.comparison_criteria = {
            'price': 'Prix',
            'quality': 'Qualité',
            'durability': 'Durabilité',
            'delivery_time': 'Délai de livraison',
            'warranty': 'Garantie',
            'features': 'Fonctionnalités'
        }

    def compare_products(self, product_ids: list) -> dict:
        """Comparer des produits"""
        # Données de démonstration
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

        comparison = {
            'products': [],
            'criteria': list(self.comparison_criteria.values()),
            'recommendation': None
        }

        for product_id in product_ids:
            if product_id in products_data:
                comparison['products'].append(products_data[product_id])

        # Recommandation basée sur le meilleur rapport qualité/prix
        if len(comparison['products']) > 1:
            best_product = max(comparison['products'],
                            key=lambda p: (p['quality'] + p['durability']) / p['price'])
            comparison['recommendation'] = best_product['name']

        return comparison

# Instance globale du comparateur
product_comparator = ProductComparator()

def compare_products(product_ids: list) -> dict:
    """Comparer des produits"""
    return product_comparator.compare_products(product_ids)

if __name__ == "__main__":
    print("Comparateur de produits opérationnel!")