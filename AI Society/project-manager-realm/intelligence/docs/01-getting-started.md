# 01. Getting Started

## Installation

### Prerequisites
- Python 3.9+
- PostgreSQL 15+
- Docker & Docker Compose (optional)

### Setup Steps

1. **Clone the repository**
```bash
cd project-manager-realm/intelligence/service
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Initialize database**
```bash
python -m alembic upgrade head
```

6. **Run the service**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Docker Setup

```bash
cd project-manager-realm/intelligence/service
docker-compose up -d
```

Service will be available at: `http://localhost:8000`

## Verify Installation

Visit the API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Check health endpoint:
```bash
curl http://localhost:8000/api/v1/health
```

## Environment Variables

Create a `.env` file in the service directory:

```bash
# Application
APP_NAME=intelligence-service
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/intelligence

# LLM Providers
GEMINI_API_KEY=your-key-here
CLAUDE_API_KEY=optional
OPENAI_API_KEY=optional

# Intelligence Configuration
INTELLIGENCE_ROOT=./intelligence
MODELS_PATH=models/providers.yaml
AGENTS_PATH=agents/
PROMPTS_PATH=prompts/

# Observability
LOG_LEVEL=INFO
STRUCTURED_LOGS=true
METRICS_PORT=9090
```

## Next Steps

1. Read the [API Guide](02-api-guide.md) to understand available endpoints
2. Explore the [Architecture](03-architecture.md) to understand the system design
3. Check [Development Guide](06-development-guide.md) for local development

---

**Need help?** See the FAQ in [troubleshooting section](troubleshooting.md)
