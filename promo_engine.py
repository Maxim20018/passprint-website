#!/usr/bin/env python3
"""
Moteur de codes promo pour PassPrint
Gère les codes de réduction, coupons et promotions
"""
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import uuid
import re

@dataclass
class PromoCode:
    """Code promo avec ses règles"""
    code: str
    name: str
    description: str
    discount_type: str  # 'percentage', 'fixed_amount', 'free_shipping'
    discount_value: float
    minimum_amount: float = 0
    maximum_discount: float = 0
    usage_limit: int = 0
    used_count: int = 0
    valid_from: datetime = None
    valid_until: datetime = None
    applicable_products: List[str] = None
    applicable_categories: List[str] = None
    first_time_only: bool = False
    is_active: bool = True

class PromoEngine:
    """Moteur de gestion des codes promo"""

    def __init__(self):
        self.promo_codes = {}

        # Codes promo par défaut
        self._initialize_default_promos()

    def _initialize_default_promos(self):
        """Initialiser les codes promo par défaut"""
        now = datetime.utcnow()

        default_promos = [
            PromoCode(
                code='WELCOME10',
                name='Bienvenue 10%',
                description='10% de réduction pour les nouveaux clients',
                discount_type='percentage',
                discount_value=10.0,
                minimum_amount=10000,
                valid_until=now + timedelta(days=30),
                first_time_only=True,
                is_active=True
            ),
            PromoCode(
                code='BULK20',
                name='Remise Gros Volume',
                description='20% de réduction pour commandes > 100,000 FCFA',
                discount_type='percentage',
                discount_value=20.0,
                minimum_amount=100000,
                valid_until=now + timedelta(days=60),
                is_active=True
            ),
            PromoCode(
                code='PRINT5000',
                name='Réduction Fixe',
                description='5,000 FCFA de réduction sur toute commande',
                discount_type='fixed_amount',
                discount_value=5000,
                minimum_amount=20000,
                valid_until=now + timedelta(days=90),
                is_active=True
            ),
            PromoCode(
                code='STUDENT15',
                name='Remise Étudiant',
                description='15% de réduction pour étudiants',
                discount_type='percentage',
                discount_value=15.0,
                minimum_amount=5000,
                valid_until=now + timedelta(days=180),
                is_active=True
            )
        ]

        for promo in default_promos:
            self.promo_codes[promo.code.upper()] = promo

    def create_promo_code(self, promo_data: Dict) -> Dict:
        """
        Créer un nouveau code promo

        Args:
            promo_data: Données du code promo

        Returns:
            Résultat de la création
        """
        try:
            # Validation du code
            code = promo_data.get('code', '').upper().strip()
            if not code or len(code) < 3:
                return {'error': 'Code promo doit contenir au moins 3 caractères'}

            if code in self.promo_codes:
                return {'error': 'Code promo déjà existant'}

            # Validation du nom
            name = promo_data.get('name', '').strip()
            if not name:
                return {'error': 'Nom du code promo requis'}

            # Création du code promo
            new_promo = PromoCode(
                code=code,
                name=name,
                description=promo_data.get('description', ''),
                discount_type=promo_data.get('discount_type', 'percentage'),
                discount_value=float(promo_data.get('discount_value', 0)),
                minimum_amount=float(promo_data.get('minimum_amount', 0)),
                maximum_discount=float(promo_data.get('maximum_discount', 0)),
                usage_limit=int(promo_data.get('usage_limit', 0)),
                valid_from=datetime.fromisoformat(promo_data['valid_from']) if promo_data.get('valid_from') else datetime.utcnow(),
                valid_until=datetime.fromisoformat(promo_data['valid_until']) if promo_data.get('valid_until') else None,
                applicable_products=promo_data.get('applicable_products', []),
                applicable_categories=promo_data.get('applicable_categories', []),
                first_time_only=promo_data.get('first_time_only', False),
                is_active=promo_data.get('is_active', True)
            )

            self.promo_codes[code] = new_promo

            return {
                'success': True,
                'message': 'Code promo créé avec succès',
                'promo_code': {
                    'code': new_promo.code,
                    'name': new_promo.name,
                    'discount_type': new_promo.discount_type,
                    'discount_value': new_promo.discount_value,
                    'valid_until': new_promo.valid_until.isoformat() if new_promo.valid_until else None
                }
            }

        except Exception as e:
            return {'error': f'Erreur création code promo: {str(e)}'}

    def validate_promo_code(self, code: str, cart_total: float, user_id: str = None, product_categories: List = None) -> Dict:
        """
        Valide un code promo pour un panier donné

        Args:
            code: Code promo à valider
            cart_total: Montant total du panier
            user_id: ID de l'utilisateur
            product_categories: Catégories des produits dans le panier

        Returns:
            Résultat de la validation avec calcul de remise
        """
        try:
            code = code.upper().strip()
            promo = self.promo_codes.get(code)

            if not promo:
                return {'error': 'Code promo invalide'}

            if not promo.is_active:
                return {'error': 'Code promo désactivé'}

            now = datetime.utcnow()
            if promo.valid_from and promo.valid_from > now:
                return {'error': 'Code promo pas encore valide'}

            if promo.valid_until and promo.valid_until < now:
                return {'error': 'Code promo expiré'}

            if promo.usage_limit > 0 and promo.used_count >= promo.usage_limit:
                return {'error': 'Limite d\'utilisation atteinte'}

            if cart_total < promo.minimum_amount:
                return {'error': f'Montant minimum requis: {promo.minimum_amount:,.0f} FCFA'}

            # Vérification première utilisation seulement
            if promo.first_time_only and user_id:
                # Ici vous vérifieriez si l'utilisateur a déjà utilisé ce code
                pass

            # Vérification catégories applicables
            if promo.applicable_categories and product_categories:
                if not any(cat in promo.applicable_categories for cat in product_categories):
                    return {'error': 'Code promo non applicable à ces produits'}

            # Calcul de la remise
            if promo.discount_type == 'percentage':
                discount_amount = cart_total * (promo.discount_value / 100)
                if promo.maximum_discount > 0:
                    discount_amount = min(discount_amount, promo.maximum_discount)
            elif promo.discount_type == 'fixed_amount':
                discount_amount = promo.discount_value
            else:
                discount_amount = 0

            final_amount = cart_total - discount_amount

            return {
                'success': True,
                'valid': True,
                'promo_code': promo.code,
                'discount_type': promo.discount_type,
                'discount_value': promo.discount_value,
                'discount_amount': round(discount_amount, 2),
                'final_amount': round(final_amount, 2),
                'savings': round(discount_amount, 2)
            }

        except Exception as e:
            return {'error': f'Erreur validation code promo: {str(e)}'}

    def apply_promo_code(self, code: str, user_id: str = None) -> Dict:
        """
        Applique un code promo (incrémente le compteur d'utilisation)

        Args:
            code: Code promo à appliquer
            user_id: ID de l'utilisateur

        Returns:
            Résultat de l'application
        """
        try:
            code = code.upper().strip()
            promo = self.promo_codes.get(code)

            if not promo:
                return {'error': 'Code promo invalide'}

            promo.used_count += 1

            return {
                'success': True,
                'message': 'Code promo appliqué avec succès',
                'used_count': promo.used_count,
                'remaining_uses': promo.usage_limit - promo.used_count if promo.usage_limit > 0 else 'illimité'
            }

        except Exception as e:
            return {'error': f'Erreur application code promo: {str(e)}'}

    def get_all_promo_codes(self) -> Dict:
        """
        Retourne tous les codes promo

        Returns:
            Dictionnaire avec tous les codes promo
        """
        try:
            return {
                code: {
                    'code': promo.code,
                    'name': promo.name,
                    'description': promo.description,
                    'discount_type': promo.discount_type,
                    'discount_value': promo.discount_value,
                    'minimum_amount': promo.minimum_amount,
                    'maximum_discount': promo.maximum_discount,
                    'usage_limit': promo.usage_limit,
                    'used_count': promo.used_count,
                    'valid_from': promo.valid_from.isoformat() if promo.valid_from else None,
                    'valid_until': promo.valid_until.isoformat() if promo.valid_until else None,
                    'applicable_categories': promo.applicable_categories,
                    'first_time_only': promo.first_time_only,
                    'is_active': promo.is_active
                }
                for code, promo in self.promo_codes.items()
            }
        except Exception as e:
            return {'error': str(e)}

    def deactivate_promo_code(self, code: str) -> Dict:
        """
        Désactiver un code promo

        Args:
            code: Code promo à désactiver

        Returns:
            Résultat de la désactivation
        """
        try:
            code = code.upper().strip()
            promo = self.promo_codes.get(code)

            if not promo:
                return {'error': 'Code promo invalide'}

            promo.is_active = False

            return {
                'success': True,
                'message': f'Code promo {code} désactivé avec succès'
            }

        except Exception as e:
            return {'error': f'Erreur désactivation: {str(e)}'}

    def get_promo_stats(self) -> Dict:
        """
        Retourne les statistiques des codes promo

        Returns:
            Statistiques d'utilisation
        """
        try:
            total_promos = len(self.promo_codes)
            active_promos = sum(1 for promo in self.promo_codes.values() if promo.is_active)
            total_uses = sum(promo.used_count for promo in self.promo_codes.values())

            # Codes les plus utilisés
            top_promos = sorted(
                self.promo_codes.items(),
                key=lambda x: x[1].used_count,
                reverse=True
            )[:5]

            return {
                'total_promo_codes': total_promos,
                'active_promo_codes': active_promos,
                'total_uses': total_uses,
                'top_promos': [
                    {
                        'code': code,
                        'name': promo.name,
                        'used_count': promo.used_count
                    }
                    for code, promo in top_promos
                ]
            }

        except Exception as e:
            return {'error': str(e)}

# Instance globale du moteur de promo
promo_engine = PromoEngine()

def validate_and_apply_promo_code(code: str, cart_total: float, user_id: str = None, categories: List = None) -> Dict:
    """
    Fonction utilitaire pour valider et appliquer un code promo

    Args:
        code: Code promo
        cart_total: Montant du panier
        user_id: ID utilisateur
        categories: Catégories des produits

    Returns:
        Résultat avec calcul de remise
    """
    return promo_engine.validate_promo_code(code, cart_total, user_id, categories)

def create_new_promo_code(promo_data: Dict) -> Dict:
    """
    Créer un nouveau code promo

    Args:
        promo_data: Données du code promo

    Returns:
        Résultat de la création
    """
    return promo_engine.create_promo_code(promo_data)

def get_available_promo_codes() -> Dict:
    """
    Retourne les codes promo disponibles

    Returns:
        Liste des codes promo actifs
    """
    return {
        code: promo_data for code, promo_data in promo_engine.get_all_promo_codes().items()
        if promo_data['is_active']
    }

if __name__ == "__main__":
    # Test du moteur de promo
    test_result = promo_engine.validate_promo_code('WELCOME10', 50000)
    print("Test de validation de code promo:")
    print(json.dumps(test_result, indent=2, ensure_ascii=False))