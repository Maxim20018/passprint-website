#!/usr/bin/env python3
"""
Système d'avis clients pour PassPrint
Gère les témoignages et évaluations des clients
"""
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import sqlite3

@dataclass
class Review:
    """Avis client"""
    id: int
    customer_id: int
    customer_name: str
    product_id: int
    product_name: str
    rating: int  # 1-5 étoiles
    title: str
    comment: str
    is_verified: bool = False
    is_published: bool = True
    created_at: datetime
    updated_at: datetime

class ReviewsSystem:
    """Système de gestion des avis clients"""

    def __init__(self):
        self.db_path = 'passprint.db'

    def get_connection(self):
        """Connexion à la base de données"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def add_review(self, review_data: Dict) -> Dict:
        """Ajouter un avis client"""
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    INSERT INTO reviews (customer_id, product_id, rating, title, comment, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (
                    review_data['customer_id'],
                    review_data['product_id'],
                    review_data['rating'],
                    review_data['title'],
                    review_data['comment']
                ))

                conn.commit()

                return {'success': True, 'message': 'Avis ajouté avec succès'}

        except Exception as e:
            return {'error': f'Erreur ajout avis: {str(e)}'}

    def get_product_reviews(self, product_id: int) -> Dict:
        """Récupérer les avis d'un produit"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute('''
                    SELECT r.*, u.first_name, u.last_name
                    FROM reviews r
                    LEFT JOIN users u ON r.customer_id = u.id
                    WHERE r.product_id = ? AND r.is_published = 1
                    ORDER BY r.created_at DESC
                ''', (product_id,))

                reviews = cursor.fetchall()

                return {
                    'reviews': [
                        {
                            'id': review['id'],
                            'customer_name': f"{review['first_name']} {review['last_name']}" if review['first_name'] else 'Client anonyme',
                            'rating': review['rating'],
                            'title': review['title'],
                            'comment': review['comment'],
                            'created_at': review['created_at'],
                            'is_verified': review['is_verified']
                        }
                        for review in reviews
                    ],
                    'total': len(reviews),
                    'average_rating': sum(r['rating'] for r in reviews) / len(reviews) if reviews else 0
                }

        except Exception as e:
            return {'error': f'Erreur récupération avis: {str(e)}'}

# Instance globale du système d'avis
reviews_system = ReviewsSystem()

def add_customer_review(review_data: Dict) -> Dict:
    """Ajouter un avis client"""
    return reviews_system.add_review(review_data)

def get_product_reviews(product_id: int) -> Dict:
    """Récupérer les avis d'un produit"""
    return reviews_system.get_product_reviews(product_id)

if __name__ == "__main__":
    print("Système d'avis clients opérationnel!")