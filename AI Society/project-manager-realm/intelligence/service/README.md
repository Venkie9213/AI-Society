# Intelligence Service - Phase 2: LLM Providers ✅

## Overview
This directory contains the core Intelligence Service application, which provides LLM-powered conversational reasoning for the AI Society's Project Manager Realm.

## Phase 2 Implementation Status: COMPLETE

### What Was Created

#### 1. **Project Structure**
```
intelligence/service/
├── app/
│   ├── __init__.py                    ✅ Package initialization
│   ├── main.py                        ✅ FastAPI application entry point
│   ├── config.py                      ✅ Configuration management (7 classes)
│   ├── database.py                    ✅ Database initialization & session management
│   ├── api/
│   │   ├── __init__.py                ✅
│   │   ├── health.py                  ✅ Health check endpoints
│   │   ├── debug.py                   ✅ Debug endpoints (dev only)│   │   ├── providers.py                ✅ Provider management endpoints│   │   └── conversations.py           ⏳ TODO: Conversation management (Phase 2)
│   ├── providers/
│   │   ├── __init__.py                ✅
│   │   ├── base.py                    ✅ Abstract LLMProvider interface
│   │   ├── gemini.py                  ✅ Gemini 1.5 Flash implementation
│   │   ├── router.py                  ✅ Provider routing with fallback
│   │   ├── manager.py                 ✅ Global provider manager
│   │   ├── claude.py                  ⏳ TODO: Claude implementation (Phase 3)
│   │   └── openai.py                  ⏳ TODO: OpenAI implementation (Phase 3)
│   ├── agents/                        ⏳ TODO: Intent routing (Phase 3)
│   ├── prompts/                       ⏳ TODO: Prompt management (Phase 4)
│   ├── kafka/                         ⏳ TODO: Event streaming (Phase 5)
│   ├── cost_management/               ⏳ TODO: Budget tracking (Phase 6)
│   ├── observability/
│   │   ├── __init__.py                ✅
│   │   ├── logging.py                 ✅ Structured logging setup
│   │   └── metrics.py                 ✅ Prometheus metrics
│   └── vector_store/                  ⏳ TODO: Embeddings & search (Phase 7)
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    ✅ Test fixtures
│   ├── unit/
│   │   ├── __init__.py                ✅
│   │   ├── test_providers.py           ✅ Provider unit tests
│   │   └── test_config.py             ⏳ TODO: Config tests
│   └── integration/                   ⏳ TODO: Integration tests
├── db/
│   └── init/
│       └── 01-init-schema.sql         ✅ Database schema
├── monitoring/
│   └── prometheus.yml                 ✅ Prometheus config
├── requirements.txt                   ✅ 45 dependencies (all pinned)
├── .env                               ✅ Development environment vars
├── .env.example                       ✅ Environment template
├── Dockerfile                         ✅ Container image definition
└── docker-compose.override.yml        ✅ Local development setup
```

#### 2. **Core Features Implemented**

**Phase 2: LLM Providers** (NEW)

**Gemini Provider** (`app/providers/gemini.py`)
- Async text generation with google-generativeai SDK
- Embedding generation with free embedding-001 model
- Automatic token counting and cost calculation
- Retry logic with exponential backoff (3 attempts)
- Health check endpoint
- Safety settings for content moderation
- Support for Gemini 1.5 Flash, 1.5 Pro, and 1.0 Pro models
- Pricing: Flash $0.075/$0.30 per 1M tokens, Pro $1.25/$5.00 per 1M tokens

**Provider Router** (`app/providers/router.py`)
- Automatic provider selection (primary + fallback sequence)
- Fallback on error with detailed logging
- Provider health checks
- Unified interface for text generation and embeddings
- Provider manager with singleton pattern
- List/get provider functionality

**Provider API Endpoints** (`app/api/providers.py`)
- `GET /api/v1/providers`: List all providers with health status
- `GET /api/v1/providers/health`: Provider health check
- `POST /api/v1/providers/test`: Test provider with prompt

**Provider Manager** (`app/providers/manager.py`)
- Global provider router initialization
- Singleton instance management
- Health check aggregation

**Phase 1: Core Infrastructure** (COMPLETE)

**FastAPI Application** (`app/main.py`)
- Async application with lifespan management
- Database initialization and connection pooling
- Metrics setup and structured logging
- Global exception handler with JSON responses
- CORS middleware for cross-origin requests
- Health check endpoints
- Root endpoint with service info

**Configuration Management** (`app/config.py`)
- 7 Pydantic BaseSettings classes:
  - `LLMConfig`: Gemini/Claude/OpenAI parameters
  - `DatabaseConfig`: PostgreSQL connection pooling
  - `KafkaConfig`: Event streaming configuration
  - `VectorStoreConfig`: Embedding database setup
  - `CostTrackingConfig`: Budget and alert thresholds
  - `LoggingConfig`: Log level and formatting
  - `AppConfig`: Main application configuration
- Environment variable loading from `.env`
- Type validation with Pydantic
- Development/production flexibility

**Database Layer** (`app/database.py`)
- AsyncEngine with connection pooling (5-20 connections)
- AsyncSession factory for dependency injection
- Database initialization with connectivity test
- Connection pool cleanup on shutdown
- SQLAlchemy 2.0 async support

**API Endpoints** (`app/api/`)
- `/api/v1/health`: Database connectivity check
- `/api/v1/metrics`: Prometheus metrics endpoint
- `/api/v1/ready`: Readiness probe for orchestration
- `/api/v1/live`: Liveness probe for orchestration
- `/api/v1/debug/config`: Configuration inspection (dev only)
- `/api/v1/debug/info`: Service information

**Observability** (`app/observability/`)
- **Logging**: Structured JSON logging with structlog
- **Metrics**: Prometheus metrics for:
  - HTTP request count & duration
  - LLM token usage and cost tracking
  - Vector DB operations
  - Kafka message processing
  - Active conversations count
  - Database connection pool size

**Provider Base** (`app/providers/base.py`)
- Abstract `LLMProvider` interface
- `LLMMessage` and `LLMResponse` dataclasses
- Defined methods for:
  - `generate()`: LLM text generation
  - `embed()`: Text embedding generation
  - `health_check()`: Provider connectivity
  - `calculate_cost()`: API cost calculation

**Infrastructure**
- Dockerfile with Python 3.11 slim base
- Non-root user for security
- Health checks and graceful shutdown
- docker-compose.override.yml with:
  - Intelligence Service container
  - PostgreSQL 15 with volume persistence
  - Kafka 7.5.0 for event streaming
  - Zookeeper for Kafka coordination
  - Prometheus for metrics collection
- Database initialization script (01-init-schema.sql)
  - Cost tracking tables (workspaces, cost_budgets, llm_costs)
  - Conversation storage (conversations, messages)
  - Materialized views for cost aggregation
  - Row-level security for multi-tenancy
  - Health check monitoring table

#### 3. **Dependencies Installed** (45 total)

**Web Framework**
- FastAPI 0.109.0
- Uvicorn 0.27.0
- python-multipart 0.0.6

**Database**
- asyncpg 0.29.0
- SQLAlchemy 2.0.23
- alembic 1.13.0
- psycopg2-binary 2.9.9

**LLM Providers**
- google-generativeai 0.3.0 (Gemini)
- anthropic 0.7.0 (Claude)
- openai 1.3.0 (GPT-4)

**Vector Databases**
- chromadb 0.4.21
- pinecone-client 3.0.2

**Event Streaming**
- aiokafka 0.10.0
- confluent-kafka 2.3.0

**Observability**
- prometheus-client 0.19.0
- structlog 24.1.0
- python-json-logger 2.0.7
- opentelemetry-api 1.21.0
- opentelemetry-sdk 1.21.0

**Testing**
- pytest 7.4.3
- pytest-asyncio 0.21.1
- pytest-cov 4.1.0
- testcontainers 3.7.0

**Utilities**
- pydantic 2.5.3
- pydantic-settings 2.1.0
- python-dotenv 1.0.0
- httpx 0.25.2
- tenacity 8.2.3
- pyyaml 6.0.1
- jinja2 3.1.2
- tiktoken 0.5.2

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 15 (or use docker-compose)

### Quick Start

1. **Copy environment configuration**
   ```bash
   cp .env.example .env
   ```

2. **Start infrastructure with Docker Compose**
   ```bash
   docker-compose -f docker-compose.override.yml up -d
   ```

3. **Verify services are running**
   ```bash
   docker-compose -f docker-compose.override.yml ps
   ```

4. **Test API**
   ```bash
   curl http://localhost:8000/api/v1/health
   curl http://localhost:8000/api/v1/metrics
   ```

5. **Access Prometheus**
   ```
   http://localhost:9090
   ```

### Local Development (without Docker)

1. **Create Python virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start services with Docker Compose**
   ```bash
   docker-compose -f docker-compose.override.yml up -d postgres kafka zookeeper prometheus
   ```

4. **Run application**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Next Phases

### Phase 3: Claude & OpenAI Providers
- [ ] Implement `app/providers/claude.py` (Claude 3.5 Sonnet)
- [ ] Implement `app/providers/openai.py` (GPT-4 Turbo)
- [ ] Implement fallback logic and error handling
- [ ] Add cost tracking for each provider

### Phase 4: Agent Routing
- [ ] Define agent interface for intent routing
- [ ] Implement intent classification
- [ ] Integrate agents with providers

### Phase 5: Prompt Management
- [ ] Create prompt template system
- [ ] Load prompts from YAML
- [ ] Support dynamic prompt rendering

### Phase 6: Kafka Integration
- [ ] Implement consumer for slack.message.received
- [ ] Implement producer for intelligence.conversations
- [ ] Add dead letter queue (DLQ) handling

### Phase 7: Cost Tracking
- [ ] Implement cost calculation and storage
- [ ] Create budget tracking and alerts
- [ ] Add materialized view refresh jobs

### Phase 8: Vector Store Integration
- [ ] Implement Chroma adapter (dev)
- [ ] Implement Pinecone adapter (prod)
- [ ] Add semantic search

### Phase 9: Testing
- [ ] Integration tests with mock providers
- [ ] E2E tests with mock Slack
- [ ] Performance benchmarks

## Configuration

All configuration is managed via environment variables (see `.env.example`):

| Variable | Purpose | Default |
|----------|---------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | (required) |
| `DATABASE_URL` | PostgreSQL connection string | postgresql://intelligence:dev_password@localhost:5432/intelligence |
| `KAFKA_BROKERS` | Kafka broker addresses | localhost:9092 |
| `VECTOR_STORE_PROVIDER` | Vector DB provider | chroma |
| `LOG_LEVEL` | Logging verbosity | info |
| `DEBUG` | Debug mode | true |

## Architecture Decisions

1. **Async-Native**: Python async/await throughout for concurrency
2. **PostgreSQL**: Unified dev/prod database with async driver (asyncpg)
3. **Kafka**: Event-sourced conversations (compacted topics)
4. **Multi-Tenant**: Row-level security (RLS) for workspace isolation
5. **Cost Aware**: Tracks LLM tokens and costs per provider
6. **Observable**: Structured logging (JSON) + Prometheus metrics
7. **Modular**: Provider adapter pattern for LLM interchangeability

## Monitoring & Debugging

**Logs**
```bash
# View structured logs
docker-compose -f docker-compose.override.yml logs -f intelligence-service
```

**Metrics**
```
http://localhost:9090/graph
```

**Database**
```bash
# Connect to PostgreSQL
psql postgresql://intelligence:dev_password@localhost:5432/intelligence
```

**Kafka Topics**
```bash
# List topics
docker exec intelligence-kafka kafka-topics --bootstrap-server localhost:9092 --list

# Monitor topic
docker exec intelligence-kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic slack.message.received
```

## References

- [Gemini Development Guide](../GEMINI_DEVELOPMENT_GUIDE.md)
- [Intelligence Implementation Guide](../INTELLIGENCE_IMPLEMENTATION_GUIDE.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Pydantic Settings](https://docs.pydantic.dev/latest/usage/settings/)

## Next Action

**Phase 3 Implementation**: Create Claude and OpenAI providers with:
- `app/providers/claude.py` - Anthropic Claude 3.5 Sonnet
- `app/providers/openai.py` - OpenAI GPT-4 Turbo
- Update fallback handling and cost tracking
- Add integration tests for multi-provider scenarios

