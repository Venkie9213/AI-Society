# 09. Deployment Guide

## Production Deployment

### Prerequisites
- Docker & Docker Compose
- PostgreSQL 15+ (managed or self-hosted)
- Server with 4GB+ RAM
- Domain name (optional but recommended)

---

## Deployment Options

## Option 1: Docker Compose (Recommended for Small/Medium)

### 1. Prepare Environment

```bash
cd intelligence/service

# Create production .env
cat > .env.production << EOF
ENVIRONMENT=production
DEBUG=false

APP_NAME=intelligence-service
APP_VERSION=1.0.0
HOST=0.0.0.0
PORT=8000

DATABASE_URL=postgresql://user:password@db:5432/intelligence

GEMINI_API_KEY=${GEMINI_API_KEY}

LOG_LEVEL=WARNING
STRUCTURED_LOGS=true

INTELLIGENCE_ROOT=/app/intelligence
EOF
```

### 2. Build Docker Image

```bash
docker build -t intelligence-service:latest .
```

### 3. Start Services

```bash
# Using docker-compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Or using Docker directly
docker run -d \
  --name intelligence-service \
  -p 8000:8000 \
  --env-file .env.production \
  -v $(pwd)/intelligence:/app/intelligence \
  intelligence-service:latest
```

### 4. Verify Deployment

```bash
# Check container logs
docker logs intelligence-service

# Health check
curl http://localhost:8000/api/v1/health

# View API docs
curl http://localhost:8000/docs
```

---

## Option 2: Cloud Deployment

### Google Cloud Run

```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/intelligence-service

# Deploy to Cloud Run
gcloud run deploy intelligence-service \
  --image gcr.io/PROJECT_ID/intelligence-service \
  --platform managed \
  --region us-central1 \
  --set-env-vars DATABASE_URL=postgresql://...,GEMINI_API_KEY=...
```

### AWS ECS

```bash
# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

docker tag intelligence-service:latest $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/intelligence-service:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/intelligence-service:latest

# Create ECS task definition and service
aws ecs create-task-definition --cli-input-json file://task-definition.json
aws ecs create-service --cluster my-cluster --service-name intelligence-service ...
```

### Heroku

```bash
# Login to Heroku
heroku login

# Create app
heroku create intelligence-service

# Set environment variables
heroku config:set GEMINI_API_KEY=... DATABASE_URL=...

# Push code
git push heroku main
```

---

## Database Setup

### Initial Setup

```bash
# Connect to production database
psql -h db-host -U postgres -d postgres

# Create database
CREATE DATABASE intelligence;

# Create user with limited permissions
CREATE USER app_user WITH PASSWORD 'strong-password';
GRANT CONNECT ON DATABASE intelligence TO app_user;
```

### Migrations

```bash
# Run migrations
alembic upgrade head

# Or from Docker
docker exec intelligence-service alembic upgrade head
```

---

## Reverse Proxy Setup (nginx)

### Basic Configuration

```nginx
# /etc/nginx/sites-available/intelligence-service
upstream intelligence_backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name intelligence-api.example.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name intelligence-api.example.com;
    
    ssl_certificate /etc/letsencrypt/live/intelligence-api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/intelligence-api.example.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;
    limit_req zone=api_limit burst=20 nodelay;
    
    location / {
        proxy_pass http://intelligence_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### Enable Configuration

```bash
# Create symlink
ln -s /etc/nginx/sites-available/intelligence-service /etc/nginx/sites-enabled/

# Test configuration
nginx -t

# Reload nginx
systemctl reload nginx
```

---

## SSL/TLS Setup

### Let's Encrypt Certificates

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d intelligence-api.example.com

# Auto-renewal
sudo certbot renew --dry-run
```

### Manual Certificate

```bash
# Generate private key and CSR
openssl req -new -newkey rsa:2048 -nodes -out api.csr -keyout api.key

# Get certificate from CA, then:
cat api.crt api.key > api.pem

# Use in nginx
ssl_certificate /path/to/api.pem;
ssl_certificate_key /path/to/api.key;
```

---

## Monitoring & Logging

### Health Checks

```bash
# Simple health endpoint
curl https://intelligence-api.example.com/api/v1/health

# Response should be:
# {"status": "healthy", "version": "1.0.0"}
```

### Application Logs

```bash
# View logs
docker logs intelligence-service

# Follow logs
docker logs -f intelligence-service

# Export logs
docker logs intelligence-service > logs.txt
```

### System Monitoring

```bash
# CPU/Memory usage
docker stats intelligence-service

# Network stats
docker network stats

# Disk usage
du -sh intelligence-service
```

---

## Backup & Recovery

### Database Backup

```bash
# Full backup
pg_dump -h db-host -U app_user intelligence > backup.sql

# With compression
pg_dump -h db-host -U app_user intelligence | gzip > backup.sql.gz

# Scheduled backup (cron)
0 2 * * * pg_dump -h db-host -U app_user intelligence | gzip > /backups/$(date +\%Y\%m\%d).sql.gz
```

### Recovery

```bash
# Restore from backup
psql -h db-host -U app_user intelligence < backup.sql

# Or from compressed
gunzip -c backup.sql.gz | psql -h db-host -U app_user intelligence
```

### Docker Volume Backup

```bash
# Backup volume
docker run --rm \
  -v intelligence-db:/data \
  -v $(pwd):/backup \
  ubuntu tar czf /backup/db-backup.tar.gz /data

# Restore volume
docker run --rm \
  -v intelligence-db:/data \
  -v $(pwd):/backup \
  ubuntu bash -c "cd /data && tar xzf /backup/db-backup.tar.gz"
```

---

## Scaling

### Horizontal Scaling (Multiple Instances)

```yaml
# docker-compose.prod.yml
services:
  web:
    deploy:
      replicas: 3  # 3 instances
    environment:
      - WORKER_ID=1  # Each gets unique ID
```

### Load Balancing with nginx

```nginx
upstream intelligence {
    server api1:8000;
    server api2:8000;
    server api3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://intelligence;
    }
}
```

### Database Connection Pooling

```bash
# In .env
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

---

## Security

### Environment Variables

```bash
# Never commit to git
echo ".env" >> .gitignore

# Use secrets manager
aws secrets create-secret --name intelligence/prod ...
```

### API Rate Limiting

```python
# app/middleware/rate_limit.py
from fastapi_limiter import FastAPILimiter

@app.post("/api/v1/agents/clarify")
@limiter.limit("100/minute")
async def clarify(request: Request):
    pass
```

### CORS Configuration

```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization"],
)
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker logs intelligence-service

# Check port availability
lsof -i :8000

# Check database connection
psql -h db-host -U app_user -d intelligence -c "SELECT 1"
```

### High Memory Usage

```bash
# Check process memory
docker stats --no-stream intelligence-service

# Reduce pool size
DATABASE_POOL_SIZE=5
```

### LLM API Errors

```bash
# Verify API key
curl -H "Authorization: Bearer $GEMINI_API_KEY" https://generativelanguage.googleapis.com/v1/models

# Check rate limits
# Implement exponential backoff in code
```

---

## Post-Deployment Checklist

- [ ] Application starts without errors
- [ ] Database migrations run successfully
- [ ] Health endpoint returns 200
- [ ] API endpoints accessible
- [ ] HTTPS/SSL working
- [ ] Logs are being collected
- [ ] Backups configured
- [ ] Monitoring active
- [ ] Documentation updated
- [ ] Team notified of deployment

---

**Next**: See [Docker Setup](10-docker-setup.md) for containerization details
