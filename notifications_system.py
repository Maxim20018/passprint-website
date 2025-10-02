#!/usr/bin/env python3
"""
Système de notifications temps réel pour PassPrint
Gère les notifications push et temps réel
"""
import json
from datetime import datetime
import asyncio

class NotificationSystem:
    """Système de notifications temps réel"""

    def __init__(self):
        self.subscribers = {}

    def subscribe(self, user_id: str, callback):
        """S'abonner aux notifications"""
        if user_id not in self.subscribers:
            self.subscribers[user_id] = []
        self.subscribers[user_id].append(callback)

    def unsubscribe(self, user_id: str, callback):
        """Se désabonner des notifications"""
        if user_id in self.subscribers:
            self.subscribers[user_id].remove(callback)

    def notify_user(self, user_id: str, notification: dict):
        """Envoyer une notification à un utilisateur"""
        if user_id in self.subscribers:
            for callback in self.subscribers[user_id]:
                try:
                    callback(notification)
                except Exception as e:
                    print(f"Erreur notification: {e}")

    def notify_all(self, notification: dict):
        """Notifier tous les utilisateurs"""
        for user_id in self.subscribers:
            self.notify_user(user_id, notification)

# Instance globale du système de notifications
notification_system = NotificationSystem()

def subscribe_to_notifications(user_id: str, callback):
    """S'abonner aux notifications"""
    notification_system.subscribe(user_id, callback)

def send_notification(user_id: str, title: str, message: str, type: str = 'info'):
    """Envoyer une notification"""
    notification = {
        'id': f"notif_{datetime.now().timestamp()}",
        'title': title,
        'message': message,
        'type': type,
        'timestamp': datetime.utcnow().isoformat(),
        'read': False
    }

    notification_system.notify_user(user_id, notification)

    return notification

if __name__ == "__main__":
    print("Système de notifications opérationnel!")