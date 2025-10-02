#!/usr/bin/env python3
"""
Interface de chat en ligne pour PassPrint
Gère les conversations en temps réel avec les clients
"""
import json
from datetime import datetime
from chat_system import chat_system

class ChatInterface:
    """Interface de chat pour l'administration"""

    def __init__(self):
        self.chat_system = chat_system

    def get_admin_interface_data(self, admin_id: str) -> Dict:
        """Données pour l'interface admin du chat"""
        try:
            sessions = self.chat_system.get_admin_sessions(admin_id)
            waiting_sessions = self.chat_system.get_waiting_sessions()

            return {
                'active_sessions': [
                    {
                        'session_id': session.session_id,
                        'customer_name': session.customer_name,
                        'customer_email': session.customer_email,
                        'status': session.status,
                        'last_activity': session.last_activity.isoformat(),
                        'message_count': len(session.messages)
                    }
                    for session in sessions
                ],
                'waiting_sessions': [
                    {
                        'session_id': session.session_id,
                        'customer_name': session.customer_name,
                        'customer_email': session.customer_email,
                        'created_at': session.created_at.isoformat()
                    }
                    for session in waiting_sessions
                ],
                'stats': self.chat_system.get_chat_stats()
            }

        except Exception as e:
            return {'error': str(e)}

    def send_admin_message(self, session_id: str, admin_id: str, admin_name: str, message: str) -> Dict:
        """Envoyer un message en tant qu'admin"""
        return self.chat_system.send_message(session_id, admin_id, admin_name, message, 'admin')

    def assign_session_to_admin(self, session_id: str, admin_id: str, admin_name: str) -> Dict:
        """Assigner une session à un admin"""
        return self.chat_system.assign_admin(session_id, admin_id, admin_name)

    def close_chat_session(self, session_id: str) -> Dict:
        """Fermer une session de chat"""
        return self.chat_system.close_session(session_id)

# Instance globale de l'interface de chat
chat_interface = ChatInterface()

def get_chat_interface_data(admin_id: str) -> Dict:
    """Obtenir les données de l'interface de chat"""
    return chat_interface.get_admin_interface_data(admin_id)

def send_chat_message(session_id: str, sender_id: str, sender_name: str, message: str, sender_type: str = 'user') -> Dict:
    """Envoyer un message de chat"""
    return chat_interface.chat_system.send_message(session_id, sender_id, sender_name, message, sender_type)

if __name__ == "__main__":
    print("Interface de chat opérationnelle!")