#!/usr/bin/env python3
"""
Système de génération de rapports PDF pour PassPrint
Crée des rapports professionnels avec ReportLab
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import json
from datetime import datetime
from typing import Dict, List, Optional
import os

class PDFReportGenerator:
    """Générateur de rapports PDF professionnel"""

    def __init__(self):
        self.output_dir = "reports"
        os.makedirs(self.output_dir, exist_ok=True)

        # Styles
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2D1B69')
        )
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            textColor=colors.HexColor('#FF6B35')
        )
        self.subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=15,
            textColor=colors.HexColor('#4A3585')
        )

    def generate_sales_report(self, sales_data: Dict, start_date: str, end_date: str) -> str:
        """
        Génère un rapport de ventes PDF

        Args:
            sales_data: Données de ventes
            start_date: Date de début
            end_date: Date de fin

        Returns:
            Chemin du fichier PDF généré
        """
        filename = f"rapport_ventes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        # Création du document
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []

        # En-tête du rapport
        header_text = f"Rapport de Ventes - PassPrint<br/>{start_date} au {end_date}"
        story.append(Paragraph(header_text, self.title_style))
        story.append(Spacer(1, 20))

        # Résumé exécutif
        summary_text = f"""
        <b>Résumé Exécutif</b><br/>
        Période: {start_date} - {end_date}<br/>
        Chiffre d'affaires total: {sales_data.get('total_revenue', 0):,.0f} FCFA<br/>
        Nombre de commandes: {sales_data.get('total_orders', 0)}<br/>
        Panier moyen: {sales_data.get('average_order', 0):,.0f} FCFA<br/>
        Taux de croissance: {sales_data.get('growth_rate', 0):.1f}%
        """
        story.append(Paragraph(summary_text, self.subheading_style))
        story.append(Spacer(1, 20))

        # Tableau des ventes par mois
        if 'monthly_sales' in sales_data:
            story.append(Paragraph("Ventes Mensuelles", self.heading_style))

            # Données du tableau
            table_data = [['Mois', 'Revenus (FCFA)', 'Commandes', 'Croissance']]
            for month in sales_data['monthly_sales']:
                table_data.append([
                    month['month'],
                    f"{month['revenue']:,.0f}",
                    str(month.get('orders', 0)),
                    f"{month.get('growth', 0):.1f}%"
                ])

            # Création du tableau
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2D1B69')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            story.append(table)
            story.append(Spacer(1, 30))

        # Graphique des ventes (simulé avec du texte pour l'instant)
        story.append(Paragraph("Évolution des Ventes", self.heading_style))
        chart_text = """
        [Graphique des ventes mensuelles]

        Décembre: 850,000 FCFA
        Janvier:  1,250,000 FCFA

        Croissance: +47.1%
        """
        story.append(Paragraph(chart_text, self.styles['Normal']))
        story.append(Spacer(1, 30))

        # Top produits
        if 'top_products' in sales_data:
            story.append(Paragraph("Top Produits", self.heading_style))

            top_table_data = [['Produit', 'Ventes', 'Quantité']]
            for product in sales_data['top_products'][:5]:
                top_table_data.append([
                    product['name'],
                    f"{product['revenue']:,.0f} FCFA",
                    str(product['quantity'])
                ])

            top_table = Table(top_table_data)
            top_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B35')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            story.append(top_table)

        # Pied de page
        story.append(Spacer(1, 50))
        footer_text = f"""
        <b>Rapport généré le:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}<br/>
        <b>PassPrint SARL</b><br/>
        Douala, Cameroun<br/>
        contact@passprint.com | +237 696 465 609
        """
        story.append(Paragraph(footer_text, self.styles['Normal']))

        # Génération du PDF
        doc.build(story)

        return filepath

    def generate_order_report(self, order_data: Dict) -> str:
        """
        Génère un rapport de commande PDF

        Args:
            order_data: Données de la commande

        Returns:
            Chemin du fichier PDF généré
        """
        filename = f"commande_{order_data.get('order_number', 'INCONNU')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []

        # En-tête
        title_text = f"Commande #{order_data.get('order_number', 'N/A')}"
        story.append(Paragraph(title_text, self.title_style))
        story.append(Spacer(1, 20))

        # Informations client
        customer_info = f"""
        <b>Informations Client</b><br/>
        Nom: {order_data.get('customer_name', 'N/A')}<br/>
        Email: {order_data.get('customer_email', 'N/A')}<br/>
        Téléphone: {order_data.get('customer_phone', 'N/A')}<br/>
        Entreprise: {order_data.get('customer_company', 'N/A')}
        """
        story.append(Paragraph(customer_info, self.subheading_style))
        story.append(Spacer(1, 20))

        # Détails de la commande
        order_details = f"""
        <b>Détails de la Commande</b><br/>
        Date: {order_data.get('created_at', 'N/A')}<br/>
        Statut: {order_data.get('status', 'N/A')}<br/>
        Montant total: {order_data.get('total_amount', 0):,.0f} FCFA<br/>
        Mode de paiement: {order_data.get('payment_method', 'N/A')}
        """
        story.append(Paragraph(order_details, self.subheading_style))
        story.append(Spacer(1, 20))

        # Produits commandés
        if 'items' in order_data:
            story.append(Paragraph("Produits Commandés", self.heading_style))

            items_data = [['Produit', 'Quantité', 'Prix Unitaire', 'Total']]
            for item in order_data['items']:
                items_data.append([
                    item.get('name', 'N/A'),
                    str(item.get('quantity', 0)),
                    f"{item.get('unit_price', 0):,.0f} FCFA",
                    f"{item.get('total_price', 0):,.0f} FCFA"
                ])

            items_table = Table(items_data)
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2D1B69')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            story.append(items_table)

        # Conditions générales
        story.append(Spacer(1, 30))
        terms_text = """
        <b>Conditions Générales</b><br/>
        • Délai de livraison: 3-5 jours ouvrés<br/>
        • Paiement à la commande<br/>
        • Garantie satisfaction client<br/>
        • Service après-vente inclus
        """
        story.append(Paragraph(terms_text, self.styles['Normal']))

        # Génération du PDF
        doc.build(story)

        return filepath

    def generate_inventory_report(self, inventory_data: Dict) -> str:
        """
        Génère un rapport d'inventaire PDF

        Args:
            inventory_data: Données d'inventaire

        Returns:
            Chemin du fichier PDF généré
        """
        filename = f"inventaire_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []

        # En-tête
        title_text = "Rapport d'Inventaire - PassPrint"
        story.append(Paragraph(title_text, self.title_style))
        story.append(Spacer(1, 20))

        # Résumé inventaire
        summary_text = f"""
        <b>Résumé Inventaire</b><br/>
        Date du rapport: {datetime.now().strftime('%d/%m/%Y')}<br/>
        Produits en stock: {inventory_data.get('in_stock', 0)}<br/>
        Produits en rupture: {inventory_data.get('out_of_stock', 0)}<br/>
        Valeur totale: {inventory_data.get('total_value', 0):,.0f} FCFA<br/>
        Alertes stock: {inventory_data.get('low_stock_alerts', 0)}
        """
        story.append(Paragraph(summary_text, self.subheading_style))
        story.append(Spacer(1, 20))

        # Tableau d'inventaire
        if 'products' in inventory_data:
            story.append(Paragraph("Détail de l'Inventaire", self.heading_style))

            inventory_table_data = [['Produit', 'Stock', 'Stock Min', 'Valeur', 'Statut']]
            for product in inventory_data['products']:
                status = "En stock" if product['stock'] > product['min_stock'] else "Rupture"
                inventory_table_data.append([
                    product['name'],
                    str(product['stock']),
                    str(product['min_stock']),
                    f"{product['value']:,.0f} FCFA",
                    status
                ])

            inventory_table = Table(inventory_table_data)
            inventory_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2D1B69')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            story.append(inventory_table)

        # Recommandations
        story.append(Spacer(1, 30))
        recommendations_text = """
        <b>Recommandations</b><br/>
        • Réapprovisionner les produits en rupture de stock<br/>
        • Optimiser les niveaux de stock minimum<br/>
        • Mettre en place un système d'alerte automatique<br/>
        • Analyser les tendances de consommation
        """
        story.append(Paragraph(recommendations_text, self.styles['Normal']))

        # Génération du PDF
        doc.build(story)

        return filepath

    def generate_customer_report(self, customer_data: Dict) -> str:
        """
        Génère un rapport clients PDF

        Args:
            customer_data: Données clients

        Returns:
            Chemin du fichier PDF généré
        """
        filename = f"rapport_clients_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []

        # En-tête
        title_text = "Rapport Clients - PassPrint"
        story.append(Paragraph(title_text, self.title_style))
        story.append(Spacer(1, 20))

        # Statistiques clients
        stats_text = f"""
        <b>Statistiques Clients</b><br/>
        Total clients: {customer_data.get('total_customers', 0)}<br/>
        Nouveaux ce mois: {customer_data.get('new_this_month', 0)}<br/>
        Clients actifs: {customer_data.get('active_customers', 0)}<br/>
        Taux de fidélité: {customer_data.get('loyalty_rate', 0):.1f}%
        """
        story.append(Paragraph(stats_text, self.subheading_style))
        story.append(Spacer(1, 20))

        # Top clients
        if 'top_customers' in customer_data:
            story.append(Paragraph("Top Clients", self.heading_style))

            top_table_data = [['Client', 'Commandes', 'Total Dépensé', 'Dernière Commande']]
            for customer in customer_data['top_customers'][:10]:
                top_table_data.append([
                    customer['name'],
                    str(customer['order_count']),
                    f"{customer['total_spent']:,.0f} FCFA",
                    customer['last_order']
                ])

            top_table = Table(top_table_data)
            top_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B35')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            story.append(top_table)

        # Génération du PDF
        doc.build(story)

        return filepath

# Instance globale du générateur de rapports
report_generator = PDFReportGenerator()

def generate_sales_pdf_report(start_date: str, end_date: str, sales_data: Dict = None) -> str:
    """
    Génère un rapport de ventes PDF

    Args:
        start_date: Date de début
        end_date: Date de fin
        sales_data: Données de ventes (optionnel)

    Returns:
        Chemin du fichier PDF généré
    """
    if not sales_data:
        # Données de démonstration
        sales_data = {
            'total_revenue': 1250000,
            'total_orders': 89,
            'average_order': 14045,
            'growth_rate': 15.3,
            'monthly_sales': [
                {'month': '2024-12', 'revenue': 850000, 'orders': 62, 'growth': 12.5},
                {'month': '2025-01', 'revenue': 1250000, 'orders': 89, 'growth': 47.1}
            ],
            'top_products': [
                {'name': 'Banderole Publicitaire', 'revenue': 450000, 'quantity': 18},
                {'name': 'Stickers Personnalisés', 'revenue': 300000, 'quantity': 20}
            ]
        }

    return report_generator.generate_sales_report(sales_data, start_date, end_date)

def generate_order_pdf_report(order_data: Dict) -> str:
    """
    Génère un rapport de commande PDF

    Args:
        order_data: Données de la commande

    Returns:
        Chemin du fichier PDF généré
    """
    return report_generator.generate_order_report(order_data)

def generate_inventory_pdf_report(inventory_data: Dict = None) -> str:
    """
    Génère un rapport d'inventaire PDF

    Args:
        inventory_data: Données d'inventaire (optionnel)

    Returns:
        Chemin du fichier PDF généré
    """
    if not inventory_data:
        # Données de démonstration
        inventory_data = {
            'in_stock': 10,
            'out_of_stock': 2,
            'total_value': 850000,
            'low_stock_alerts': 3,
            'products': [
                {'name': 'Banderole Premium', 'stock': 15, 'min_stock': 5, 'value': 375000},
                {'name': 'Stickers Deluxe', 'stock': 0, 'min_stock': 10, 'value': 0},
                {'name': 'Clé USB 32GB', 'stock': 25, 'min_stock': 5, 'value': 212500}
            ]
        }

    return report_generator.generate_inventory_report(inventory_data)

def generate_customer_pdf_report(customer_data: Dict = None) -> str:
    """
    Génère un rapport clients PDF

    Args:
        customer_data: Données clients (optionnel)

    Returns:
        Chemin du fichier PDF généré
    """
    if not customer_data:
        # Données de démonstration
        customer_data = {
            'total_customers': 156,
            'new_this_month': 23,
            'active_customers': 89,
            'loyalty_rate': 67.5,
            'top_customers': [
                {'name': 'Marie Douala', 'order_count': 12, 'total_spent': 450000, 'last_order': '2025-01-15'},
                {'name': 'Jean-Pierre Nguema', 'order_count': 8, 'total_spent': 320000, 'last_order': '2025-01-12'}
            ]
        }

    return report_generator.generate_customer_report(customer_data)

def get_available_reports() -> List[str]:
    """
    Retourne la liste des rapports disponibles

    Returns:
        Liste des types de rapports
    """
    return [
        'sales_report',
        'order_report',
        'inventory_report',
        'customer_report',
        'analytics_report'
    ]

if __name__ == "__main__":
    # Test du générateur de rapports
    print("Test de génération de rapport PDF...")

    # Rapport de ventes
    sales_report = generate_sales_pdf_report("01/12/2024", "31/01/2025")
    print(f"Rapport de ventes généré: {sales_report}")

    # Rapport d'inventaire
    inventory_report = generate_inventory_pdf_report()
    print(f"Rapport d'inventaire généré: {inventory_report}")

    print("Génération de rapports terminée avec succès!")