#!/usr/bin/env python3
"""
Schémas de validation pour PassPrint
Utilise Marshmallow pour la validation et la sérialisation
"""
from marshmallow import Schema, fields, validates, ValidationError, pre_load, post_dump
from marshmallow.validate import Length, Range, Email, OneOf, Regexp
import re
from datetime import datetime

class BaseSchema(Schema):
    """Schéma de base avec validation commune"""

    @validates('email')
    def validate_email_format(self, value):
        """Valider le format de l'email"""
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise ValidationError('Format d\'email invalide')

    @validates('phone')
    def validate_phone_format(self, value):
        """Valider le format du téléphone"""
        if value:
            # Supprimer tous les caractères non numériques
            phone_digits = re.sub(r'\D', '', value)

            # Vérifier la longueur (8-15 chiffres)
            if not (8 <= len(phone_digits) <= 15):
                raise ValidationError('Numéro de téléphone invalide (8-15 chiffres requis)')

class UserRegistrationSchema(BaseSchema):
    """Schéma de validation pour l'inscription utilisateur"""
    email = fields.Email(required=True, validate=Email())
    password = fields.String(
        required=True,
        validate=[
            Length(min=8, max=128),
            Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]',
                   error='Le mot de passe doit contenir au moins une minuscule, une majuscule, un chiffre et un caractère spécial')
        ]
    )
    first_name = fields.String(
        required=True,
        validate=Length(min=1, max=50),
        error_messages={'required': 'Le prénom est requis'}
    )
    last_name = fields.String(
        required=True,
        validate=Length(min=1, max=50),
        error_messages={'required': 'Le nom de famille est requis'}
    )
    phone = fields.String(
        validate=Length(max=20),
        allow_none=True
    )
    company = fields.String(
        validate=Length(max=100),
        allow_none=True
    )

    @validates('password')
    def validate_password_strength(self, value):
        """Validation supplémentaire de la force du mot de passe"""
        common_passwords = {'password', '123456', 'password123', 'admin', 'qwerty', 'azerty'}
        if value.lower() in common_passwords:
            raise ValidationError('Ce mot de passe est trop courant')

class UserLoginSchema(BaseSchema):
    """Schéma de validation pour la connexion utilisateur"""
    email = fields.Email(required=True, validate=Email())
    password = fields.String(required=True)

class PasswordChangeSchema(Schema):
    """Schéma de validation pour le changement de mot de passe"""
    current_password = fields.String(required=True)
    new_password = fields.String(
        required=True,
        validate=[
            Length(min=8, max=128),
            Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]',
                   error='Le mot de passe doit contenir au moins une minuscule, une majuscule, un chiffre et un caractère spécial')
        ]
    )

    @validates('new_password')
    def validate_password_not_same(self, value):
        """Vérifier que le nouveau mot de passe est différent de l'ancien"""
        # Cette validation sera effectuée côté serveur avec le mot de passe actuel

class ProductSchema(Schema):
    """Schéma de validation pour les produits"""
    name = fields.String(
        required=True,
        validate=Length(min=1, max=100),
        error_messages={'required': 'Le nom du produit est requis'}
    )
    description = fields.String(
        validate=Length(max=1000),
        allow_none=True
    )
    price = fields.Float(
        required=True,
        validate=Range(min=0),
        error_messages={'required': 'Le prix est requis'}
    )
    category = fields.String(
        required=True,
        validate=OneOf(['print', 'supplies', 'usb', 'other']),
        error_messages={'required': 'La catégorie est requise'}
    )
    stock_quantity = fields.Integer(
        validate=Range(min=0),
        allow_none=True,
        missing=0
    )
    image_url = fields.URL(
        validate=Length(max=255),
        allow_none=True
    )
    is_active = fields.Boolean(allow_none=True, missing=True)

class ProductUpdateSchema(Schema):
    """Schéma de validation pour la mise à jour des produits"""
    name = fields.String(
        validate=Length(min=1, max=100),
        allow_none=True
    )
    description = fields.String(
        validate=Length(max=1000),
        allow_none=True
    )
    price = fields.Float(
        validate=Range(min=0),
        allow_none=True
    )
    category = fields.String(
        validate=OneOf(['print', 'supplies', 'usb', 'other']),
        allow_none=True
    )
    stock_quantity = fields.Integer(
        validate=Range(min=0),
        allow_none=True
    )
    image_url = fields.URL(
        validate=Length(max=255),
        allow_none=True
    )
    is_active = fields.Boolean(allow_none=True)

class OrderCreateSchema(Schema):
    """Schéma de validation pour la création de commande"""
    customer_id = fields.Integer(
        validate=Range(min=1),
        allow_none=True
    )
    shipping_address = fields.String(
        validate=Length(max=500),
        allow_none=True
    )
    shipping_phone = fields.String(
        validate=Length(max=20),
        allow_none=True
    )
    shipping_email = fields.Email(
        validate=Length(max=120),
        allow_none=True
    )
    notes = fields.String(
        validate=Length(max=1000),
        allow_none=True
    )

class QuoteCreateSchema(Schema):
    """Schéma de validation pour la création de devis"""
    customer_id = fields.Integer(
        validate=Range(min=1),
        allow_none=True
    )
    project_name = fields.String(
        required=True,
        validate=Length(min=1, max=100),
        error_messages={'required': 'Le nom du projet est requis'}
    )
    project_description = fields.String(
        validate=Length(max=2000),
        allow_none=True
    )
    project_type = fields.String(
        validate=OneOf(['print', 'design', 'both']),
        allow_none=True
    )
    format = fields.String(
        validate=Length(max=20),
        allow_none=True
    )
    quantity = fields.Integer(
        validate=Range(min=1),
        allow_none=True
    )
    material = fields.String(
        validate=Length(max=50),
        allow_none=True
    )
    finishing = fields.String(
        validate=Length(max=100),
        allow_none=True
    )
    estimated_price = fields.Float(
        validate=Range(min=0),
        allow_none=True
    )

class CartItemSchema(Schema):
    """Schéma de validation pour les éléments du panier"""
    product_id = fields.Integer(
        required=True,
        validate=Range(min=1),
        error_messages={'required': 'L\'ID du produit est requis'}
    )
    quantity = fields.Integer(
        required=True,
        validate=Range(min=1, max=1000),
        error_messages={'required': 'La quantité est requise'}
    )
    specifications = fields.Dict(
        allow_none=True,
        missing=dict
    )

class CartUpdateSchema(Schema):
    """Schéma de validation pour la mise à jour du panier"""
    items = fields.List(
        fields.Nested(CartItemSchema),
        allow_none=True
    )

class NewsletterSubscriptionSchema(BaseSchema):
    """Schéma de validation pour l'abonnement à la newsletter"""
    email = fields.Email(
        required=True,
        validate=Email(),
        error_messages={'required': 'L\'adresse email est requise'}
    )
    first_name = fields.String(
        validate=Length(max=50),
        allow_none=True
    )
    last_name = fields.String(
        validate=Length(max=50),
        allow_none=True
    )

class FileUploadSchema(Schema):
    """Schéma de validation pour l'upload de fichiers"""
    file = fields.Raw(
        required=True,
        error_messages={'required': 'Un fichier est requis'}
    )

    @validates('file')
    def validate_file(self, value):
        """Valider le fichier uploadé"""
        if not hasattr(value, 'filename') or not value.filename:
            raise ValidationError('Nom de fichier manquant')

        # Liste des extensions autorisées
        allowed_extensions = {'pdf', 'png', 'jpg', 'jpeg', 'ai', 'eps', 'zip', 'doc', 'docx'}

        # Obtenir l'extension
        filename = value.filename.lower()
        extension = filename.split('.')[-1] if '.' in filename else ''

        if extension not in allowed_extensions:
            raise ValidationError(f'Extension de fichier non autorisée. Extensions acceptées: {", ".join(allowed_extensions)}')

        # Vérifier la taille (50MB max)
        max_size = 50 * 1024 * 1024  # 50MB
        if hasattr(value, 'seek') and hasattr(value, 'tell'):
            current_pos = value.tell()
            value.seek(0, 2)  # Aller à la fin
            file_size = value.tell()
            value.seek(current_pos)  # Retour à la position initiale

            if file_size > max_size:
                raise ValidationError('Fichier trop volumineux (50MB maximum)')

class PromoCodeSchema(Schema):
    """Schéma de validation pour les codes promo"""
    code = fields.String(
        required=True,
        validate=[
            Length(min=2, max=20),
            Regexp(r'^[A-Z0-9]+$', error='Le code promo ne peut contenir que des lettres majuscules et des chiffres')
        ],
        error_messages={'required': 'Le code promo est requis'}
    )
    discount_type = fields.String(
        required=True,
        validate=OneOf(['percentage', 'fixed_amount']),
        error_messages={'required': 'Le type de remise est requis'}
    )
    discount_value = fields.Float(
        required=True,
        validate=Range(min=0),
        error_messages={'required': 'La valeur de remise est requise'}
    )
    min_order_amount = fields.Float(
        validate=Range(min=0),
        allow_none=True
    )
    max_uses = fields.Integer(
        validate=Range(min=1),
        allow_none=True
    )
    valid_from = fields.DateTime(allow_none=True)
    valid_until = fields.DateTime(allow_none=True)

    @validates('valid_until')
    def validate_date_range(self, value):
        """Vérifier que la date de fin est après la date de début"""
        if hasattr(self, 'valid_from') and self.valid_from and value:
            if value <= self.valid_from:
                raise ValidationError('La date de fin doit être après la date de début')

class PaymentIntentSchema(Schema):
    """Schéma de validation pour les intentions de paiement"""
    amount = fields.Integer(
        required=True,
        validate=Range(min=100),  # Minimum 100 FCFA
        error_messages={'required': 'Le montant est requis'}
    )
    currency = fields.String(
        validate=OneOf(['xof']),
        missing='xof'
    )
    order_id = fields.String(
        validate=Length(max=100),
        allow_none=True
    )
    customer_email = fields.Email(
        validate=Email(),
        allow_none=True
    )

class SystemConfigSchema(Schema):
    """Schéma de validation pour la configuration système"""
    key = fields.String(
        required=True,
        validate=[
            Length(min=1, max=100),
            Regexp(r'^[A-Z_][A-Z0-9_]*$', error='La clé doit être en majuscules avec des underscores')
        ],
        error_messages={'required': 'La clé est requise'}
    )
    value = fields.Raw(
        required=True,
        error_messages={'required': 'La valeur est requise'}
    )
    description = fields.String(
        validate=Length(max=255),
        allow_none=True
    )
    data_type = fields.String(
        validate=OneOf(['string', 'int', 'float', 'bool', 'json']),
        missing='string'
    )
    is_sensitive = fields.Boolean(missing=False)

class PaginationSchema(Schema):
    """Schéma de validation pour la pagination"""
    page = fields.Integer(
        validate=Range(min=1),
        missing=1
    )
    per_page = fields.Integer(
        validate=Range(min=1, max=100),
        missing=20
    )
    sort_by = fields.String(
        validate=Length(max=50),
        allow_none=True
    )
    sort_order = fields.String(
        validate=OneOf(['asc', 'desc']),
        missing='asc'
    )

class FilterSchema(Schema):
    """Schéma de base pour les filtres"""
    def __init__(self, allowed_filters=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allowed_filters = allowed_filters or []

    def validate_filters(self, data, **kwargs):
        """Valider que seuls les filtres autorisés sont utilisés"""
        if self.allowed_filters:
            for key in data.keys():
                if key not in self.allowed_filters and key not in ['page', 'per_page', 'sort_by', 'sort_order']:
                    raise ValidationError(f'Filtre non autorisé: {key}')

# Schémas composites pour les requêtes complexes
class ProductFilterSchema(FilterSchema):
    """Schéma de validation pour les filtres de produits"""
    category = fields.String(
        validate=OneOf(['print', 'supplies', 'usb', 'other']),
        allow_none=True
    )
    min_price = fields.Float(
        validate=Range(min=0),
        allow_none=True
    )
    max_price = fields.Float(
        validate=Range(min=0),
        allow_none=True
    )
    in_stock = fields.Boolean(allow_none=True)

    def __init__(self, *args, **kwargs):
        super().__init__(
            allowed_filters=['category', 'min_price', 'max_price', 'in_stock'],
            *args, **kwargs
        )

class OrderFilterSchema(FilterSchema):
    """Schéma de validation pour les filtres de commandes"""
    status = fields.String(
        validate=OneOf(['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']),
        allow_none=True
    )
    payment_status = fields.String(
        validate=OneOf(['pending', 'paid', 'failed', 'refunded']),
        allow_none=True
    )
    customer_id = fields.Integer(
        validate=Range(min=1),
        allow_none=True
    )
    date_from = fields.DateTime(allow_none=True)
    date_to = fields.DateTime(allow_none=True)

    def __init__(self, *args, **kwargs):
        super().__init__(
            allowed_filters=['status', 'payment_status', 'customer_id', 'date_from', 'date_to'],
            *args, **kwargs
        )

    @validates('date_to')
    def validate_date_range(self, value):
        """Vérifier que date_to est après date_from"""
        if hasattr(self, 'date_from') and self.date_from and value:
            if value <= self.date_from:
                raise ValidationError('La date de fin doit être après la date de début')

# Fonctions utilitaires pour la validation
def validate_data(schema_class, data, partial=False):
    """
    Valider les données avec un schéma Marshmallow

    Args:
        schema_class: Classe du schéma à utiliser
        data: Données à valider
        partial: Validation partielle (pour les mises à jour)

    Returns:
        dict: Données validées ou erreurs
    """
    try:
        schema = schema_class(partial=partial)
        validated_data = schema.load(data)
        return {'valid': True, 'data': validated_data}
    except ValidationError as e:
        return {'valid': False, 'errors': e.messages}

def serialize_data(schema_class, data, many=False):
    """
    Sérialiser les données avec un schéma Marshmallow

    Args:
        schema_class: Classe du schéma à utiliser
        data: Données à sérialiser
        many: Sérialisation de plusieurs éléments

    Returns:
        dict: Données sérialisées
    """
    try:
        schema = schema_class()
        return schema.dump(data, many=many)
    except Exception as e:
        return {'error': f'Erreur de sérialisation: {str(e)}'}

# Schémas pour les réponses API
class APIResponseSchema(Schema):
    """Schéma de base pour les réponses API"""
    message = fields.String()
    data = fields.Raw(allow_none=True)
    errors = fields.Raw(allow_none=True)
    pagination = fields.Nested({
        'page': fields.Integer(),
        'per_page': fields.Integer(),
        'total': fields.Integer(),
        'pages': fields.Integer()
    }, allow_none=True)

class ErrorResponseSchema(Schema):
    """Schéma pour les réponses d'erreur"""
    error = fields.String(required=True)
    code = fields.String(allow_none=True)
    details = fields.Raw(allow_none=True)

# Exemple d'utilisation dans les contrôleurs
def validate_request(schema_class, request_data, partial=False):
    """
    Fonction utilitaire pour valider les requêtes dans les contrôleurs

    Args:
        schema_class: Classe du schéma de validation
        request_data: Données de la requête
        partial: Validation partielle

    Returns:
        tuple: (données_validées, erreurs)
    """
    validation_result = validate_data(schema_class, request_data, partial)

    if not validation_result['valid']:
        return None, validation_result['errors']

    return validation_result['data'], None

if __name__ == "__main__":
    print("✅ Schémas de validation PassPrint configurés")

    # Exemple de validation
    user_data = {
        'email': 'test@example.com',
        'password': 'TestPassword123!',
        'first_name': 'John',
        'last_name': 'Doe'
    }

    result = validate_data(UserRegistrationSchema, user_data)
    if result['valid']:
        print("✅ Données utilisateur validées")
    else:
        print(f"❌ Erreurs de validation: {result['errors']}")