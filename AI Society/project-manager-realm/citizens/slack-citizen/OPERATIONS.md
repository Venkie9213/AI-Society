# Slack Citizen — Operations Guide

This document explains how to start, stop and operate the Slack Citizen service locally, how to debug logs, where to find metrics, and how to access Swagger (OpenAPI) and Kafka UI.

**Assumptions**
- You are working in the `citizens/slack-citizen` folder.
- Docker and docker-compose are installed and available on PATH.
- `.env` contains required secrets (`SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, etc.).

---

## 1) Start the application

Start the full local stack (Kafka, Zookeeper, kafka-ui, Prometheus, Slack Citizen):

```bash
cd citizens/slack-citizen
docker-compose up -d
```

Start only the Slack Citizen (assumes infra already running):

```bash
docker-compose up -d slack-citizen
```

Run locally (no Docker for the app):

```bash
# prepare venv once
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# start Kafka via docker-compose if needed
docker-compose up -d kafka zookeeper kafka-ui
# run the app
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Health / readiness checks:
- Health endpoint: `GET http://localhost:8000/health`
- Prometheus metrics: `http://localhost:9090/metrics` (Prometheus service port)

---

## 2) Stop the application

Stop the app container only:

```bash
docker-compose stop slack-citizen
```

Stop and remove all services (including Kafka data):

```bash
docker-compose down
# remove volumes (clears Kafka topics and data)
docker-compose down -v
```

Stop a single container and keep others running:

```bash
docker-compose stop kafka-ui
```

---

## 3) Debug the logs

Follow logs for the Slack Citizen service:

```bash
cd citizens/slack-citizen
docker-compose logs -f slack-citizen
```

Common greps:

```bash
# show ERROR lines
docker-compose logs slack-citizen | grep ERROR

# show recent 200 lines
docker-compose logs --tail=200 slack-citizen
```

Key log events to look for:
- `slack_signature_verified` — request signature validated
- `slack_message_processed` — inbound Slack message processed and published
- `event_published` — event successfully produced to Kafka (shows topic/partition/offset)
- `slack_api_errors_total` or Slack client errors — issues calling Slack Web API

If you need raw request inspection (useful with ngrok):
- Open ngrok inspector: http://127.0.0.1:4040 → Requests
- Compare `X-Slack-Signature` and `X-Slack-Request-Timestamp` headers with app logs

Temporary debug logging
- During development we sometimes add extra debug logging in `src/middleware/auth.py` for signature failures. Remove or silence these logs before committing to production.

---

## 4) Metrics

Prometheus (local) is available at `http://localhost:9090` (mapped from container `prometheus:9090`). The application exposes metrics on the port configured in `.env` (default is 9090 for the metrics container). Key metrics exported by the app:

- `slack_messages_received{tenant_id,channel_type}` — number of Slack inbound messages
- `slack_messages_processing_duration_seconds` — histogram of processing durations
- `kafka_messages_published_total{topic}` — events published to Kafka
- `slack_api_calls_total` and `slack_api_errors_total` — Slack Web API usage and errors

Quick curl to fetch app metrics:

```bash
curl http://localhost:9090/metrics | head -n 50
```

Add Prometheus alerting or Grafana dashboards in production for these metrics.

---

## 5) Swagger (OpenAPI) and Kafka UI

Swagger / OpenAPI

- OpenAPI UI: `http://localhost:8000/docs`
- Raw OpenAPI JSON: `http://localhost:8000/openapi.json`

Use the Swagger UI to try endpoints such as `/webhooks/slack/events` (note: Slack will call this endpoint with signed requests; manual testing via Swagger will not include Slack headers). For signature-protected endpoints, use the signed curl/test scripts or ngrok + Slack.

Kafka UI

- Kafka UI (pre-configured in docker-compose) is available at `http://localhost:8080`.
- Steps:
  - Open `http://localhost:8080`
  - Select cluster `local` (matching docker-compose config)
  - Click "Topics" and search for `project-manager.slack.message.received`
  - Click the topic and choose "Messages" to fetch and view message payloads
  - Inspect consumer groups and partitions if consumers are stuck

CLI Alternatives (if you prefer terminal):

```bash
# List topics
docker exec -it slack-citizen-kafka kafka-topics --bootstrap-server localhost:9092 --list

# Consume last N messages (prints keys & timestamps)
docker exec -it slack-citizen-kafka kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic project-manager.slack.message.received --from-beginning --max-messages 5 \
  --property print.key=true --property print.timestamp=true
```

---

## Troubleshooting checklist

- Signature failures: verify `SLACK_SIGNING_SECRET` in `.env`; ensure system time is correct; check ngrok forwarded body is raw bytes
- No Kafka messages: confirm `event_published` in `slack-citizen` logs, check Kafka UI and producer logs
- Slack bot can't post: verify `SLACK_BOT_TOKEN` and required scopes, and that bot is invited to the channel

---

## Quick commands summary

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f slack-citizen

# Swagger
open http://localhost:8000/docs

# Kafka UI
open http://localhost:8080
```

If you'd like, I can add a small `scripts/` folder with helper scripts for signed test POSTs, or add an `OPERATIONS.md` link into the repository `README.md`. Which would you prefer?