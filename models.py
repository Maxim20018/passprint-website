"""
Modèles de base de données pour PassPrint
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    """Modèle utilisateur"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    company = db.Column(db.String(100))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    orders = db.relationship('Order', backref='customer', lazy=True)
    quotes = db.relationship('Quote', backref='customer', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'company': self.company,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat()
        }

class Product(db.Model):
    """Modèle produit"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 'print', 'supplies', 'usb'
    stock_quantity = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relations
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'category': self.category,
            'stock_quantity': self.stock_quantity,
            'image_url': self.image_url,
            'is_active': self.is_active
        }

class Order(db.Model):
    """Modèle commande"""
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, processing, shipped, delivered, cancelled
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, failed, refunded
    stripe_payment_id = db.Column(db.String(100))

    # Informations de livraison
    shipping_address = db.Column(db.Text)
    shipping_phone = db.Column(db.String(20))
    shipping_email = db.Column(db.String(120))

    # Notes et commentaires
    notes = db.Column(db.Text)
    internal_notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'customer_id': self.customer_id,
            'total_amount': self.total_amount,
            'status': self.status,
            'payment_status': self.payment_status,
            'stripe_payment_id': self.stripe_payment_id,
            'shipping_address': self.shipping_address,
            'shipping_phone': self.shipping_phone,
            'shipping_email': self.shipping_email,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'items': [item.to_dict() for item in self.items]
        }

class OrderItem(db.Model):
    """Modèle élément de commande"""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    # Spécifications du produit personnalisé
    specifications = db.Column(db.Text)  # JSON string des options (format, finition, etc.)

    def to_dict(self):
        specs = json.loads(self.specifications) if self.specifications else {}
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'product_name': self.product.name,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_price': self.total_price,
            'specifications': specs
        }

class Quote(db.Model):
    """Modèle devis"""
    id = db.Column(db.Integer, primary_key=True)
    quote_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Informations du projet
    project_name = db.Column(db.String(100))
    project_description = db.Column(db.Text)
    project_type = db.Column(db.String(50))  # 'print', 'design', 'both'

    # Spécifications techniques
    format = db.Column(db.String(20))
    quantity = db.Column(db.Integer)
    material = db.Column(db.String(50))
    finishing = db.Column(db.String(100))

    # Prix et statut
    estimated_price = db.Column(db.Float)
    final_price = db.Column(db.Float)
    status = db.Column(db.String(20), default='draft')  # draft, sent, approved, rejected, expired

    # Fichiers joints
    files = db.Column(db.Text)  # JSON array des chemins de fichiers

    # Dates d'échéance
    valid_until = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'quote_number': self.quote_number,
            'customer_id': self.customer_id,
            'project_name': self.project_name,
            'project_description': self.project_description,
            'project_type': self.project_type,
            'format': self.format,
            'quantity': self.quantity,
            'material': self.material,
            'finishing': self.finishing,
            'estimated_price': self.estimated_price,
            'final_price': self.final_price,
            'status': self.status,
            'files': json.loads(self.files) if self.files else [],
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'created_at': self.created_at.isoformat()
        }

class Cart(db.Model):
    """Modèle panier d'achat"""
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False)  # Pour les utilisateurs non connectés
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # NULL si utilisateur non connecté

    # Éléments du panier (JSON)
    items = db.Column(db.Text, nullable=False)  # JSON array des éléments

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'customer_id': self.customer_id,
            'items': json.loads(self.items) if self.items else [],
            'created_at': self.created_at.isoformat()
        }

class File(db.Model):
    """Modèle fichier uploadé"""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    mime_type = db.Column(db.String(100))

    # Métadonnées
    width = db.Column(db.Integer)  # Pour les images
    height = db.Column(db.Integer)  # Pour les images
    pages = db.Column(db.Integer)  # Pour les PDFs

    # Relations
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'))
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))

    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'mime_type': self.mime_type,
            'width': self.width,
            'height': self.height,
            'pages': self.pages,
            'quote_id': self.quote_id,
            'order_id': self.order_id,
            'uploaded_at': self.uploaded_at.isoformat()
        }

class NewsletterSubscriber(db.Model):
    """Modèle abonné newsletter"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    source = db.Column(db.String(50), default='website')  # website, import, etc.

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'subscribed_at': self.subscribed_at.isoformat(),
            'is_active': self.is_active,
            'source': self.source
        }