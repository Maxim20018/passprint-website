#!/usr/bin/env python3
"""
Système de chat en ligne pour PassPrint
Permet la communication en temps réel avec les clients
"""
import json
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
import threading
import time

@dataclass
class ChatMessage:
    """Message de chat"""
    id: str
    sender_id: str
    sender_name: str
    sender_type: str  # 'user', 'admin', 'system'
    message: str
    timestamp: datetime
    is_read: bool = False
    message_type: str = 'text'  # 'text', 'image', 'file', 'system'

@dataclass
class ChatSession:
    """Session de chat"""
    session_id: str
    customer_id: str
    customer_name: str
    customer_email: str
    status: str  # 'active', 'waiting', 'closed'
    created_at: datetime
    last_activity: datetime
    assigned_admin: str = None
    messages: List[ChatMessage] = None

    def __post_init__(self):
        if self.messages is None:
            self.messages = []

class ChatSystem:
    """Système de chat en temps réel"""

    def __init__(self):
        self.sessions = {}  # session_id -> ChatSession
        self.waiting_sessions = []  # sessions en attente
        self.active_sessions = {}  # admin_id -> session_id
        self.admins_online = set()

        # Démarrer le thread de nettoyage
        self.cleanup_thread = threading.Thread(target=self._cleanup_sessions, daemon=True)
        self.cleanup_thread.start()

    def create_session(self, customer_id: str, customer_name: str, customer_email: str) -> str:
        """
        Créer une nouvelle session de chat

        Args:
            customer_id: ID du client
            customer_name: Nom du client
            customer_email: Email du client

        Returns:
            ID de la session créée
        """
        session_id = str(uuid.uuid4())

        session = ChatSession(
            session_id=session_id,
            customer_id=customer_id,
            customer_name=customer_name,
            customer_email=customer_email,
            status='waiting',
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )

        # Message de bienvenue automatique
        welcome_message = ChatMessage(
            id=str(uuid.uuid4()),
            sender_id='system',
            sender_name='PassPrint',
            sender_type='system',
            message=f"Bonjour {customer_name}! 👋\n\nUn conseiller va vous répondre dans quelques instants. En attendant, vous pouvez nous décrire votre projet d'impression.",
            timestamp=datetime.utcnow(),
            message_type='system'
        )

        session.messages.append(welcome_message)
        self.sessions[session_id] = session
        self.waiting_sessions.append(session_id)

        return session_id

    def send_message(self, session_id: str, sender_id: str, sender_name: str, message: str, sender_type: str = 'user') -> Dict:
        """
        Envoyer un message dans une session

        Args:
            session_id: ID de la session
            sender_id: ID de l'expéditeur
            sender_name: Nom de l'expéditeur
            message: Contenu du message
            sender_type: Type d'expéditeur

        Returns:
            Résultat de l'envoi
        """
        try:
            if session_id not in self.sessions:
                return {'error': 'Session non trouvée'}

            session = self.sessions[session_id]

            # Vérifier si la session est active
            if session.status == 'closed':
                return {'error': 'Session fermée'}

            # Créer le message
            chat_message = ChatMessage(
                id=str(uuid.uuid4()),
                sender_id=sender_id,
                sender_name=sender_name,
                sender_type=sender_type,
                message=message,
                timestamp=datetime.utcnow()
            )

            session.messages.append(chat_message)
            session.last_activity = datetime.utcnow()

            # Si c'est un message client et qu'aucun admin n'est assigné
            if sender_type == 'user' and not session.assigned_admin:
                session.status = 'waiting'

            return {
                'success': True,
                'message': chat_message
            }

        except Exception as e:
            return {'error': f'Erreur envoi message: {str(e)}'}

    def assign_admin(self, session_id: str, admin_id: str, admin_name: str) -> Dict:
        """
        Assigner un admin à une session

        Args:
            session_id: ID de la session
            admin_id: ID de l'admin
            admin_name: Nom de l'admin

        Returns:
            Résultat de l'assignation
        """
        try:
            if session_id not in self.sessions:
                return {'error': 'Session non trouvée'}

            session = self.sessions[session_id]

            # Retirer de la liste d'attente
            if session_id in self.waiting_sessions:
                self.waiting_sessions.remove(session_id)

            # Assigner l'admin
            session.assigned_admin = admin_id
            session.status = 'active'

            # Ajouter aux sessions actives de l'admin
            self.active_sessions[admin_id] = session_id

            # Message de confirmation
            assign_message = ChatMessage(
                id=str(uuid.uuid4()),
                sender_id=admin_id,
                sender_name=admin_name,
                sender_type='admin',
                message=f"Bonjour! Je suis {admin_name}, votre conseiller PassPrint. Comment puis-je vous aider avec votre projet d'impression?",
                timestamp=datetime.utcnow()
            )

            session.messages.append(assign_message)

            return {
                'success': True,
                'message': 'Admin assigné avec succès',
                'session': session
            }

        except Exception as e:
            return {'error': f'Erreur assignation admin: {str(e)}'}

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """
        Récupérer une session de chat

        Args:
            session_id: ID de la session

        Returns:
            Session de chat ou None
        """
        return self.sessions.get(session_id)

    def get_waiting_sessions(self) -> List[ChatSession]:
        """
        Récupérer les sessions en attente

        Returns:
            Liste des sessions en attente
        """
        return [self.sessions[sid] for sid in self.waiting_sessions]

    def get_admin_sessions(self, admin_id: str) -> List[ChatSession]:
        """
        Récupérer les sessions d'un admin

        Args:
            admin_id: ID de l'admin

        Returns:
            Liste des sessions de l'admin
        """
        admin_session_ids = [sid for aid, sid in self.active_sessions.items() if aid == admin_id]
        return [self.sessions[sid] for sid in admin_session_ids if sid in self.sessions]

    def close_session(self, session_id: str) -> Dict:
        """
        Fermer une session de chat

        Args:
            session_id: ID de la session

        Returns:
            Résultat de la fermeture
        """
        try:
            if session_id not in self.sessions:
                return {'error': 'Session non trouvée'}

            session = self.sessions[session_id]
            session.status = 'closed'

            # Retirer des sessions actives
            for admin_id, sid in list(self.active_sessions.items()):
                if sid == session_id:
                    del self.active_sessions[admin_id]
                    break

            # Message de fermeture
            close_message = ChatMessage(
                id=str(uuid.uuid4()),
                sender_id='system',
                sender_name='PassPrint',
                sender_type='system',
                message="Cette conversation a été fermée. Merci d'avoir utilisé notre service de chat!",
                timestamp=datetime.utcnow(),
                message_type='system'
            )

            session.messages.append(close_message)

            return {
                'success': True,
                'message': 'Session fermée avec succès'
            }

        except Exception as e:
            return {'error': f'Erreur fermeture session: {str(e)}'}

    def get_session_messages(self, session_id: str, limit: int = 50) -> Dict:
        """
        Récupérer les messages d'une session

        Args:
            session_id: ID de la session
            limit: Nombre maximum de messages

        Returns:
            Messages de la session
        """
        try:
            session = self.get_session(session_id)
            if not session:
                return {'error': 'Session non trouvée'}

            messages = session.messages[-limit:]  # Derniers messages

            return {
                'session_id': session_id,
                'messages': [
                    {
                        'id': msg.id,
                        'sender_id': msg.sender_id,
                        'sender_name': msg.sender_name,
                        'sender_type': msg.sender_type,
                        'message': msg.message,
                        'timestamp': msg.timestamp.isoformat(),
                        'is_read': msg.is_read,
                        'message_type': msg.message_type
                    }
                    for msg in messages
                ],
                'total_messages': len(session.messages),
                'status': session.status
            }

        except Exception as e:
            return {'error': f'Erreur récupération messages: {str(e)}'}

    def mark_messages_read(self, session_id: str, user_id: str) -> Dict:
        """
        Marquer les messages comme lus

        Args:
            session_id: ID de la session
            user_id: ID de l'utilisateur

        Returns:
            Résultat du marquage
        """
        try:
            session = self.get_session(session_id)
            if not session:
                return {'error': 'Session non trouvée'}

            # Marquer les messages non lus comme lus
            for message in session.messages:
                if message.sender_id != user_id and not message.is_read:
                    message.is_read = True

            return {
                'success': True,
                'message': 'Messages marqués comme lus'
            }

        except Exception as e:
            return {'error': f'Erreur marquage messages: {str(e)}'}

    def get_chat_stats(self) -> Dict:
        """
        Obtenir les statistiques du chat

        Returns:
            Statistiques du système de chat
        """
        try:
            total_sessions = len(self.sessions)
            active_sessions = len([s for s in self.sessions.values() if s.status == 'active'])
            waiting_sessions = len(self.waiting_sessions)
            closed_sessions = len([s for s in self.sessions.values() if s.status == 'closed'])

            total_messages = sum(len(session.messages) for session in self.sessions.values())

            return {
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'waiting_sessions': waiting_sessions,
                'closed_sessions': closed_sessions,
                'total_messages': total_messages,
                'admins_online': len(self.admins_online),
                'average_session_duration': 'N/A'  # Calcul à implémenter
            }

        except Exception as e:
            return {'error': f'Erreur statistiques chat: {str(e)}'}

    def _cleanup_sessions(self):
        """
        Nettoyer les sessions inactives (thread en arrière-plan)
        """
        while True:
            try:
                current_time = datetime.utcnow()
                inactive_threshold = timedelta(hours=2)  # 2 heures d'inactivité

                sessions_to_remove = []

                for session_id, session in self.sessions.items():
                    if session.status == 'active' and (current_time - session.last_activity) > inactive_threshold:
                        session.status = 'closed'
                        sessions_to_remove.append(session_id)

                        # Message de fermeture automatique
                        auto_close_message = ChatMessage(
                            id=str(uuid.uuid4()),
                            sender_id='system',
                            sender_name='PassPrint',
                            sender_type='system',
                            message="Conversation fermée automatiquement due à l'inactivité.",
                            timestamp=current_time,
                            message_type='system'
                        )
                        session.messages.append(auto_close_message)

                # Nettoyer les sessions fermées depuis plus de 24h
                cleanup_threshold = timedelta(hours=24)
                for session_id in sessions_to_remove:
                    session = self.sessions[session_id]
                    if (current_time - session.last_activity) > cleanup_threshold:
                        del self.sessions[session_id]

                time.sleep(300)  # Vérifier toutes les 5 minutes

            except Exception as e:
                print(f"Erreur nettoyage sessions: {e}")
                time.sleep(300)

# Instance globale du système de chat
chat_system = ChatSystem()

def create_chat_session(customer_id: str, customer_name: str, customer_email: str) -> str:
    """
    Créer une nouvelle session de chat

    Args:
        customer_id: ID du client
        customer_name: Nom du client
        customer_email: Email du client

    Returns:
        ID de la session créée
    """
    return chat_system.create_session(customer_id, customer_name, customer_email)

def send_chat_message(session_id: str, sender_id: str, sender_name: str, message: str, sender_type: str = 'user') -> Dict:
    """
    Envoyer un message de chat

    Args:
        session_id: ID de la session
        sender_id: ID de l'expéditeur
        sender_name: Nom de l'expéditeur
        message: Contenu du message
        sender_type: Type d'expéditeur

    Returns:
        Résultat de l'envoi
    """
    return chat_system.send_message(session_id, sender_id, sender_name, message, sender_type)

def get_chat_session(session_id: str):
    """
    Récupérer une session de chat

    Args:
        session_id: ID de la session

    Returns:
        Session de chat
    """
    return chat_system.get_session(session_id)

def get_waiting_sessions():
    """
    Récupérer les sessions en attente

    Returns:
        Liste des sessions en attente
    """
    return chat_system.get_waiting_sessions()

if __name__ == "__main__":
    # Test du système de chat
    session_id = chat_system.create_session("user123", "Test User", "test@example.com")
    print(f"Session créée: {session_id}")

    result = chat_system.send_message(session_id, "user123", "Test User", "Bonjour, j'ai besoin d'aide!")
    print(f"Message envoyé: {result['success']}")