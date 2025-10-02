#!/usr/bin/env python3
"""
Calculateur de taxes pour PassPrint
Gère les taxes et frais selon la localisation
"""
import json

class TaxCalculator:
    """Calculateur de taxes"""

    def __init__(self):
        self.tax_rates = {
            'cameroun': {
                'tva': 0.1925,  # 19.25%
                'autres_taxes': 0.00
            },
            'senegal': {
                'tva': 0.18,    # 18%
                'autres_taxes': 0.01
            }
        }

    def calculate_taxes(self, amount: float, country: str = 'cameroun'):
        """Calculer les taxes"""
        if country not in self.tax_rates:
            country = 'cameroun'

        rates = self.tax_rates[country]
        tva_amount = amount * rates['tva']
        other_taxes = amount * rates['autres_taxes']
        total_taxes = tva_amount + other_taxes
        total_with_taxes = amount + total_taxes

        return {
            'base_amount': amount,
            'tva_rate': rates['tva'],
            'tva_amount': round(tva_amount, 2),
            'other_taxes': round(other_taxes, 2),
            'total_taxes': round(total_taxes, 2),
            'total_with_taxes': round(total_with_taxes, 2)
        }

# Instance globale du calculateur de taxes
tax_calculator = TaxCalculator()

def calculate_order_taxes(amount: float, country: str = 'cameroun'):
    """Calculer les taxes d'une commande"""
    return tax_calculator.calculate_taxes(amount, country)

if __name__ == "__main__":
    print("Calculateur de taxes opérationnel!")