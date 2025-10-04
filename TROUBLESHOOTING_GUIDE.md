# 🔧 Troubleshooting Guide - PassPrint

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Application Issues](#application-issues)
3. [Database Issues](#database-issues)
4. [Performance Issues](#performance-issues)
5. [Security Issues](#security-issues)
6. [Deployment Issues](#deployment-issues)
7. [Monitoring Issues](#monitoring-issues)
8. [Backup Issues](#backup-issues)
9. [Integration Issues](#integration-issues)
10. [Emergency Procedures](#emergency-procedures)

## Quick Diagnostics

### System Health Check

```bash
# 1. Check application health
curl -f http://localhost:5000/api/health || echo "❌ Application not responding"

# 2. Check database connectivity
python -c "
from app import create_app
from models import db
app = create_app()
with app.app_context():
    try:
        db.engine.connect()
        print('✅ Database OK')
    except Exception as e:
        print(f'❌ Database error: {e}')
"

# 3. Check Redis connectivity
python -c "
import redis
try:
    r = redis.Redis.from_url('redis://localhost:6379/0')
    r.ping()
    print('✅ Redis OK')
except Exception as e:
    print(f'❌ Redis error: {e}')
"

# 4. Check system resources
python -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}%')
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'Disk: {psutil.disk_usage(\"/\").percent}%')
"
```

### Service Status Check

```bash
# Check all services
sudo systemctl status passprint --no-pager
sudo systemctl status celery-workers --no-pager
sudo systemctl status nginx --no-pager
sudo systemctl status postgresql --no-pager
sudo systemctl status redis --no-pager

# Check logs for errors
sudo journalctl -u passprint --since "1 hour ago" | grep -i error
tail -f /opt/passprint-website/logs/app.log | grep -i error
```

## Application Issues

### Application Won't Start

**Symptoms**: Application fails to start or immediately crashes

**Diagnosis**:
```bash
# Check for Python errors
python -c "import app; print('Import successful')"

# Check configuration
python -c "from config import get_config; print('Config loaded')"

# Check database migrations
python -c "
from app import create_app
app = create_app()
with app.app_context():
    from models import db
    print('Database models loaded')
"
```

**Common Solutions**:

1. **Missing Dependencies**
```bash
pip install -r requirements.txt
# or
pip install --upgrade -r requirements.txt
```

2. **Configuration Issues**
```bash
# Check environment variables
echo $SECRET_KEY
echo $DATABASE_URL
echo $REDIS_URL

# Validate configuration
python -c "
from config import get_config
try:
    config = get_config()
    print('Configuration valid')
except Exception as e:
    print(f'Configuration error: {e}')
"
```

3. **Database Issues**
```bash
# Check database connectivity
python -c "
from app import create_app
from models import db
app = create_app()
with app.app_context():
    try:
        db.create_all()
        print('Database tables created')
    except Exception as e:
        print(f'Database error: {e}')
"
```

4. **Port Conflicts**
```bash
# Check if port 5000 is in use
lsof -i :5000 || echo "Port 5000 available"

# Kill conflicting process
sudo lsof -ti:5000 | xargs sudo kill -9
```

### Application Crashes

**Symptoms**: Application starts but crashes under load or specific operations

**Diagnosis**:
```bash
# Check recent logs
tail -f logs/app.log | grep -i "error\|exception\|traceback"

# Check system resources during crash
htop

# Monitor memory usage
python -c "
import psutil
import time
for i in range(10):
    print(f'Memory: {psutil.virtual_memory().percent}%')
    time.sleep(1)
"
```

**Common Solutions**:

1. **Memory Issues**
```bash
# Check for memory leaks
python performance_optimizer.py memory_analysis

# Restart application with memory limits
sudo systemctl restart passprint
```

2. **Database Connection Issues**
```bash
# Check database connections
python -c "
from models import db
print('Pool size:', db.engine.pool.size())
print('Checked out:', db.engine.pool.checkedout())
"
```

3. **File Handle Leaks**
```bash
# Check open files
lsof -p $(pgrep -f "python.*app.py") | wc -l

# Restart to clear handles
sudo systemctl restart passprint
```

### Slow Response Times

**Symptoms**: API endpoints respond slowly or timeout

**Diagnosis**:
```bash
# Test response times
time curl http://localhost:5000/api/health

# Check database query performance
python database_optimizer.py analyze

# Monitor system performance
python monitoring_alerting.py metrics
```

**Common Solutions**:

1. **Database Optimization**
```bash
# Create performance indexes
python database_optimizer.py optimize

# Check slow queries
python -c "
from database_optimizer import analyze_database_performance
analysis = analyze_database_performance()
slow_queries = analysis.get('slow_queries', [])
for query in slow_queries[:5]:
    print(f'Slow query: {query}')
"
```

2. **Cache Issues**
```bash
# Check cache performance
python redis_cache.py health_check

# Clear problematic caches
python redis_cache.py clear_all
```

3. **Resource Constraints**
```bash
# Check system resources
python -c "
import psutil
cpu = psutil.cpu_percent(interval=1)
memory = psutil.virtual_memory().percent
print(f'CPU: {cpu}%, Memory: {memory}%')

if cpu > 80 or memory > 85:
    print('High resource usage detected')
"
```

## Database Issues

### Connection Issues

**Symptoms**: Database connection failures or timeouts

**Diagnosis**:
```bash
# Test database connection
python -c "
from app import create_app
from models import db
app = create_app()
with app.app_context():
    try:
        result = db.engine.execute('SELECT 1')
        print('✅ Database connection successful')
    except Exception as e:
        print(f'❌ Database error: {e}')
"
```

**Common Solutions**:

1. **PostgreSQL Issues**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-*.log

# Restart PostgreSQL
sudo systemctl restart postgresql
```

2. **SQLite Issues**
```bash
# Check SQLite file
ls -la passprint.db

# Check file permissions
chmod 644 passprint.db

# Check file integrity
sqlite3 passprint.db "PRAGMA integrity_check;"
```

3. **Connection Pool Issues**
```bash
# Check connection pool
python -c "
from models import db
pool = db.engine.pool
print(f'Pool size: {pool.size()}')
print(f'Checked out: {pool.checkedout()}')
print(f'Invalid: {pool.invalid()}')
"
```

### Query Performance Issues

**Symptoms**: Slow database queries affecting application performance

**Diagnosis**:
```bash
# Enable query logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Run application and monitor queries
python app.py 2>&1 | grep "SELECT\|INSERT\|UPDATE\|DELETE"
```

**Common Solutions**:

1. **Missing Indexes**
```bash
# Analyze and create indexes
python database_optimizer.py analyze
python database_optimizer.py optimize
```

2. **Query Optimization**
```bash
# Profile slow queries
python database_optimizer.py profile

# Optimize specific queries
python -c "
from database_optimizer import optimize_query_performance
result = optimize_query_performance('SELECT * FROM users WHERE email = ?', 'user_lookup')
print('Optimization suggestions:', result.get('optimization_suggestions', []))
"
```

3. **Connection Issues**
```bash
# Check connection pool settings
python -c "
from config import get_config
config = get_config()
print('Pool settings:', config.SQLALCHEMY_ENGINE_OPTIONS)
"
```

## Performance Issues

### High CPU Usage

**Symptoms**: CPU usage consistently above 80%

**Diagnosis**:
```bash
# Identify CPU-intensive processes
ps aux --sort=-pcpu | head -10

# Check for infinite loops
python -c "
import time
for i in range(5):
    print(f'CPU usage: {psutil.cpu_percent(interval=1)}%')
    time.sleep(1)
"
```

**Common Solutions**:

1. **Query Optimization**
```bash
# Find slow queries
python database_optimizer.py analyze

# Optimize database
python database_optimizer.py optimize
```

2. **Cache Issues**
```bash
# Check cache performance
python redis_cache.py get_stats

# Clear problematic caches
python redis_cache.py clear_namespace temp
```

3. **Application Issues**
```bash
# Profile application performance
python performance_optimizer.py run_comprehensive
```

### Memory Issues

**Symptoms**: Memory usage growing continuously or memory errors

**Diagnosis**:
```bash
# Monitor memory usage
python -c "
import psutil
import time
process = psutil.Process()
for i in range(10):
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f'Memory: {memory_mb:.1f}MB')
    time.sleep(1)
"

# Check for memory leaks
python performance_optimizer.py memory_analysis
```

**Common Solutions**:

1. **Memory Leak Detection**
```bash
# Run memory analysis
python performance_optimizer.py memory_analysis

# Check for common leaks
python -c "
import gc
print('Objects before GC:', len(gc.get_objects()))
gc.collect()
print('Objects after GC:', len(gc.get_objects()))
"
```

2. **Cache Memory Issues**
```bash
# Check cache memory usage
python redis_cache.py get_stats

# Clear memory caches
python redis_cache.py clear_all
```

3. **Application Memory Issues**
```bash
# Restart application to clear memory
sudo systemctl restart passprint

# Monitor memory after restart
python performance_optimizer.py memory_analysis
```

### Disk Space Issues

**Symptoms**: Low disk space affecting application performance

**Diagnosis**:
```bash
# Check disk usage
df -h

# Check large files
find /opt/passprint-website -type f -size +100M -exec ls -lh {} \;

# Check log file sizes
du -sh logs/*.log
```

**Common Solutions**:

1. **Clean Up Logs**
```bash
# Rotate and compress logs
sudo logrotate -f /etc/logrotate.d/passprint

# Clean old logs
find logs/ -name "*.log" -mtime +30 -delete

# Compress old backups
find backups/ -name "*.db" -mtime +7 -exec gzip {} \;
```

2. **Clean Up Temporary Files**
```bash
# Clean temp directory
rm -rf temp/*

# Clean old uploads
find uploads/ -mtime +30 -type f -delete

# Clean old backups
python backup_system.py cleanup
```

3. **Increase Disk Space**
```bash
# Add more storage if needed
# or
# Move logs/backups to external storage
```

## Security Issues

### Authentication Issues

**Symptoms**: Login failures or authentication errors

**Diagnosis**:
```bash
# Check authentication logs
tail -f logs/security.log | grep -i "login\|auth"

# Check failed login attempts
python -c "
from models import AuditLog
from datetime import datetime, timedelta

recent_failures = AuditLog.query.filter(
    AuditLog.action == 'failed_login',
    AuditLog.created_at >= datetime.utcnow() - timedelta(minutes=5)
).count()

print(f'Failed logins (5min): {recent_failures}')
"
```

**Common Solutions**:

1. **Account Lockout**
```bash
# Check if account is locked
python -c "
from security_system import security_system
lockout = security_system.check_account_lockout('user@example.com')
print('Account locked:', lockout['locked'])
"

# Reset failed attempts (admin only)
python -c "
from security_system import security_system
# This would require admin access
"
```

2. **Password Issues**
```bash
# Reset password via email
curl -X POST http://localhost:5000/api/auth/forgot-password \
  -H 'Content-Type: application/json' \
  -d '{"email": "user@example.com"}'
```

3. **Token Issues**
```bash
# Verify token
curl -X POST http://localhost:5000/api/auth/verify \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

### Security Alerts

**Symptoms**: Security monitoring alerts triggered

**Diagnosis**:
```bash
# Check security logs
tail -f logs/security.log

# Check audit logs
python -c "
from models import AuditLog
from datetime import datetime, timedelta

recent_events = AuditLog.query.filter(
    AuditLog.created_at >= datetime.utcnow() - timedelta(hours=1)
).order_by(AuditLog.created_at.desc()).limit(10).all()

for event in recent_events:
    print(f'{event.action}: {event.details}')
"
```

**Common Solutions**:

1. **Suspicious Activity**
```bash
# Check for suspicious IPs
python -c "
from models import AuditLog
from collections import Counter

recent_ips = AuditLog.query.filter(
    AuditLog.ip_address.isnot(None)
).order_by(AuditLog.created_at.desc()).limit(100).all()

ip_counts = Counter([event.ip_address for event in recent_ips])
suspicious_ips = [ip for ip, count in ip_counts.items() if count > 50]

print('Suspicious IPs:', suspicious_ips)
"
```

2. **Brute Force Attacks**
```bash
# Check for brute force attempts
python -c "
from models import AuditLog
from datetime import datetime, timedelta

failed_attempts = AuditLog.query.filter(
    AuditLog.action == 'failed_login',
    AuditLog.created_at >= datetime.utcnow() - timedelta(minutes=5)
).count()

print(f'Failed attempts (5min): {failed_attempts}')

if failed_attempts > 20:
    print('⚠️ Potential brute force attack detected')
"
```

## Deployment Issues

### Docker Issues

**Symptoms**: Docker containers fail to start or work properly

**Diagnosis**:
```bash
# Check container status
docker-compose ps

# Check container logs
docker-compose logs web
docker-compose logs db
docker-compose logs redis

# Check resource usage
docker stats
```

**Common Solutions**:

1. **Container Issues**
```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Clean up Docker
docker system prune -a
docker volume prune
```

2. **Network Issues**
```bash
# Check Docker network
docker network ls
docker network inspect passprint_default

# Restart Docker service
sudo systemctl restart docker
```

### Kubernetes Issues

**Symptoms**: Pods fail to start or services unavailable

**Diagnosis**:
```bash
# Check pod status
kubectl get pods -n passprint

# Check pod logs
kubectl logs -n passprint deployment/passprint

# Check service endpoints
kubectl get endpoints -n passprint

# Check events
kubectl get events -n passprint --sort-by=.metadata.creationTimestamp
```

**Common Solutions**:

1. **Resource Issues**
```bash
# Check resource quotas
kubectl describe resourcequota -n passprint

# Check node resources
kubectl describe nodes | grep -A 10 "Allocated resources"
```

2. **Configuration Issues**
```bash
# Check config maps and secrets
kubectl get configmap,secret -n passprint

# Validate YAML files
kubectl apply --dry-run=client -f deployment.yaml
```

### SSL Certificate Issues

**Symptoms**: HTTPS not working or certificate errors

**Diagnosis**:
```bash
# Check certificate status
sudo certbot certificates

# Test SSL configuration
curl -I https://your-domain.com

# Check Nginx SSL configuration
sudo nginx -t
sudo systemctl reload nginx
```

**Common Solutions**:

1. **Certificate Expired**
```bash
# Renew certificate
sudo certbot renew

# Check renewal status
sudo certbot certificates
```

2. **Certificate Misconfiguration**
```bash
# Reissue certificate
sudo certbot certonly --standalone -d your-domain.com

# Update Nginx configuration
sudo nano /etc/nginx/sites-available/passprint
sudo nginx -t
sudo systemctl reload nginx
```

## Monitoring Issues

### Metrics Not Collecting

**Symptoms**: Monitoring dashboard shows no data or outdated information

**Diagnosis**:
```bash
# Check monitoring service
python -c "
from monitoring_alerting import get_monitoring_dashboard
dashboard = get_monitoring_dashboard()
print('Monitoring running:', dashboard.metrics_collector.running if dashboard else False)
"

# Check metrics collection
curl http://localhost:5000/api/monitoring/metrics
```

**Common Solutions**:

1. **Monitoring Not Started**
```bash
# Start monitoring manually
python -c "
from monitoring_alerting import init_monitoring
from app import create_app
app = create_app()
init_monitoring(app)
print('Monitoring started')
"
```

2. **Configuration Issues**
```bash
# Check monitoring configuration
python -c "
from config import get_config
config = get_config()
print('Monitoring enabled:', config.MONITORING_CONFIG.get('enabled', False))
"
```

### Alerts Not Firing

**Symptoms**: Monitoring shows issues but no alerts are sent

**Diagnosis**:
```bash
# Check alert configuration
python -c "
from monitoring_alerting import get_monitoring_dashboard
dashboard = get_monitoring_dashboard()
alert_manager = dashboard.alert_manager
print('Alert rules:', len(alert_manager.alert_rules))
print('Notification channels:', len(alert_manager.notification_channels))
"

# Test alert manually
python -c "
from monitoring_alerting import get_monitoring_dashboard
dashboard = get_monitoring_dashboard()
test_metrics = {'system': {'cpu': {'percent': 95}}}
dashboard.alert_manager.check_alerts(test_metrics)
"
```

**Common Solutions**:

1. **Email Configuration**
```bash
# Test email configuration
python -c "
from flask_mail import Mail, Message
from app import create_app

app = create_app()
with app.app_context():
    mail = Mail(app)
    try:
        msg = Message('Test Alert', recipients=['admin@example.com'])
        print('✅ Email configuration valid')
    except Exception as e:
        print(f'❌ Email error: {e}')
"
```

2. **Slack Configuration**
```bash
# Test Slack webhook
python -c "
import requests
webhook_url = 'https://hooks.slack.com/your-webhook'
response = requests.post(webhook_url, json={'text': 'Test alert'})
print('Slack status:', response.status_code)
"
```

## Backup Issues

### Backup Failures

**Symptoms**: Automated backups fail or produce errors

**Diagnosis**:
```bash
# Check backup logs
tail -f logs/app.log | grep -i backup

# Check backup status
python backup_system.py get_status

# Test backup manually
python backup_system.py create_full
```

**Common Solutions**:

1. **Disk Space Issues**
```bash
# Check available space
df -h /opt/passprint-website

# Clean old backups
python backup_system.py cleanup

# Check backup directory permissions
ls -ld backups/
chmod 755 backups/
```

2. **Database Connection Issues**
```bash
# Test database connection
python -c "
from app import create_app
from models import db
app = create_app()
with app.app_context():
    try:
        db.engine.connect()
        print('✅ Database connection OK')
    except Exception as e:
        print(f'❌ Database error: {e}')
"
```

3. **PostgreSQL Issues**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check pg_dump availability
which pg_dump

# Test pg_dump manually
pg_dump --version
```

### Backup Restoration Issues

**Symptoms**: Backup restoration fails or produces incomplete results

**Diagnosis**:
```bash
# Check backup file integrity
python backup_system.py test_integrity backups/latest.dump

# Check database before restoration
python -c "
from app import create_app
from models import db
app = create_app()
with app.app_context():
    from models import User
    print('Users before restoration:', User.query.count())
"
```

**Common Solutions**:

1. **Corrupted Backup Files**
```bash
# Find latest valid backup
python -c "
from backup_system import backup_system
status = backup_system.get_backup_status()
valid_backups = [b for b in status if b['status'] == 'success']
if valid_backups:
    latest = max(valid_backups, key=lambda x: x['created_at'])
    print('Latest valid backup:', latest['file_path'])
else:
    print('No valid backups found')
"
```

2. **Permission Issues**
```bash
# Check file permissions
ls -la backups/latest.dump

# Fix permissions
chmod 644 backups/latest.dump
chown passprint:passprint backups/latest.dump
```

3. **Database State Issues**
```bash
# Create emergency backup before restoration
python backup_system.py create_database_backup

# Restore with verification
python backup_system.py restore_database backups/latest.dump
```

## Integration Issues

### Payment Integration Issues

**Symptoms**: Stripe payments fail or webhook errors

**Diagnosis**:
```bash
# Check Stripe configuration
python -c "
import os
print('Stripe secret key set:', bool(os.getenv('STRIPE_SECRET_KEY')))
print('Stripe webhook secret set:', bool(os.getenv('STRIPE_WEBHOOK_SECRET')))
"

# Test Stripe connection
python -c "
import stripe
stripe.api_key = 'sk_test_...'
try:
    balance = stripe.Balance.retrieve()
    print('✅ Stripe connection OK')
except Exception as e:
    print(f'❌ Stripe error: {e}')
"
```

**Common Solutions**:

1. **Webhook Configuration**
```bash
# Check webhook endpoint
curl -X POST https://your-domain.com/api/webhooks/stripe \
  -H 'Content-Type: application/json' \
  -d '{"test": "webhook"}'

# Verify webhook signature
python -c "
import stripe
# Verify webhook signature in your webhook handler
"
```

2. **API Key Issues**
```bash
# Check API key format
python -c "
import os
key = os.getenv('STRIPE_SECRET_KEY', '')
print('Key length:', len(key))
print('Key prefix:', key[:7] if len(key) > 7 else 'Too short')
"
```

### Email Integration Issues

**Symptoms**: Email sending fails or emails not received

**Diagnosis**:
```bash
# Test SMTP connection
python -c "
import smtplib
try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('your-email@gmail.com', 'your-password')
    server.quit()
    print('✅ SMTP connection OK')
except Exception as e:
    print(f'❌ SMTP error: {e}')
"
```

**Common Solutions**:

1. **Gmail SMTP Issues**
```bash
# Enable 2FA and generate app password
# Use app password instead of regular password
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-character-app-password
```

2. **SendGrid Issues**
```bash
# Test SendGrid API
python -c "
import requests
response = requests.get('https://api.sendgrid.com/v3/user/account',
                       headers={'Authorization': 'Bearer YOUR_API_KEY'})
print('SendGrid status:', response.status_code)
"
```

### CDN Integration Issues

**Symptoms**: Static assets not loading or CDN not working

**Diagnosis**:
```bash
# Test CDN connectivity
curl -I https://cdn.your-domain.com/static/css/style.css

# Check DNS configuration
nslookup cdn.your-domain.com

# Check CloudFlare status
curl -I https://your-domain.com/cdn-cgi/trace
```

**Common Solutions**:

1. **CloudFlare Issues**
```bash
# Check CloudFlare configuration
# Login to CloudFlare dashboard
# Verify DNS records
# Check SSL/TLS settings
# Verify cache rules
```

2. **AWS CloudFront Issues**
```bash
# Check distribution status
aws cloudfront get-distribution --id YOUR_DISTRIBUTION_ID

# Test invalidation
aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths "/*"
```

## Emergency Procedures

### System Recovery

**Complete System Failure**:
```bash
# 1. Assess the situation
python monitoring_alerting.py metrics

# 2. Create emergency backup
python backup_system.py create_full

# 3. Restore from latest backup
python disaster_recovery.py initiate_automatic_recovery

# 4. Verify system health
curl http://localhost:5000/api/health

# 5. Notify stakeholders
python -c "
# Send emergency notification
"
```

### Database Recovery

**Database Corruption**:
```bash
# 1. Stop application
sudo systemctl stop passprint

# 2. Create emergency backup
cp passprint.db passprint.db.emergency.$(date +%Y%m%d_%H%M%S)

# 3. Restore from backup
python backup_system.py restore_database backups/latest_valid_backup.dump

# 4. Verify restoration
python -c "
from app import create_app
from models import db
app = create_app()
with app.app_context():
    from models import User, Order
    print('Users:', User.query.count())
    print('Orders:', Order.query.count())
"

# 5. Restart application
sudo systemctl start passprint
```

### Security Incident Response

**Security Breach Detected**:
```bash
# 1. Isolate the system
sudo ufw deny from 0.0.0.0/0

# 2. Change all passwords
python -c "
# Generate new passwords and update
"

# 3. Audit access logs
python -c "
from models import AuditLog
from datetime import datetime, timedelta

recent_access = AuditLog.query.filter(
    AuditLog.created_at >= datetime.utcnow() - timedelta(hours=24)
).all()

for event in recent_access:
    print(f'{event.created_at}: {event.action} from {event.ip_address}')
"

# 4. Notify security team
# Send emergency security notification

# 5. Investigate and recover
python security_system.py audit_security_events
```

### Performance Emergency

**System Under Extreme Load**:
```bash
# 1. Enable maintenance mode
python -c "
from models import SystemConfig
from models import db

config = SystemConfig.query.filter_by(key='maintenance_mode').first()
if not config:
    config = SystemConfig(key='maintenance_mode', value='true')
    db.session.add(config)
else:
    config.value = 'true'
db.session.commit()
"

# 2. Restart services with reduced load
sudo systemctl restart passprint
sudo systemctl restart nginx

# 3. Clear caches
python redis_cache.py clear_all

# 4. Monitor recovery
python monitoring_alerting.py metrics

# 5. Gradually restore normal operation
```

## Advanced Troubleshooting

### Log Analysis

**Extract Error Patterns**:
```bash
# Find most common errors
tail -f logs/app.log | grep -o '"error": "[^"]*"' | sort | uniq -c | sort -nr

# Find slow endpoints
tail -f logs/app.log | grep -o '"endpoint": "[^"]*"' | sort | uniq -c | sort -nr

# Find IP patterns
tail -f logs/app.log | grep -o '"ip_address": "[^"]*"' | sort | uniq -c | sort -nr
```

### Database Query Analysis

**Find Slow Queries**:
```bash
# Enable slow query logging
python -c "
from config import get_config
config = get_config()
config.SQLALCHEMY_ECHO = True
"

# Analyze query patterns
python database_optimizer.py analyze
```

### Memory Analysis

**Deep Memory Investigation**:
```bash
# Use memory profiler
python -m memory_profiler app.py

# Check object types
python -c "
import gc
from collections import Counter

objects = gc.get_objects()
types = Counter(type(obj).__name__ for obj in objects)
print('Top object types:', types.most_common(10))
"
```

### Network Analysis

**Check Network Issues**:
```bash
# Test connectivity
ping 8.8.8.8
traceroute your-domain.com

# Check open ports
netstat -tlnp | grep :5000

# Check firewall
sudo ufw status
```

## Automated Diagnostics

### Create Diagnostic Script

```bash
#!/bin/bash
# diagnostic.sh - Automated system diagnostics

echo "🔍 PassPrint System Diagnostics"
echo "================================"

# 1. System Health
echo "1. System Health:"
curl -s http://localhost:5000/api/health | jq . 2>/dev/null || echo "❌ API not responding"

# 2. Database
echo "2. Database:"
python -c "
from app import create_app
from models import db
app = create_app()
with app.app_context():
    try:
        db.engine.connect()
        print('✅ Database OK')
    except Exception as e:
        print(f'❌ Database error: {e}')
"

# 3. Services
echo "3. Services:"
sudo systemctl is-active passprint && echo "✅ PassPrint running" || echo "❌ PassPrint stopped"
sudo systemctl is-active redis && echo "✅ Redis running" || echo "❌ Redis stopped"
sudo systemctl is-active postgresql && echo "✅ PostgreSQL running" || echo "❌ PostgreSQL stopped"

# 4. Resources
echo "4. Resources:"
python -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}%')
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'Disk: {psutil.disk_usage(\"/\").percent}%')
"

# 5. Recent Errors
echo "5. Recent Errors:"
tail -5 logs/app.log | grep -i error || echo "No recent errors"

echo "================================"
echo "Diagnostics complete"
```

### Performance Benchmarking

```bash
# benchmark.sh - Performance benchmarking

echo "⚡ Performance Benchmark"
echo "======================="

# Test API endpoints
echo "Testing API endpoints..."
time curl -s http://localhost:5000/api/health > /dev/null
echo "Health check: $?"

time curl -s http://localhost:5000/api/products > /dev/null
echo "Products list: $?"

# Test database performance
echo "Testing database performance..."
python database_optimizer.py analyze

# Test load
echo "Testing load..."
python load_testing.py run_comprehensive

echo "======================="
echo "Benchmark complete"
```

## Support Integration

### Generate Support Bundle

```python
# support_bundle.py
import json
import os
from datetime import datetime
from pathlib import Path

def generate_support_bundle():
    """Generate a support bundle with system information"""
    bundle = {
        'timestamp': datetime.utcnow().isoformat(),
        'system_info': {},
        'configuration': {},
        'recent_logs': {},
        'performance_metrics': {},
        'error_summary': {}
    }

    # System information
    bundle['system_info'] = {
        'platform': os.uname().sysname,
        'python_version': os.sys.version,
        'environment': os.getenv('FLASK_ENV', 'unknown')
    }

    # Configuration (without secrets)
    from config import get_config
    config = get_config()
    bundle['configuration'] = {
        'debug': config.DEBUG,
        'database_url': config.SQLALCHEMY_DATABASE_URI.replace('password', '***'),
        'redis_url': config.REDIS_URL.replace('password', '***') if hasattr(config, 'REDIS_URL') else 'not set'
    }

    # Recent logs
    log_files = ['logs/app.log', 'logs/error.log', 'logs/security.log']
    for log_file in log_files:
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                lines = f.readlines()
                bundle['recent_logs'][log_file] = lines[-50:]  # Last 50 lines

    # Performance metrics
    try:
        from monitoring_alerting import get_monitoring_dashboard
        dashboard = get_monitoring_dashboard()
        if dashboard:
            bundle['performance_metrics'] = dashboard.metrics_collector.metrics
    except:
        bundle['performance_metrics'] = {'error': 'Could not collect metrics'}

    # Save bundle
    bundle_file = f"support_bundle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(bundle_file, 'w') as f:
        json.dump(bundle, f, indent=2, default=str)

    return bundle_file

if __name__ == "__main__":
    bundle_file = generate_support_bundle()
    print(f"Support bundle generated: {bundle_file}")
```

### Remote Diagnostics

```python
# remote_diagnostics.py
import requests
import json

def run_remote_diagnostics(api_url, auth_token):
    """Run diagnostics on remote system"""
    headers = {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json'
    }

    # Collect remote metrics
    try:
        health = requests.get(f'{api_url}/api/monitoring/health', headers=headers)
        metrics = requests.get(f'{api_url}/api/monitoring/metrics', headers=headers)
        alerts = requests.get(f'{api_url}/api/monitoring/alerts', headers=headers)

        return {
            'health': health.json() if health.status_code == 200 else {'error': 'Health check failed'},
            'metrics': metrics.json() if metrics.status_code == 200 else {'error': 'Metrics failed'},
            'alerts': alerts.json() if alerts.status_code == 200 else {'error': 'Alerts failed'}
        }

    except Exception as e:
        return {'error': str(e)}
```

## Prevention Measures

### Proactive Monitoring

```bash
# Setup proactive monitoring
python -c "
# Check system health every 5 minutes
import time
import subprocess

while True:
    result = subprocess.run(['curl', '-s', 'http://localhost:5000/api/health'], capture_output=True)
    if result.returncode != 0:
        print('System health check failed!')
        # Send alert
    time.sleep(300)
"
```

### Automated Maintenance

```bash
# daily_maintenance.sh
#!/bin/bash

# Log maintenance
find logs/ -name "*.log" -mtime +7 -exec rm {} \;

# Backup cleanup
python backup_system.py cleanup

# Database maintenance
python database_optimizer.py optimize

# Performance check
python performance_optimizer.py run_comprehensive

# Security audit
python security_system.py audit_security_events
```

### Health Check Automation

```python
# health_check_monitor.py
import time
import requests
from datetime import datetime

def monitor_system_health():
    """Monitor system health continuously"""
    while True:
        try:
            response = requests.get('http://localhost:5000/api/health', timeout=10)

            if response.status_code != 200:
                print(f"Health check failed: {response.status_code}")

                # Try to restart services
                import subprocess
                subprocess.run(['sudo', 'systemctl', 'restart', 'passprint'])

            time.sleep(60)  # Check every minute

        except Exception as e:
            print(f"Health monitor error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    monitor_system_health()
```

## Getting Help

### Support Escalation

1. **Self-Service**: Use this troubleshooting guide
2. **Documentation**: Check the main documentation
3. **Community**: Ask questions in the community forum
4. **Email Support**: Contact support@passprint.com
5. **Emergency Support**: Use the emergency contact number

### Support Information

When contacting support, please include:

- **System Information**: Operating system, Python version
- **Error Messages**: Complete error logs
- **Configuration**: Environment and settings (without secrets)
- **Recent Changes**: What changed before the issue occurred
- **Troubleshooting Steps**: What you've already tried

### Emergency Contacts

- **Technical Emergency**: +225 01 02 03 04 05
- **Security Emergency**: security@passprint.com
- **Data Emergency**: data@passprint.com

## Best Practices

### Prevention

1. **Regular Monitoring**: Set up automated health checks
2. **Log Management**: Implement proper log rotation
3. **Backup Testing**: Regularly test backup restoration
4. **Security Updates**: Keep all software updated
5. **Performance Monitoring**: Track performance trends

### Documentation

1. **Keep Records**: Document all changes and issues
2. **Update Procedures**: Keep troubleshooting guides current
3. **Share Knowledge**: Document solutions for the team
4. **Regular Reviews**: Review and update documentation

### Training

1. **Team Training**: Train team on common issues
2. **Documentation**: Keep documentation accessible
3. **Runbooks**: Create runbooks for common procedures
4. **Drills**: Conduct regular emergency drills

---

For additional help, contact the PassPrint support team or refer to the main documentation.