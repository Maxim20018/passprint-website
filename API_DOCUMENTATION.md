# 📚 API Documentation - PassPrint

## Table of Contents

1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Endpoints Reference](#endpoints-reference)
4. [Request/Response Formats](#requestresponse-formats)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [Pagination](#pagination)
8. [Filtering and Sorting](#filtering-and-sorting)
9. [Webhooks](#webhooks)
10. [SDK Examples](#sdk-examples)
11. [Testing the API](#testing-the-api)

## API Overview

PassPrint provides a comprehensive REST API for integrating with the printing services platform.

### Base URL

```bash
# Production
https://api.passprint.com/v1/

# Development
http://localhost:5000/api/
```

### API Versions

- **Current Version**: v1.0
- **Content-Type**: `application/json`
- **Authentication**: JWT Bearer tokens

### Key Features

- 🔐 **Secure Authentication** with JWT tokens
- 📊 **Real-time Monitoring** and metrics
- 🚀 **High Performance** with caching and optimization
- 🛡️ **Enterprise Security** with rate limiting and validation
- 📈 **Comprehensive Analytics** and reporting
- 🔄 **Background Processing** with Celery integration

## Authentication

### Getting an Access Token

```bash
# 1. Register a new user
curl -X POST https://api.passprint.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+2250102030405",
    "company": "Example Corp"
  }'

# 2. Login to get JWT token
curl -X POST https://api.passprint.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }'

# Response:
{
  "message": "Connexion réussie",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_admin": false
  },
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Using the Token

```bash
# Include token in Authorization header
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://api.passprint.com/api/products

# Or use the token in requests
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  https://api.passprint.com/api/orders
```

### Token Verification

```bash
# Verify token validity
curl -X POST https://api.passprint.com/api/auth/verify \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Response:
{
  "valid": true,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

## Endpoints Reference

### Authentication Endpoints

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+2250102030405",
  "company": "Example Corp"
}
```

**Response (201):**
```json
{
  "message": "Utilisateur créé avec succès",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+2250102030405",
    "company": "Example Corp",
    "is_admin": false,
    "created_at": "2025-01-04T10:00:00Z"
  },
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### User Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200):**
```json
{
  "message": "Connexion réussie",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_admin": false
  },
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Change Password
```http
POST /api/auth/change-password
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "current_password": "oldpassword",
  "new_password": "NewSecurePassword123!"
}
```

**Response (200):**
```json
{
  "message": "Mot de passe changé avec succès"
}
```

### Product Endpoints

#### List Products
```http
GET /api/products?page=1&per_page=20&category=print&sort_by=price&sort_order=asc
```

**Query Parameters:**
- `page` (integer): Page number (default: 1)
- `per_page` (integer): Items per page (default: 20, max: 100)
- `category` (string): Filter by category (print, supplies, usb, other)
- `min_price` (float): Minimum price filter
- `max_price` (float): Maximum price filter
- `in_stock` (boolean): Only show in-stock products
- `sort_by` (string): Sort field (name, price, created_at)
- `sort_order` (string): Sort order (asc, desc)

**Response (200):**
```json
{
  "products": [
    {
      "id": 1,
      "name": "Carte de visite standard",
      "description": "Carte de visite 300g couché mat",
      "price": 25000,
      "category": "print",
      "stock_quantity": 100,
      "image_url": "https://example.com/image.jpg",
      "is_active": true,
      "created_at": "2025-01-04T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "pages": 8
  }
}
```

#### Get Product Details
```http
GET /api/products/{product_id}
```

**Response (200):**
```json
{
  "id": 1,
  "name": "Carte de visite standard",
  "description": "Carte de visite 300g couché mat",
  "price": 25000,
  "category": "print",
  "stock_quantity": 100,
  "image_url": "https://example.com/image.jpg",
  "is_active": true,
  "created_at": "2025-01-04T10:00:00Z"
}
```

### Order Endpoints

#### Create Order
```http
POST /api/orders
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "customer_id": 1,
  "shipping_address": "123 Main Street, Abidjan, Côte d'Ivoire",
  "shipping_phone": "+2250102030405",
  "shipping_email": "customer@example.com",
  "notes": "Livraison urgente"
}
```

**Response (201):**
```json
{
  "message": "Commande créée avec succès",
  "order": {
    "id": 1,
    "order_number": "PP20250104120001",
    "customer_id": 1,
    "total_amount": 50000,
    "status": "pending",
    "payment_status": "pending",
    "shipping_address": "123 Main Street, Abidjan, Côte d'Ivoire",
    "shipping_phone": "+2250102030405",
    "shipping_email": "customer@example.com",
    "notes": "Livraison urgente",
    "created_at": "2025-01-04T12:00:01Z",
    "items": [
      {
        "id": 1,
        "product_id": 1,
        "product_name": "Carte de visite standard",
        "quantity": 2,
        "unit_price": 25000,
        "total_price": 50000
      }
    ]
  }
}
```

#### Get Order Details
```http
GET /api/orders/{order_number}
```

**Response (200):**
```json
{
  "id": 1,
  "order_number": "PP20250104120001",
  "customer_id": 1,
  "total_amount": 50000,
  "status": "confirmed",
  "payment_status": "paid",
  "shipping_address": "123 Main Street, Abidjan, Côte d'Ivoire",
  "shipping_phone": "+2250102030405",
  "shipping_email": "customer@example.com",
  "notes": "Livraison urgente",
  "created_at": "2025-01-04T12:00:01Z",
  "items": [...]
}
```

### Quote Endpoints

#### Create Quote
```http
POST /api/quotes
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json

{
  "project_name": "Brochures entreprise",
  "project_description": "Brochures A4 pour présentation entreprise",
  "project_type": "print",
  "format": "A4",
  "quantity": 1000,
  "material": "Couché 150g",
  "finishing": "Mat",
  "estimated_price": 150000
}
```

**Response (201):**
```json
{
  "message": "Devis créé avec succès",
  "quote": {
    "id": 1,
    "quote_number": "DEV20250104120001",
    "customer_id": 1,
    "project_name": "Brochures entreprise",
    "project_description": "Brochures A4 pour présentation entreprise",
    "project_type": "print",
    "format": "A4",
    "quantity": 1000,
    "material": "Couché 150g",
    "finishing": "Mat",
    "estimated_price": 150000,
    "status": "draft",
    "valid_until": "2025-02-03T12:00:01Z",
    "created_at": "2025-01-04T12:00:01Z"
  }
}
```

### Cart Endpoints

#### Get Cart
```http
GET /api/cart
Session-ID: your-session-id
```

**Response (200):**
```json
{
  "items": [
    {
      "product_id": 1,
      "name": "Carte de visite standard",
      "price": 25000,
      "quantity": 2,
      "specifications": {}
    }
  ],
  "total": 50000,
  "session_id": "your-session-id"
}
```

#### Add to Cart
```http
POST /api/cart
Session-ID: your-session-id
Content-Type: application/json

{
  "product_id": 1,
  "quantity": 2,
  "specifications": {
    "format": "A4",
    "material": "Couché 300g"
  }
}
```

### File Upload Endpoints

#### Upload File
```http
POST /api/upload
Content-Type: multipart/form-data

file: (binary file data)
```

**Response (201):**
```json
{
  "message": "Fichier uploadé avec succès",
  "file": {
    "id": 1,
    "filename": "unique_filename.pdf",
    "original_filename": "document.pdf",
    "file_path": "/uploads/unique_filename.pdf",
    "file_size": 1024000,
    "file_type": "pdf",
    "mime_type": "application/pdf",
    "uploaded_at": "2025-01-04T12:00:01Z"
  }
}
```

### Payment Endpoints

#### Create Payment Intent
```http
POST /api/create-payment-intent
Content-Type: application/json

{
  "amount": 50000,
  "currency": "xof",
  "order_id": "PP20250104120001",
  "customer_email": "customer@example.com"
}
```

**Response (200):**
```json
{
  "client_secret": "pi_xxx_secret_xxx",
  "payment_intent_id": "pi_xxx"
}
```

### Newsletter Endpoints

#### Subscribe to Newsletter
```http
POST /api/newsletter/subscribe
Content-Type: application/json

{
  "email": "subscriber@example.com",
  "first_name": "Newsletter",
  "last_name": "Subscriber"
}
```

**Response (201):**
```json
{
  "message": "Inscription à la newsletter réussie",
  "subscriber": {
    "id": 1,
    "email": "subscriber@example.com",
    "first_name": "Newsletter",
    "last_name": "Subscriber",
    "subscribed_at": "2025-01-04T12:00:01Z",
    "is_active": true,
    "source": "website"
  }
}
```

### Admin Endpoints

#### Get Dashboard Statistics
```http
GET /api/admin/dashboard
Authorization: Bearer ADMIN_JWT_TOKEN
```

**Response (200):**
```json
{
  "stats": {
    "total_users": 1250,
    "total_orders": 890,
    "total_products": 45,
    "total_quotes": 234,
    "pending_orders": 12,
    "monthly_revenue": 15000000,
    "out_of_stock": 3
  },
  "recent_orders": [...]
}
```

#### Manage Products (Admin)
```http
POST /api/admin/products
Authorization: Bearer ADMIN_JWT_TOKEN
Content-Type: application/json

{
  "name": "Nouveau produit",
  "description": "Description du produit",
  "price": 35000,
  "category": "print",
  "stock_quantity": 50,
  "is_active": true
}
```

## Request/Response Formats

### Content Types

- **Requests**: `application/json`
- **File Uploads**: `multipart/form-data`
- **Responses**: `application/json`

### Date Formats

All timestamps use ISO 8601 format:
```json
{
  "created_at": "2025-01-04T10:00:00Z",
  "updated_at": "2025-01-04T10:30:00Z"
}
```

### Currency Format

All monetary values are in FCFA (XOF):
```json
{
  "price": 25000,
  "total_amount": 150000
}
```

### Pagination Format

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

## Error Handling

### Error Response Format

```json
{
  "error": "Description of the error",
  "code": "ERROR_CODE",
  "details": {
    "field": "specific_field",
    "message": "Field-specific error message"
  }
}
```

### Common HTTP Status Codes

- **200**: Success
- **201**: Created
- **400**: Bad Request (invalid data)
- **401**: Unauthorized (invalid/missing token)
- **403**: Forbidden (insufficient permissions)
- **404**: Not Found
- **409**: Conflict (duplicate data)
- **422**: Unprocessable Entity (validation errors)
- **423**: Locked (account locked)
- **429**: Too Many Requests (rate limited)
- **500**: Internal Server Error

### Error Examples

#### Validation Error
```json
HTTP 400 Bad Request
{
  "error": "Données invalides",
  "code": "VALIDATION_ERROR",
  "details": {
    "email": "Format d'email invalide",
    "password": "Le mot de passe doit contenir au moins 8 caractères"
  }
}
```

#### Authentication Error
```json
HTTP 401 Unauthorized
{
  "error": "Token invalide ou expiré",
  "code": "INVALID_TOKEN"
}
```

#### Rate Limiting Error
```json
HTTP 429 Too Many Requests
{
  "error": "Limite de taux dépassée",
  "code": "RATE_LIMIT_EXCEEDED",
  "details": {
    "limit": 100,
    "window": 3600,
    "reset_time": "2025-01-04T11:00:00Z"
  }
}
```

## Rate Limiting

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1609459200
```

### Rate Limit Categories

- **Authentication**: 5 requests/minute
- **API General**: 100 requests/minute
- **File Upload**: 10 requests/minute
- **Admin Operations**: 50 requests/minute

## Pagination

### Query Parameters

```http
GET /api/products?page=2&per_page=50&sort_by=name&sort_order=desc
```

### Pagination Response

```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "per_page": 50,
    "total": 1000,
    "pages": 20,
    "has_next": true,
    "has_prev": true,
    "next_page": 3,
    "prev_page": 1
  }
}
```

## Filtering and Sorting

### Filtering Examples

```bash
# Filter by category
GET /api/products?category=print

# Filter by price range
GET /api/products?min_price=10000&max_price=50000

# Filter by stock status
GET /api/products?in_stock=true

# Multiple filters
GET /api/products?category=print&min_price=10000&in_stock=true
```

### Sorting Examples

```bash
# Sort by price ascending
GET /api/products?sort_by=price&sort_order=asc

# Sort by name descending
GET /api/products?sort_by=name&sort_order=desc

# Sort by creation date
GET /api/products?sort_by=created_at&sort_order=desc
```

### Advanced Filtering

```bash
# Date range filtering
GET /api/orders?date_from=2025-01-01&date_to=2025-01-31

# Status filtering
GET /api/orders?status=pending,confirmed

# Multiple categories
GET /api/products?category=print,supplies
```

## Webhooks

### Webhook Configuration

Configure webhooks in your application settings:

```json
{
  "webhook_url": "https://your-app.com/webhooks/passprint",
  "events": [
    "order.created",
    "order.updated",
    "payment.succeeded",
    "payment.failed"
  ],
  "secret": "your-webhook-secret"
}
```

### Webhook Events

#### Order Events
- `order.created`: New order created
- `order.updated`: Order status changed
- `order.cancelled`: Order cancelled
- `order.shipped`: Order shipped

#### Payment Events
- `payment.succeeded`: Payment completed successfully
- `payment.failed`: Payment failed
- `payment.refunded`: Payment refunded

#### Quote Events
- `quote.created`: New quote created
- `quote.accepted`: Quote accepted by customer
- `quote.expired`: Quote expired

### Webhook Payload Example

```json
{
  "event": "order.created",
  "timestamp": "2025-01-04T12:00:01Z",
  "data": {
    "id": 1,
    "order_number": "PP20250104120001",
    "customer_id": 1,
    "total_amount": 50000,
    "status": "pending",
    "created_at": "2025-01-04T12:00:01Z"
  },
  "webhook_id": "wh_1234567890"
}
```

### Webhook Verification

```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    """Verify webhook signature"""
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)
```

## SDK Examples

### Python SDK

```python
# pip install passprint-api-client
from passprint import PassPrintClient

# Initialize client
client = PassPrintClient(
    api_key='your-api-key',
    base_url='https://api.passprint.com'
)

# Authenticate
auth_response = client.authenticate('user@example.com', 'password')
token = auth_response['token']

# Set token for subsequent requests
client.set_token(token)

# Get products
products = client.get_products(category='print', page=1)

# Create order
order_data = {
    'customer_id': 1,
    'shipping_address': '123 Main St',
    'shipping_phone': '+2250102030405'
}
order = client.create_order(order_data)

# Upload file
with open('document.pdf', 'rb') as f:
    file_response = client.upload_file(f, 'document.pdf')
```

### JavaScript SDK

```javascript
// npm install passprint-api-client
import PassPrintClient from 'passprint-api-client';

const client = new PassPrintClient({
  apiKey: 'your-api-key',
  baseURL: 'https://api.passprint.com'
});

// Authenticate
const authResponse = await client.authenticate('user@example.com', 'password');
client.setToken(authResponse.token);

// Get products
const products = await client.getProducts({
  category: 'print',
  page: 1
});

// Create order
const order = await client.createOrder({
  customerId: 1,
  shippingAddress: '123 Main St',
  shippingPhone: '+2250102030405'
});
```

### PHP SDK

```php
<?php
// composer require passprint/api-client
require_once 'vendor/autoload.php';

use PassPrint\Client;

$client = new Client([
    'api_key' => 'your-api-key',
    'base_url' => 'https://api.passprint.com'
]);

// Authenticate
$authResponse = $client->authenticate('user@example.com', 'password');
$client->setToken($authResponse['token']);

// Get products
$products = $client->getProducts([
    'category' => 'print',
    'page' => 1
]);

// Create order
$order = $client->createOrder([
    'customer_id' => 1,
    'shipping_address' => '123 Main St',
    'shipping_phone' => '+2250102030405'
]);
?>
```

## Testing the API

### Using cURL

```bash
# Health check
curl https://api.passprint.com/api/health

# Get products with authentication
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.passprint.com/api/products

# Create order
curl -X POST https://api.passprint.com/api/orders \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "shipping_address": "123 Main St",
    "shipping_phone": "+2250102030405"
  }'
```

### Using Postman

1. **Import the API Collection**
   - Download: https://api.passprint.com/api/openapi.json
   - Import into Postman

2. **Set Environment Variables**
   ```json
   {
     "base_url": "https://api.passprint.com",
     "token": "your-jwt-token"
   }
   ```

3. **Test Authentication**
   - POST {{base_url}}/api/auth/login
   - Set token variable from response

### Automated Testing

```python
# test_api.py
import requests
import pytest

class TestPassPrintAPI:
    def setup_method(self):
        self.base_url = "https://api.passprint.com"
        self.token = self.get_auth_token()

    def get_auth_token(self):
        response = requests.post(f"{self.base_url}/api/auth/login", json={
            'email': 'test@example.com',
            'password': 'password'
        })
        return response.json()['token']

    def test_get_products(self):
        response = requests.get(
            f"{self.base_url}/api/products",
            headers={'Authorization': f'Bearer {self.token}'}
        )

        assert response.status_code == 200
        data = response.json()
        assert 'products' in data
        assert 'pagination' in data

    def test_create_order(self):
        order_data = {
            'customer_id': 1,
            'shipping_address': '123 Test St',
            'shipping_phone': '+2250102030405'
        }

        response = requests.post(
            f"{self.base_url}/api/orders",
            headers={'Authorization': f'Bearer {self.token}'},
            json=order_data
        )

        assert response.status_code == 201
        data = response.json()
        assert 'order' in data
        assert 'order_number' in data['order']
```

### API Testing Tools

#### Using pytest

```bash
# Install test dependencies
pip install pytest requests

# Run API tests
pytest test_api.py -v

# Run with coverage
pytest test_api.py --cov=requests --cov-report=html
```

#### Using Newman (Postman CLI)

```bash
# Install Newman
npm install -g newman

# Run Postman collection
newman run PassPrint_API_Collection.json \
  --environment PassPrint_Environment.json \
  --reporters cli,json \
  --reporter-json-export results.json
```

## Best Practices

### API Usage Guidelines

1. **Always use HTTPS** in production
2. **Store tokens securely** and rotate regularly
3. **Handle rate limits** gracefully
4. **Validate responses** before processing
5. **Use pagination** for large datasets
6. **Cache frequently accessed data**
7. **Monitor API usage** and performance
8. **Handle errors** appropriately

### Security Considerations

1. **Token Storage**: Store JWT tokens securely (httpOnly cookies)
2. **Token Expiration**: Handle token refresh automatically
3. **Input Validation**: Always validate API responses
4. **Error Handling**: Don't expose sensitive information in errors
5. **Rate Limiting**: Implement client-side rate limiting
6. **Logging**: Log API calls for debugging (without sensitive data)

### Performance Optimization

1. **Use Caching**: Cache product lists and static data
2. **Batch Requests**: Combine multiple operations when possible
3. **Pagination**: Use appropriate page sizes
4. **Compression**: Enable gzip compression
5. **Connection Reuse**: Use connection pooling
6. **Async Processing**: Use async/await for multiple requests

## Support

### Getting Help

1. **API Documentation**: https://api.passprint.com/docs
2. **Interactive Testing**: https://api.passprint.com/docs
3. **GitHub Issues**: https://github.com/passprint/api/issues
4. **Email Support**: api-support@passprint.com

### Rate Limits

- **Free Tier**: 1,000 requests/hour
- **Pro Tier**: 10,000 requests/hour
- **Enterprise Tier**: 100,000 requests/hour

### SLA

- **Uptime**: 99.9% monthly
- **Response Time**: <500ms average
- **Support Response**: <24 hours

## Changelog

### Version 1.0.0
- Initial API release
- Authentication and authorization
- Product and order management
- File upload capabilities
- Payment processing
- Newsletter management
- Admin dashboard API

### Upcoming Features
- Real-time notifications
- Advanced analytics
- Multi-language support
- Mobile API optimization
- WebSocket support

---

For more information, visit the [API Documentation Portal](https://api.passprint.com/docs) or contact our developer support team.