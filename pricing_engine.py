#!/usr/bin/env python3
"""
Moteur de calcul automatique des prix pour PassPrint
Calcule les prix en fonction des spécifications, quantités et options
"""
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PricingRule:
    """Règle de tarification"""
    product_type: str
    base_price: float
    min_quantity: int
    max_quantity: int
    discount_per_unit: float
    setup_fee: float = 0
    rush_order_multiplier: float = 1.5
    bulk_discount_threshold: int = 50
    bulk_discount_rate: float = 0.15

class PricingEngine:
    """Moteur de calcul des prix avancé"""

    def __init__(self):
        self.rules = {
            'banderole': PricingRule(
                product_type='banderole',
                base_price=25000,
                min_quantity=1,
                max_quantity=100,
                discount_per_unit=100,
                setup_fee=5000,
                bulk_discount_threshold=10,
                bulk_discount_rate=0.20
            ),
            'sticker': PricingRule(
                product_type='sticker',
                base_price=15000,
                min_quantity=50,
                max_quantity=10000,
                discount_per_unit=50,
                setup_fee=3000,
                bulk_discount_threshold=500,
                bulk_discount_rate=0.25
            ),
            'panneau': PricingRule(
                product_type='panneau',
                base_price=45000,
                min_quantity=1,
                max_quantity=50,
                discount_per_unit=500,
                setup_fee=8000,
                bulk_discount_threshold=5,
                bulk_discount_rate=0.15
            ),
            'usb': PricingRule(
                product_type='usb',
                base_price=8500,
                min_quantity=5,
                max_quantity=1000,
                discount_per_unit=200,
                setup_fee=2000,
                bulk_discount_threshold=50,
                bulk_discount_rate=0.30
            )
        }

        # Options de finition et leurs coûts
        self.finishing_options = {
            'lamination_mate': 5000,
            'lamination_brillante': 7000,
            'decoupe_personnalisee': 10000,
            'dorure_chand': 15000,
            'vernish_selectif': 12000,
            'embossage': 20000,
            'perforation': 3000,
            'pliage': 2000
        }

        # Suppléments par format
        self.format_multipliers = {
            'A6': 0.3,
            'A5': 0.5,
            'A4': 0.8,
            'A3': 1.0,
            'A2': 1.5,
            'A1': 2.0,
            'A0': 3.0,
            '2x1m': 2.5,
            '3x2m': 4.0,
            'personnalise': 1.2
        }

        # Suppléments de délai
        self.deadline_multipliers = {
            'standard': 1.0,      # 3-5 jours
            'express': 1.3,       # 24-48h
            'urgent': 1.8,        # même jour
            'weekend': 2.0        # weekend/férié
        }

    def calculate_price(self, specifications: Dict) -> Dict:
        """
        Calcule le prix total d'un produit selon ses spécifications

        Args:
            specifications: Dictionnaire avec les specs du produit

        Returns:
            Dictionnaire avec le calcul détaillé du prix
        """
        try:
            product_type = specifications.get('product_type', 'banderole')
            quantity = specifications.get('quantity', 1)
            format_size = specifications.get('format', 'A3')
            deadline = specifications.get('deadline', 'standard')
            finishing = specifications.get('finishing', [])

            # Récupérer la règle de tarification
            rule = self.rules.get(product_type)
            if not rule:
                return {'error': f'Type de produit non supporté: {product_type}'}

            # Validation de la quantité
            if quantity < rule.min_quantity or quantity > rule.max_quantity:
                return {'error': f'Quantité doit être entre {rule.min_quantity} et {rule.max_quantity}'}

            # Prix de base
            base_price = rule.base_price

            # Multiplicateur de format
            format_multiplier = self.format_multipliers.get(format_size, 1.0)
            base_price *= format_multiplier

            # Prix par quantité avec remise
            quantity_price = base_price * quantity

            # Remise par quantité
            if quantity > 10:
                discount_rate = min((quantity - 10) * 0.02, 0.30)  # Max 30% de remise
                quantity_price *= (1 - discount_rate)

            # Remise en gros
            if quantity >= rule.bulk_discount_threshold:
                quantity_price *= (1 - rule.bulk_discount_rate)

            # Supplément de délai
            deadline_multiplier = self.deadline_multipliers.get(deadline, 1.0)
            quantity_price *= deadline_multiplier

            # Coûts de finition
            finishing_cost = 0
            if isinstance(finishing, list):
                for finish in finishing:
                    finishing_cost += self.finishing_options.get(finish, 0)
            elif isinstance(finishing, str):
                finishing_cost = self.finishing_options.get(finishing, 0)

            # Frais de setup (une fois par commande)
            setup_cost = rule.setup_fee

            # Calcul du total
            subtotal = quantity_price + finishing_cost + setup_cost

            # TVA (19.25% au Cameroun)
            tva_rate = 0.1925
            tva_amount = subtotal * tva_rate

            # Total TTC
            total_ttc = subtotal + tva_amount

            return {
                'success': True,
                'breakdown': {
                    'base_price': round(base_price, 2),
                    'quantity': quantity,
                    'quantity_price': round(quantity_price, 2),
                    'format_multiplier': format_multiplier,
                    'deadline_multiplier': deadline_multiplier,
                    'finishing_cost': round(finishing_cost, 2),
                    'setup_cost': round(setup_cost, 2),
                    'subtotal_ht': round(subtotal, 2),
                    'tva_rate': tva_rate,
                    'tva_amount': round(tva_amount, 2),
                    'total_ttc': round(total_ttc, 2)
                },
                'summary': {
                    'product_type': product_type,
                    'quantity': quantity,
                    'format': format_size,
                    'deadline': deadline,
                    'finishing': finishing,
                    'unit_price': round(total_ttc / quantity, 2),
                    'total_price': round(total_ttc, 2)
                }
            }

        except Exception as e:
            return {'error': f'Erreur de calcul: {str(e)}'}

    def get_price_range(self, product_type: str, format_size: str = 'A3') -> Dict:
        """
        Retourne la fourchette de prix pour un type de produit

        Args:
            product_type: Type de produit
            format_size: Format du produit

        Returns:
            Dictionnaire avec prix minimum et maximum
        """
        rule = self.rules.get(product_type)
        if not rule:
            return {'error': f'Type de produit non supporté: {product_type}'}

        format_multiplier = self.format_multipliers.get(format_size, 1.0)

        # Prix minimum (quantité minimale)
        min_price = (rule.base_price * format_multiplier * rule.min_quantity) + rule.setup_fee
        min_price *= (1 + 0.1925)  # TVA

        # Prix maximum (quantité maximale avec remise)
        max_price = (rule.base_price * format_multiplier * rule.max_quantity) + rule.setup_fee
        max_price *= (1 - rule.bulk_discount_rate)  # Remise en gros
        max_price *= (1 + 0.1925)  # TVA

        return {
            'product_type': product_type,
            'format': format_size,
            'price_range': {
                'minimum': round(min_price, 2),
                'maximum': round(max_price, 2),
                'currency': 'FCFA'
            },
            'quantity_range': {
                'minimum': rule.min_quantity,
                'maximum': rule.max_quantity
            }
        }

    def calculate_bulk_discount(self, product_type: str, quantity: int) -> Dict:
        """
        Calcule la remise en fonction de la quantité

        Args:
            product_type: Type de produit
            quantity: Quantité commandée

        Returns:
            Dictionnaire avec le détail de la remise
        """
        rule = self.rules.get(product_type)
        if not rule:
            return {'error': f'Type de produit non supporté: {product_type}'}

        base_price = rule.base_price
        total_base = base_price * quantity

        # Remise progressive
        progressive_discount = 0
        if quantity > 10:
            progressive_discount = min((quantity - 10) * 0.02, 0.30)

        # Remise en gros
        bulk_discount = 0
        if quantity >= rule.bulk_discount_threshold:
            bulk_discount = rule.bulk_discount_rate

        total_discount = progressive_discount + bulk_discount
        discounted_price = total_base * (1 - total_discount)

        return {
            'quantity': quantity,
            'base_total': round(total_base, 2),
            'progressive_discount': f"{progressive_discount:.1%}",
            'bulk_discount': f"{bulk_discount:.1%}",
            'total_discount': f"{total_discount:.1%}",
            'discounted_total': round(discounted_price, 2),
            'savings': round(total_base - discounted_price, 2)
        }

    def get_finishing_options(self) -> Dict:
        """
        Retourne les options de finition disponibles avec leurs prix

        Returns:
            Dictionnaire avec toutes les options de finition
        """
        return {
            'lamination_mate': {
                'name': 'Lamination Mate',
                'price': self.finishing_options['lamination_mate'],
                'description': 'Protection mate anti-reflet'
            },
            'lamination_brillante': {
                'name': 'Lamination Brillante',
                'price': self.finishing_options['lamination_brillante'],
                'description': 'Protection brillante premium'
            },
            'decoupe_personnalisee': {
                'name': 'Découpe Personnalisée',
                'price': self.finishing_options['decoupe_personnalisee'],
                'description': 'Découpe selon forme spécifique'
            },
            'dorure_chand': {
                'name': 'Dorure à Chaud',
                'price': self.finishing_options['dorure_chand'],
                'description': 'Effet doré métallique'
            },
            'vernish_selectif': {
                'name': 'Vernis Sélectif',
                'price': self.finishing_options['vernish_selectif'],
                'description': 'Vernis sur zones spécifiques'
            },
            'embossage': {
                'name': 'Embossage',
                'price': self.finishing_options['embossage'],
                'description': 'Relief en creux ou en bosse'
            },
            'perforation': {
                'name': 'Perforation',
                'price': self.finishing_options['perforation'],
                'description': 'Ligne de perforation'
            },
            'pliage': {
                'name': 'Pliage',
                'price': self.finishing_options['pliage'],
                'description': 'Pliage selon spécifications'
            }
        }

    def estimate_delivery_time(self, product_type: str, quantity: int, deadline: str) -> Dict:
        """
        Estime le délai de livraison

        Args:
            product_type: Type de produit
            quantity: Quantité
            deadline: Niveau d'urgence

        Returns:
            Dictionnaire avec l'estimation du délai
        """
        base_times = {
            'banderole': 3,
            'sticker': 2,
            'panneau': 5,
            'usb': 7
        }

        base_time = base_times.get(product_type, 3)

        # Ajustement selon la quantité
        if quantity > 50:
            base_time += 2
        elif quantity > 20:
            base_time += 1

        # Ajustement selon l'urgence
        urgency_times = {
            'standard': base_time,
            'express': max(base_time - 1, 1),
            'urgent': 0,
            'weekend': base_time + 1
        }

        estimated_days = urgency_times.get(deadline, base_time)

        return {
            'product_type': product_type,
            'quantity': quantity,
            'deadline': deadline,
            'estimated_days': estimated_days,
            'estimated_date': (datetime.now() + timedelta(days=estimated_days)).strftime('%Y-%m-%d'),
            'is_weekend': datetime.now().weekday() >= 5
        }

# Instance globale du moteur de tarification
pricing_engine = PricingEngine()

def calculate_product_price(product_type: str, specifications: Dict) -> Dict:
    """
    Fonction utilitaire pour calculer le prix d'un produit

    Args:
        product_type: Type de produit
        specifications: Spécifications du produit

    Returns:
        Dictionnaire avec le calcul du prix
    """
    specifications['product_type'] = product_type
    return pricing_engine.calculate_price(specifications)

def get_available_formats() -> List[str]:
    """Retourne les formats disponibles"""
    return list(pricing_engine.format_multipliers.keys())

def get_available_deadlines() -> List[str]:
    """Retourne les délais disponibles"""
    return list(pricing_engine.deadline_multipliers.keys())

def get_product_rules() -> Dict:
    """Retourne les règles de tarification"""
    return {
        name: {
            'base_price': rule.base_price,
            'min_quantity': rule.min_quantity,
            'max_quantity': rule.max_quantity,
            'setup_fee': rule.setup_fee,
            'bulk_discount_threshold': rule.bulk_discount_threshold,
            'bulk_discount_rate': rule.bulk_discount_rate
        }
        for name, rule in pricing_engine.rules.items()
    }

if __name__ == "__main__":
    # Test du moteur de tarification
    test_specs = {
        'product_type': 'banderole',
        'quantity': 5,
        'format': '2x1m',
        'deadline': 'express',
        'finishing': ['lamination_brillante', 'decoupe_personnalisee']
    }

    result = pricing_engine.calculate_price(test_specs)
    print("Test de calcul de prix:")
    print(json.dumps(result, indent=2, ensure_ascii=False))