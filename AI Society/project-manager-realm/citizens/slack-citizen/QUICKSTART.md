# Slack Citizen - Quick Start Guide

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- Slack workspace with admin access
- Slack app with bot token and signing secret

## Setup Steps

### 1. Create a Slack App

1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name your app (e.g., "AI Society Bot")
4. Select your workspace
5. Navigate to "OAuth & Permissions"
   - Add these Bot Token Scopes:
     - `chat:write`
     - `channels:read`
     - `groups:read`
     - `im:read`
     - `mpim:read`
     - `reactions:write`
     - `users:read`
   - Install app to workspace
   - Copy the "Bot User OAuth Token" (starts with `xoxb-`)
6. Navigate to "Basic Information"
   - Copy the "Signing Secret"
7. Navigate to "Event Subscriptions"
   - Enable Events
   - Set Request URL: `https://your-domain.com/webhooks/slack/events`
   - Subscribe to bot events:
     - `message.channels`
     - `message.groups`
     - `message.im`
     - `app_mention`

### 2. Configure Environment

```bash
cd citizens/slack-citizen

# Copy environment template
cp .env.example .env

# Edit .env with your Slack credentials
nano .env
```

Update these values in `.env`:
```bash
PROJECT_MANAGER_SLACK_SIGNING_SECRET=your_signing_secret_here
PROJECT_MANAGER_SLACK_BOT_TOKEN=xoxb-your-bot-token-here
```

### 3. Start the Service with Docker

```bash
# Start all services (Kafka, Zookeeper, Slack Citizen, Kafka UI)
docker-compose up -d

# View logs
docker-compose logs -f slack-citizen

# Check service health
curl http://localhost:8000/health
```

Services running:
- **Slack Citizen**: http://localhost:8000
- **Kafka UI**: http://localhost:8080
- **Prometheus Metrics**: http://localhost:9090
- **Kafka**: localhost:9092

### 4. Local Development Setup

For development without Docker:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start Kafka separately
docker-compose up -d kafka zookeeper kafka-ui

# Run the application
uvicorn src.main:app --reload --port 8000
```

### 5. Expose Webhook Endpoint

For local development, use ngrok to expose your webhook:

```bash
# Install ngrok (if not installed)
brew install ngrok  # macOS

# Start ngrok tunnel
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Update Slack Event Subscriptions Request URL:
# https://abc123.ngrok.io/webhooks/slack/events
```

### 6. Test the Integration

1. **Send a test message in Slack:**
   ```
   Hey bot, I need a feature to export reports
   ```

2. **Check the logs:**
   ```bash
   docker-compose logs -f slack-citizen
   ```

3. **Verify event was published:**
   - Open Kafka UI: http://localhost:8080
   - Navigate to Topics
   - Check `project-manager.slack.message.received`

4. **Check bot acknowledgment:**
   - Bot should react with 👀 emoji to your message

## Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_webhooks.py -v
```

### Manual API Testing

```bash
# Health check
curl http://localhost:8000/health

# Readiness check
curl http://localhost:8000/ready

# Test slash command (would need valid Slack signature)
curl -X POST http://localhost:8000/webhooks/slack/commands \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "token=test&team_id=T123&channel_id=C123&user_id=U123&command=/test&text=hello"
```

## Monitoring

### View Metrics

```bash
# Prometheus metrics endpoint
curl http://localhost:9090/metrics
```

Key metrics:
- `slack_messages_received_total` - Total messages received
- `slack_api_calls_total` - Slack API calls made
- `kafka_messages_published_total` - Events published to Kafka

### View Logs

```bash
# Follow service logs
docker-compose logs -f slack-citizen

# Filter by log level
docker-compose logs slack-citizen | grep ERROR

# View last 100 lines
docker-compose logs --tail=100 slack-citizen
```

### Kafka UI

Access Kafka UI at http://localhost:8080 to:
- View topics and messages
- Monitor consumer groups
- Check partition details
- Browse message content

## Troubleshooting

### Signature Verification Fails

**Problem:** `Invalid Slack signature` errors

**Solutions:**
1. Verify `PROJECT_MANAGER_SLACK_SIGNING_SECRET` matches your Slack app
2. Check system clock is synchronized
3. Ensure raw request body is used (not parsed)
4. Check webhook URL is HTTPS (use ngrok for local dev)

### Events Not Publishing to Kafka

**Problem:** Messages received but not in Kafka

**Solutions:**
1. Check Kafka is running: `docker-compose ps`
2. Verify connection: `docker-compose logs kafka`
3. Check producer logs: `docker-compose logs slack-citizen | grep kafka_producer`
4. Ensure topic auto-creation is enabled (default in docker-compose)

### Bot Not Responding

**Problem:** Bot doesn't react or send messages

**Solutions:**
1. Verify bot token is valid: `PROJECT_MANAGER_SLACK_BOT_TOKEN` in `.env`
2. Check bot has required scopes in Slack app settings
3. Ensure bot is invited to the channel: `/invite @YourBot`
4. Check logs for Slack API errors

### Docker Build Issues

**Problem:** Docker image build fails

**Solutions:**
```bash
# Clean build
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d

# Check for port conflicts
lsof -i :8000
lsof -i :9092
```

## Stopping the Service

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clears Kafka data)
docker-compose down -v

# Stop specific service
docker-compose stop slack-citizen
```

## Next Steps

1. **Integrate with other services:**
   - Set up Requirement Service to consume `slack.message.received` events
   - Configure Pulse Engine to process workflows

2. **Add slash commands:**
   - Implement custom command handlers in [src/routes/webhooks.py](src/routes/webhooks.py)
   - Register commands in Slack app settings

3. **Customize notifications:**
   - Modify event handlers in [src/main.py](src/main.py)
   - Add Block Kit templates for rich messages

4. **Deploy to production:**
   - Set up secrets management (AWS Secrets Manager, HashiCorp Vault)
   - Configure Kubernetes manifests
   - Set up monitoring and alerting
   - Enable rate limiting per tenant

## Useful Commands

```bash
# View all containers
docker-compose ps

# Restart service
docker-compose restart slack-citizen

# View Kafka topics
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9093 --list

# Consume from topic
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9093 \
  --topic project-manager.slack.message.received \
  --from-beginning

# Python shell with imports
docker-compose exec slack-citizen python -c "from src.config import settings; print(settings.app_version)"
```

## Support

For issues and questions:
1. Check logs: `docker-compose logs slack-citizen`
2. Review Kafka messages in Kafka UI
3. Verify Slack app configuration
4. Check [README.md](README.md) for architecture details
5. Review [event-mappings.md](../../schemas/citizens/slack/event-mappings.md) for event schemas
