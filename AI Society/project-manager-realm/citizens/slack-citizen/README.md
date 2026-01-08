# Slack Citizen

The Slack citizen is a bidirectional adapter between Slack and the AI Society event-driven platform. It handles inbound webhooks from Slack and sends outbound notifications via the Slack Web API.

## Architecture

### Inbound Flow
1. Slack sends webhook (message, command, interaction) to FastAPI endpoint
2. Verify Slack signature using signing secret
3. Extract `tenant_id` from Slack `team_id`
4. Map Slack event to internal event schema
5. Publish event to Kafka topic (e.g., `project-manager.slack.message.received`)
6. Return 200 OK immediately (async processing)

### Outbound Flow
1. Subscribe to internal events (e.g., `project-manager.requirement.created`)
2. Process event and extract Slack notification details
3. Call Slack Web API to post message/notification
4. Implement retry logic with exponential backoff
5. Publish failures to Dead Letter Queue

## Tech Stack

- **Framework**: Python 3.11+ with FastAPI
- **Slack Integration**: slack-sdk
- **Event Bus**: Apache Kafka (aiokafka)
- **Validation**: Pydantic
- **Observability**: structlog, prometheus-client
- **Containerization**: Docker

## Project Structure

```
slack-citizen/
├── src/
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Configuration management
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── webhooks.py            # Inbound webhook handlers
│   │   └── health.py              # Health check endpoints
│   ├── clients/
│   │   ├── __init__.py
│   │   └── slack_client.py        # Outbound Slack Web API client
│   ├── events/
│   │   ├── __init__.py
│   │   ├── producer.py            # Kafka event producer
│   │   └── consumer.py            # Kafka event consumer
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── slack_schemas.py       # Slack event models
│   │   └── internal_schemas.py    # Internal event schemas
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth.py                # Slack signature verification
│   │   ├── correlation.py         # Correlation ID middleware
│   │   └── tenant.py              # Multi-tenancy middleware
│   └── utils/
│       ├── __init__.py
│       ├── retry.py               # Retry logic with DLQ
│       ├── mapping.py             # Event mapping utilities
│       └── observability.py       # Logging and metrics
├── tests/
│   ├── __init__.py
│   ├── test_webhooks.py
│   ├── test_slack_client.py
│   └── test_event_mapping.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Configuration

Required environment variables:

```bash
# Slack
PROJECT_MANAGER_SLACK_SIGNING_SECRET=your_signing_secret
PROJECT_MANAGER_SLACK_BOT_TOKEN=xoxb-your-bot-token

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_PREFIX=project-manager

# Multi-tenancy
TENANT_MAPPING_SERVICE_URL=http://localhost:8080/tenants

# Observability
JAEGER_AGENT_HOST=localhost
JAEGER_AGENT_PORT=6831
PROMETHEUS_PORT=9090
LOG_LEVEL=INFO
```

## Events Published

- `project-manager.slack.message.received` - User sends message in Slack
- `project-manager.slack.command.invoked` - Slash command executed
- `project-manager.slack.interaction.triggered` - Button/modal interaction

## Events Consumed

- `project-manager.requirement.created` - Notify in Slack about new requirement
- `project-manager.requirement.clarification.completed` - Post PRD to Slack thread
- `project-manager.pulse.execution.failed` - Send alert to Slack channel

## Development

### Local Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy environment configuration:
```bash
cp .env.example .env
# Edit .env with your Slack credentials
```

3. Start Kafka and dependencies:
```bash
docker-compose up -d kafka zookeeper
```

4. Run the service:
```bash
uvicorn src.main:app --reload --port 8000
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_webhooks.py -v
```

### Docker

```bash
# Build image
docker build -t slack-citizen:latest .

# Run with docker-compose
docker-compose up
```

## Security Considerations

1. **Signature Verification**: All Slack webhooks verified using signing secret
2. **Token Management**: Bot tokens stored in secrets manager (not env vars in production)
3. **Rate Limiting**: Implement per-tenant rate limiting
4. **Tenant Isolation**: Validate tenant_id to prevent cross-tenant access
5. **Idempotency**: Event handlers check for duplicate event_id

## Monitoring

### Metrics (Prometheus)

- `slack_messages_received_total{tenant_id, channel_type}` - Messages received counter
- `slack_messages_processing_seconds{tenant_id}` - Processing duration histogram
- `slack_api_calls_total{tenant_id, endpoint, status}` - Outbound API call counter
- `slack_api_errors_total{tenant_id, error_type}` - API error counter

### Logs (Structured)

All logs include:
- `tenant_id` - Multi-tenancy isolation
- `correlation_id` - Request tracing
- `event_id` - Event deduplication
- `timestamp` - ISO 8601 format

## Troubleshooting

### Webhook Signature Verification Fails
- Verify `PROJECT_MANAGER_SLACK_SIGNING_SECRET` matches your Slack app configuration
- Check system clock is synchronized (signature includes timestamp)
- Ensure raw request body is used (not parsed JSON)

### Events Not Being Published to Kafka
- Verify Kafka bootstrap servers are reachable
- Check topic exists or auto-creation is enabled
- Review Kafka consumer group lag

### Slack API Rate Limiting
- Implement exponential backoff with retry logic
- Consider batching notifications
- Use tier-specific rate limits per tenant

## Contributing

When adding new features:
1. Follow the existing project structure
2. Add Pydantic schemas for new event types
3. Update event mapping documentation in `../../schemas/citizens/slack/`
4. Add tests with >80% coverage
5. Update this README with new events published/consumed
