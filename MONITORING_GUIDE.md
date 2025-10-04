# 📊 Monitoring Guide - PassPrint

## Table of Contents

1. [Monitoring Overview](#monitoring-overview)
2. [System Health Monitoring](#system-health-monitoring)
3. [Performance Monitoring](#performance-monitoring)
4. [Security Monitoring](#security-monitoring)
5. [Database Monitoring](#database-monitoring)
6. [Application Monitoring](#application-monitoring)
7. [Alert Configuration](#alert-configuration)
8. [Dashboard Setup](#dashboard-setup)
9. [External Integrations](#external-integrations)
10. [Troubleshooting](#troubleshooting)

## Monitoring Overview

PassPrint includes comprehensive monitoring capabilities covering:

- **System Health**: CPU, memory, disk, network monitoring
- **Application Performance**: Response times, throughput, error rates
- **Database Performance**: Query performance, connection monitoring
- **Security Events**: Authentication, authorization, threat detection
- **Business Metrics**: Orders, users, revenue tracking
- **Infrastructure Monitoring**: Services, dependencies, external APIs

## System Health Monitoring

### Real-Time Metrics Collection

The monitoring system collects metrics every 5 seconds:

```python
# Access current metrics
from monitoring_alerting import get_monitoring_dashboard

dashboard = get_monitoring_dashboard()
current_metrics = dashboard.metrics_collector.metrics

# System metrics
cpu_usage = current_metrics['system']['cpu']['percent']
memory_usage = current_metrics['system']['memory']['percent']
disk_usage = current_metrics['system']['disk']['percent']
```

### Health Check Endpoints

#### Application Health
```bash
# Basic health check
curl http://localhost:5000/api/health

# Detailed health check
curl http://localhost:5000/api/monitoring/health

# System metrics
curl http://localhost:5000/api/monitoring/metrics
```

#### Database Health
```bash
# Database connectivity
python -c "
from models import db
try:
    db.engine.connect()
    print('✅ Database healthy')
except Exception as e:
    print(f'❌ Database error: {e}')
"
```

#### Service Health
```bash
# Check all services
sudo systemctl status passprint redis postgresql nginx

# Check service dependencies
python -c "
import redis
from app import create_app

# Test Redis
try:
    r = redis.Redis.from_url('redis://localhost:6379/0')
    r.ping()
    print('✅ Redis healthy')
except:
    print('❌ Redis error')

# Test application
try:
    app = create_app()
    with app.app_context():
        from models import User
        User.query.first()
    print('✅ Application healthy')
except Exception as e:
    print(f'❌ Application error: {e}')
"
```

## Performance Monitoring

### Response Time Tracking

Monitor API endpoint performance:

```python
# Enable performance monitoring
from performance_optimizer import profile_performance

@profile_performance('api_endpoint')
def my_api_endpoint():
    # Your endpoint logic
    pass
```

### Database Query Monitoring

Track slow queries and performance:

```python
# Profile database operations
from database_optimizer import profile_query

with profile_query("SELECT * FROM users", "user_query"):
    users = User.query.all()
```

### Cache Performance Monitoring

Monitor cache effectiveness:

```python
# Get cache statistics
from redis_cache import get_cache_stats

stats = get_cache_stats()
print(f"Cache efficiency: {stats}")
```

### Load Testing

Run performance tests:

```bash
# Run comprehensive load test
python load_testing.py run_comprehensive

# Test specific endpoint
python load_testing.py run_load_test /api/products

# Generate performance report
python performance_optimizer.py generate_report
```

## Security Monitoring

### Security Event Tracking

Monitor authentication and security events:

```python
# Get recent security events
from models import AuditLog

recent_events = AuditLog.query.filter(
    AuditLog.created_at >= datetime.utcnow() - timedelta(hours=1)
).order_by(AuditLog.created_at.desc()).all()

for event in recent_events:
    print(f"{event.action}: {event.details}")
```

### Threat Detection

Monitor for suspicious activities:

```python
# Check for failed login attempts
from models import AuditLog
from datetime import datetime, timedelta

failed_logins = AuditLog.query.filter(
    AuditLog.action == 'failed_login',
    AuditLog.created_at >= datetime.utcnow() - timedelta(minutes=5)
).count()

if failed_logins > 10:
    print("⚠️ High number of failed login attempts detected")
```

### Security Metrics

```python
# Get security statistics
from monitoring_alerting import get_monitoring_dashboard

dashboard = get_monitoring_dashboard()
security_metrics = dashboard.metrics_collector.metrics.get('security', {})

print(f"Security score: {security_metrics.get('events', {}).get('security_score', 100)}")
```

## Database Monitoring

### Query Performance Analysis

```python
# Analyze slow queries
from database_optimizer import analyze_database_performance

analysis = analyze_database_performance()

if 'slow_queries' in analysis:
    for query in analysis['slow_queries']:
        print(f"Slow query: {query['query']} ({query['mean_time']}ms)")
```

### Database Health Checks

```python
# Comprehensive database health check
from database_optimizer import DatabaseOptimizer

optimizer = DatabaseOptimizer()
health = optimizer.analyze_database_performance()

print(f"Database size: {health.get('database_size', 0)} bytes")
print(f"Table count: {health.get('table_count', 0)}")
print(f"Index count: {health.get('index_count', 0)}")
```

### Connection Pool Monitoring

```python
# Monitor database connections
from monitoring_alerting import get_monitoring_dashboard

dashboard = get_monitoring_dashboard()
db_metrics = dashboard.metrics_collector.metrics.get('database', {})

connection_healthy = db_metrics.get('stats', {}).get('connection_healthy', False)
print(f"Database connection: {'✅ Healthy' if connection_healthy else '❌ Unhealthy'}")
```

## Application Monitoring

### API Endpoint Monitoring

Monitor API performance:

```python
# Get API performance metrics
from monitoring_alerting import get_monitoring_dashboard

dashboard = get_monitoring_dashboard()
app_metrics = dashboard.metrics_collector.metrics.get('application', {})

print(f"Application health: {app_metrics.get('health', {}).get('status', 'unknown')}")
```

### Error Rate Monitoring

Track application errors:

```python
# Monitor error rates
from monitoring_alerting import get_monitoring_dashboard

dashboard = get_monitoring_dashboard()
error_analysis = dashboard.metrics_collector.metrics.get('application', {}).get('performance', {}).get('log_analysis', {})

error_count = error_analysis.get('error_count', 0)
total_lines = error_analysis.get('total_lines', 1)
error_rate = error_count / total_lines

print(f"Error rate: {error_rate:.2%}")
```

### Business Metrics Monitoring

Track business KPIs:

```python
# Monitor business metrics
from models import Order, User, Product

today = datetime.utcnow().date()

orders_today = Order.query.filter(
    Order.created_at >= today
).count()

users_today = User.query.filter(
    User.created_at >= today
).count()

revenue_today = Order.query.filter(
    Order.created_at >= today,
    Order.payment_status == 'paid'
).with_entities(func.sum(Order.total_amount)).scalar() or 0

print(f"Orders today: {orders_today}")
print(f"New users today: {users_today}")
print(f"Revenue today: {revenue_today} FCFA")
```

## Alert Configuration

### Alert Rules Setup

Configure monitoring alerts:

```python
# Configure alert thresholds
ALERT_THRESHOLDS = {
    'cpu_usage': 80,           # Alert if CPU > 80%
    'memory_usage': 85,        # Alert if Memory > 85%
    'disk_usage': 90,          # Alert if Disk > 90%
    'error_rate': 5,           # Alert if Error rate > 5%
    'response_time': 2000,     # Alert if Response time > 2s
    'security_score': 70       # Alert if Security score < 70
}
```

### Email Alert Configuration

```python
# Configure email alerts
ALERT_EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'username': 'alerts@your-domain.com',
    'password': 'your-app-password',
    'recipients': ['admin@your-domain.com', 'ops@your-domain.com']
}
```

### Slack Alert Configuration

```python
# Configure Slack alerts
SLACK_CONFIG = {
    'webhook_url': 'https://hooks.slack.com/your-webhook-url',
    'channel': '#alerts',
    'username': 'PassPrint Monitor',
    'icon_emoji': ':warning:'
}
```

### Custom Alert Rules

```python
# monitoring_alerting.py - Add custom alert rules

CUSTOM_ALERT_RULES = {
    'high_order_volume': {
        'condition': lambda metrics: self._check_order_volume(metrics),
        'severity': 'info',
        'message': 'High order volume detected: {order_count} orders/hour',
        'cooldown_minutes': 60
    },
    'payment_failure_spike': {
        'condition': lambda metrics: self._check_payment_failures(metrics),
        'severity': 'critical',
        'message': 'Payment failure spike detected',
        'cooldown_minutes': 15
    }
}
```

## Dashboard Setup

### Monitoring Dashboard Access

1. **Admin Access**: Navigate to `/admin/monitoring`
2. **API Access**: Use `/api/monitoring/*` endpoints
3. **Real-Time Updates**: Dashboard updates every 30 seconds

### Dashboard Features

- **System Overview**: CPU, memory, disk utilization
- **Performance Charts**: Response times, throughput, error rates
- **Alert Management**: View and resolve active alerts
- **Database Status**: Connection health, query performance
- **Security Status**: Recent events, threat level
- **Business Metrics**: Orders, users, revenue tracking

### Custom Dashboard Widgets

```javascript
// Add custom widget to monitoring dashboard
function addCustomWidget() {
    const widget = {
        id: 'custom_orders',
        title: 'Recent Orders',
        type: 'chart',
        dataSource: '/api/monitoring/orders',
        refreshInterval: 60000
    };

    // Add to dashboard
    dashboard.addWidget(widget);
}
```

## External Integrations

### Prometheus Integration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'passprint'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Grafana Dashboard Setup

1. **Install Grafana**
```bash
sudo apt install grafana
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
```

2. **Access Grafana**: http://localhost:3000 (admin/admin)

3. **Add Data Source**
   - Name: Prometheus
   - Type: Prometheus
   - URL: http://localhost:9090

4. **Import Dashboard**
```bash
# Import the provided dashboard JSON
curl -X POST http://localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d @monitoring_dashboard.json
```

### Sentry Error Tracking

```python
# Configure Sentry
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="https://your-sentry-dsn@sentry.io/project",
    integrations=[FlaskIntegration()],
    environment="production",
    traces_sample_rate=1.0
)
```

### Elasticsearch Log Aggregation

```python
# Configure Elasticsearch
from elasticsearch import Elasticsearch

es = Elasticsearch(['http://localhost:9200'])
es.index(index='passprint-logs', document={
    'timestamp': datetime.utcnow(),
    'level': 'INFO',
    'message': 'Application started',
    'service': 'passprint'
})
```

## Troubleshooting

### Common Monitoring Issues

#### Metrics Not Collecting

```bash
# Check if monitoring is enabled
python -c "
from config import get_config
config = get_config()
print('Monitoring enabled:', config.MONITORING_CONFIG.get('enabled', False))
"

# Check monitoring service status
python -c "
from monitoring_alerting import get_monitoring_dashboard
dashboard = get_monitoring_dashboard()
print('Monitoring running:', dashboard.metrics_collector.running if dashboard else False)
"
```

#### Alerts Not Firing

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
test_metrics = {'system': {'cpu': {'percent': 90}}}
dashboard.alert_manager.check_alerts(test_metrics)
"
```

#### Dashboard Not Loading

```bash
# Check dashboard file
ls -la monitoring_dashboard.html

# Check API endpoints
curl http://localhost:5000/api/monitoring/health
curl http://localhost:5000/api/monitoring/metrics

# Check browser console for JavaScript errors
# Open Developer Tools → Console
```

### Performance Issues

#### High CPU Usage

```bash
# Identify CPU-intensive processes
ps aux --sort=-pcpu | head -10

# Check for slow queries
python database_optimizer.py analyze

# Monitor application performance
python performance_optimizer.py memory_analysis
```

#### Memory Leaks

```bash
# Check memory usage
python performance_optimizer.py memory_analysis

# Monitor garbage collection
python -c "
import gc
print('Objects tracked:', len(gc.get_objects()))
gc.collect()
print('After GC:', len(gc.get_objects()))
"
```

#### Slow Database Queries

```bash
# Analyze query performance
python database_optimizer.py analyze

# Check database connections
python -c "
from models import db
engine = db.engine
print('Pool size:', engine.pool.size())
print('Checked out:', engine.pool.checkedout())
"
```

### Alert Troubleshooting

#### Email Alerts Not Working

```bash
# Test email configuration
python -c "
from flask_mail import Mail, Message
from app import create_app

app = create_app()
with app.app_context():
    mail = Mail(app)
    try:
        msg = Message('Test Alert', recipients=['test@example.com'])
        print('✅ Email configuration valid')
    except Exception as e:
        print(f'❌ Email error: {e}')
"
```

#### Slack Alerts Not Working

```bash
# Test Slack webhook
python -c "
import requests
import json

webhook_url = 'https://hooks.slack.com/your-webhook-url'
payload = {
    'text': 'Test alert from PassPrint',
    'username': 'PassPrint Monitor'
}

response = requests.post(webhook_url, json=payload)
print('Slack status:', response.status_code)
"
```

### Database Monitoring Issues

#### Connection Pool Issues

```bash
# Check database connections
python -c "
from models import db
from sqlalchemy import text

try:
    result = db.engine.execute(text('SELECT COUNT(*) FROM pg_stat_activity'))
    connections = result.fetchone()[0]
    print(f'Active connections: {connections}')
except Exception as e:
    print(f'Error: {e}')
"
```

#### Query Performance Issues

```bash
# Enable query logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Run application and monitor queries
python app.py
```

### Cache Monitoring Issues

#### Redis Connection Issues

```bash
# Test Redis connection
python -c "
import redis
try:
    r = redis.Redis.from_url('redis://localhost:6379/0')
    r.ping()
    print('✅ Redis connected')
    print('Memory usage:', r.info()['used_memory_human'])
except Exception as e:
    print(f'❌ Redis error: {e}')
"
```

#### Cache Performance Issues

```bash
# Analyze cache performance
python performance_optimizer.py cache_analysis

# Check cache hit/miss ratios
python -c "
from redis_cache import get_cache_stats
stats = get_cache_stats()
print('Cache stats:', stats)
"
```

## Advanced Monitoring

### Custom Metrics

```python
# Add custom metrics
from monitoring_config import get_monitoring_integration

monitoring = get_monitoring_integration()

# Record custom metric
monitoring.record_custom_metric('orders_processed', 150, 'counter')
monitoring.record_custom_metric('avg_order_value', 25000, 'gauge')
```

### Performance Profiling

```python
# Profile specific functions
from performance_optimizer import profile_performance

@profile_performance('heavy_computation')
def heavy_function():
    # Your heavy computation
    pass

# Profile database operations
from database_optimizer import profile_query

with profile_query("SELECT * FROM large_table", "large_table_query"):
    results = db.session.execute(large_query)
```

### Load Testing

```bash
# Run load test scenarios
python load_testing.py run_comprehensive

# Test specific scenarios
python load_testing.py run_load_test /api/products 100

# Generate performance report
python performance_optimizer.py generate_report
```

### Monitoring API Usage

```python
# Get monitoring data programmatically
from monitoring_alerting import get_monitoring_dashboard

dashboard = get_monitoring_dashboard()

# Get current metrics
metrics = dashboard.metrics_collector.metrics

# Get alert history
alerts = dashboard.alert_manager.get_alert_history(10)

# Get performance summary
summary = dashboard.metrics_collector.get_metrics_summary(60)
```

## Best Practices

### Monitoring Best Practices

1. **Set appropriate thresholds** based on your system capacity
2. **Monitor trends** not just absolute values
3. **Use multiple notification channels** for critical alerts
4. **Regular review** of monitoring data and alerts
5. **Test alerts** regularly to ensure they work
6. **Document** your monitoring setup and procedures

### Alert Management

1. **Avoid alert fatigue** by setting appropriate cooldown periods
2. **Categorize alerts** by severity and impact
3. **Have escalation procedures** for critical alerts
4. **Document alert responses** for future reference
5. **Regular review** of alert effectiveness

### Performance Monitoring

1. **Baseline your system** before going to production
2. **Monitor resource usage** trends over time
3. **Set up proactive alerts** for capacity planning
4. **Regular performance reviews** and optimization
5. **Load test** before major changes

## Support

### Getting Help

1. **Check the dashboard**: `/admin/monitoring`
2. **Review logs**: `tail -f logs/app.log`
3. **Test endpoints**: Use the API endpoints directly
4. **Run diagnostics**: Use the troubleshooting scripts
5. **Contact support**: Include monitoring data in support requests

### Emergency Monitoring

In case of system issues:

1. **Check basic health**: `curl http://localhost:5000/api/health`
2. **Review recent alerts**: Check the monitoring dashboard
3. **Check system resources**: `htop`, `df -h`, `free -h`
4. **Review error logs**: `tail -f logs/error.log`
5. **Check service status**: `sudo systemctl status passprint`

## Configuration

### Monitoring Configuration

```python
# config.py - Monitoring settings
MONITORING_CONFIG = {
    'enabled': True,
    'metrics_enabled': True,
    'alerting_enabled': True,
    'log_aggregation': True,
    'collection_interval': 5,  # seconds
    'retention_days': 30
}

# Alert thresholds
ALERT_THRESHOLDS = {
    'cpu_percent': 80,
    'memory_percent': 85,
    'disk_percent': 90,
    'error_rate': 5,
    'response_time_ms': 2000
}
```

### Custom Monitoring Setup

```python
# Custom monitoring setup
from monitoring_alerting import init_monitoring
from monitoring_config import init_monitoring_integration

# Initialize monitoring
app = create_app()
init_monitoring(app)
init_monitoring_integration(app)

# Add custom metrics
monitoring = get_monitoring_integration()
monitoring.record_custom_metric('business_orders', order_count)
```

## Metrics Reference

### System Metrics
- `cpu_percent`: CPU utilization percentage
- `memory_percent`: Memory utilization percentage
- `disk_percent`: Disk utilization percentage
- `network_bytes_sent`: Network bytes sent
- `network_bytes_recv`: Network bytes received

### Application Metrics
- `response_times`: API response times
- `error_rates`: Application error rates
- `active_users`: Number of active users
- `cache_hit_ratio`: Cache performance ratio

### Database Metrics
- `query_times`: Database query execution times
- `connection_count`: Active database connections
- `table_sizes`: Size of database tables
- `index_usage`: Index utilization statistics

### Security Metrics
- `failed_logins`: Failed authentication attempts
- `suspicious_activities`: Detected security threats
- `security_score`: Overall security health score
- `audit_events`: Security audit events

## API Reference

### Monitoring API Endpoints

```bash
# Health check
GET /api/monitoring/health

# Current metrics
GET /api/monitoring/metrics

# Metrics summary
GET /api/monitoring/metrics/summary?duration=60

# Alert history
GET /api/monitoring/alerts?limit=50

# Performance metrics
GET /api/monitoring/performance

# Resolve alert
POST /api/monitoring/alerts/{alert_id}/resolve
```

### Response Examples

```json
// Health response
{
  "monitoring_system": "healthy",
  "metrics_collection": "running",
  "alerts_enabled": true,
  "timestamp": "2025-01-04T10:00:00Z"
}

// Metrics response
{
  "metrics": {
    "system": {
      "cpu": {"percent": 45.2},
      "memory": {"percent": 67.8},
      "disk": {"percent": 34.1}
    },
    "application": {
      "health": {"healthy": true}
    }
  },
  "timestamp": "2025-01-04T10:00:00Z"
}
```

## Maintenance

### Regular Monitoring Tasks

1. **Daily**
   - Review system health dashboard
   - Check for new alerts
   - Monitor resource usage trends

2. **Weekly**
   - Review performance reports
   - Analyze slow queries
   - Check backup status

3. **Monthly**
   - Review and update alert thresholds
   - Analyze long-term trends
   - Update monitoring configuration

### Log Management

```bash
# Configure log rotation
sudo nano /etc/logrotate.d/passprint

# Monitor log file sizes
du -sh logs/*.log

# Archive old logs
find logs/ -name "*.log" -mtime +30 -exec gzip {} \;
```

### Metrics Cleanup

```python
# Clean up old metrics
from monitoring_alerting import get_monitoring_dashboard

dashboard = get_monitoring_dashboard()

# Clear old metrics (keep last 24 hours)
cutoff_time = datetime.utcnow() - timedelta(hours=24)
# Implementation depends on your metrics storage
```

## Security Considerations

### Monitoring Security

1. **Access Control**: Restrict monitoring dashboard to admin users
2. **Data Protection**: Don't log sensitive information
3. **Secure Communication**: Use HTTPS for monitoring endpoints
4. **Audit Logging**: Monitor who accesses monitoring data
5. **Alert Security**: Secure alert notification channels

### Compliance

- **GDPR**: Ensure monitoring doesn't log personal data
- **Data Retention**: Configure appropriate retention periods
- **Access Logging**: Log all monitoring access
- **Encryption**: Encrypt monitoring data at rest and in transit

## Advanced Features

### Anomaly Detection

```python
# Implement anomaly detection
from monitoring_alerting import get_monitoring_dashboard

dashboard = get_monitoring_dashboard()

# Analyze metrics for anomalies
metrics = dashboard.metrics_collector.metrics
anomalies = detect_anomalies(metrics)

if anomalies:
    send_anomaly_alert(anomalies)
```

### Predictive Monitoring

```python
# Predict future resource needs
from performance_optimizer import performance_analyzer

analyzer = performance_analyzer
capacity_plan = analyzer._generate_capacity_plan()

print(f"Recommended CPU cores: {capacity_plan['recommended_capacity']['cpu_cores']}")
print(f"Recommended memory: {capacity_plan['recommended_capacity']['memory_gb']}GB")
```

### Custom Dashboards

```javascript
// Create custom monitoring dashboard
const customDashboard = {
    widgets: [
        {
            type: 'chart',
            title: 'Custom Orders Chart',
            dataSource: '/api/monitoring/custom-orders',
            chartType: 'line'
        },
        {
            type: 'metric',
            title: 'Revenue Today',
            dataSource: '/api/monitoring/revenue',
            format: 'currency'
        }
    ]
};
```

## Integration Examples

### External Monitoring Integration

```python
# Integrate with external monitoring systems
from monitoring_config import get_monitoring_integration

monitoring = get_monitoring_integration()

# Send metrics to external system
external_metrics = {
    'cpu_usage': monitoring.metrics['system']['cpu']['percent'],
    'memory_usage': monitoring.metrics['system']['memory']['percent'],
    'response_time': monitoring.metrics['application']['performance']['avg_response_time']
}

requests.post('https://external-monitor.com/metrics', json=external_metrics)
```

### Alert Integration

```python
# Custom alert integration
from monitoring_alerting import get_monitoring_dashboard

dashboard = get_monitoring_dashboard()

# Check for custom conditions
def check_custom_alerts():
    # Your custom alert logic
    if custom_condition():
        send_custom_alert()

# Integrate with existing alert system
dashboard.alert_manager.alert_rules['custom_alert'] = {
    'condition': check_custom_alerts,
    'severity': 'warning',
    'message': 'Custom alert triggered'
}
```

## Performance Impact

### Monitoring Overhead

The monitoring system is designed to have minimal performance impact:

- **CPU Overhead**: < 2% average
- **Memory Overhead**: < 10MB
- **Network Overhead**: < 1MB/hour
- **Storage Overhead**: < 50MB/day

### Optimization Tips

1. **Adjust collection intervals** based on your needs
2. **Use sampling** for high-frequency metrics
3. **Archive old data** to reduce storage usage
4. **Monitor the monitoring** system itself
5. **Tune alert thresholds** to reduce noise

## Support and Troubleshooting

### Common Issues

#### Monitoring Not Starting

```bash
# Check configuration
python -c "
from config import get_config
config = get_config()
print('Monitoring enabled:', config.MONITORING_CONFIG.get('enabled', False))
"

# Check for errors in logs
tail -f logs/app.log | grep -i monitoring
```

#### Metrics Not Updating

```bash
# Check metrics collection
python -c "
from monitoring_alerting import get_monitoring_dashboard
dashboard = get_monitoring_dashboard()
print('Collection running:', dashboard.metrics_collector.running)
print('Last metrics:', dashboard.metrics_collector.metrics.get('system', {}).get('timestamp'))
"
```

#### Alerts Not Working

```bash
# Test alert system
python -c "
from monitoring_alerting import get_monitoring_dashboard
dashboard = get_monitoring_dashboard()

# Simulate high CPU
test_metrics = {'system': {'cpu': {'percent': 95}}}
dashboard.alert_manager.check_alerts(test_metrics)
print('Recent alerts:', len(dashboard.alert_manager.alert_history))
"
```

### Getting Help

1. **Check the monitoring dashboard** for current status
2. **Review the logs** for error messages
3. **Test individual components** using the API endpoints
4. **Check system resources** for capacity issues
5. **Contact support** with monitoring data and error details

---

For additional support, refer to the troubleshooting section or contact the development team.