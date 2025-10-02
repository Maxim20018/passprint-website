#!/usr/bin/env python3
"""
Webhooks Stripe pour PassPrint
Gère les événements de paiement en temps réel
"""
import stripe
import json
import os
from datetime import datetime
from flask import request, jsonify

class StripeWebhookHandler:
    """Gestionnaire des webhooks Stripe"""

    def __init__(self):
        self.stripe_secret = os.getenv('STRIPE_SECRET_KEY', 'sk_test_dev_key')
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', 'whsec_dev_key')
        stripe.api_key = self.stripe_secret

    def handle_webhook(self, payload: str, signature: str) -> Dict:
        """
        Traiter un webhook Stripe

        Args:
            payload: Données du webhook
            signature: Signature du webhook

        Returns:
            Résultat du traitement
        """
        try:
            # Vérifier la signature
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )

            # Traiter l'événement
            event_type = event['type']

            if event_type == 'payment_intent.succeeded':
                return self._handle_payment_succeeded(event['data']['object'])
            elif event_type == 'payment_intent.payment_failed':
                return self._handle_payment_failed(event['data']['object'])
            elif event_type == 'checkout.session.completed':
                return self._handle_checkout_completed(event['data']['object'])
            else:
                return {'status': 'ignored', 'event_type': event_type}

        except Exception as e:
            return {'error': f'Erreur webhook: {str(e)}'}

    def _handle_payment_succeeded(self, payment_intent) -> Dict:
        """Traiter un paiement réussi"""
        try:
            # Mettre à jour le statut de la commande
            order_id = payment_intent.get('metadata', {}).get('order_id')

            if order_id:
                # Mettre à jour la base de données
                self._update_order_status(order_id, 'paid', payment_intent['id'])

                # Envoyer email de confirmation
                self._send_payment_confirmation_email(order_id)

            return {
                'status': 'success',
                'event': 'payment_succeeded',
                'payment_intent_id': payment_intent['id'],
                'amount': payment_intent['amount']
            }

        except Exception as e:
            return {'error': f'Erreur traitement paiement: {str(e)}'}

    def _handle_payment_failed(self, payment_intent) -> Dict:
        """Traiter un paiement échoué"""
        try:
            order_id = payment_intent.get('metadata', {}).get('order_id')

            if order_id:
                self._update_order_status(order_id, 'payment_failed', payment_intent['id'])

            return {
                'status': 'success',
                'event': 'payment_failed',
                'payment_intent_id': payment_intent['id']
            }

        except Exception as e:
            return {'error': f'Erreur traitement échec paiement: {str(e)}'}

    def _handle_checkout_completed(self, session) -> Dict:
        """Traiter une session de checkout terminée"""
        try:
            return {
                'status': 'success',
                'event': 'checkout_completed',
                'session_id': session['id']
            }

        except Exception as e:
            return {'error': f'Erreur checkout: {str(e)}'}

    def _update_order_status(self, order_id: str, status: str, payment_id: str):
        """Mettre à jour le statut d'une commande"""
        try:
            # Connexion à la base de données
            import sqlite3
            with sqlite3.connect('passprint.db') as conn:
                conn.execute('''
                    UPDATE orders
                    SET payment_status = ?, stripe_payment_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (status, payment_id, order_id))

                conn.commit()

        except Exception as e:
            print(f"Erreur mise à jour commande: {e}")

    def _send_payment_confirmation_email(self, order_id: str):
        """Envoyer email de confirmation de paiement"""
        try:
            # Récupérer les infos de la commande
            import sqlite3
            with sqlite3.connect('passprint.db') as conn:
                cursor = conn.execute('''
                    SELECT o.*, u.email as customer_email
                    FROM orders o
                    LEFT JOIN users u ON o.customer_id = u.id
                    WHERE o.id = ?
                ''', (order_id,))

                order = cursor.fetchone()

                if order and order['customer_email']:
                    # Envoyer email de confirmation
                    from email_system import send_payment_confirmation
                    send_payment_confirmation(order['customer_email'], {
                        'order_number': f"PP{order_id}",
                        'amount': order['total_amount'],
                        'payment_id': order['stripe_payment_id']
                    })

        except Exception as e:
            print(f"Erreur envoi email confirmation: {e}")

# Instance globale du gestionnaire de webhooks
webhook_handler = StripeWebhookHandler()

def handle_stripe_webhook(payload: str, signature: str) -> Dict:
    """
    Traiter un webhook Stripe

    Args:
        payload: Données du webhook
        signature: Signature du webhook

    Returns:
        Résultat du traitement
    """
    return webhook_handler.handle_webhook(payload, signature)

if __name__ == "__main__":
    print("Système de webhooks Stripe opérationnel!")