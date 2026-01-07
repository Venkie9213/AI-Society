# Citizens

Purpose
- Integration adapters to external systems (Jira, GitHub, Slack, Google Workspace, DataDog, Figma).

Responsibilities
- Provide inbound webhook handlers that validate signatures and map events to internal schemas.
- Provide outbound clients for making authenticated API calls to external systems.
- Implement retry and DLQ strategies for failed outbound calls.

## Implemented Citizens

### ✅ Slack Citizen (Python + FastAPI)

**Status:** Complete and ready for deployment

**Location:** [slack-citizen/](slack-citizen/)

**Features:**
- ✅ Inbound webhook handlers for Slack events, commands, and interactions
- ✅ Signature verification middleware for security
- ✅ Multi-tenancy support with tenant ID mapping
- ✅ Kafka event producer for publishing internal events
- ✅ Kafka event consumer for outbound notifications
- ✅ Outbound Slack Web API client with retry logic
- ✅ Structured logging and Prometheus metrics
- ✅ Docker containerization with docker-compose
- ✅ Comprehensive test suite
- ✅ Event mapping documentation

**Tech Stack:**
- Python 3.11+
- FastAPI
- slack-sdk
- aiokafka
- Pydantic
- structlog
- prometheus-client

**Quick Start:**
```bash
cd slack-citizen
cp .env.example .env
# Edit .env with your Slack credentials
docker-compose up -d
```

See [slack-citizen/QUICKSTART.md](slack-citizen/QUICKSTART.md) for detailed setup instructions.

**Events Published:**
- `project-manager.slack.message.received`
- `project-manager.slack.command.invoked`
- `project-manager.slack.interaction.triggered`

**Events Consumed:**
- `project-manager.requirement.requirement.created`
- `project-manager.requirement.clarification.completed`
- `project-manager.pulse.execution.failed`

**Documentation:**
- [README.md](slack-citizen/README.md) - Architecture and overview
- [QUICKSTART.md](slack-citizen/QUICKSTART.md) - Setup guide
- [Event Mappings](../schemas/citizens/slack/event-mappings.md) - Schema documentation

---

## Planned Citizens

### 🔜 Jira Citizen
- Integration with Jira for issue tracking
- Webhook handlers for issue events
- API client for creating/updating issues

### 🔜 GitHub Citizen
- Integration with GitHub for repository management
- Webhook handlers for PR, commits, issues
- API client for repository operations

### 🔜 Google Workspace Citizen
- Integration with Google Calendar, Drive, Docs
- Event subscriptions via Google Cloud Pub/Sub
- API clients for workspace operations

### 🔜 DataDog Citizen
- Integration for monitoring and alerting
- Webhook handlers for alert events
- API client for metrics and logs

### 🔜 Figma Citizen
- Integration for design collaboration
- Webhook handlers for file updates
- API client for design file access

---

## Architecture Guidelines

All citizens should follow these patterns:

### Event-Driven Communication
- Publish events to Kafka for inbound webhook data
- Subscribe to Kafka topics for outbound notifications
- Use event envelope standard (see [event-mappings.md](../schemas/citizens/slack/event-mappings.md))

### Security
- Verify webhook signatures (HMAC, OAuth, etc.)
- Store credentials in secrets manager (not env vars in production)
- Implement rate limiting per tenant

### Multi-Tenancy
- Extract and validate `tenant_id` from all requests
- Include `tenant_id` in all events and logs
- Isolate data and operations per tenant

### Observability
- Structured logging with `tenant_id` and `correlation_id`
- Prometheus metrics for key operations
- Distributed tracing with OpenTelemetry

### Resilience
- Implement retry logic with exponential backoff
- Use Dead Letter Queue (DLQ) for failed messages
- Handle idempotency to prevent duplicate processing

### Testing
- Unit tests for core logic
- Integration tests with mocked external APIs
- Contract tests for event schemas

---

## Development Workflow

### Creating a New Citizen

1. **Set up project structure:**
   ```bash
   mkdir {service}-citizen
   cd {service}-citizen
   # Create src/, tests/, requirements.txt, Dockerfile, etc.
   ```

2. **Implement core components:**
   - Configuration management
   - Webhook handlers with signature verification
   - API client with retry logic
   - Event producer/consumer
   - Middleware (auth, correlation, tenant)

3. **Add observability:**
   - Structured logging
   - Prometheus metrics
   - Health check endpoints

4. **Create documentation:**
   - README with architecture overview
   - QUICKSTART guide
   - Event mapping schemas under `../schemas/citizens/{service}/`

5. **Write tests:**
   - Unit tests for mapping logic
   - Integration tests for webhook handlers
   - Mock external API responses

6. **Containerize:**
   - Dockerfile for the service
   - docker-compose.yml with dependencies
   - prometheus.yml for metrics scraping

---

## Next Steps

1. ✅ ~~Create Slack citizen implementation~~
2. 🔄 Deploy Slack citizen to staging environment
3. 🔄 Integrate with Requirement Service
4. 🔄 Test end-to-end workflow: Slack → Event Bus → Service → Slack
5. 🔜 Create Jira citizen for issue tracking
6. 🔜 Create GitHub citizen for repository integration
