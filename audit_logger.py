#!/usr/bin/env python3
"""
Système d'audit logs pour PassPrint
Enregistre toutes les actions importantes
"""
import sqlite3
import json
from datetime import datetime
import os

class AuditLogger:
    """Système d'audit logs"""

    def __init__(self):
        self.db_path = 'passprint.db'

    def log_action(self, user_id: str, action: str, details: dict, ip_address: str = None):
        """Enregistrer une action"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO audit_logs (user_id, action, details, ip_address, created_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, action, json.dumps(details, default=str), ip_address))

                conn.commit()

        except Exception as e:
            print(f"Erreur audit log: {e}")

    def get_logs(self, limit: int = 100, user_id: str = None, action: str = None):
        """Récupérer les logs d'audit"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = 'SELECT * FROM audit_logs WHERE 1=1'
                params = []

                if user_id:
                    query += ' AND user_id = ?'
                    params.append(user_id)

                if action:
                    query += ' AND action = ?'
                    params.append(action)

                query += ' ORDER BY created_at DESC LIMIT ?'
                params.append(limit)

                cursor = conn.execute(query, params)
                return [
                    {
                        'id': row[0],
                        'user_id': row[1],
                        'action': row[2],
                        'details': json.loads(row[3]) if row[3] else {},
                        'ip_address': row[4],
                        'created_at': row[5]
                    }
                    for row in cursor.fetchall()
                ]

        except Exception as e:
            return []

# Instance globale de l'audit logger
audit_logger = AuditLogger()

def log_user_action(user_id: str, action: str, details: dict, ip_address: str = None):
    """Enregistrer une action utilisateur"""
    audit_logger.log_action(user_id, action, details, ip_address)

def get_audit_logs(limit: int = 100, user_id: str = None, action: str = None):
    """Récupérer les logs d'audit"""
    return audit_logger.get_logs(limit, user_id, action)

if __name__ == "__main__":
    print("Système d'audit logs opérationnel!")