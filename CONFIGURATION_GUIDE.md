# ⚙️ Configuration Guide - PassPrint

## Table of Contents

1. [Environment Configuration](#environment-configuration)
2. [Database Configuration](#database-configuration)
3. [Security Configuration](#security-configuration)
4. [Monitoring Configuration](#monitoring-configuration)
5. [Performance Configuration](#performance-configuration)
6. [Backup Configuration](#backup-configuration)
7. [Email Configuration](#email-configuration)
8. [Payment Configuration](#payment-configuration)
9. [CDN Configuration](#cdn-configuration)
10. [Development Configuration](#development-configuration)

## Environment Configuration

### Environment Variables Overview

PassPrint uses environment variables for configuration management. Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit with your configuration
nano .env
```

### Core Application Settings

```bash
# Application Environment
FLASK_ENV=production          # development, testing, production
DEBUG=false                   # Enable/disable debug mode
SECRET_KEY=your-secret-key    # Flask secret key (32+ characters)
JWT_SECRET_KEY=jwt-secret    # JWT token secret key (32+ characters)

# Server Configuration
HOST=0.0.0.0                 # Server host
PORT=5000                    # Server port
WORKERS=4                    # Number of Gunicorn workers

# URLs
APP_URL=https://your-domain.com
API_BASE_URL=https://api.your-domain.com
```

### Database Configuration

#### SQLite (Development/Testing)

```bash
# SQLite Configuration
DATABASE_URL=sqlite:///passprint.db

# Performance Settings
SQLALCHEMY_ENGINE_OPTIONS='{"pool_pre_ping": true, "pool_recycle": 300}'
SQLALCHEMY_POOL_SIZE=10
SQLALCHEMY_MAX_OVERFLOW=20
```

#### PostgreSQL (Production)

```bash
# PostgreSQL Configuration
DATABASE_URL=postgresql://username:password@hostname:5432/database_name

# Connection Pooling
SQLALCHEMY_ENGINE_OPTIONS='{
    "pool_pre_ping": true,
    "pool_recycle": 300,
    "pool_size": 10,
    "max_overflow": 20,
    "pool_timeout": 30
}'

# PostgreSQL Specific
PGHOST=localhost
PGPORT=5432
PGDATABASE=passprint_prod
PGUSER=passprint
PGPASSWORD=your-secure-password

# Backup Settings
PG_BACKUP_JOBS=2
PG_COMPRESSION_LEVEL=9
PG_BUFFER_SIZE=8192kB
```

### Security Configuration

#### Authentication Settings

```bash
# JWT Configuration
JWT_ACCESS_TOKEN_EXPIRES=3600    # 1 hour
JWT_REFRESH_TOKEN_EXPIRES=86400  # 24 hours
JWT_ALGORITHM=HS256

# Password Policies
PASSWORD_MIN_LENGTH=12
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15

# Session Security
SESSION_TIMEOUT_MINUTES=60
CSRF_PROTECTION=true
SECURE_COOKIES=true
```

#### Rate Limiting

```bash
# API Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_BURST=20

# Specific Limits
AUTH_RATE_LIMIT=5/minute
API_RATE_LIMIT=100/minute
UPLOAD_RATE_LIMIT=10/minute
```

#### Security Headers

```bash
# Security Headers (configured in Nginx)
SECURE_HEADERS=true
HSTS_MAX_AGE=31536000
CSP_ENABLED=true
XSS_PROTECTION=true
```

### Monitoring Configuration

#### Application Monitoring

```bash
# Monitoring Settings
MONITORING_ENABLED=true
METRICS_COLLECTION_INTERVAL=5
ALERT_EMAIL_ENABLED=true

# Prometheus
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090

# Sentry (Error Tracking)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# Elasticsearch (Log Aggregation)
ELASTICSEARCH_ENABLED=true
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
LOG_AGGREGATION=true
```

#### Alert Configuration

```bash
# Alert Settings
ALERT_EMAIL_RECIPIENTS=admin@your-domain.com,ops@your-domain.com
ALERT_WEBHOOK_URL=https://hooks.slack.com/your-webhook-url

# Alert Thresholds
CPU_ALERT_THRESHOLD=80
MEMORY_ALERT_THRESHOLD=85
DISK_ALERT_THRESHOLD=90
ERROR_RATE_ALERT_THRESHOLD=5

# Alert Cooldown (minutes)
ALERT_COOLDOWN_CPU=5
ALERT_COOLDOWN_MEMORY=5
ALERT_COOLDOWN_DISK=15
```

### Performance Configuration

#### Caching Settings

```bash
# Redis Cache
REDIS_URL=redis://localhost:6379/0
CACHE_ENABLED=true
CACHE_TTL=300
CACHE_LONG_TTL=3600
CACHE_SHORT_TTL=60

# Memory Cache
MEMORY_CACHE_SIZE=1000
CACHE_HIT_RATIO_THRESHOLD=0.8
```

#### Database Performance

```bash
# Query Optimization
SLOW_QUERY_THRESHOLD=1.0
QUERY_TIMEOUT=30
AUTO_ANALYZE=true
AUTO_VACUUM=true

# Connection Management
DB_MAX_CONNECTIONS=20
DB_CONNECTION_TIMEOUT=30
DB_CONNECTION_POOL_SIZE=10
```

#### Application Performance

```bash
# Performance Settings
REQUEST_TIMEOUT=30
UPLOAD_TIMEOUT=300
PROCESSING_TIMEOUT=600

# Resource Limits
MAX_FILE_SIZE=52428800
MAX_REQUEST_SIZE=10485760
MAX_BATCH_SIZE=1000
```

### Backup Configuration

#### Backup Settings

```bash
# Backup Configuration
BACKUP_ENABLED=true
BACKUP_FREQUENCY_HOURS=24
BACKUP_RETENTION_DAYS=30
BACKUP_COMPRESSION=true
BACKUP_ENCRYPTION=false

# PostgreSQL Backup
PG_BACKUP_JOBS=2
PG_COMPRESSION_LEVEL=9
PITR_ENABLED=false

# File Backups
FILE_BACKUP_ENABLED=true
SNAPSHOT_ENABLED=true
SNAPSHOT_RETENTION_DAYS=7
```

#### Cloud Backup

```bash
# AWS S3 Backup
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
S3_BUCKET_NAME=passprint-backups
S3_REGION=us-east-1

# Google Cloud Storage
GCS_BUCKET_NAME=passprint-backups
GCS_PROJECT_ID=your-project-id
```

### Email Configuration

#### SMTP Settings

```bash
# SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_TLS=true
SMTP_SSL=false

# Email Templates
EMAIL_TEMPLATES_DIR=templates/emails
DEFAULT_FROM_EMAIL=noreply@your-domain.com
```

#### Email Service Providers

```bash
# SendGrid
SENDGRID_API_KEY=your-sendgrid-key
SENDGRID_FROM_EMAIL=noreply@your-domain.com

# Amazon SES
SES_REGION=us-east-1
SES_ACCESS_KEY=your-ses-key
SES_SECRET_KEY=your-ses-secret
```

### Payment Configuration

#### Stripe Settings

```bash
# Stripe Configuration
STRIPE_PUBLIC_KEY=pk_live_your_stripe_public_key
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Stripe Options
STRIPE_CURRENCY=XOF
STRIPE_PAYMENT_METHODS=card,mobilepay
STRIPE_WEBHOOK_URL=https://your-domain.com/api/webhooks/stripe
```

#### Payment Processing

```bash
# Payment Settings
PAYMENT_TIMEOUT=300
PAYMENT_RETRY_ATTEMPTS=3
PAYMENT_CURRENCIES=XOF,EUR,USD

# Refund Policy
AUTO_REFUND_ENABLED=false
REFUND_WINDOW_DAYS=30
```

### CDN Configuration

#### CloudFlare Settings

```bash
# CloudFlare CDN
CLOUDFLARE_ENABLED=true
CLOUDFLARE_ZONE_ID=your-zone-id
CLOUDFLARE_API_TOKEN=your-api-token
CLOUDFLARE_CDN_URL=https://cdn.your-domain.com

# Cache Settings
CLOUDFLARE_CACHE_TTL=3600
CLOUDFLARE_BROWSER_TTL=86400
```

#### AWS CloudFront

```bash
# AWS CloudFront
AWS_CDN_ENABLED=true
AWS_DISTRIBUTION_ID=your-distribution-id
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_CDN_URL=https://your-distribution.cloudfront.net
```

### Development Configuration

#### Development Settings

```bash
# Development Environment
FLASK_ENV=development
DEBUG=true
RELOAD=true
SQLALCHEMY_ECHO=false

# Development Database
DATABASE_URL=sqlite:///passprint_dev.db

# Development Tools
FLASK_DEBUG=true
WERKZEUG_DEBUG_PIN=off
```

#### Testing Configuration

```bash
# Testing Environment
FLASK_ENV=testing
TESTING=true
DATABASE_URL=sqlite:///test.db
REDIS_URL=redis://localhost:6379/1

# Disable external services in tests
MAIL_SUPPRESS_SEND=true
BACKUP_ENABLED=false
MONITORING_ENABLED=false
```

## Configuration Files

### Application Configuration (`config.py`)

The main configuration file supports multiple environments:

```python
class DevelopmentConfig(Config):
    DEBUG = True
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///passprint_dev.db')

class ProductionConfig(Config):
    DEBUG = False
    DATABASE_URL = os.getenv('DATABASE_URL')  # Must be set

class TestingConfig(Config):
    TESTING = True
    DATABASE_URL = 'sqlite:///test.db'
    MAIL_SUPPRESS_SEND = True
```

### Nginx Configuration (`nginx.conf`)

Production web server configuration with SSL and security headers.

### Gunicorn Configuration (`gunicorn.conf.py`)

WSGI server configuration for production deployment.

## Environment-Specific Setup

### Production Setup Checklist

- [ ] Set strong SECRET_KEY and JWT_SECRET_KEY
- [ ] Configure production DATABASE_URL
- [ ] Set up SMTP for email notifications
- [ ] Configure Stripe payment keys
- [ ] Set up SSL certificates
- [ ] Configure CDN (optional)
- [ ] Set up monitoring and alerting
- [ ] Configure backup retention policies
- [ ] Set up log aggregation

### Development Setup Checklist

- [ ] Install development dependencies
- [ ] Set up local database
- [ ] Configure debug mode
- [ ] Set up local Redis (optional)
- [ ] Configure email testing
- [ ] Set up local monitoring

### Testing Setup Checklist

- [ ] Install test dependencies
- [ ] Configure test database
- [ ] Set up test fixtures
- [ ] Configure mock services
- [ ] Set up test reporting

## Security Configuration

### SSL/TLS Setup

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d your-domain.com

# Configure auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Security Headers

Configure Nginx to include security headers:

```nginx
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### Firewall Configuration

```bash
# Configure UFW
sudo ufw allow 'OpenSSH'
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Install and configure fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

## Monitoring Configuration

### Prometheus Setup

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'passprint'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
```

### Grafana Dashboard

1. **Install Grafana**
```bash
sudo apt install grafana
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
```

2. **Access Grafana**: http://localhost:3000 (admin/admin)

3. **Add Prometheus Data Source**
   - Name: Prometheus
   - Type: Prometheus
   - URL: http://localhost:9090

4. **Import Dashboard**: Use the provided dashboard JSON

### Alert Rules

```yaml
# alertmanager.yml
route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'email'

receivers:
  - name: 'email'
    email_configs:
      - to: 'admin@your-domain.com'
        from: 'alerts@your-domain.com'
        smarthost: 'smtp.your-domain.com:587'
        auth_username: 'alerts@your-domain.com'
        auth_password: 'your-password'
```

## Performance Configuration

### Database Performance Tuning

#### PostgreSQL Tuning

```ini
# /etc/postgresql/13/main/postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
checkpoint_segments = 32
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.5
effective_io_concurrency = 200
```

#### Application-Level Optimization

```python
# Database connection optimization
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_size': 10,
    'max_overflow': 20,
    'pool_timeout': 30
}

# Query optimization
SLOW_QUERY_THRESHOLD = 1.0
AUTO_EXPLAIN = True
```

### Caching Configuration

#### Redis Configuration

```ini
# /etc/redis/redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
tcp-keepalive 300
timeout 300
```

#### Application Cache Settings

```python
# Cache TTL settings
CACHE_TTL = {
    'products': 3600,      # 1 hour
    'users': 1800,         # 30 minutes
    'orders': 900,         # 15 minutes
    'sessions': 3600       # 1 hour
}

# Cache strategies
CACHE_STRATEGY = {
    'default': 'redis',
    'fallback': 'memory',
    'serialize': 'json'
}
```

## Backup Configuration

### Backup Schedule

```bash
# Daily database backup
0 3 * * * /opt/passprint-website/venv/bin/python backup_system.py create_database_backup

# Weekly full backup
0 2 * * 0 /opt/passprint-website/venv/bin/python backup_system.py create_full_backup

# Monthly cleanup
0 1 1 * * /opt/passprint-website/venv/bin/python backup_system.py cleanup_old_backups
```

### Backup Retention Policies

```python
# Configuration in config.py
BACKUP_RETENTION = {
    'daily_backups': 30,      # Keep 30 days
    'weekly_backups': 90,     # Keep 90 days
    'monthly_backups': 365,   # Keep 1 year
    'full_backups': 2555      # Keep 7 years (legal requirement)
}
```

## Email Configuration

### SMTP Setup

#### Gmail SMTP

```bash
# Enable 2FA on Gmail account
# Generate App Password: https://myaccount.google.com/apppasswords

SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-character-app-password
```

#### SendGrid Setup

```bash
# SendGrid Configuration
SENDGRID_API_KEY=SG.your-sendgrid-api-key
SENDGRID_FROM_EMAIL=noreply@your-domain.com

# Template IDs
SENDGRID_TEMPLATES = {
    'welcome': 'd-123456789',
    'order_confirmation': 'd-987654321',
    'newsletter': 'd-456789123'
}
```

#### Amazon SES Setup

```bash
# SES Configuration
SES_REGION=us-east-1
SES_ACCESS_KEY=your-ses-access-key
SES_SECRET_KEY=your-ses-secret-key
SES_FROM_EMAIL=noreply@your-domain.com
```

## Payment Configuration

### Stripe Setup

1. **Create Stripe Account**: https://stripe.com
2. **Get API Keys**: Dashboard → Developers → API Keys
3. **Configure Webhooks**: Dashboard → Developers → Webhooks

```bash
# Stripe Configuration
STRIPE_PUBLIC_KEY=pk_live_your_public_key
STRIPE_SECRET_KEY=sk_live_your_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Webhook URL
STRIPE_WEBHOOK_URL=https://your-domain.com/api/webhooks/stripe
```

### Supported Payment Methods

```python
PAYMENT_METHODS = {
    'card': {
        'enabled': True,
        'currencies': ['XOF', 'EUR', 'USD']
    },
    'mobile_money': {
        'enabled': True,
        'providers': ['orange_money', 'mtn_money', 'moov_money']
    },
    'bank_transfer': {
        'enabled': True,
        'processing_days': 3
    }
}
```

## CDN Configuration

### CloudFlare Setup

1. **Add Domain**: CloudFlare Dashboard → Add Site
2. **Update DNS**: Point to your load balancer
3. **Configure SSL**: Set to "Full (strict)"

```bash
# CloudFlare Configuration
CLOUDFLARE_ZONE_ID=your-zone-id
CLOUDFLARE_API_TOKEN=your-api-token
CLOUDFLARE_CDN_URL=https://cdn.your-domain.com

# Cache Rules
CLOUDFLARE_CACHE_TTL = {
    'static_assets': 31536000,  # 1 year
    'api_responses': 0,         # No cache
    'user_uploads': 2592000     # 30 days
}
```

### AWS CloudFront Setup

```bash
# Create distribution
aws cloudfront create-distribution --distribution-config file://cloudfront-config.json

# Invalidate cache
aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths "/*"
```

## Development Configuration

### Development Tools Setup

```bash
# Install development tools
pip install black isort flake8 mypy pytest pytest-cov

# Configure pre-commit hooks
pre-commit install

# Setup development database
export FLASK_ENV=development
export DATABASE_URL=sqlite:///passprint_dev.db
python init_db.py
```

### IDE Configuration

#### VSCode Settings

```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

#### PyCharm Configuration

1. **Interpreter**: Select the virtual environment
2. **Working Directory**: Set to project root
3. **Environment Variables**: Configure in Run Configuration
4. **Templates**: Enable Django support for Jinja2 templates

## Configuration Validation

### Configuration Checker

```python
# config_checker.py
import os
from config import get_config

def validate_configuration():
    """Validate the current configuration"""
    issues = []
    config = get_config()

    # Check required settings
    if not config.SECRET_KEY or len(config.SECRET_KEY) < 32:
        issues.append("SECRET_KEY must be at least 32 characters")

    if not config.JWT_SECRET_KEY or len(config.JWT_SECRET_KEY) < 32:
        issues.append("JWT_SECRET_KEY must be at least 32 characters")

    if 'sqlite' in config.SQLALCHEMY_DATABASE_URI and config.ENVIRONMENT == 'production':
        issues.append("SQLite should not be used in production")

    # Check service availability
    try:
        import redis
        r = redis.from_url(config.REDIS_URL)
        r.ping()
    except:
        issues.append("Redis is not available")

    return issues

if __name__ == "__main__":
    issues = validate_configuration()
    if issues:
        print("Configuration issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ Configuration is valid")
```

### Environment-Specific Validation

#### Production Validation

```python
def validate_production_config():
    """Validate production configuration"""
    required_vars = [
        'SECRET_KEY', 'JWT_SECRET_KEY', 'DATABASE_URL',
        'SMTP_USERNAME', 'SMTP_PASSWORD', 'STRIPE_SECRET_KEY'
    ]

    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)

    return missing
```

#### Development Validation

```python
def validate_development_config():
    """Validate development configuration"""
    warnings = []

    if os.getenv('DEBUG', 'false').lower() != 'true':
        warnings.append("Debug mode should be enabled in development")

    if 'sqlite' not in os.getenv('DATABASE_URL', ''):
        warnings.append("SQLite is recommended for development")

    return warnings
```

## Configuration Management

### Using Environment Variables

```bash
# Load environment variables
export FLASK_ENV=production
export SECRET_KEY=your-secret-key
export DATABASE_URL=postgresql://...

# Run application
python app.py
```

### Using Docker Environment

```yaml
# docker-compose.yml
services:
  web:
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    env_file:
      - .env
```

### Configuration Hot Reload

```python
# Enable configuration hot reload in development
class DevelopmentConfig(Config):
    # Auto-reload configuration
    CONFIG_RELOAD = True
    CONFIG_POLL_INTERVAL = 30  # seconds
```

## Troubleshooting Configuration

### Common Configuration Issues

#### Database Connection Issues

```bash
# Test database connection
python -c "
from app import create_app
from models import db
app = create_app()
with app.app_context():
    try:
        db.engine.connect()
        print('✅ Database connection successful')
    except Exception as e:
        print(f'❌ Database error: {e}')
"
```

#### Redis Connection Issues

```bash
# Test Redis connection
python -c "
import redis
try:
    r = redis.Redis.from_url('redis://localhost:6379/0')
    r.ping()
    print('✅ Redis connection successful')
except Exception as e:
    print(f'❌ Redis error: {e}')
"
```

#### Email Configuration Issues

```bash
# Test email configuration
python -c "
from flask_mail import Mail, Message
from app import create_app

app = create_app()
with app.app_context():
    mail = Mail(app)
    try:
        msg = Message('Test', recipients=['test@example.com'])
        # Don't actually send in test
        print('✅ Email configuration valid')
    except Exception as e:
        print(f'❌ Email error: {e}')
"
```

### Configuration Debugging

#### Debug Mode

```python
# Enable configuration debugging
import logging

logging.basicConfig(level=logging.DEBUG)

# Print current configuration
from config import get_config
config = get_config()
print(f"Database URL: {config.SQLALCHEMY_DATABASE_URI}")
print(f"Redis URL: {config.REDIS_URL}")
print(f"Environment: {config.ENVIRONMENT}")
```

#### Configuration Validation Script

```bash
#!/bin/bash
# validate_config.sh

echo "🔍 Validating PassPrint configuration..."

# Check required files
files=(".env" "requirements.txt" "config.py")
for file in "${files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing file: $file"
        exit 1
    fi
done

# Check required environment variables
required_vars=("SECRET_KEY" "DATABASE_URL" "REDIS_URL")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Missing environment variable: $var"
        exit 1
    fi
done

# Test services
python -c "
import redis
from app import create_app
from models import db

try:
    r = redis.Redis.from_url('redis://localhost:6379/0')
    r.ping()
    print('✅ Redis OK')
except:
    print('❌ Redis FAIL')

try:
    app = create_app()
    with app.app_context():
        db.engine.connect()
    print('✅ Database OK')
except Exception as e:
    print(f'❌ Database FAIL: {e}')
"

echo "✅ Configuration validation complete"
```

## Best Practices

### Security Best Practices

1. **Use strong, unique keys**
   ```bash
   # Generate secure keys
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Rotate secrets regularly**
   ```bash
   # Rotate secrets monthly
   0 0 1 * * /path/to/rotate_secrets.sh
   ```

3. **Use environment-specific configurations**
   ```bash
   # Different configs for different environments
   FLASK_ENV=production python app.py
   FLASK_ENV=development python app.py
   ```

4. **Validate configuration on startup**
   ```python
   def validate_config():
       required_settings = ['SECRET_KEY', 'DATABASE_URL']
       for setting in required_settings:
           if not getattr(config, setting):
               raise ValueError(f"Missing required setting: {setting}")
   ```

### Performance Best Practices

1. **Optimize database connections**
   ```python
   SQLALCHEMY_ENGINE_OPTIONS = {
       'pool_size': 10,
       'max_overflow': 20,
       'pool_timeout': 30,
       'pool_recycle': 3600
   }
   ```

2. **Configure appropriate cache TTL**
   ```python
   CACHE_TTL = {
       'static_content': 3600,
       'dynamic_content': 300,
       'user_data': 1800
   }
   ```

3. **Set resource limits**
   ```ini
   # /etc/systemd/system/passprint.service
   MemoryLimit=512M
   LimitNOFILE=65536
   ```

### Maintenance Best Practices

1. **Regular configuration reviews**
   ```bash
   # Monthly configuration audit
   python config_audit.py
   ```

2. **Automated configuration validation**
   ```bash
   # Pre-deployment validation
   ./validate_config.sh
   ```

3. **Configuration backup**
   ```bash
   # Backup configuration
   cp .env .env.backup.$(date +%Y%m%d)
   ```

## Support

For configuration issues:

1. **Check the logs**: `tail -f logs/app.log`
2. **Run configuration validation**: `python config_checker.py`
3. **Test individual components**: Use the troubleshooting scripts
4. **Contact support**: Include your configuration (without secrets) in support requests

## Configuration Templates

### Production Template

```bash
# .env.production
FLASK_ENV=production
DEBUG=false
SECRET_KEY=your-production-secret-key
JWT_SECRET_KEY=your-production-jwt-key

DATABASE_URL=postgresql://passprint:prod_password@db-host:5432/passprint_prod
REDIS_URL=redis://redis-host:6379/0

SMTP_SERVER=smtp.your-domain.com
SMTP_USERNAME=passprint@your-domain.com
SMTP_PASSWORD=your-smtp-password

STRIPE_PUBLIC_KEY=pk_live_your_key
STRIPE_SECRET_KEY=sk_live_your_key

MONITORING_ENABLED=true
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
```

### Development Template

```bash
# .env.development
FLASK_ENV=development
DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=dev-jwt-secret-key

DATABASE_URL=sqlite:///passprint_dev.db
REDIS_URL=redis://localhost:6379/0

SMTP_SERVER=localhost
SMTP_PORT=1025
MAIL_SUPPRESS_SEND=true

# Use test keys for Stripe
STRIPE_PUBLIC_KEY=pk_test_your_test_key
STRIPE_SECRET_KEY=sk_test_your_test_key

MONITORING_ENABLED=false
```

---

For more detailed configuration examples, see the deployment guide or contact the development team.