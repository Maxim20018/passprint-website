#!/usr/bin/env python3
"""
Tâches Celery pour PassPrint
Gestion des tâches en arrière-plan (emails, fichiers, notifications)
"""
import os
import logging
from datetime import datetime, timedelta
from celery import Celery
from celery.schedules import crontab
import redis
import json
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import requests
from pathlib import Path

# Configuration Celery
celery_app = Celery(
    'passprint_tasks',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)

# Configuration Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Configuration des retries
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_retry_delay=30,
    task_max_retries=3,

    # Configuration des workers
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,

    # Configuration des résultats
    result_expires=3600,  # 1 heure
    result_backend_transport_options={
        'master_name': 'mymaster'
    }
)

# Configuration des tâches périodiques
celery_app.conf.beat_schedule = {
    'send-daily-reports': {
        'task': 'celery_tasks.send_daily_reports',
        'schedule': crontab(hour=9, minute=0),  # Tous les jours à 9h
    },
    'cleanup-old-files': {
        'task': 'celery_tasks.cleanup_old_files',
        'schedule': crontab(hour=2, minute=0),  # Tous les jours à 2h
    },
    'backup-database': {
        'task': 'celery_tasks.create_database_backup',
        'schedule': crontab(hour=3, minute=0),  # Tous les jours à 3h
    },
    'send-pending-emails': {
        'task': 'celery_tasks.send_pending_emails',
        'schedule': 300.0,  # Toutes les 5 minutes
    },
    'update-analytics': {
        'task': 'celery_tasks.update_analytics',
        'schedule': crontab(hour=1, minute=0),  # Tous les jours à 1h
    },
}

celery_app.conf.beat_scheduler = 'redbeat.RedBeatScheduler'
celery_app.conf.redbeat_redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

logger = logging.getLogger(__name__)

# Tâches Email
@celery_app.task(bind=True, max_retries=3)
def send_email_async(self, to_email: str, subject: str, html_content: str, text_content: str = None):
    """Envoyer un email de manière asynchrone"""
    try:
        from flask_mail import Mail, Message
        from app import create_app

        app = create_app()

        with app.app_context():
            mail = Mail(app)

            msg = Message(
                subject=subject,
                recipients=[to_email],
                html=html_content,
                body=text_content
            )

            mail.send(msg)

        logger.info(f"Email envoyé à {to_email}: {subject}")
        return {'status': 'sent', 'email': to_email}

    except Exception as e:
        logger.error(f"Erreur envoi email à {to_email}: {e}")
        raise self.retry(exc=e, countdown=60)

@celery_app.task(bind=True, max_retries=3)
def send_bulk_emails(self, recipients: list, subject: str, html_content: str, text_content: str = None):
    """Envoyer des emails en masse"""
    try:
        from flask_mail import Mail, Message
        from app import create_app

        app = create_app()
        results = []

        with app.app_context():
            mail = Mail(app)

            for recipient in recipients:
                try:
                    msg = Message(
                        subject=subject,
                        recipients=[recipient],
                        html=html_content,
                        body=text_content
                    )

                    mail.send(msg)
                    results.append({'email': recipient, 'status': 'sent'})

                except Exception as e:
                    logger.error(f"Erreur envoi email à {recipient}: {e}")
                    results.append({'email': recipient, 'status': 'failed', 'error': str(e)})

        logger.info(f"Emails envoyés: {len([r for r in results if r['status'] == 'sent'])}/{len(recipients)}")
        return results

    except Exception as e:
        logger.error(f"Erreur envoi emails en masse: {e}")
        raise self.retry(exc=e, countdown=60)

@celery_app.task(bind=True, max_retries=3)
def send_order_confirmation_email(self, order_id: int, customer_email: str):
    """Envoyer email de confirmation de commande"""
    try:
        from app import create_app
        from models import Order

        app = create_app()

        with app.app_context():
            order = Order.query.get(order_id)
            if not order:
                raise ValueError(f"Commande {order_id} non trouvée")

            # Générer le contenu de l'email
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #2D1B69 0%, #FF6B35 100%); color: white; padding: 2rem; text-align: center;">
                    <h1 style="margin: 0;">PassPrint</h1>
                    <p style="margin: 0.5rem 0 0 0;">Confirmation de commande</p>
                </div>

                <div style="padding: 2rem; background: #f8f9fa;">
                    <h2 style="color: #2D1B69;">Bonjour!</h2>
                    <p>Merci pour votre commande. Voici les détails de votre commande #{order.order_number}:</p>

                    <div style="background: white; padding: 1.5rem; border-radius: 8px; margin: 1rem 0;">
                        <h3>Détails de la commande</h3>
                        <p><strong>Montant total:</strong> {order.total_amount:.0f} FCFA</p>
                        <p><strong>Date:</strong> {order.created_at.strftime('%d/%m/%Y %H:%M')}</p>
                        <p><strong>Statut:</strong> {get_status_label(order.status)}</p>
                    </div>

                    <div style="text-align: center; margin: 2rem 0;">
                        <a href="{os.getenv('APP_URL', 'http://localhost:5000')}/pages/contact.html"
                           style="background: #FF6B35; color: white; padding: 1rem 2rem; text-decoration: none; border-radius: 8px;">
                            Nous contacter
                        </a>
                    </div>
                </div>

                <div style="background: #2D1B69; color: white; padding: 1rem; text-align: center;">
                    <p style="margin: 0;">&copy; 2025 PassPrint. Tous droits réservés.</p>
                </div>
            </div>
            """

            # Envoyer l'email
            send_email_async.delay(customer_email, f"Confirmation de commande #{order.order_number}", html_content)

        return {'status': 'sent', 'order_id': order_id}

    except Exception as e:
        logger.error(f"Erreur email confirmation commande {order_id}: {e}")
        raise self.retry(exc=e, countdown=60)

@celery_app.task(bind=True, max_retries=3)
def send_newsletter_email(self, subscriber_id: int, newsletter_content: dict):
    """Envoyer une newsletter"""
    try:
        from app import create_app
        from models import NewsletterSubscriber

        app = create_app()

        with app.app_context():
            subscriber = NewsletterSubscriber.query.get(subscriber_id)
            if not subscriber or not subscriber.is_active:
                return {'status': 'cancelled', 'reason': 'subscriber_not_found_or_inactive'}

            # Générer le contenu personnalisé
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #2D1B69 0%, #FF6B35 100%); color: white; padding: 2rem; text-align: center;">
                    <h1 style="margin: 0;">PassPrint</h1>
                    <p style="margin: 0.5rem 0 0 0;">Newsletter</p>
                </div>

                <div style="padding: 2rem; background: #f8f9fa;">
                    <h2 style="color: #2D1B69;">Bonjour {subscriber.first_name or 'cher client'}!</h2>

                    <div style="background: white; padding: 1.5rem; border-radius: 8px; margin: 1rem 0;">
                        {newsletter_content.get('content', '')}
                    </div>

                    <div style="text-align: center; margin: 2rem 0;">
                        <a href="{newsletter_content.get('cta_url', os.getenv('APP_URL', 'http://localhost:5000'))}"
                           style="background: #FF6B35; color: white; padding: 1rem 2rem; text-decoration: none; border-radius: 8px;">
                            {newsletter_content.get('cta_text', 'Visitez notre site')}
                        </a>
                    </div>
                </div>
            </div>
            """

            # Envoyer l'email
            send_email_async.delay(
                subscriber.email,
                newsletter_content.get('subject', 'Newsletter PassPrint'),
                html_content
            )

        return {'status': 'sent', 'subscriber_id': subscriber_id}

    except Exception as e:
        logger.error(f"Erreur newsletter {subscriber_id}: {e}")
        raise self.retry(exc=e, countdown=60)

# Tâches de traitement de fichiers
@celery_app.task(bind=True, max_retries=3)
def process_uploaded_file(self, file_id: int, processing_options: dict = None):
    """Traiter un fichier uploadé (conversion, optimisation, etc.)"""
    try:
        from app import create_app
        from models import File
        from PIL import Image
        import subprocess

        app = create_app()

        with app.app_context():
            file_record = File.query.get(file_id)
            if not file_record:
                raise ValueError(f"Fichier {file_id} non trouvé")

            file_path = Path(file_record.file_path)

            if not file_path.exists():
                raise ValueError(f"Fichier non trouvé: {file_path}")

            processing_options = processing_options or {}

            # Traitement selon le type de fichier
            if file_record.file_type.lower() in ['jpg', 'jpeg', 'png']:
                # Optimisation d'image
                with Image.open(file_path) as img:
                    # Redimensionner si nécessaire
                    max_width = processing_options.get('max_width', 1920)
                    max_height = processing_options.get('max_height', 1080)

                    if img.width > max_width or img.height > max_height:
                        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

                    # Optimiser et sauvegarder
                    if file_record.file_type.lower() in ['jpg', 'jpeg']:
                        img.save(file_path, 'JPEG', quality=85, optimize=True)
                    else:
                        img.save(file_path, 'PNG', optimize=True)

                    # Mettre à jour les métadonnées
                    file_record.width, file_record.height = img.size
                    file_record.file_size = file_path.stat().st_size

            elif file_record.file_type.lower() == 'pdf':
                # Optimisation PDF (si Ghostscript est disponible)
                try:
                    optimized_path = file_path.with_suffix('.optimized.pdf')
                    subprocess.run([
                        'gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
                        '-dPDFSETTINGS=/ebook', '-dNOPAUSE', '-dQUIET', '-dBATCH',
                        f'-sOutputFile={optimized_path}', str(file_path)
                    ], check=True, timeout=300)

                    # Remplacer le fichier original
                    if optimized_path.exists():
                        optimized_path.replace(file_path)
                        file_record.file_size = file_path.stat().st_size

                except (subprocess.SubprocessError, FileNotFoundError):
                    logger.warning("Ghostscript non disponible pour l'optimisation PDF")

            # Sauvegarder les changements
            from models import db
            db.session.commit()

        logger.info(f"Fichier traité: {file_id}")
        return {'status': 'processed', 'file_id': file_id}

    except Exception as e:
        logger.error(f"Erreur traitement fichier {file_id}: {e}")
        raise self.retry(exc=e, countdown=60)

@celery_app.task(bind=True, max_retries=2)
def generate_quote_pdf(self, quote_id: int):
    """Générer un PDF pour un devis"""
    try:
        from app import create_app
        from models import Quote
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors

        app = create_app()

        with app.app_context():
            quote = Quote.query.get(quote_id)
            if not quote:
                raise ValueError(f"Devis {quote_id} non trouvé")

            # Créer le PDF
            filename = f"quote_{quote.quote_number}.pdf"
            pdf_path = Path('uploads') / filename

            # Créer le document
            doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            # En-tête
            header_style = styles['Heading1']
            header_style.textColor = colors.HexColor('#2D1B69')

            story.append(Paragraph("PassPrint - Devis", header_style))
            story.append(Spacer(1, 0.5 * inch))

            # Informations du devis
            story.append(Paragraph(f"<b>Numéro de devis:</b> {quote.quote_number}", styles['Normal']))
            story.append(Paragraph(f"<b>Date:</b> {quote.created_at.strftime('%d/%m/%Y')}", styles['Normal']))
            story.append(Paragraph(f"<b>Valide jusqu'au:</b> {quote.valid_until.strftime('%d/%m/%Y')}", styles['Normal']))
            story.append(Spacer(1, 0.3 * inch))

            # Détails du projet
            story.append(Paragraph("Détails du projet:", styles['Heading2']))

            project_data = [
                ['Projet', quote.project_name or 'Non spécifié'],
                ['Description', quote.project_description or 'Non spécifiée'],
                ['Format', quote.format or 'Non spécifié'],
                ['Quantité', str(quote.quantity) if quote.quantity else 'Non spécifiée'],
                ['Prix estimé', f"{quote.estimated_price or 0:,.0f} FCFA".replace(',', ' ')],
            ]

            project_table = Table(project_data)
            project_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            story.append(project_table)
            story.append(Spacer(1, 0.5 * inch))

            # Pied de page
            footer_style = styles['Normal']
            footer_style.textColor = colors.gray
            story.append(Paragraph("Ce devis est généré automatiquement et est valide jusqu'à la date indiquée.", footer_style))

            # Générer le PDF
            doc.build(story)

            # Mettre à jour le devis avec le chemin du PDF
            quote.pdf_path = str(pdf_path)
            from models import db
            db.session.commit()

        logger.info(f"PDF devis généré: {quote_id}")
        return {'status': 'generated', 'file_path': str(pdf_path)}

    except Exception as e:
        logger.error(f"Erreur génération PDF devis {quote_id}: {e}")
        raise self.retry(exc=e, countdown=60)

# Tâches de sauvegarde
@celery_app.task(bind=True, max_retries=2)
def create_database_backup(self):
    """Créer une sauvegarde de la base de données"""
    try:
        from backup_system import backup_system

        success = backup_system.create_database_backup()

        if success:
            logger.info("Sauvegarde base de données créée")
            return {'status': 'success'}
        else:
            raise Exception("Échec de la sauvegarde")

    except Exception as e:
        logger.error(f"Erreur sauvegarde base de données: {e}")
        raise self.retry(exc=e, countdown=300)  # Réessayer dans 5 minutes

@celery_app.task(bind=True, max_retries=2)
def create_files_backup(self):
    """Créer une sauvegarde des fichiers"""
    try:
        from backup_system import backup_system

        success = backup_system.create_files_backup()

        if success:
            logger.info("Sauvegarde fichiers créée")
            return {'status': 'success'}
        else:
            raise Exception("Échec de la sauvegarde fichiers")

    except Exception as e:
        logger.error(f"Erreur sauvegarde fichiers: {e}")
        raise self.retry(exc=e, countdown=300)

# Tâches de nettoyage
@celery_app.task(bind=True)
def cleanup_old_files(self):
    """Nettoyer les anciens fichiers temporaires"""
    try:
        cleanup_dirs = ['uploads', 'backups']
        deleted_files = []

        for dir_name in cleanup_dirs:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                continue

            # Supprimer les fichiers de plus de 30 jours
            cutoff_date = datetime.utcnow() - timedelta(days=30)

            for file_path in dir_path.rglob('*'):
                if file_path.is_file():
                    file_modified = datetime.fromtimestamp(file_path.stat().st_mtime)

                    if file_modified < cutoff_date:
                        # Vérifier que ce n'est pas un fichier actif
                        if not self._is_file_active(file_path):
                            file_path.unlink()
                            deleted_files.append(str(file_path))

        logger.info(f"Fichiers nettoyés: {len(deleted_files)}")
        return {'status': 'success', 'deleted_files': len(deleted_files)}

    except Exception as e:
        logger.error(f"Erreur nettoyage fichiers: {e}")
        return {'status': 'error', 'error': str(e)}

def _is_file_active(self, file_path: Path) -> bool:
    """Vérifier si un fichier est actif (utilisé par une commande/devis)"""
    try:
        from models import File, Order, Quote

        # Vérifier si le fichier est référencé dans la base
        file_record = File.query.filter_by(filename=file_path.name).first()
        if file_record:
            return True

        # Vérifier les références dans les devis/commandes
        if file_record.quote_id or file_record.order_id:
            return True

        return False

    except Exception:
        # En cas d'erreur, considérer le fichier comme actif
        return True

# Tâches d'analytics
@celery_app.task(bind=True)
def update_analytics(self):
    """Mettre à jour les statistiques d'analytics"""
    try:
        from app import create_app
        from models import Order, User, Product, Quote
        from redis_cache import cache_manager

        app = create_app()

        with app.app_context():
            # Calculer les statistiques du jour
            today = datetime.utcnow().date()

            daily_stats = {
                'date': today.isoformat(),
                'orders_count': Order.query.filter(
                    Order.created_at >= today
                ).count(),
                'users_count': User.query.filter(
                    User.created_at >= today
                ).count(),
                'revenue': float(Order.query.filter(
                    Order.created_at >= today,
                    Order.payment_status == 'paid'
                ).with_entities(func.sum(Order.total_amount)).scalar() or 0),
                'products_sold': Product.query.join(OrderItem).join(Order).filter(
                    Order.created_at >= today,
                    Order.payment_status == 'paid'
                ).with_entities(func.sum(OrderItem.quantity)).scalar() or 0
            }

            # Mettre en cache les statistiques
            cache_key = cache_manager.generate_key('daily_stats', today.isoformat())
            cache_manager.set(cache_key, daily_stats, ttl=86400, namespace='analytics')  # 24h

            logger.info(f"Analytics mis à jour: {daily_stats}")
            return daily_stats

    except Exception as e:
        logger.error(f"Erreur mise à jour analytics: {e}")
        return {'status': 'error', 'error': str(e)}

@celery_app.task(bind=True)
def send_daily_reports(self):
    """Envoyer le rapport quotidien"""
    try:
        from app import create_app
        from models import User

        app = create_app()

        with app.app_context():
            # Récupérer les administrateurs
            admins = User.query.filter_by(is_admin=True).all()

            if not admins:
                logger.warning("Aucun administrateur trouvé pour le rapport quotidien")
                return {'status': 'no_admins'}

            # Générer le rapport
            report_data = generate_daily_report()

            # Envoyer à chaque administrateur
            for admin in admins:
                if admin.email:
                    try:
                        html_content = generate_report_html(report_data)

                        send_email_async.delay(
                            admin.email,
                            f"Rapport quotidien PassPrint - {datetime.now().strftime('%d/%m/%Y')}",
                            html_content
                        )
                    except Exception as e:
                        logger.error(f"Erreur envoi rapport à {admin.email}: {e}")

            return {'status': 'sent', 'admins_count': len(admins)}

    except Exception as e:
        logger.error(f"Erreur rapport quotidien: {e}")
        return {'status': 'error', 'error': str(e)}

def generate_daily_report():
    """Générer les données du rapport quotidien"""
    from models import Order, User, Product, Quote
    from datetime import datetime, timedelta

    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)

    return {
        'date': today.isoformat(),
        'orders': {
            'today': Order.query.filter(Order.created_at >= today).count(),
            'yesterday': Order.query.filter(
                Order.created_at >= yesterday,
                Order.created_at < today
            ).count(),
            'total': Order.query.count()
        },
        'users': {
            'today': User.query.filter(User.created_at >= today).count(),
            'total': User.query.count()
        },
        'products': {
            'total': Product.query.count(),
            'active': Product.query.filter_by(is_active=True).count(),
            'out_of_stock': Product.query.filter(
                Product.stock_quantity <= 0,
                Product.is_active == True
            ).count()
        },
        'quotes': {
            'today': Quote.query.filter(Quote.created_at >= today).count(),
            'pending': Quote.query.filter_by(status='draft').count(),
            'total': Quote.query.count()
        }
    }

def generate_report_html(report_data):
    """Générer le HTML du rapport"""
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #2D1B69 0%, #FF6B35 100%); color: white; padding: 2rem; text-align: center;">
            <h1 style="margin: 0;">Rapport Quotidien PassPrint</h1>
            <p style="margin: 0.5rem 0 0 0;">{report_data['date']}</p>
        </div>

        <div style="padding: 2rem;">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
                <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 8px; text-align: center;">
                    <h3 style="color: #2D1B69; margin: 0 0 0.5rem 0;">Commandes</h3>
                    <p style="font-size: 2rem; font-weight: bold; color: #FF6B35; margin: 0;">{report_data['orders']['today']}</p>
                    <p style="color: #666; margin: 0;">Aujourd'hui</p>
                </div>

                <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 8px; text-align: center;">
                    <h3 style="color: #2D1B69; margin: 0 0 0.5rem 0;">Utilisateurs</h3>
                    <p style="font-size: 2rem; font-weight: bold; color: #FF6B35; margin: 0;">{report_data['users']['today']}</p>
                    <p style="color: #666; margin: 0;">Aujourd'hui</p>
                </div>

                <div style="background: #f8f9fa; padding: 1.5rem; border-radius: 8px; text-align: center;">
                    <h3 style="color: #2D1B69; margin: 0 0 0.5rem 0;">Produits Actifs</h3>
                    <p style="font-size: 2rem; font-weight: bold; color: #FF6B35; margin: 0;">{report_data['products']['active']}</p>
                    <p style="color: #666; margin: 0;">En stock</p>
                </div>
            </div>

            <div style="background: white; border: 1px solid #ddd; border-radius: 8px; padding: 1.5rem;">
                <h3 style="color: #2D1B69; margin: 0 0 1rem 0;">Détails</h3>
                <p><strong>Total commandes:</strong> {report_data['orders']['total']}</p>
                <p><strong>Total utilisateurs:</strong> {report_data['users']['total']}</p>
                <p><strong>Devis en attente:</strong> {report_data['quotes']['pending']}</p>
                <p><strong>Produits en rupture:</strong> {report_data['products']['out_of_stock']}</p>
            </div>
        </div>

        <div style="background: #2D1B69; color: white; padding: 1rem; text-align: center;">
            <p style="margin: 0;">Rapport généré automatiquement par PassPrint</p>
        </div>
    </div>
    """

# Tâches de notifications
@celery_app.task(bind=True, max_retries=3)
def send_webhook_notification(self, webhook_url: str, event_type: str, data: dict):
    """Envoyer une notification webhook"""
    try:
        payload = {
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        }

        response = requests.post(
            webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        response.raise_for_status()

        logger.info(f"Webhook envoyé: {event_type} -> {webhook_url}")
        return {'status': 'sent', 'response_code': response.status_code}

    except Exception as e:
        logger.error(f"Erreur webhook {event_type}: {e}")
        raise self.retry(exc=e, countdown=60)

# Tâches de traitement en lot
@celery_app.task(bind=True)
def process_batch_orders(self, order_ids: list):
    """Traiter un lot de commandes"""
    try:
        from app import create_app
        from models import Order

        app = create_app()
        results = []

        with app.app_context():
            for order_id in order_ids:
                try:
                    order = Order.query.get(order_id)
                    if order:
                        # Logique de traitement de commande
                        # (validation, mise à jour du stock, etc.)
                        results.append({'order_id': order_id, 'status': 'processed'})
                    else:
                        results.append({'order_id': order_id, 'status': 'not_found'})

                except Exception as e:
                    logger.error(f"Erreur traitement commande {order_id}: {e}")
                    results.append({'order_id': order_id, 'status': 'error', 'error': str(e)})

        logger.info(f"Traitement lot commandes: {len([r for r in results if r['status'] == 'processed'])}/{len(order_ids)}")
        return results

    except Exception as e:
        logger.error(f"Erreur traitement lot commandes: {e}")
        return {'status': 'error', 'error': str(e)}

# Tâches utilitaires
@celery_app.task(bind=True)
def health_check(self):
    """Vérification de santé des tâches Celery"""
    try:
        # Vérifier la connexion Redis
        redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        redis_client.ping()

        # Vérifier les workers actifs
        active_tasks = len(celery_app.control.inspect().active() or [])

        return {
            'status': 'healthy',
            'redis_connected': True,
            'active_tasks': active_tasks,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

# Démarrer le scheduler si exécuté directement
if __name__ == "__main__":
    print("🚀 Système de tâches Celery PassPrint démarré")

    # Démarrer le worker
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'worker':
        print("👷 Démarrage du worker Celery...")
        celery_app.start(argv=['celery', 'worker', '--loglevel=info'])

    elif len(sys.argv) > 1 and sys.argv[1] == 'beat':
        print("⏰ Démarrage du scheduler Celery...")
        celery_app.start(argv=['celery', 'beat', '--loglevel=info'])

    else:
        print("Usage: python celery_tasks.py [worker|beat]")
        print("  worker: Démarrer un worker")
        print("  beat: Démarrer le scheduler")