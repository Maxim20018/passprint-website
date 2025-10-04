# 👨‍💻 Development Guide - PassPrint

## Table of Contents

1. [Development Setup](#development-setup)
2. [Project Structure](#project-structure)
3. [Code Organization](#code-organization)
4. [Development Workflow](#development-workflow)
5. [Testing Guidelines](#testing-guidelines)
6. [Code Quality](#code-quality)
7. [Performance Development](#performance-development)
8. [Security Development](#security-development)
9. [Database Development](#database-development)
10. [API Development](#api-development)
11. [Frontend Integration](#frontend-integration)
12. [Deployment Development](#deployment-development)

## Development Setup

### Prerequisites

**Required Software:**
- **Python 3.9+**: Main development language
- **PostgreSQL 13+**: Development database
- **Redis 5.0+**: Caching and background jobs
- **Git**: Version control
- **Docker**: Containerization (optional)
- **Node.js 16+**: Frontend development (optional)

**Development Tools:**
- **PyCharm** or **VSCode**: IDE
- **Postman** or **Insomnia**: API testing
- **pgAdmin**: Database management
- **Redis Desktop Manager**: Redis management

### Environment Setup

1. **Clone Repository**
```bash
git clone https://github.com/your-org/passprint.git
cd passprint
```

2. **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**
```bash
# Install main dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r tests/requirements.txt

# Install in development mode
pip install -e .
```

4. **Configure Environment**
```bash
# Copy development environment
cp .env.example .env

# Edit with development settings
nano .env
```

**Development Environment Variables:**
```bash
FLASK_ENV=development
DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=dev-jwt-secret-key
DATABASE_URL=sqlite:///passprint_dev.db
REDIS_URL=redis://localhost:6379/0
```

5. **Initialize Database**
```bash
# Create database tables
python init_db.py

# Run migrations
python -c "from app import create_app; app = create_app(); app.app_context().push(); from models import db; db.create_all()"
```

6. **Start Development Server**
```bash
# Start the application
python app.py

# Or use Flask CLI
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

### Development Services

**Start Required Services:**
```bash
# Start Redis
redis-server

# Start PostgreSQL (if using)
sudo systemctl start postgresql

# Start background workers
python -c "from celery_tasks import celery_app; celery_app.start()"

# Start monitoring
python monitoring_alerting.py
```

## Project Structure

### Directory Organization

```
passprint/
├── app.py                 # Main application entry point
├── models.py              # Database models and schemas
├── config.py              # Configuration management
├── requirements.txt       # Production dependencies
├── .env                   # Environment variables
│
├── api_docs.py            # API documentation and routes
├── validation_schemas.py  # Input validation schemas
├── logging_config.py      # Logging configuration
├── security_system.py     # Security implementation
├── backup_system.py       # Backup and recovery system
├── disaster_recovery.py   # Disaster recovery procedures
├── postgresql_backup.py   # PostgreSQL backup strategies
├── database_optimizer.py  # Database performance optimization
├── performance_optimizer.py # Performance optimization
├── load_testing.py        # Load testing framework
├── monitoring_alerting.py # Monitoring and alerting
├── monitoring_config.py   # Monitoring integrations
├── cdn_config.py          # CDN configuration
├── celery_tasks.py        # Background job processing
├── redis_cache.py         # Caching implementation
│
├── tests/                 # Test suite
│   ├── __init__.py        # Test configuration
│   ├── conftest.py        # Pytest fixtures
│   ├── test_*.py          # Test files
│   └── requirements.txt    # Test dependencies
│
├── migrations/            # Database migrations
│   └── versions/          # Migration files
│
├── recovery_scripts/      # Disaster recovery scripts
├── logs/                  # Application logs
├── backups/               # Database and file backups
├── uploads/               # User uploaded files
├── temp/                  # Temporary files
└── static/                # Static assets
```

### Code Organization

#### Models (`models.py`)
- Database models with relationships
- Serialization methods
- Validation constraints
- Business logic methods

#### Configuration (`config.py`)
- Environment-specific settings
- Feature flags
- Third-party service configurations
- Security settings

#### API Layer (`api_docs.py`)
- REST API endpoints
- Request/response handling
- Authentication middleware
- Rate limiting

#### Business Logic
- **Pricing Engine**: `pricing_engine.py`
- **Promotion Engine**: `promo_engine.py`
- **Stock Manager**: `stock_manager.py`
- **Notification System**: `notifications_system.py`

#### Infrastructure
- **Security**: `security_system.py`
- **Monitoring**: `monitoring_*.py`
- **Backup**: `backup_system.py`, `disaster_recovery.py`
- **Performance**: `*_optimizer.py`

## Development Workflow

### Git Workflow

**Branch Strategy:**
```bash
# Create feature branch
git checkout -b feature/amazing-feature

# Develop feature
# Make changes, add tests, update documentation

# Commit changes
git add .
git commit -m "Add amazing feature"

# Push branch
git push origin feature/amazing-feature

# Create pull request
# Code review and testing
# Merge to main
```

**Commit Guidelines:**
```bash
# Format: [Type] Brief description

[FEAT] Add user authentication system
[FIX] Resolve database connection timeout
[DOCS] Update API documentation
[TEST] Add integration tests for payments
[REFACTOR] Optimize database queries
[SECURITY] Implement CSRF protection
[PERF] Add caching for product listings
```

### Development Cycle

1. **Feature Planning**
   - Create GitHub issue
   - Define requirements
   - Plan implementation approach

2. **Development**
   - Create feature branch
   - Implement functionality
   - Add tests
   - Update documentation

3. **Testing**
   - Run unit tests
   - Run integration tests
   - Test manually
   - Performance testing

4. **Code Review**
   - Submit pull request
   - Address review comments
   - Update code as needed

5. **Deployment**
   - Merge to main branch
   - Deploy to staging
   - Test in staging environment
   - Deploy to production

### Code Review Checklist

- [ ] **Functionality**: Does it work as expected?
- [ ] **Tests**: Are tests included and passing?
- [ ] **Documentation**: Is it properly documented?
- [ ] **Security**: Are security considerations addressed?
- [ ] **Performance**: Are performance implications considered?
- [ ] **Error Handling**: Are errors handled properly?
- [ ] **Logging**: Are important events logged?
- [ ] **Code Style**: Follows project conventions?
- [ ] **Dependencies**: Are new dependencies justified?
- [ ] **Backwards Compatibility**: Does it break existing functionality?

## Testing Guidelines

### Testing Structure

#### Unit Tests
```python
# tests/test_example.py
import pytest
from app import create_app
from models import User

class TestUserModel:
    def test_user_creation(self, db):
        user = User(email='test@example.com', first_name='Test')
        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.email == 'test@example.com'
```

#### Integration Tests
```python
class TestUserAPI:
    def test_user_registration(self, client):
        response = client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'password123',
            'first_name': 'Test',
            'last_name': 'User'
        })

        assert response.status_code == 201
        data = response.get_json()
        assert 'token' in data
```

#### Performance Tests
```python
class TestPerformance:
    @pytest.mark.performance
    def test_api_response_time(self, client):
        import time

        start_time = time.time()
        response = client.get('/api/products')
        end_time = time.time()

        assert response.status_code == 200
        assert end_time - start_time < 1.0  # Should respond in < 1 second
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run only unit tests
pytest -m unit

# Run performance tests
pytest -m performance

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_auth.py::TestAuthentication::test_user_registration_success
```

### Test Data Management

#### Fixtures
```python
# tests/conftest.py
@pytest.fixture
def sample_user(db):
    user = User(
        email='test@example.com',
        first_name='Test',
        last_name='User'
    )
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def authenticated_client(client, sample_user):
    # Login and return authenticated client
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'password'
    })
    token = response.get_json()['token']

    client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {token}'
    return client
```

#### Test Data Factory
```python
# tests/factories.py
class UserFactory:
    @staticmethod
    def create_user(**kwargs):
        defaults = {
            'email': 'user@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
        defaults.update(kwargs)
        return User(**defaults)

    @staticmethod
    def create_admin_user(**kwargs):
        defaults = {
            'email': 'admin@example.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'is_admin': True
        }
        defaults.update(kwargs)
        return User(**defaults)
```

## Code Quality

### Code Style

**Python Style Guide:**
- Follow **PEP 8** conventions
- Use **Black** for code formatting
- Use **isort** for import sorting
- Use **flake8** for linting

**Configuration:**
```ini
# .flake8
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,migrations,venv

# setup.cfg
[isort]
profile = black
line_length = 88
known_first_party = app
```

### Type Hints

```python
# Good: With type hints
def create_user(email: str, first_name: str, last_name: str) -> User:
    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name
    )
    return user

# Bad: Without type hints
def create_user(email, first_name, last_name):
    user = User(email, first_name, last_name)
    return user
```

### Documentation

#### Docstrings
```python
def create_user(email: str, first_name: str, last_name: str) -> User:
    """
    Create a new user with the provided information.

    Args:
        email: User's email address
        first_name: User's first name
        last_name: User's last name

    Returns:
        User: The created user instance

    Raises:
        ValueError: If email is invalid
        IntegrityError: If email already exists

    Example:
        >>> user = create_user('user@example.com', 'John', 'Doe')
        >>> user.email
        'user@example.com'
    """
    pass
```

#### Module Documentation
```python
"""
User management module for PassPrint.

This module provides functionality for user authentication,
authorization, and profile management.

Classes:
    User: User model with authentication methods
    UserManager: User management utilities

Functions:
    create_user: Create a new user account
    authenticate_user: Authenticate user credentials
    generate_token: Generate JWT token for user
"""
```

### Code Quality Tools

#### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 22.10.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 5.0.4
    hooks:
      - id: flake8
```

#### GitHub Actions
```yaml
# .github/workflows/quality.yml
name: Code Quality

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install black isort flake8 mypy

      - name: Check formatting
        run: |
          black --check --diff .
          isort --check-only --diff .

      - name: Lint code
        run: flake8 .

      - name: Type check
        run: mypy app/
```

## Performance Development

### Performance Testing

#### Load Testing
```python
# performance_test.py
import time
import pytest
from load_testing import LoadTestEngine

class TestLoadPerformance:
    def test_api_under_load(self):
        """Test API performance under load"""
        engine = LoadTestEngine()

        # Run load test
        result = engine.run_comprehensive_load_test()

        # Assert performance requirements
        assert result['overall_summary']['avg_response_time'] < 1.0
        assert result['overall_summary']['success_rate'] > 0.95
```

#### Memory Testing
```python
class TestMemoryUsage:
    def test_no_memory_leaks(self):
        """Test for memory leaks"""
        from performance_optimizer import MemoryOptimizer

        optimizer = MemoryOptimizer()

        # Take initial snapshot
        initial = optimizer.take_memory_snapshot()

        # Perform operations
        for _ in range(100):
            # Simulate operations
            pass

        # Take final snapshot
        final = optimizer.take_memory_snapshot()

        # Check for significant memory increase
        memory_increase = final['rss_mb'] - initial['rss_mb']
        assert memory_increase < 50  # Less than 50MB increase
```

### Database Optimization

#### Query Optimization
```python
# Optimize database queries
from database_optimizer import profile_query

class OptimizedUserService:
    @profile_query("user_lookup")
    def get_user_by_email(self, email: str):
        # Use indexed query
        return User.query.filter_by(email=email).first()

    def get_users_with_orders(self):
        # Optimize with joins
        return User.query.join(Order).options(
            selectinload(User.orders)
        ).all()
```

#### Index Management
```python
# Create performance indexes
from database_optimizer import DatabaseOptimizer

def optimize_database_indexes():
    optimizer = DatabaseOptimizer()
    result = optimizer.create_optimization_indexes()

    if result['success']:
        print(f"Created {result['total_indexes']} indexes")
    else:
        print(f"Index creation failed: {result['errors']}")
```

### Caching Strategies

#### Cache Implementation
```python
# Implement caching for frequently accessed data
from redis_cache import cache_manager

class CachedProductService:
    def get_products(self, category: str = None):
        cache_key = f"products:{category or 'all'}"

        # Check cache first
        cached = cache_manager.get(cache_key, 'products')
        if cached:
            return cached

        # Fetch from database
        query = Product.query.filter_by(is_active=True)
        if category:
            query = query.filter_by(category=category)

        products = query.all()

        # Cache for 1 hour
        cache_manager.set(cache_key, products, ttl=3600, namespace='products')

        return products
```

#### Cache Invalidation
```python
# Invalidate cache when data changes
class ProductService:
    def update_product(self, product_id: int, data: dict):
        # Update product
        product = Product.query.get(product_id)
        product.name = data['name']
        db.session.commit()

        # Invalidate related caches
        from redis_cache import clear_cache
        clear_cache('products')

        # Log cache invalidation
        logger.info(f"Cache invalidated for product {product_id}")
```

## Security Development

### Security Testing

#### Authentication Testing
```python
class TestSecurity:
    def test_password_hashing(self):
        """Test password hashing security"""
        from security_system import generate_password_hash

        password = "SecurePassword123!"
        hashed = generate_password_hash(password)

        # Verify hash properties
        assert hashed != password
        assert len(hashed) > 20
        assert "$" in hashed  # bcrypt format

    def test_token_security(self):
        """Test JWT token security"""
        from app import generate_token

        token = generate_token(1)

        # Verify token format
        assert len(token) > 100
        assert "." in token  # JWT format
```

#### Input Validation Testing
```python
class TestInputValidation:
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        malicious_input = "'; DROP TABLE users; --"

        # Should not cause SQL errors
        response = client.post('/api/auth/login', json={
            'email': malicious_input,
            'password': 'password'
        })

        # Should return validation error, not SQL error
        assert response.status_code == 400

    def test_xss_prevention(self):
        """Test XSS prevention"""
        xss_input = "<script>alert('xss')</script>"

        response = client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'password',
            'first_name': xss_input,
            'last_name': 'User'
        })

        # Should sanitize or reject XSS input
        assert response.status_code in [201, 400]
```

### Security Code Review

#### Security Checklist
- [ ] Input validation and sanitization
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] CSRF protection
- [ ] Authentication and authorization
- [ ] Secure password storage
- [ ] Secure token handling
- [ ] Rate limiting
- [ ] Security headers
- [ ] Audit logging

#### Secure Coding Practices
```python
# Good: Parameterized queries
def get_user_by_email(email: str):
    return User.query.filter_by(email=email).first()

# Bad: String formatting
def get_user_by_email_bad(email: str):
    return User.query.filter(f"email = '{email}'").first()

# Good: Input validation
from validation_schemas import validate_data, UserRegistrationSchema

def register_user(data: dict):
    validation = validate_data(UserRegistrationSchema, data)
    if not validation['valid']:
        raise ValueError("Invalid data")

# Bad: No validation
def register_user_bad(data: dict):
    user = User(**data)  # Dangerous!
```

## Database Development

### Database Design

#### Model Development
```python
# models.py
class User(db.Model):
    """User model with proper relationships and constraints"""

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    company = db.Column(db.String(100), nullable=True)
    is_admin = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    orders = db.relationship('Order', back_populates='customer', lazy='dynamic')
    quotes = db.relationship('Quote', back_populates='customer', lazy='dynamic')

    def to_dict(self):
        """Serialize model to dictionary"""
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
```

#### Migration Development
```python
# migrations/versions/001_add_user_table.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table('user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=50), nullable=False),
        sa.Column('last_name', sa.String(length=50), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('company', sa.String(length=100), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # Create indexes
    op.create_index('ix_user_email', 'user', ['email'])
    op.create_index('ix_user_created_at', 'user', ['created_at'])

def downgrade():
    op.drop_index('ix_user_created_at', table_name='user')
    op.drop_index('ix_user_email', table_name='user')
    op.drop_table('user')
```

### Database Testing

#### Database Test Setup
```python
# tests/conftest.py
@pytest.fixture(scope='function')
def db(app):
    """Create and configure test database"""
    from models import db

    with app.app_context():
        db.create_all()

        # Create test data
        seed_test_data()

        yield db

        # Cleanup
        db.session.remove()
        db.drop_all()

def seed_test_data():
    """Create test data for development"""
    from models import User, Product

    # Create test users
    admin_user = User(
        email='admin@test.com',
        first_name='Admin',
        last_name='Test',
        is_admin=True
    )
    db.session.add(admin_user)

    # Create test products
    products = [
        Product(name='Test Product 1', price=10000, category='print'),
        Product(name='Test Product 2', price=20000, category='usb'),
    ]

    for product in products:
        db.session.add(product)

    db.session.commit()
```

## API Development

### API Endpoint Development

#### RESTful Design
```python
# api/products.py
from flask_restx import Namespace, Resource, fields

api = Namespace('products', description='Product operations')

product_model = api.model('Product', {
    'id': fields.Integer(readOnly=True),
    'name': fields.String(required=True),
    'description': fields.String,
    'price': fields.Float(required=True),
    'category': fields.String(required=True),
    'stock_quantity': fields.Integer,
    'is_active': fields.Boolean
})

@api.route('/')
class ProductList(Resource):
    @api.doc('list_products')
    @api.marshal_list_with(product_model)
    def get(self):
        """List all products"""
        return Product.query.filter_by(is_active=True).all()

    @api.doc('create_product')
    @api.expect(product_model)
    @api.marshal_with(product_model, code=201)
    def post(self):
        """Create a new product"""
        data = request.get_json()
        product = Product(**data)
        db.session.add(product)
        db.session.commit()
        return product, 201

@api.route('/<int:id>')
class ProductItem(Resource):
    @api.doc('get_product')
    @api.marshal_with(product_model)
    def get(self, id):
        """Get product by ID"""
        return Product.query.get_or_404(id)

    @api.doc('update_product')
    @api.expect(product_model)
    @api.marshal_with(product_model)
    def put(self, id):
        """Update product"""
        product = Product.query.get_or_404(id)
        data = request.get_json()

        for key, value in data.items():
            setattr(product, key, value)

        db.session.commit()
        return product
```

### API Testing

#### API Test Structure
```python
# tests/test_api_products.py
class TestProductAPI:
    def test_get_products(self, client):
        """Test GET /api/products"""
        response = client.get('/api/products')

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_create_product(self, client, admin_auth_headers):
        """Test POST /api/products"""
        product_data = {
            'name': 'New Product',
            'price': 15000,
            'category': 'print'
        }

        response = client.post('/api/products',
                             json=product_data,
                             headers=admin_auth_headers)

        assert response.status_code == 201
        data = response.get_json()
        assert data['name'] == 'New Product'

    def test_update_product(self, client, admin_auth_headers):
        """Test PUT /api/products/{id}"""
        # Create product first
        product = Product(name='Update Test', price=10000)
        db.session.add(product)
        db.session.commit()

        update_data = {'name': 'Updated Product', 'price': 12000}

        response = client.put(f'/api/products/{product.id}',
                            json=update_data,
                            headers=admin_auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data['name'] == 'Updated Product'
        assert data['price'] == 12000
```

## Frontend Integration

### API Integration

#### JavaScript API Client
```javascript
// js/api.js
class PassPrintAPI {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
        this.token = localStorage.getItem('passprint_token');
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        if (this.token) {
            config.headers.Authorization = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, config);

            if (response.status === 401) {
                // Token expired, redirect to login
                this.logout();
                return;
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}`);
            }

            return data;

        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    async login(email, password) {
        const data = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });

        this.token = data.token;
        localStorage.setItem('passprint_token', this.token);

        return data;
    }

    async getProducts(filters = {}) {
        const params = new URLSearchParams(filters);
        return this.request(`/products?${params}`);
    }

    async createOrder(orderData) {
        return this.request('/orders', {
            method: 'POST',
            body: JSON.stringify(orderData)
        });
    }

    logout() {
        this.token = null;
        localStorage.removeItem('passprint_token');
    }
}

// Export for use in other files
window.PassPrintAPI = PassPrintAPI;
```

#### React Integration
```jsx
// components/ProductList.jsx
import React, { useState, useEffect } from 'react';
import { PassPrintAPI } from '../api';

function ProductList() {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadProducts();
    }, []);

    const loadProducts = async () => {
        try {
            setLoading(true);
            const api = new PassPrintAPI();
            const data = await api.getProducts({ category: 'print' });
            setProducts(data.products);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error}</div>;

    return (
        <div className="product-list">
            {products.map(product => (
                <div key={product.id} className="product-card">
                    <h3>{product.name}</h3>
                    <p>{product.description}</p>
                    <span className="price">{product.price} FCFA</span>
                </div>
            ))}
        </div>
    );
}

export default ProductList;
```

## Deployment Development

### Development Deployment

#### Docker Development
```dockerfile
# Dockerfile.dev
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 5000

# Development command
CMD ["python", "app.py"]
```

#### Docker Compose Development
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  web:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "5000:5000"
    volumes:
      - .:/app
      - /app/venv
    environment:
      - FLASK_ENV=development
      - DATABASE_URL=postgresql://passprint:password@db:5432/passprint_dev
    depends_on:
      - db
      - redis

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=passprint_dev
      - POSTGRES_USER=passprint
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    volumes:
      - redis_dev_data:/data

volumes:
  postgres_dev_data:
  redis_dev_data:
```

### Production Deployment Development

#### CI/CD Pipeline
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements.txt

      - name: Run tests
        run: pytest --cov=app

      - name: Build application
        run: docker build -t passprint:latest .

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - name: Deploy to production
        run: |
          # Deploy using your deployment method
          echo "Deploying to production..."
```

### Development Tools

#### Development Scripts
```bash
#!/bin/bash
# scripts/dev.sh

case "$1" in
    "setup")
        echo "Setting up development environment..."
        python -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        python init_db.py
        echo "Setup complete!"
        ;;

    "test")
        echo "Running tests..."
        pytest -v
        ;;

    "lint")
        echo "Running linters..."
        black --check .
        isort --check-only .
        flake8 .
        ;;

    "format")
        echo "Formatting code..."
        black .
        isort .
        ;;

    "serve")
        echo "Starting development server..."
        python app.py
        ;;

    "monitor")
        echo "Starting monitoring..."
        python monitoring_alerting.py
        ;;

    *)
        echo "Usage: $0 {setup|test|lint|format|serve|monitor}"
        exit 1
        ;;
esac
```

#### Development Configuration
```python
# config/development.py
class DevelopmentConfig(Config):
    DEBUG = True
    DEVELOPMENT = True
    TESTING = False

    # Development database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///passprint_dev.db')

    # Development settings
    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0

    # Development logging
    LOG_LEVEL = 'DEBUG'

    # Disable CSRF in development
    WTF_CSRF_ENABLED = False

    # Development email
    MAIL_SUPPRESS_SEND = True
```

## Best Practices

### Development Best Practices

1. **Code Organization**
   - Keep functions small and focused
   - Use meaningful variable names
   - Follow PEP 8 conventions
   - Document complex logic

2. **Error Handling**
   - Handle exceptions appropriately
   - Provide meaningful error messages
   - Log errors with context
   - Don't expose sensitive information

3. **Security**
   - Validate all inputs
   - Use parameterized queries
   - Hash sensitive data
   - Implement proper authentication

4. **Performance**
   - Profile slow operations
   - Use caching appropriately
   - Optimize database queries
   - Monitor resource usage

5. **Testing**
   - Write tests for new functionality
   - Test edge cases
   - Use descriptive test names
   - Keep tests fast and isolated

### Development Workflow

1. **Plan**: Define requirements and approach
2. **Implement**: Write code with tests
3. **Test**: Run comprehensive tests
4. **Review**: Code review and feedback
5. **Deploy**: Deploy to staging first
6. **Monitor**: Monitor performance and errors

### Debugging

#### Debug Mode
```python
# Enable debug logging
import logging
logging.getLogger().setLevel(logging.DEBUG)

# Debug database queries
app.config['SQLALCHEMY_ECHO'] = True

# Debug template rendering
app.config['EXPLAIN_TEMPLATE_LOADING'] = True
```

#### Development Tools
```python
# Use Flask debugger
from flask import Flask
app = Flask(__name__)
app.config['DEBUG'] = True

# Use Werkzeug debugger
if __name__ == '__main__':
    app.run(debug=True)
```

## Advanced Development

### Custom Extensions

#### Flask Extensions
```python
# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
cors = CORS()

def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    cors.init_app(app)
```

### Middleware Development

#### Custom Middleware
```python
# middleware.py
class SecurityMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # Add security headers
        def custom_start_response(status, headers, exc_info=None):
            headers.append(('X-Content-Type-Options', 'nosniff'))
            headers.append(('X-Frame-Options', 'DENY'))
            return start_response(status, headers, exc_info)

        return self.app(environ, custom_start_response)

# Apply middleware
app.wsgi_app = SecurityMiddleware(app.wsgi_app)
```

### Plugin System

#### Extensible Architecture
```python
# plugins.py
class PluginManager:
    def __init__(self):
        self.plugins = {}

    def register_plugin(self, name: str, plugin_class):
        self.plugins[name] = plugin_class

    def get_plugin(self, name: str):
        return self.plugins.get(name)

# Usage
plugin_manager = PluginManager()
plugin_manager.register_plugin('payment', StripePaymentPlugin)
plugin_manager.register_plugin('notification', EmailNotificationPlugin)
```

## Performance Development

### Performance Profiling

#### Function Profiling
```python
# profile_code.py
import cProfile
import pstats
from functools import wraps

def profile_function(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()

        result = func(*args, **kwargs)

        profiler.disable()
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(20)

        return result
    return wrapper

@profile_function
def slow_function():
    # Your code here
    pass
```

#### Memory Profiling
```python
# memory_profile.py
from memory_profiler import profile

@profile
def memory_intensive_function():
    large_list = [i for i in range(100000)]
    return sum(large_list)
```

### Database Performance

#### Query Optimization
```python
# Optimize slow queries
class OptimizedQueryService:
    def get_products_with_cache(self, category: str = None):
        # Use caching for frequently accessed data
        cache_key = f"products:{category or 'all'}"

        cached = cache.get(cache_key)
        if cached:
            return cached

        # Optimized query with indexes
        query = Product.query.filter_by(is_active=True)
        if category:
            query = query.filter_by(category=category)

        # Use selectinload for relationships
        products = query.options(selectinload(Product.reviews)).all()

        cache.set(cache_key, products, ttl=3600)
        return products
```

## Security Development

### Security Testing

#### Security Test Suite
```python
# tests/test_security.py
class TestSecurity:
    def test_password_security(self):
        """Test password security measures"""
        from security_system import generate_password_hash, check_password_hash

        password = "SecurePassword123!"
        hashed = generate_password_hash(password)

        # Test password verification
        assert check_password_hash(hashed, password)
        assert not check_password_hash(hashed, "wrongpassword")

        # Test hash uniqueness
        hashed2 = generate_password_hash(password)
        assert hashed != hashed2

    def test_input_sanitization(self):
        """Test input sanitization"""
        from security_system import sanitize_input

        malicious_input = {
            'name': '<script>alert("xss")</script>',
            'description': 'Normal text'
        }

        sanitized = sanitize_input(malicious_input)

        # Should remove or escape malicious content
        assert '<script>' not in sanitized['name']
        assert sanitized['description'] == 'Normal text'
```

### Security Headers

#### Security Middleware
```python
# security_middleware.py
class SecurityHeadersMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        def custom_start_response(status, headers, exc_info=None):
            # Add security headers
            security_headers = [
                ('X-Content-Type-Options', 'nosniff'),
                ('X-Frame-Options', 'DENY'),
                ('X-XSS-Protection', '1; mode=block'),
                ('Strict-Transport-Security', 'max-age=31536000; includeSubDomains'),
                ('Content-Security-Policy', "default-src 'self'"),
                ('Referrer-Policy', 'strict-origin-when-cross-origin')
            ]

            for header, value in security_headers:
                headers.append((header, value))

            return start_response(status, headers, exc_info)

        return self.app(environ, custom_start_response)
```

## Integration Development

### Third-Party Integrations

#### Payment Integration
```python
# integrations/stripe.py
class StripeIntegration:
    def __init__(self, api_key: str):
        import stripe
        self.stripe = stripe
        self.stripe.api_key = api_key

    def create_payment_intent(self, amount: int, currency: str = 'xof'):
        """Create Stripe payment intent"""
        try:
            intent = self.stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                metadata={'integration': 'passprint'}
            )
            return intent
        except self.stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            raise

    def confirm_payment(self, payment_intent_id: str):
        """Confirm payment"""
        try:
            intent = self.stripe.PaymentIntent.retrieve(payment_intent_id)
            return intent.status == 'succeeded'
        except self.stripe.error.StripeError as e:
            logger.error(f"Payment confirmation error: {e}")
            raise
```

#### Email Integration
```python
# integrations/email.py
class EmailIntegration:
    def __init__(self, smtp_config: dict):
        self.smtp_config = smtp_config

    def send_email(self, to: str, subject: str, html_content: str):
        """Send email via SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_config['username']
            msg['To'] = to

            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            with smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port']) as server:
                server.starttls()
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)

            return True

        except Exception as e:
            logger.error(f"Email sending error: {e}")
            raise
```

## Development Tools

### Development Scripts

#### Setup Script
```bash
#!/bin/bash
# scripts/setup_dev.sh

echo "Setting up development environment..."

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r tests/requirements.txt

# Setup pre-commit hooks
pre-commit install

# Initialize database
python init_db.py

# Create .env file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

echo "Development environment setup complete!"
echo "Run 'source venv/bin/activate' to activate the environment"
echo "Run 'python app.py' to start the development server"
```

#### Test Script
```bash
#!/bin/bash
# scripts/run_tests.sh

echo "Running test suite..."

# Activate virtual environment
source venv/bin/activate

# Run different test categories
echo "Running unit tests..."
pytest -m unit -v

echo "Running integration tests..."
pytest -m integration -v

echo "Running security tests..."
pytest -m security -v

echo "Running performance tests..."
pytest -m performance -v

# Generate coverage report
echo "Generating coverage report..."
pytest --cov=app --cov-report=html --cov-report=xml

echo "Test suite complete!"
echo "Coverage report: htmlcov/index.html"
```

### IDE Configuration

#### VSCode Configuration
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true,
        "source.fixAll.flake8": true
    },
    "files.associations": {
        "*.html": "html",
        "*.css": "css",
        "*.js": "javascript"
    }
}
```

#### PyCharm Configuration
1. **Interpreter**: Select the virtual environment
2. **Working Directory**: Set to project root
3. **Environment Variables**: Configure in Run Configuration
4. **Templates**: Enable Django support for Jinja2 templates
5. **Code Style**: Configure Black and isort

## Advanced Development

### Microservices Architecture

#### Service Separation
```python
# services/user_service.py
class UserService:
    def __init__(self, db_session):
        self.db = db_session

    def create_user(self, user_data: dict):
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        return user

    def get_user(self, user_id: int):
        return self.db.query(User).filter_by(id=user_id).first()

# services/product_service.py
class ProductService:
    def __init__(self, db_session, cache_manager):
        self.db = db_session
        self.cache = cache_manager

    def get_products(self, category: str = None):
        cache_key = f"products:{category or 'all'}"

        cached = self.cache.get(cache_key)
        if cached:
            return cached

        query = self.db.query(Product).filter_by(is_active=True)
        if category:
            query = query.filter_by(category=category)

        products = query.all()
        self.cache.set(cache_key, products, ttl=3600)

        return products
```

### Event-Driven Architecture

#### Event System
```python
# events/event_manager.py
class EventManager:
    def __init__(self):
        self.listeners = defaultdict(list)

    def subscribe(self, event_type: str, listener: Callable):
        self.listeners[event_type].append(listener)

    def publish(self, event_type: str, event_data: dict):
        for listener in self.listeners[event_type]:
            try:
                listener(event_data)
            except Exception as e:
                logger.error(f"Event listener error: {e}")

# Usage
event_manager = EventManager()

def order_created_handler(event_data):
    order_id = event_data['order_id']
    # Send notification, update inventory, etc.

event_manager.subscribe('order.created', order_created_handler)

# Publish event
event_manager.publish('order.created', {'order_id': 123})
```

### Configuration Management

#### Dynamic Configuration
```python
# config/dynamic_config.py
class DynamicConfig:
    def __init__(self):
        self.config_cache = {}
        self.config_listeners = []

    def get_config(self, key: str, default=None):
        if key not in self.config_cache:
            self.config_cache[key] = self._load_config(key)

        return self.config_cache[key]

    def update_config(self, key: str, value):
        self.config_cache[key] = value

        # Notify listeners
        for listener in self.config_listeners:
            listener(key, value)

    def _load_config(self, key: str):
        # Load from database or external source
        from models import SystemConfig
        config = SystemConfig.query.filter_by(key=key).first()
        return config.value if config else None
```

## Production Development

### Production Debugging

#### Production Debug Mode
```python
# Enable production debugging safely
class ProductionDebugConfig:
    DEBUG = False
    TESTING = False

    # Safe debugging
    PROPAGATE_EXCEPTIONS = True
    PRESERVE_CONTEXT_ON_EXCEPTION = False

    # Enhanced logging
    LOG_LEVEL = 'INFO'
    SECURITY_EVENT_LOGGING = True
```

### Performance Monitoring

#### Custom Performance Metrics
```python
# monitoring/custom_metrics.py
from monitoring_config import get_monitoring_integration

monitoring = get_monitoring_integration()

def record_business_metric(metric_name: str, value: float, tags: dict = None):
    """Record business-specific metrics"""
    monitoring.record_custom_metric(metric_name, value, 'gauge')

    # Log with context
    logger.info(f"Business metric: {metric_name} = {value}", extra={
        'metric_name': metric_name,
        'metric_value': value,
        'metric_tags': tags or {}
    })

# Usage
record_business_metric('orders_per_hour', 15.5, {'region': 'west_africa'})
record_business_metric('avg_order_value', 25000, {'currency': 'XOF'})
```

## Development Best Practices

### Code Quality

1. **Write self-documenting code**
   ```python
   # Good
   def calculate_total_price(items: List[Item], discount: float = 0.0) -> float:
       """Calculate total price with optional discount"""

   # Bad
   def calc(x, y=0):
       # No documentation, unclear parameters
   ```

2. **Use type hints**
   ```python
   from typing import List, Dict, Optional

   def process_orders(orders: List[Order], user_id: int) -> Dict[str, int]:
       # Function with proper type hints
   ```

3. **Handle exceptions properly**
   ```python
   def safe_database_operation():
       try:
           # Database operation
           pass
       except IntegrityError as e:
           logger.error(f"Database integrity error: {e}")
           raise ValidationError("Invalid data provided")
       except OperationalError as e:
           logger.error(f"Database operational error: {e}")
           raise ServiceError("Database temporarily unavailable")
   ```

### Security

1. **Validate all inputs**
   ```python
   from validation_schemas import validate_data, UserRegistrationSchema

   def register_user(data: dict):
       validation = validate_data(UserRegistrationSchema, data)
       if not validation['valid']:
           raise ValidationError("Invalid registration data")
   ```

2. **Use secure defaults**
   ```python
   # Good
   is_admin = False  # Secure default

   # Bad
   is_admin = request.args.get('admin', False)  # Insecure
   ```

3. **Log security events**
   ```python
   from security_system import log_security_event

   def login_user(email: str, password: str):
       user = authenticate_user(email, password)
       if user:
           log_security_event('login_success', f"User {email} logged in")
       else:
           log_security_event('login_failure', f"Failed login for {email}")
   ```

### Performance

1. **Profile slow operations**
   ```python
   from performance_optimizer import profile_performance

   @profile_performance('heavy_operation')
   def heavy_database_operation():
       # Your slow operation
   ```

2. **Use caching appropriately**
   ```python
   from redis_cache import cache_manager

   def get_frequently_accessed_data():
       cache_key = "frequent_data"

       cached = cache_manager.get(cache_key)
       if cached:
           return cached

       # Expensive operation
       data = expensive_database_query()
       cache_manager.set(cache_key, data, ttl=3600)
       return data
   ```

3. **Optimize database queries**
   ```python
   # Good: Use specific queries
   user = User.query.filter_by(email=email).first()

   # Bad: Use broad queries
   users = User.query.all()
   user = next((u for u in users if u.email == email), None)
   ```

## Development Workflow

### Feature Development

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-user-authentication
   ```

2. **Implement Feature**
   ```python
   # Implement with tests
   def test_new_feature():
       # Test implementation
       pass

   def new_feature():
       # Feature implementation
       pass
   ```

3. **Test Thoroughly**
   ```bash
   pytest tests/test_new_feature.py -v
   pytest -m integration -k new_feature
   ```

4. **Code Review**
   - Submit pull request
   - Address review comments
   - Update documentation

5. **Deploy**
   ```bash
   git merge feature/new-user-authentication
   python deploy.py
   ```

### Bug Fixes

1. **Identify Issue**
   - Check error logs
   - Reproduce the issue
   - Identify root cause

2. **Create Fix Branch**
   ```bash
   git checkout -b fix/database-connection-issue
   ```

3. **Implement Fix**
   ```python
   def fix_database_connection():
       # Implement fix with proper error handling
       try:
           # Fixed code
       except Exception as e:
           logger.error(f"Database connection error: {e}")
           raise
   ```

4. **Test Fix**
   ```bash
   pytest tests/test_database.py -v
   ```

5. **Deploy Fix**
   ```bash
   git merge fix/database-connection-issue
   sudo systemctl restart passprint
   ```

## Advanced Development

### Custom Flask Extensions

#### Database Extension
```python
# extensions/database.py
from flask_sqlalchemy import SQLAlchemy

class PassPrintSQLAlchemy(SQLAlchemy):
    def init_app(self, app):
        super().init_app(app)

        # Add custom functionality
        @app.teardown_appcontext
        def shutdown_session(exception=None):
            if exception:
                self.session.rollback()
            self.session.remove()

db = PassPrintSQLAlchemy()
```

#### Monitoring Extension
```python
# extensions/monitoring.py
class MonitoringExtension:
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        from monitoring_alerting import init_monitoring
        init_monitoring(app)

monitoring = MonitoringExtension()
```

### Plugin Architecture

#### Plugin Base Class
```python
# plugins/base.py
class BasePlugin:
    def __init__(self, app):
        self.app = app

    def register(self):
        """Register plugin with application"""
        raise NotImplementedError

    def unregister(self):
        """Unregister plugin"""
        pass

    def get_config(self):
        """Get plugin configuration"""
        return {}

    def set_config(self, config: dict):
        """Set plugin configuration"""
        pass
```

#### Payment Plugin Example
```python
# plugins/stripe_plugin.py
from plugins.base import BasePlugin

class StripePlugin(BasePlugin):
    def register(self):
        """Register Stripe payment routes"""
        @self.app.route('/api/payments/stripe/webhook', methods=['POST'])
        def stripe_webhook():
            # Handle Stripe webhook
            pass

    def create_payment(self, amount: int, currency: str):
        """Create Stripe payment"""
        import stripe
        return stripe.PaymentIntent.create(
            amount=amount,
            currency=currency
        )
```

### API Versioning

#### Versioned API Routes
```python
# api/v1/routes.py
from flask import Blueprint

api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

@api_v1.route('/products')
def get_products():
    # V1 implementation
    pass

# api/v2/routes.py
from flask import Blueprint

api_v2 = Blueprint('api_v2', __name__, url_prefix='/api/v2')

@api_v2.route('/products')
def get_products():
    # V2 implementation with improvements
    pass
```

### Database Versioning

#### Migration Management
```python
# Manage database migrations
from flask_migrate import Migrate, upgrade, downgrade

migrate = Migrate(app, db)

def run_migrations():
    """Run database migrations"""
    with app.app_context():
        upgrade()

def rollback_migration(version: str):
    """Rollback to specific migration"""
    with app.app_context():
        downgrade(version)
```

## Development Tools

### Code Generation

#### Model Generator
```python
# scripts/generate_model.py
def generate_model(model_name: str, fields: dict):
    """Generate SQLAlchemy model"""

    model_code = f"""
class {model_name}(db.Model):
    __tablename__ = '{model_name.lower()}'

    id = db.Column(db.Integer, primary_key=True)
"""

    for field_name, field_type in fields.items():
        if field_type == 'string':
            model_code += f"    {field_name} = db.Column(db.String(255))\n"
        elif field_type == 'integer':
            model_code += f"    {field_name} = db.Column(db.Integer)\n"
        elif field_type == 'boolean':
            model_code += f"    {field_name} = db.Column(db.Boolean)\n"
        elif field_type == 'datetime':
            model_code += f"    {field_name} = db.Column(db.DateTime)\n"

    return model_code
```

### Database Tools

#### Database Inspector
```python
# tools/db_inspector.py
from sqlalchemy import inspect

def inspect_database():
    """Inspect database structure"""
    inspector = inspect(db.engine)

    for table_name in inspector.get_table_names():
        print(f"Table: {table_name}")

        columns = inspector.get_columns(table_name)
        for column in columns:
            print(f"  - {column['name']}: {column['type']}")

        indexes = inspector.get_indexes(table_name)
        for index in indexes:
            print(f"  - Index: {index['name']}")
```

### Performance Tools

#### Performance Profiler
```python
# tools/performance_profiler.py
import cProfile
import pstats
import io

def profile_endpoint(endpoint_function):
    """Profile Flask endpoint"""

    def profiler(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()

        try:
            return endpoint_function(*args, **kwargs)
        finally:
            profiler.disable()

            s = io.StringIO()
            stats = pstats.Stats(profiler, stream=s)
            stats.sort_stats('cumulative')
            stats.print_stats(20)

            print(s.getvalue())

    return profiler
```

## Deployment Development

### Development Deployment

#### Staging Environment
```bash
# Deploy to staging
export FLASK_ENV=staging
export DATABASE_URL=postgresql://passprint:password@staging-db:5432/passprint_staging

python deploy.py --environment=staging
```

#### Production Deployment
```bash
# Deploy to production
export FLASK_ENV=production
export DATABASE_URL=postgresql://passprint:password@prod-db:5432/passprint_prod

python deploy.py --environment=production
```

### Docker Development

#### Multi-Stage Docker Build
```dockerfile
# Dockerfile
FROM python:3.9-slim as base

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base as development

# Development dependencies
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Source code
COPY . .

# Development command
CMD ["python", "app.py"]

FROM base as production

# Production dependencies only
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

# Production optimizations
RUN python -c "import compileall; compileall.compile_dir('.')"
RUN find . -name "*.pyc" -delete

# Production command
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
```

## Best Practices Summary

### Code Quality
- ✅ Write comprehensive tests
- ✅ Use type hints
- ✅ Document complex functions
- ✅ Follow PEP 8 conventions
- ✅ Use meaningful variable names

### Security
- ✅ Validate all inputs
- ✅ Use parameterized queries
- ✅ Hash sensitive data
- ✅ Implement proper authentication
- ✅ Log security events

### Performance
- ✅ Profile slow operations
- ✅ Use caching appropriately
- ✅ Optimize database queries
- ✅ Monitor resource usage
- ✅ Handle errors gracefully

### Maintainability
- ✅ Keep functions small and focused
- ✅ Use descriptive names
- ✅ Document code thoroughly
- ✅ Follow consistent patterns
- ✅ Update dependencies regularly

---

For additional development resources, visit the [Developer Portal](https://dev.passprint.com) or contact the development team.
</content>