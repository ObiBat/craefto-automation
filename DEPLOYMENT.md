# 🚀 CRAEFTO Automation - Deployment Guide

This guide covers deploying the CRAEFTO Automation Platform to production environments.

## 📋 Prerequisites

### Required Services
- **Docker & Docker Compose** (v20.10+)
- **PostgreSQL** (v15+) or **Supabase**
- **Redis** (v7+)
- **Domain name** with SSL certificate
- **Container registry** (Docker Hub, AWS ECR, etc.)

### Required API Keys
- **OpenAI API Key** (GPT-4 access)
- **Anthropic API Key** (Claude access)
- **Supabase URL & Key** (Database)
- **Twitter API Keys** (Social publishing)
- **LinkedIn API Keys** (Social publishing)
- **ConvertKit API Key** (Email campaigns)
- **Midjourney Webhook** (Image generation)

## 🏗️ Deployment Options

### Option 1: Docker Compose (Recommended)

#### 1. Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

#### 2. Application Deployment
```bash
# Clone repository
git clone https://github.com/your-username/craefto-automation.git
cd craefto-automation

# Create production environment file
cp env.template .env

# Edit environment variables
nano .env
```

#### 3. Configure Environment Variables
```bash
# Core Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
SECRET_KEY=your-super-secret-key-change-this-in-production

# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
REDIS_URL=redis://redis:6379/0

# AI APIs
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Social Media
TWITTER_API_KEY=your-twitter-key
TWITTER_API_SECRET=your-twitter-secret
LINKEDIN_CLIENT_ID=your-linkedin-id
LINKEDIN_CLIENT_SECRET=your-linkedin-secret

# Email
CONVERTKIT_API_KEY=your-convertkit-key

# Monitoring
SENTRY_DSN=your-sentry-dsn
GRAFANA_ADMIN_PASSWORD=secure-password
```

#### 4. Deploy with Docker Compose
```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Verify health
curl http://localhost:8000/health
```

### Option 2: Kubernetes Deployment

#### 1. Create Kubernetes Manifests
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: craefto-automation
---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: craefto-config
  namespace: craefto-automation
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  REDIS_URL: "redis://redis-service:6379/0"
---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: craefto-secrets
  namespace: craefto-automation
type: Opaque
stringData:
  SECRET_KEY: "your-secret-key"
  OPENAI_API_KEY: "sk-your-key"
  SUPABASE_URL: "https://your-project.supabase.co"
  SUPABASE_KEY: "your-key"
---
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: craefto-app
  namespace: craefto-automation
spec:
  replicas: 3
  selector:
    matchLabels:
      app: craefto-app
  template:
    metadata:
      labels:
        app: craefto-app
    spec:
      containers:
      - name: craefto-app
        image: your-registry/craefto-automation:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: craefto-config
        - secretRef:
            name: craefto-secrets
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: craefto-service
  namespace: craefto-automation
spec:
  selector:
    app: craefto-app
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: craefto-ingress
  namespace: craefto-automation
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.craefto.com
    secretName: craefto-tls
  rules:
  - host: api.craefto.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: craefto-service
            port:
              number: 80
```

#### 2. Deploy to Kubernetes
```bash
# Apply manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n craefto-automation
kubectl get services -n craefto-automation
kubectl get ingress -n craefto-automation

# Check logs
kubectl logs -f deployment/craefto-app -n craefto-automation
```

### Option 3: Cloud Platform Deployment

#### AWS ECS with Fargate
```json
{
  "family": "craefto-automation",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "craefto-app",
      "image": "your-account.dkr.ecr.region.amazonaws.com/craefto-automation:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:craefto/openai-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/craefto-automation",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

#### Google Cloud Run
```bash
# Build and push image
docker build -t gcr.io/your-project/craefto-automation:latest .
docker push gcr.io/your-project/craefto-automation:latest

# Deploy to Cloud Run
gcloud run deploy craefto-automation \
  --image gcr.io/your-project/craefto-automation:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --set-env-vars ENVIRONMENT=production \
  --set-secrets OPENAI_API_KEY=openai-key:latest
```

## 🔧 Production Configuration

### 1. Environment Variables
```bash
# Production environment template
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=False

# Security
SECRET_KEY=generate-a-secure-random-key
ALLOWED_ORIGINS=https://craefto.com,https://app.craefto.com

# Database
DATABASE_URL=postgresql://user:pass@host:5432/craefto_prod
REDIS_URL=redis://host:6379/0

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
PROMETHEUS_ENABLED=True

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# Performance
WORKERS=4
MAX_CONNECTIONS=100
TIMEOUT=30
```

### 2. Nginx Configuration
```nginx
# nginx/nginx.prod.conf
upstream craefto_backend {
    server craefto-app:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name api.craefto.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.craefto.com;

    ssl_certificate /etc/nginx/ssl/craefto.crt;
    ssl_certificate_key /etc/nginx/ssl/craefto.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    # Proxy settings
    location / {
        proxy_pass http://craefto_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
    }

    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://craefto_backend;
    }

    # Static files (if any)
    location /static/ {
        alias /var/www/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 3. Database Migration
```bash
# Create production database
psql -h your-db-host -U postgres -c "CREATE DATABASE craefto_prod;"

# Run migrations (if using Alembic)
alembic upgrade head

# Or manually create tables using your database utility
python scripts/create_tables.py
```

### 4. SSL Certificate Setup
```bash
# Using Let's Encrypt with Certbot
sudo apt install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d api.craefto.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 Monitoring Setup

### 1. Prometheus Configuration
```yaml
# monitoring/prometheus.prod.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'craefto-automation'
    static_configs:
      - targets: ['craefto-app:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:9113']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### 2. Grafana Dashboard
```json
{
  "dashboard": {
    "title": "CRAEFTO Automation Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "5xx errors"
          }
        ]
      }
    ]
  }
}
```

### 3. Alerting Rules
```yaml
# monitoring/alert_rules.yml
groups:
  - name: craefto_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"

      - alert: ServiceDown
        expr: up{job="craefto-automation"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service is down"
          description: "CRAEFTO Automation service is not responding"
```

## 🔒 Security Considerations

### 1. API Security
- **API Keys**: Store in environment variables or secrets manager
- **Rate Limiting**: Implement per-IP and per-user limits
- **CORS**: Configure allowed origins
- **HTTPS**: Use SSL/TLS certificates
- **Input Validation**: Validate all input data

### 2. Infrastructure Security
- **Firewall**: Only allow necessary ports
- **Network Segmentation**: Isolate services
- **Regular Updates**: Keep systems patched
- **Monitoring**: Log and monitor all activities
- **Backup**: Regular automated backups

### 3. Container Security
```dockerfile
# Use non-root user
RUN groupadd -r craefto && useradd -r -g craefto craefto
USER craefto

# Scan for vulnerabilities
RUN trivy filesystem --exit-code 1 .

# Health checks
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

## 🚀 Performance Optimization

### 1. Application Level
- **Connection Pooling**: Configure database pools
- **Caching**: Use Redis for frequently accessed data
- **Async Operations**: Use async/await for I/O operations
- **Load Balancing**: Distribute traffic across instances

### 2. Database Optimization
```sql
-- Create indexes for frequently queried columns
CREATE INDEX idx_content_created_at ON content(created_at);
CREATE INDEX idx_content_status ON content(status);
CREATE INDEX idx_performance_metrics_date ON performance_metrics(date);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM content WHERE status = 'published';
```

### 3. Caching Strategy
```python
# Redis caching configuration
CACHE_CONFIG = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Cache frequently accessed data
@cache.memoize(timeout=3600)  # 1 hour
def get_trending_topics():
    return research_agent.find_trending_topics()
```

## 🔄 Backup and Recovery

### 1. Database Backup
```bash
#!/bin/bash
# scripts/backup-database.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="craefto_backup_$DATE.sql"

# Create backup
pg_dump $DATABASE_URL > $BACKUP_FILE

# Compress
gzip $BACKUP_FILE

# Upload to S3 (optional)
aws s3 cp $BACKUP_FILE.gz s3://craefto-backups/

# Keep only last 7 days
find . -name "craefto_backup_*.sql.gz" -mtime +7 -delete
```

### 2. Application Data Backup
```bash
#!/bin/bash
# scripts/backup-app-data.sh

# Backup logs
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/

# Backup configuration
tar -czf config_backup_$(date +%Y%m%d).tar.gz config/

# Backup generated assets
tar -czf assets_backup_$(date +%Y%m%d).tar.gz assets/
```

### 3. Disaster Recovery
```bash
#!/bin/bash
# scripts/restore-from-backup.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Stop services
docker-compose down

# Restore database
gunzip -c $BACKUP_FILE | psql $DATABASE_URL

# Restart services
docker-compose up -d

echo "Restore completed"
```

## 📈 Scaling

### 1. Horizontal Scaling
```yaml
# docker-compose.scale.yml
version: '3.8'
services:
  craefto-app:
    deploy:
      replicas: 5
      resources:
        limits:
          cpus: '1'
          memory: 1G
      update_config:
        parallelism: 2
        delay: 10s
      restart_policy:
        condition: on-failure
```

### 2. Auto-scaling with Kubernetes
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: craefto-hpa
  namespace: craefto-automation
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: craefto-app
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## 🛠️ Maintenance

### 1. Regular Maintenance Tasks
```bash
# Weekly maintenance script
#!/bin/bash

echo "Starting weekly maintenance..."

# Update system packages
sudo apt update && sudo apt upgrade -y

# Clean up Docker
docker system prune -f

# Rotate logs
logrotate /etc/logrotate.conf

# Check disk space
df -h

# Check service status
docker-compose ps

echo "Maintenance completed"
```

### 2. Health Monitoring
```bash
#!/bin/bash
# scripts/health-check.sh

# Check API health
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is healthy"
else
    echo "❌ API is down"
    # Send alert
    curl -X POST "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK" \
         -H 'Content-type: application/json' \
         --data '{"text":"🚨 CRAEFTO API is down!"}'
fi

# Check database
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "✅ Database is healthy"
else
    echo "❌ Database is down"
fi

# Check Redis
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is healthy"
else
    echo "❌ Redis is down"
fi
```

## 📞 Troubleshooting

### Common Issues

1. **High Memory Usage**
   ```bash
   # Check memory usage
   docker stats
   
   # Restart services
   docker-compose restart
   ```

2. **Database Connection Issues**
   ```bash
   # Check database connectivity
   pg_isready -h db-host -p 5432
   
   # Check connection pool
   docker-compose logs craefto-app | grep "connection"
   ```

3. **API Rate Limits**
   ```bash
   # Check rate limit logs
   docker-compose logs nginx | grep "limiting"
   
   # Adjust rate limits in nginx config
   ```

4. **SSL Certificate Issues**
   ```bash
   # Check certificate expiration
   openssl x509 -in /etc/nginx/ssl/craefto.crt -text -noout
   
   # Renew certificate
   sudo certbot renew
   ```

This deployment guide provides comprehensive instructions for deploying the CRAEFTO Automation Platform in production environments with proper security, monitoring, and maintenance procedures.
