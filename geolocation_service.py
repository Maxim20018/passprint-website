#!/usr/bin/env python3
"""
Service de géolocalisation pour PassPrint
Gère la localisation et les calculs de distance
"""
import json

class GeolocationService:
    """Service de géolocalisation"""

    def __init__(self):
        self.company_location = {
            'lat': 4.0511,
            'lng': 9.7679,
            'address': 'Douala, Cameroun'
        }

    def calculate_distance(self, lat1: float, lng1: float, lat2: float = None, lng2: float = None):
        """Calculer la distance entre deux points"""
        if lat2 is None or lng2 is None:
            lat2, lng2 = self.company_location['lat'], self.company_location['lng']

        # Calcul simple de distance (formule de Haversine simplifiée)
        distance = ((lat1 - lat2) ** 2 + (lng1 - lng2) ** 2) ** 0.5 * 111  # km approximatif
        return round(distance, 2)

    def get_delivery_zones(self):
        """Obtenir les zones de livraison"""
        return {
            'zone_1': {'name': 'Centre-ville', 'max_distance': 5, 'delivery_fee': 1000},
            'zone_2': {'name': 'Périphérie', 'max_distance': 15, 'delivery_fee': 2500},
            'zone_3': {'name': 'Extérieur', 'max_distance': 50, 'delivery_fee': 5000}
        }

# Instance globale du service de géolocalisation
geolocation_service = GeolocationService()

def calculate_delivery_fee(lat: float, lng: float):
    """Calculer les frais de livraison"""
    distance = geolocation_service.calculate_distance(lat, lng)
    zones = geolocation_service.get_delivery_zones()

    for zone_id, zone in zones.items():
        if distance <= zone['max_distance']:
            return {
                'distance': distance,
                'zone': zone['name'],
                'delivery_fee': zone['delivery_fee']
            }

    return {
        'distance': distance,
        'zone': 'Hors zone',
        'delivery_fee': 10000
    }

if __name__ == "__main__":
    print("Service de géolocalisation opérationnel!")