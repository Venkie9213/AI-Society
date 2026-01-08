# 10. Docker Setup

## Overview

The Intelligence Service is containerized using Docker and orchestrated with Docker Compose for easy deployment and scaling.

---

## Docker Structure

```
intelligence/service/
├── Dockerfile                 # Main application image
├── docker-compose.yml         # Development setup
├── docker-compose.prod.yml    # Production setup
├── docker-compose.override.yml # Local overrides
├── .dockerignore
├── requirements.txt
└── ...
```

---

## Building the Docker Image

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build Commands

```bash
# Build image
docker build -t intelligence-service:latest .

# Build with specific tag
docker build -t intelligence-service:v1.0.0 .

# Build with build args
docker build \
  --build-arg PYTHON_VERSION=3.11 \
  -t intelligence-service:latest .
```

---

## Docker Compose Setup

### Development Environment

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    container_name: intelligence-web
    ports:
      - "8000:8000"
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
      - DATABASE_URL=postgresql://app:password@db:5432/intelligence
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - .:/app
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    networks:
      - intelligence

  db:
    image: postgres:15-alpine
    container_name: intelligence-db
    environment:
      - POSTGRES_USER=app
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=intelligence
    ports:
      - "5432:5432"
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - intelligence

volumes:
  db_data:

networks:
  intelligence:
    driver: bridge
```

### Production Environment

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  web:
    build: .
    container_name: intelligence-web
    restart: always
    environment:
      - DEBUG=false
      - LOG_LEVEL=WARNING
      - DATABASE_URL=postgresql://app:${DB_PASSWORD}@db:5432/intelligence
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    depends_on:
      db:
        condition: service_healthy
    networks:
      - intelligence
    labels:
      - "com.example.description=Intelligence Service"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  db:
    image: postgres:15-alpine
    container_name: intelligence-db
    restart: always
    environment:
      - POSTGRES_USER=app
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=intelligence
    volumes:
      - db_data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - intelligence

  nginx:
    image: nginx:alpine
    container_name: intelligence-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    networks:
      - intelligence

volumes:
  db_data:

networks:
  intelligence:
    driver: bridge
```

---

## Running Containers

### Development

```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Production

```bash
# Start with production config
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f web

# Scale services
docker-compose up -d --scale web=3
```

---

## Container Management

### Executing Commands

```bash
# Run command in container
docker exec intelligence-web ls -la

# Run interactive shell
docker exec -it intelligence-web bash

# Run Python command
docker exec intelligence-web python -c "import app; print(app.__version__)"

# Run migrations
docker exec intelligence-web alembic upgrade head
```

### Container Inspection

```bash
# View running containers
docker ps

# View all containers
docker ps -a

# Container details
docker inspect intelligence-web

# Container logs
docker logs intelligence-web

# Follow logs
docker logs -f intelligence-web

# Limit log lines
docker logs --tail 100 intelligence-web
```

### Container Resource Management

```bash
# View resource usage
docker stats intelligence-web

# Limit memory
docker run -m 512m intelligence-service

# Limit CPU
docker run --cpus="1.5" intelligence-service
```

---

## Image Management

### Building Variations

```bash
# Build development image
docker build -t intelligence-service:dev \
  --target development .

# Build production image
docker build -t intelligence-service:prod \
  --target production .

# Build with specific Python version
docker build --build-arg PYTHON_VERSION=3.10 \
  -t intelligence-service:py310 .
```

### Publishing Images

```bash
# Tag image
docker tag intelligence-service:latest myregistry/intelligence-service:latest

# Push to registry
docker push myregistry/intelligence-service:latest

# Pull from registry
docker pull myregistry/intelligence-service:latest
```

---

## Networking

### Container Networks

```bash
# Create custom network
docker network create intelligence-net

# Run container on network
docker run --network intelligence-net --name web intelligence-service

# Connect running container to network
docker network connect intelligence-net container-id

# Inspect network
docker network inspect intelligence-net
```

### Port Mapping

```yaml
# Single port
ports:
  - "8000:8000"

# Multiple ports
ports:
  - "8000:8000"
  - "9090:9090"

# Expose to specific interface
ports:
  - "127.0.0.1:8000:8000"
```

---

## Environment Configuration

### .env File

```bash
# .env (development)
DEBUG=true
LOG_LEVEL=DEBUG
GEMINI_API_KEY=dev-key

# .env.prod (production)
DEBUG=false
LOG_LEVEL=WARNING
GEMINI_API_KEY=${GEMINI_API_KEY}
```

### Environment Override

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  web:
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
```

---

## Volume Management

### Persistent Data

```yaml
# Named volumes
volumes:
  db_data:
    driver: local

# Bind mounts
volumes:
  - ./data:/app/data

# Anonymous volumes
volumes:
  - /app/temp
```

### Backup Volumes

```bash
# Backup
docker run --rm \
  -v intelligence-db_data:/data \
  -v $(pwd):/backup \
  busybox tar czf /backup/db.tar.gz /data

# Restore
docker run --rm \
  -v intelligence-db_data:/data \
  -v $(pwd):/backup \
  busybox tar xzf /backup/db.tar.gz -C /
```

---

## Health Checks

### Configure Health Check

```yaml
# docker-compose.yml
services:
  web:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Health Endpoint

```python
# app/api/health.py
@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "intelligence-service",
        "version": "1.0.0"
    }
```

---

## Logging

### Container Logs

```bash
# View logs
docker logs intelligence-web

# Follow logs in real-time
docker logs -f intelligence-web

# Show last 100 lines
docker logs --tail 100 intelligence-web

# Show logs since specific time
docker logs --since 1h intelligence-web
```

### Log Configuration

```yaml
# docker-compose.yml
services:
  web:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## .dockerignore

```
.git
.gitignore
.venv
venv
__pycache__
*.pyc
.pytest_cache
.coverage
htmlcov/
dist/
build/
*.egg-info/
.env
.env.local
.DS_Store
node_modules/
.vscode
.idea
*.log
```

---

## Docker Best Practices

### 1. Use Specific Base Image Versions
```dockerfile
# ❌ Bad - always updates
FROM python:latest

# ✅ Good - specific version
FROM python:3.11-slim
```

### 2. Multi-stage Builds

```dockerfile
# Build stage
FROM python:3.11 as builder
RUN pip install -r requirements.txt

# Runtime stage
FROM python:3.11-slim
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
```

### 3. Layer Caching

```dockerfile
# ❌ Bad - invalidates cache
COPY . .
RUN pip install -r requirements.txt

# ✅ Good - leverages cache
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
```

### 4. Non-root User

```dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs intelligence-web

# Inspect image
docker inspect intelligence-service:latest

# Run interactively
docker run -it intelligence-service bash
```

### Connection Issues

```bash
# Check network
docker network inspect intelligence

# Inspect container networking
docker inspect intelligence-web | grep -i network

# Test connectivity
docker exec intelligence-web ping db
```

### Memory Issues

```bash
# Check usage
docker stats intelligence-web

# Reduce container memory limit
docker update -m 512m intelligence-web
```

---

## Useful Commands

```bash
# Clean up unused resources
docker system prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Remove all stopped containers
docker container prune

# Show image history
docker history intelligence-service

# Save image to tar
docker save intelligence-service:latest > image.tar

# Load image from tar
docker load < image.tar
```

---

**See also**: [Deployment Guide](09-deployment-guide.md) for production deployment
