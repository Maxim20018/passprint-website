# 🚢 Deployment Guide - PassPrint

## Table of Contents

1. [Production Deployment](#production-deployment)
2. [Docker Deployment](#docker-deployment)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Load Balancer Configuration](#load-balancer-configuration)
5. [CDN Setup](#cdn-setup)
6. [SSL/TLS Configuration](#ssltls-configuration)
7. [Service Configuration](#service-configuration)
8. [Environment Setup](#environment-setup)
9. [Post-Deployment Verification](#post-deployment-verification)
10. [Scaling and High Availability](#scaling-and-high-availability)

## Production Deployment

### Server Requirements

**Minimum Specifications:**
- **OS**: Ubuntu 20.04 LTS / Debian 11 / CentOS 8+
- **CPU**: 2 cores (4+ recommended)
- **RAM**: 4GB (8GB+ recommended)
- **Storage**: 50GB SSD (100GB+ recommended)
- **Network**: 100Mbps (1Gbps recommended)

**Recommended Specifications:**
- **OS**: Ubuntu 22.04 LTS
- **CPU**: 4+ cores
- **RAM**: 16GB+
- **Storage**: 200GB+ NVMe SSD
- **Network**: 1Gbps+

### Automated Deployment

#### Using the Deployment Script

```bash
# 1. Clone the repository
git clone https://github.com/your-org/passprint.git
cd passprint

# 2. Make deployment script executable
chmod +x deploy.py

# 3. Run deployment (requires sudo)
sudo python deploy.py

# 4. Configure environment variables
cp .env.example .env
nano .env  # Edit with your configuration

# 5. Initialize the application
python init_db.py

# 6. Start services
sudo systemctl start passprint
sudo systemctl start celery-workers
sudo systemctl enable passprint
sudo systemctl enable celery-workers
```

#### Manual Deployment Steps

```bash
# 1. Update system packages
sudo apt update && sudo apt upgrade -y

# 2. Install system dependencies
sudo apt install -y python3-pip python3-venv postgresql postgresql-contrib \
    redis-server nginx certbot python3-dev build-essential

# 3. Install Node.js for frontend assets (optional)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 4. Configure PostgreSQL
sudo -u postgres createuser --interactive --pwprompt passprint
sudo -u postgres createdb passprint_prod -O passprint

# 5. Configure Redis
sudo nano /etc/redis/redis.conf
# Set: maxmemory 256mb
# Set: maxmemory-policy allkeys-lru
sudo systemctl restart redis

# 6. Setup Python virtual environment
python3 -m venv /opt/passprint-website/venv
source /opt/passprint-website/venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 7. Setup SSL certificate
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# 8. Configure Nginx
sudo cp nginx.conf /etc/nginx/sites-available/passprint
sudo ln -s /etc/nginx/sites-available/passprint /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 9. Configure systemd services
sudo cp recovery_scripts/passprint.service /etc/systemd/system/
sudo cp recovery_scripts/celery-workers.service /etc/systemd/system/
sudo systemctl daemon-reload

# 10. Initialize database
python init_db.py

# 11. Run database migrations
python -c "from app import create_app; app = create_app(); app.app_context().push(); from models import db; db.create_all()"

# 12. Start services
sudo systemctl start passprint
sudo systemctl start celery-workers
```

## Docker Deployment

### Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://passprint:password@db:5432/passprint_prod
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - uploads:/app/uploads
      - backups:/app/backups
      - logs:/app/logs

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=passprint_prod
      - POSTGRES_USER=passprint
      - POSTGRES_PASSWORD=your-secure-password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  celery-worker:
    build: .
    command: celery -A celery_tasks.celery_app worker --loglevel=info
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  celery-beat:
    build: .
    command: celery -A celery_tasks.celery_app beat --loglevel=info
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - web

volumes:
  postgres_data:
  redis_data:
  uploads:
  backups:
  logs:
```

### Docker Build and Deploy

```bash
# 1. Build the application image
docker build -t passprint:latest .

# 2. Start all services
docker-compose up -d

# 3. Run database migrations
docker-compose exec web python init_db.py

# 4. Verify deployment
docker-compose ps
curl http://localhost:5000/api/health
```

## Kubernetes Deployment

### Namespace Setup

```bash
# Create namespace
kubectl create namespace passprint

# Create secrets
kubectl create secret generic passprint-secrets \
  --namespace=passprint \
  --from-literal=database-url="postgresql://passprint:password@postgres-service/passprint_prod" \
  --from-literal=redis-url="redis://redis-service:6379/0" \
  --from-literal=secret-key="your-secret-key" \
  --from-literal=jwt-secret-key="your-jwt-secret-key"
```

### PostgreSQL Deployment

```yaml
# postgresql-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: passprint
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:13
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: passprint_prod
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: passprint-secrets
              key: db-username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: passprint-secrets
              key: db-password
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
        - name: backups
          mountPath: /backups
  volumes:
  - name: postgres-data
    persistentVolumeClaim:
      claimName: postgres-pvc
  - name: backups
    persistentVolumeClaim:
      claimName: backups-pvc
```

### Application Deployment

```yaml
# app-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: passprint
  namespace: passprint
spec:
  replicas: 3
  selector:
    matchLabels:
      app: passprint
  template:
    metadata:
      labels:
        app: passprint
    spec:
      containers:
      - name: passprint
        image: passprint:latest
        ports:
        - containerPort: 5000
        env:
        - name: FLASK_ENV
          value: production
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: passprint-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: passprint-secrets
              key: redis-url
        livenessProbe:
          httpGet:
            path: /api/health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### Service Configuration

```yaml
# services.yaml
apiVersion: v1
kind: Service
metadata:
  name: passprint-service
  namespace: passprint
spec:
  selector:
    app: passprint
  ports:
  - port: 80
    targetPort: 5000
  type: ClusterIP

---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: passprint
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP

---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: passprint
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
  type: ClusterIP
```

## Load Balancer Configuration

### Nginx Load Balancer

```nginx
# /etc/nginx/sites-available/passprint
upstream passprint_backend {
    server 10.0.1.10:5000 weight=3;
    server 10.0.1.11:5000 weight=2;
    server 10.0.1.12:5000 weight=1;

    keepalive 32;
    keepalive_requests 100;
    keepalive_timeout 60s;
    least_conn;
}

server {
    listen 80;
    server_name passprint.your-domain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name passprint.your-domain.com;

    ssl_certificate /etc/ssl/certs/passprint.crt;
    ssl_certificate_key /etc/ssl/private/passprint.key;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header Strict-Transport-Security "max-age=31536000";

    location / {
        proxy_pass http://passprint_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://passprint_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Rate limiting for API
        limit_req zone=api burst=20 nodelay;
    }
}
```

### HAProxy Configuration

```haproxy
# /etc/haproxy/haproxy.cfg
global
    log /dev/log local0
    log /dev/log local1 notice
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin
    stats timeout 30s
    user haproxy
    group haproxy
    daemon

defaults
    log global
    mode http
    option httplog
    option dontlognull
    timeout connect 5000
    timeout client 50000
    timeout server 50000

frontend http_front
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/passprint.pem
    redirect scheme https if !{ ssl_fc }

    acl is_api path_beg /api/
    use_backend api_backend if is_api
    default_backend web_backend

backend web_backend
    balance leastconn
    option httpchk GET /api/health
    server web1 10.0.1.10:5000 check
    server web2 10.0.1.11:5000 check
    server web3 10.0.1.12:5000 check

backend api_backend
    balance leastconn
    option httpchk GET /api/health
    server api1 10.0.1.20:5000 check
    server api2 10.0.1.21:5000 check
```

## CDN Setup

### CloudFlare Configuration

1. **Add your domain to CloudFlare**
2. **Update DNS records** to point to your load balancer
3. **Enable SSL/TLS Encryption**: Full (strict)
4. **Configure Page Rules**:
   ```
   URL Pattern: *your-domain.com/*
   Cache Level: Cache Everything
   Edge Cache TTL: 2 hours
   ```

5. **Enable Brotli compression**
6. **Configure WAF (Web Application Firewall)**
7. **Enable HTTP/2 and HTTP/3**

### AWS CloudFront Setup

```bash
# Create CloudFront distribution
aws cloudfront create-distribution \
  --distribution-config file://cloudfront-config.json

# cloudfront-config.json
{
  "CallerReference": "passprint-cdn-001",
  "Comment": "PassPrint CDN Distribution",
  "DefaultCacheBehavior": {
    "TargetOriginId": "passprint-origin",
    "ViewerProtocolPolicy": "redirect-to-https",
    "MinTTL": 0,
    "DefaultTTL": 86400,
    "MaxTTL": 31536000,
    "Compress": true,
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {"Forward": "none"}
    }
  },
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "passprint-origin",
        "DomainName": "passprint.your-domain.com",
        "CustomOriginConfig": {
          "HTTPPort": 80,
          "HTTPSPort": 443,
          "OriginProtocolPolicy": "https-only"
        }
      }
    ]
  },
  "Enabled": true,
  "IPv6Enabled": true,
  "HttpVersion": "http2",
  "CacheBehaviors": {
    "Quantity": 2,
    "Items": [
      {
        "PathPattern": "/api/*",
        "TargetOriginId": "passprint-origin",
        "ViewerProtocolPolicy": "redirect-to-https",
        "MinTTL": 0,
        "DefaultTTL": 0,
        "MaxTTL": 0,
        "Compress": true,
        "ForwardedValues": {
          "QueryString": true,
          "Cookies": {"Forward": "all"}
        }
      }
    ]
  }
}
```

## SSL/TLS Configuration

### Let's Encrypt Setup

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Configure auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Certificate Management

```bash
# Check certificate status
sudo certbot certificates

# Renew certificate manually
sudo certbot renew

# Revoke certificate (if needed)
sudo certbot revoke --cert-name your-domain.com
```

### SSL Configuration Best Practices

```nginx
# /etc/nginx/snippets/ssl-params.conf
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
ssl_prefer_server_ciphers off;

ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_session_tickets off;

# HSTS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

# Security headers
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Referrer-Policy "strict-origin-when-cross-origin";
```

## Service Configuration

### Systemd Services

#### PassPrint Application Service

```ini
# /etc/systemd/system/passprint.service
[Unit]
Description=PassPrint Web Application
After=network.target postgresql.service redis.service
Requires=postgresql.service redis.service

[Service]
Type=simple
User=passprint
Group=passprint
WorkingDirectory=/opt/passprint-website
Environment=FLASK_ENV=production
Environment=PATH=/opt/passprint-website/venv/bin
ExecStart=/opt/passprint-website/venv/bin/gunicorn --config gunicorn.conf.py app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/passprint-website/uploads /opt/passprint-website/backups /opt/passprint-website/logs

# Resource limits
LimitNOFILE=65536
MemoryLimit=512M

[Install]
WantedBy=multi-user.target
```

#### Celery Workers Service

```ini
# /etc/systemd/system/celery-workers.service
[Unit]
Description=PassPrint Celery Workers
After=network.target redis.service
Requires=redis.service

[Service]
Type=simple
User=passprint
Group=passprint
WorkingDirectory=/opt/passprint-website
Environment=FLASK_ENV=production
Environment=PATH=/opt/passprint-website/venv/bin
ExecStart=/opt/passprint-website/venv/bin/celery -A celery_tasks.celery_app worker --loglevel=info --concurrency=2
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3

# Resource limits
MemoryLimit=256M
LimitNOFILE=4096

[Install]
WantedBy=multi-user.target
```

### Gunicorn Configuration

```python
# gunicorn.conf.py
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests
max_requests = 1000
max_requests_jitter = 50

# Logging
loglevel = "info"
accesslog = "/opt/passprint-website/logs/gunicorn_access.log"
errorlog = "/opt/passprint-website/logs/gunicorn_error.log"

# Process naming
proc_name = "passprint_gunicorn"

# Server mechanics
daemon = False
pidfile = "/opt/passprint-website/passprint.pid"
user = "passprint"
group = "passprint"
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "/etc/ssl/private/passprint.key"
# certfile = "/etc/ssl/certs/passprint.crt"
```

## Environment Setup

### Production Environment Variables

```bash
# Application
FLASK_ENV=production
SECRET_KEY=your-256-bit-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
DEBUG=False

# Database
DATABASE_URL=postgresql://passprint:secure_password@localhost:5432/passprint_prod

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=passprint@your-domain.com
SMTP_PASSWORD=your-app-specific-password

# Stripe
STRIPE_PUBLIC_KEY=pk_live_your_stripe_public_key
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
PROMETHEUS_ENABLED=true
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200

# Backup
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30
CLOUD_BACKUP_ENABLED=false

# Performance
CACHE_TTL=300
LOAD_TEST_ENABLED=false
```

### Security Hardening

```bash
# 1. Create dedicated user
sudo useradd --system --shell /bin/false --home /opt/passprint-website --create-home passprint

# 2. Set proper permissions
sudo chown -R passprint:passprint /opt/passprint-website
sudo chmod -R 750 /opt/passprint-website
sudo chmod -R 770 /opt/passprint-website/uploads
sudo chmod -R 770 /opt/passprint-website/backups
sudo chmod -R 770 /opt/passprint-website/logs

# 3. Configure firewall
sudo ufw allow 'OpenSSH'
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# 4. Install fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## Post-Deployment Verification

### Health Checks

```bash
# 1. Application health
curl -f http://localhost:5000/api/health

# 2. Database connectivity
python -c "
from app import create_app
from models import db, User
app = create_app()
with app.app_context():
    try:
        users = User.query.limit(1).all()
        print('✅ Database connection successful')
    except Exception as e:
        print(f'❌ Database error: {e}')
"

# 3. Redis connectivity
python -c "
import redis
try:
    r = redis.Redis.from_url('redis://localhost:6379/0')
    r.ping()
    print('✅ Redis connection successful')
except Exception as e:
    print(f'❌ Redis error: {e}')
"

# 4. Service status
sudo systemctl status passprint --no-pager
sudo systemctl status celery-workers --no-pager
sudo systemctl status nginx --no-pager
```

### Performance Tests

```bash
# 1. Load testing
python load_testing.py run_comprehensive

# 2. Database performance
python database_optimizer.py analyze

# 3. Memory usage
python performance_optimizer.py memory_analysis

# 4. Backup functionality
python backup_system.py test_integrity
```

### Security Verification

```bash
# 1. SSL certificate
curl -I https://your-domain.com | grep -i "strict-transport-security"

# 2. Security headers
curl -I https://your-domain.com | grep -E "(X-Frame-Options|X-Content-Type-Options|X-XSS-Protection)"

# 3. DNS resolution
nslookup your-domain.com

# 4. Firewall status
sudo ufw status
```

## Scaling and High Availability

### Horizontal Scaling

#### Add New Application Server

```bash
# 1. Provision new server
# 2. Install dependencies (same as main server)
# 3. Configure environment
# 4. Update load balancer configuration

# Update Nginx upstream
sudo nano /etc/nginx/sites-available/passprint

# Add new server to upstream
upstream passprint_backend {
    server 10.0.1.10:5000 weight=3;  # Existing server
    server 10.0.1.11:5000 weight=2;  # Existing server
    server 10.0.1.12:5000 weight=1;  # Existing server
    server 10.0.1.13:5000 weight=2;  # New server
}
```

#### Database Scaling

```bash
# PostgreSQL read replicas
sudo -u postgres createuser --replication --pwprompt replica_user

# Configure replication in postgresql.conf
# primary_conninfo = 'host=primary-db port=5432 user=replica_user password=password'
# hot_standby = on
```

### Vertical Scaling

#### Increase Resources

```bash
# 1. Stop services
sudo systemctl stop passprint celery-workers

# 2. Increase memory/CPU allocation in systemd
sudo nano /etc/systemd/system/passprint.service
# Update MemoryLimit and CPUQuota

# 3. Update Gunicorn workers
sudo nano gunicorn.conf.py
# workers = multiprocessing.cpu_count() * 2 + 1

# 4. Restart services
sudo systemctl daemon-reload
sudo systemctl start passprint celery-workers
```

### Monitoring Scaling

```bash
# Scale monitoring components
kubectl scale deployment passprint --replicas=5
kubectl scale deployment postgres --replicas=2
kubectl scale deployment redis --replicas=3

# Auto-scaling configuration
kubectl autoscale deployment passprint --cpu-percent=70 --min=3 --max=10
```

## Troubleshooting Deployment

### Common Issues

#### Application Won't Start

```bash
# Check application logs
sudo journalctl -u passprint -f

# Check system resources
htop

# Verify environment variables
python -c "from config import get_config; config = get_config(); print('DB URL:', config.SQLALCHEMY_DATABASE_URI)"

# Test database connection
python -c "
from app import create_app
app = create_app()
with app.app_context():
    from models import db
    try:
        db.engine.connect()
        print('✅ Database connection successful')
    except Exception as e:
        print(f'❌ Database error: {e}')
"
```

#### Performance Issues

```bash
# Check slow queries
python database_optimizer.py analyze

# Monitor system resources
python monitoring_alerting.py metrics

# Check cache performance
python performance_optimizer.py cache_analysis

# Run load test
python load_testing.py run_comprehensive
```

#### SSL Certificate Issues

```bash
# Check certificate status
sudo certbot certificates

# Test SSL configuration
curl -I https://your-domain.com

# Check Nginx SSL configuration
sudo nginx -t
sudo systemctl reload nginx
```

### Emergency Procedures

#### Quick Service Restart

```bash
# Restart all services
sudo systemctl restart passprint celery-workers nginx redis postgresql

# Check status
sudo systemctl status passprint celery-workers --no-pager
```

#### Emergency Database Recovery

```bash
# 1. Stop application
sudo systemctl stop passprint

# 2. Restore latest backup
python backup_system.py restore_database backups/latest_backup.dump

# 3. Verify restoration
python -c "
from app import create_app
from models import db
app = create_app()
with app.app_context():
    from models import User
    count = User.query.count()
    print(f'✅ Database restored: {count} users found')
"

# 4. Restart application
sudo systemctl start passprint
```

#### File System Recovery

```bash
# Restore uploaded files
python backup_system.py restore_files backups/latest_files_backup.tar.gz

# Verify file restoration
ls -la uploads/
```

## Maintenance Procedures

### Regular Maintenance

#### Daily Tasks

```bash
# 1. Check system health
curl -f http://localhost:5000/api/health

# 2. Monitor error logs
tail -f logs/error.log | grep -v "INFO"

# 3. Check disk usage
df -h

# 4. Monitor memory usage
free -h
```

#### Weekly Tasks

```bash
# 1. Full system backup
python backup_system.py create_full

# 2. Security updates
sudo apt update && sudo apt upgrade -y

# 3. Log rotation
sudo logrotate -f /etc/logrotate.d/passprint

# 4. Performance analysis
python performance_optimizer.py run_comprehensive
```

#### Monthly Tasks

```bash
# 1. Database maintenance
python postgresql_backup.py optimize

# 2. SSL certificate renewal
sudo certbot renew

# 3. Dependency updates
pip list --outdated
pip install -r requirements.txt --upgrade

# 4. Full system audit
python monitoring_alerting.py generate_report
```

### Log Management

```bash
# Configure log rotation
sudo nano /etc/logrotate.d/passprint

# /etc/logrotate.d/passprint
/opt/passprint-website/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 passprint passprint
    postrotate
        systemctl reload passprint || true
    endscript
}
```

### Backup Management

```bash
# Create manual backup
python backup_system.py create_full

# Check backup status
python backup_system.py get_status

# Test backup integrity
python backup_system.py test_integrity backups/latest.dump

# Cleanup old backups
python backup_system.py cleanup
```

## Support and Monitoring

### Monitoring Setup

```bash
# Install monitoring tools
sudo apt install prometheus grafana

# Configure Prometheus
sudo nano /etc/prometheus/prometheus.yml

# Configure Grafana
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
```

### Alert Configuration

```bash
# Configure alerting rules
sudo nano /etc/prometheus/alerts.yml

# Example alert rules
groups:
  - name: passprint
    rules:
      - alert: HighErrorRate
        expr: rate(passprint_api_errors_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
```

### Support Contacts

- **Technical Support**: tech@your-domain.com
- **Emergency Support**: emergency@your-domain.com
- **Monitoring Dashboard**: https://monitoring.your-domain.com

## Security Considerations

### Production Security Checklist

- [ ] SSL/TLS certificates installed and valid
- [ ] Firewall configured and active
- [ ] Security headers implemented
- [ ] Database credentials secured
- [ ] API keys rotated regularly
- [ ] Backups encrypted
- [ ] Access logging enabled
- [ ] Security monitoring active
- [ ] Dependencies updated
- [ ] Security patches applied

### Compliance

- **GDPR Compliance**: User data handling procedures
- **Data Retention**: Automated data cleanup policies
- **Audit Logging**: Complete audit trail maintenance
- **Incident Response**: Documented procedures for security incidents

## Performance Optimization

### Production Tuning

```bash
# Database tuning
sudo nano /etc/postgresql/13/main/postgresql.conf

# Key settings for production
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
checkpoint_segments = 32
wal_buffers = 16MB
default_statistics_target = 100

# Application tuning
sudo nano /etc/security/limits.conf

# Add limits for passprint user
passprint soft nofile 65536
passprint hard nofile 65536
passprint soft nproc 4096
passprint hard nproc 4096
```

### Monitoring and Alerting

```bash
# Install monitoring stack
sudo apt install prometheus grafana

# Configure alerts for:
# - High CPU usage (>80%)
# - High memory usage (>85%)
# - Database connection failures
# - High error rates (>5%)
# - Backup failures
# - Security incidents
```

## Cost Optimization

### Resource Optimization

1. **Right-size instances** based on actual usage
2. **Use reserved instances** for predictable workloads
3. **Implement auto-scaling** to handle traffic spikes
4. **Optimize storage** with appropriate retention policies
5. **Use spot instances** for non-critical workloads

### Monitoring Costs

1. **Optimize log retention** periods
2. **Use sampling** for high-volume metrics
3. **Archive old data** to cheaper storage
4. **Set up cost alerts** for monitoring expenses

## Success Metrics

### Key Performance Indicators

- **Application Availability**: >99.9%
- **Average Response Time**: <500ms
- **Error Rate**: <0.1%
- **Database Query Time**: <100ms average
- **Backup Success Rate**: >99%
- **Security Incidents**: 0 critical incidents

### Monitoring Dashboard

Access the monitoring dashboard at:
- **Main Dashboard**: https://your-domain.com/admin/monitoring
- **Metrics API**: https://your-domain.com/api/monitoring/metrics
- **Health Check**: https://your-domain.com/api/health

---

For additional support, contact the development team or refer to the troubleshooting section in the main README.