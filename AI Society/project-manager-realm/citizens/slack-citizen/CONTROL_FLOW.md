# Slack Citizen - Control Flow Documentation

This document explains the complete control flow and architecture of the Slack Citizen service, detailing how requests flow through the system in both inbound (Slack → Platform) and outbound (Platform → Slack) directions.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Inbound Flow: Slack → Platform](#inbound-flow-slack--platform)
3. [Outbound Flow: Platform → Slack](#outbound-flow-platform--slack)
4. [Component Interaction](#component-interaction)
5. [Data Flow Diagrams](#data-flow-diagrams)
6. [Error Handling & Retry Logic](#error-handling--retry-logic)

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Slack Citizen Service                     │
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  Middleware  │───▶│    Routes    │───▶│   Clients    │      │
│  │              │    │              │    │              │      │
│  │ • Auth       │    │ • Webhooks   │    │ • Slack API  │      │
│  │ • Tenant     │    │ • Health     │    │              │      │
│  │ • Correlation│    │              │    │              │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                    │                    │              │
│         ▼                    ▼                    ▼              │
│  ┌──────────────────────────────────────────────────────┐      │
│  │              Event Producer/Consumer                  │      │
│  │               (Kafka Integration)                     │      │
│  └──────────────────────────────────────────────────────┘      │
│                             │                                    │
└─────────────────────────────┼────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Kafka Broker   │
                    │  (Event Bus)    │
                    └─────────────────┘
```

### Key Components

1. **Middleware Layer** - Request preprocessing and validation
2. **Routes Layer** - Endpoint handlers and request routing
3. **Clients Layer** - External API integrations (Slack Web API)
4. **Events Layer** - Kafka producer/consumer for event streaming
5. **Utils Layer** - Cross-cutting concerns (logging, metrics, retry logic)

---

## Inbound Flow: Slack → Platform

This flow handles incoming webhooks from Slack and converts them into internal platform events.

### Flow Diagram

```
Slack App
   │
   │ HTTP POST /webhooks/slack/events
   ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Middleware Pipeline (Bottom to Top)                      │
├─────────────────────────────────────────────────────────────┤
│ SlackSignatureMiddleware                                    │
│ • Extract X-Slack-Signature & X-Slack-Request-Timestamp    │
│ • Compute HMAC-SHA256 with signing secret                   │
│ • Verify signature matches (prevent tampering)              │
│ • Check timestamp (prevent replay attacks, ±5 min)          │
│ • Store raw body in request.state.body                      │
│ • ❌ 401 if signature invalid                               │
└─────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│ CorrelationMiddleware                                        │
│ • Extract X-Correlation-ID from headers                     │
│ • Generate new UUID if not present                          │
│ • Store in request.state.correlation_id                     │
│ • Add to logging context (structlog)                        │
│ • Include in response headers                               │
└─────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│ TenantMiddleware                                             │
│ • Parse body JSON (from request.state.body)                 │
│ • Extract team_id from Slack payload                        │
│ • Map team_id → tenant_id                                   │
│   - Check in-memory cache first                             │
│   - Call tenant mapping service (optional)                  │
│   - Fallback to default tenant_id                           │
│ • Store in request.state.tenant_id                          │
│ • Add to logging context                                    │
└─────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Route Handler: slack_events()                            │
├─────────────────────────────────────────────────────────────┤
│ • Parse JSON body from request.state.body                   │
│ • Handle URL verification challenge                         │
│   - If type == "url_verification"                           │
│   - Return {"challenge": payload.challenge}                 │
│   - ✅ Slack verifies webhook is working                    │
│                                                              │
│ • Validate with Pydantic: SlackEventWrapper                 │
│ • Extract event type: event.event.type                      │
│ • Track metrics: slack_messages_received counter            │
│ • Delegate to event processor                               │
└─────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Event Processor: _process_slack_event()                  │
├─────────────────────────────────────────────────────────────┤
│ Route by event type:                                        │
│ • "message" → _handle_message_event()                       │
│ • "app_mention" → _handle_app_mention_event()               │
│ • other → log and skip                                      │
└─────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Message Handler: _handle_message_event()                 │
├─────────────────────────────────────────────────────────────┤
│ • Validate with Pydantic: SlackMessage                      │
│ • Skip bot messages (subtype == "bot_message")              │
│ • Skip edited/deleted messages                              │
│                                                              │
│ • Map to internal event using:                              │
│   map_slack_message_to_internal_event()                     │
│   - Generate message_id: "msg_{uuid}"                       │
│   - Generate event_id: UUID                                 │
│   - Convert timestamp to ISO 8601                           │
│   - Structure as EventEnvelope with standard fields         │
│                                                              │
│ • Publish to Kafka:                                         │
│   - Topic: "project-manager.slack.message.received"         │
│   - Key: event_id (for partitioning)                        │
│   - Value: JSON serialized event                            │
│                                                              │
│ • Add reaction acknowledgment:                              │
│   - Call slack_client.add_reaction()                        │
│   - Emoji: "eyes" 👀                                        │
│   - Channel: message.channel                                │
│   - Timestamp: message.ts                                   │
└─────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Kafka Producer: publish_event()                          │
├─────────────────────────────────────────────────────────────┤
│ • Serialize event to JSON                                   │
│ • Add optional headers (correlation_id, etc.)               │
│ • Send to Kafka with compression (gzip)                     │
│ • Wait for acknowledgment from broker                       │
│ • Track metrics: kafka_messages_published counter           │
│ • Log success with partition and offset                     │
│ • ❌ Retry on failure, publish to DLQ if exhausted          │
└─────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Response to Slack                                         │
├─────────────────────────────────────────────────────────────┤
│ • Return 200 OK immediately (within 3 seconds)              │
│ • Body: {"ok": true}                                        │
│ • All processing happens asynchronously                     │
│ • Slack won't retry if we respond fast                      │
└─────────────────────────────────────────────────────────────┘
```

### Inbound Request Lifecycle

```python
# 1. Request arrives with Slack webhook
POST /webhooks/slack/events
Headers:
  X-Slack-Signature: v0=abc123...
  X-Slack-Request-Timestamp: 1704621000
Body:
  {
    "token": "...",
    "team_id": "T123456",
    "event": {
      "type": "message",
      "user": "U123456",
      "text": "I need a PDF export feature",
      "channel": "C123456",
      "ts": "1704621000.123456"
    },
    "event_id": "Ev123456",
    "event_time": 1704621000
  }

# 2. After middleware processing
request.state:
  - body: <raw bytes>
  - correlation_id: "550e8400-e29b-41d4-a716-446655440000"
  - tenant_id: "tenant_T123456"

# 3. Mapped to internal event
EventEnvelope:
  event_id: "650e8400-e29b-41d4-a716-446655440001"
  occurred_at: "2026-01-07T10:30:00.000Z"
  tenant_id: "tenant_T123456"
  source: "slack-citizen"
  payload_version: "v1"
  payload:
    message_id: "msg_a1b2c3d4e5f6"
    slack_user_id: "U123456"
    slack_channel_id: "C123456"
    text: "I need a PDF export feature"
    ...

# 4. Published to Kafka topic
Topic: project-manager.slack.message.received
Partition: 0
Offset: 42
```

---
## LLM Integration Flow (via Intelligence Service)

The Slack Citizen service acts as a **thin adapter** between Slack and the platform's event bus. All LLM processing logic resides in the **Intelligence Service**, maintaining proper separation of concerns.

### Complete Flow with Intelligence Service

```
User sends message in Slack
   │
   ▼
┌─────────────────────────────────────────────────────────┐
│ Slack Citizen: Inbound Message Processing                │
│ • Receives webhook from Slack                            │
│ • Validates signature & extracts tenant                  │
│ • Publishes to: "slack.message.received"                 │
│ • Adds 👀 reaction to acknowledge receipt                 │
└─────────────────────────────────────────────────────────┘
   │
   │ Kafka Topic: slack.message.received
   ▼
┌─────────────────────────────────────────────────────────┐
│ Intelligence Service: LLM Processing                     │
│ • Consumes from: "slack.message.received"                │
│ • Determines intent & routes to appropriate LLM agent    │
│ • Processes message through LLM (OpenAI, Claude, etc.)  │
│ • Formats response (text + optional blocks)              │
│ • Publishes to: "slack.reply.requested"                  │
└─────────────────────────────────────────────────────────┘
   │
   │ Kafka Topic: slack.reply.requested
   ▼
┌─────────────────────────────────────────────────────────┐
│ Slack Citizen: Outbound Reply Processing                │
│ • Consumes from: "slack.reply.requested"                 │
│ • Validates SlackReplyRequestedPayload                   │
│ • Calls Slack Web API to post message                    │
│ • Posts to same channel/thread                           │
│ • Handles rate limiting & retries                        │
└─────────────────────────────────────────────────────────┘
   │
   ▼
User sees reply in Slack thread
```

### Event Schemas

**slack.message.received** (published by Slack Citizen):
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "occurred_at": "2024-01-07T12:00:00Z",
  "tenant_id": "tenant_123",
  "source": "slack-citizen",
  "payload_version": "1.0",
  "payload": {
    "message_id": "msg_abc123",
    "channel_id": "C123456",
    "thread_ts": "1704621000.123456",
    "user_id": "U123456",
    "text": "How do I export reports?",
    "timestamp": "1704621000.123456"
  }
}
```

**slack.reply.requested** (published by Intelligence Service):
```json
{
  "event_id": "660e8400-e29b-41d4-a716-446655440001",
  "occurred_at": "2024-01-07T12:00:05Z",
  "tenant_id": "tenant_123",
  "source": "intelligence-service",
  "payload_version": "1.0",
  "payload": {
    "message_text": "To export reports, go to Reports > Export > Select Format (PDF/CSV)...",
    "slack_channel_id": "C123456",
    "slack_thread_ts": "1704621000.123456",
    "slack_user_id": "U123456",
    "blocks": [
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": "To export reports:\n1. Navigate to *Reports*\n2. Click *Export*"
        }
      }
    ]
  }
}
```

### Separation of Concerns

**Slack Citizen (Thin Adapter)**:
- ✅ Webhook validation & security
- ✅ Slack API integration (post messages, reactions)
- ✅ Event transformation (Slack format ↔ Internal format)
- ✅ Rate limiting & retry logic for Slack API
- ❌ NO business logic
- ❌ NO LLM integration
- ❌ NO intent detection

**Intelligence Service (Smart Core)**:
- ✅ LLM integration (OpenAI, Claude, etc.)
- ✅ Intent detection & routing
- ✅ Conversation context management
- ✅ Response generation & formatting
- ✅ Business logic & decision making
- ❌ NO Slack-specific code
- ❌ NO direct Slack API calls

---
## Outbound Flow: Platform → Slack

This flow handles internal platform events and sends notifications back to Slack.

### Flow Diagram

```
Kafka Broker
   │
   │ Topic: project-manager.requirement.requirement.created
   ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Kafka Consumer: EventConsumer                            │
├─────────────────────────────────────────────────────────────┤
│ • Subscribe to topics in startup (lifespan)                 │
│   - requirement.requirement.created                         │
│   - requirement.clarification.completed                     │
│   - pulse.execution.failed                                  │
│   - slack.reply.requested (from Intelligence Service)       │
│                                                              │
│ • Poll for messages (getmany, timeout 1000ms)               │
│ • Deserialize JSON → Python dict                            │
│ • Track metrics: kafka_messages_consumed counter            │
│ • Delegate to handler: handle_internal_event()              │
│ • Manual commit after successful processing                 │
│ • ❌ Don't commit on error (reprocess on restart)           │
└─────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Event Router: handle_internal_event()                    │
├─────────────────────────────────────────────────────────────┤
│ • Validate with Pydantic: EventEnvelope                     │
│ • Extract source service                                    │
│ • Add correlation_id to logging context                     │
│                                                              │
│ Route by source:                                            │
│ • "requirement-service" → handle_requirement_event()        │
│ • "pulse.*" → handle_pulse_event()                          │
│ • "intelligence-service" → handle_intelligence_event()      │
│ • other → log and skip                                      │
│                                                              │
│ • Track metrics: event_processing_duration histogram        │
└─────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Handler Routing                                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ A) handle_requirement_event()                               │
│    • Parse payload to determine event subtype               │
│    • Route to appropriate notifier                          │
│                                                              │
│ B) handle_pulse_event()                                     │
│    • Handle pulse execution failures                        │
│    • Notify users of errors                                 │
│                                                              │
│ C) handle_intelligence_event() [NEW]                        │
│    • Validates SlackReplyRequestedPayload                   │
│    • Calls send_slack_reply()                               │
│    • Posts LLM response back to Slack                       │
└─────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Notification: notify_requirement_created()               │
├─────────────────────────────────────────────────────────────┤
│ • Extract Slack metadata from payload.metadata:             │
│   - slack_channel_id: "C123456"                             │
│   - slack_thread_ts: "1704621000.123456" (optional)         │
│                                                              │
│ • ❌ Skip if no channel_id (can't determine where to post)  │
│                                                              │
│ • Build Block Kit message:                                  │
│   - Section with title and requirement_id                   │
│   - Section with description                                │
│   - Rich formatting with markdown                           │
│                                                              │
│ • Call slack_client.post_message()                          │
│   - Pass channel, blocks, thread_ts, tenant_id              │
└─────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Slack Client: post_message()                             │
├─────────────────────────────────────────────────────────────┤
│ • Wrapped with @retry_with_dlq decorator                    │
│   - Max 3 retry attempts                                    │
│   - Exponential backoff (1s, 2s, 4s...)                     │
│   - DLQ topic: "slack.notifications.failed"                 │
│                                                              │
│ • Call Slack Web API: chat.postMessage                      │
│   - Use AsyncWebClient from slack-sdk                       │
│   - Authenticate with bot token                             │
│   - Pass channel, text, blocks, thread_ts                   │
│                                                              │
│ • Track metrics:                                            │
│   - slack_api_calls_total counter                           │
│   - slack_api_errors_total counter (on failure)             │
│                                                              │
│ • ✅ Return Slack response with message timestamp           │
│ • ❌ On retry exhaustion → publish to DLQ                   │
└─────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Slack API Response                                        │
├─────────────────────────────────────────────────────────────┤
│ Success response:                                           │
│ {                                                            │
│   "ok": true,                                               │
│   "channel": "C123456",                                     │
│   "ts": "1704621010.123456",                                │
│   "message": { ... }                                        │
│ }                                                            │
│                                                              │
│ • Message appears in Slack channel                          │
│ • User sees notification about requirement                  │
└─────────────────────────────────────────────────────────────┘
```

### Outbound Event Lifecycle

```python
# 1. Internal event from another service
Event in Kafka:
  Topic: project-manager.requirement.requirement.created
  Payload:
    event_id: "750e8400-e29b-41d4-a716-446655440002"
    occurred_at: "2026-01-07T10:35:00.000Z"
    tenant_id: "tenant_T123456"
    source: "requirement-service"
    payload:
      requirement_id: "req_abc123"
      title: "PDF Export Feature"
      description: "Users need ability to export reports as PDF"
      metadata:
        slack_channel_id: "C123456"
        slack_thread_ts: "1704621000.123456"

# 2. Consumer receives and processes
Consumer Group: slack-citizen-consumer
Partition: 0
Offset: 15

# 3. Mapped to Slack message
Slack API Call:
  Method: chat.postMessage
  Params:
    channel: "C123456"
    thread_ts: "1704621000.123456"
    text: "✅ Requirement created: PDF Export Feature"
    blocks: [
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": "*New Requirement Created*\n\n*Title:* PDF Export Feature\n*ID:* `req_abc123`"
        }
      },
      ...
    ]

# 4. Response from Slack
{
  "ok": true,
  "ts": "1704621010.123456",
  "message": {...}
}
```

---

## Component Interaction

### Startup Sequence

```
Application Start (main.py lifespan)
   │
   ├─▶ 1. Configure Logging (structlog)
   │      • Set up JSON formatter
   │      • Add timestamp, log level
   │      • Configure console renderer for dev
   │
   ├─▶ 2. Start Metrics Server
   │      • Prometheus HTTP server on port 9090
   │      • Register all metrics (counters, histograms)
   │
   ├─▶ 3. Initialize Kafka Producer
   │      • Connect to Kafka bootstrap servers
   │      • Configure serializers (JSON)
   │      • Enable compression (gzip)
   │
   ├─▶ 4. Start Kafka Consumer (background task)
   │      • Subscribe to topics
   │      • Join consumer group
   │      • Start polling loop
   │
   └─▶ 5. Application Ready
          • FastAPI starts Uvicorn server
          • Listen on port 8000
          • Accept incoming requests
```

### Request Processing Pipeline

```
Incoming HTTP Request
   │
   ▼
┌──────────────────────────────────┐
│   Middleware Stack (LIFO)        │
│                                   │
│   TenantMiddleware               │◀─── Applied 3rd
│          ↓                        │
│   CorrelationMiddleware          │◀─── Applied 2nd
│          ↓                        │
│   SlackSignatureMiddleware       │◀─── Applied 1st
│          ↓                        │
│   Request reaches route handler  │
└──────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────┐
│   Route Handler                   │
│   • Validate request              │
│   • Process business logic        │
│   • Call external services        │
│   • Publish events                │
└──────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────┐
│   Response                        │
│   • Add correlation ID header     │
│   • Return JSON                   │
└──────────────────────────────────┘
```

---

## Data Flow Diagrams

### Complete End-to-End Flow

```
┌─────────────┐                                                    ┌─────────────┐
│   Slack     │                                                    │   Slack     │
│   Channel   │                                                    │   Channel   │
└──────┬──────┘                                                    └──────▲──────┘
       │                                                                  │
       │ User sends message                                              │ Bot posts notification
       │ "I need PDF export"                                             │ "✅ Requirement created"
       │                                                                  │
       ▼                                                                  │
┌─────────────────────────────────────────────────────────────┐    ┌────┴──────┐
│                   Slack Citizen Service                      │    │  Slack    │
│                                                               │    │  Web API  │
│  ┌─────────────────────────────────────────────────────┐    │    └────▲──────┘
│  │ Inbound Pipeline                                     │    │         │
│  │                                                       │    │         │
│  │  Webhook → Middleware → Validate → Map → Publish    │    │    ┌────┴──────────┐
│  └──────────────────────────┬────────────────────────────┘    │    │ post_message()│
│                             │                                  │    └────▲──────────┘
│                             ▼                                  │         │
│                      ┌──────────────┐                         │         │
│                      │ Kafka        │                         │    ┌────┴───────────┐
│                      │ Producer     │                         │    │ notify_*()     │
│                      └──────┬───────┘                         │    └────▲───────────┘
│                             │                                  │         │
│                             │                                  │    ┌────┴────────┐
│  ┌──────────────────────────┴────────────────────────────┐    │    │ Consumer    │
│  │ Outbound Pipeline                                      │    │    │ Handler     │
│  │                                                        │    │    └────▲────────┘
│  │  Consumer ← Parse ← Route ← Notify ← Slack API       │    │         │
│  └────────────────────────────────────────────────────────┘    │         │
└────────────────────────────────────────────────────────────────┘         │
                             │                                              │
                             │                                              │
                             ▼                                              │
                    ┌────────────────────┐                                 │
                    │                    │                                 │
                    │   Kafka Broker     │                                 │
                    │                    │                                 │
                    │  Topics:           │                                 │
                    │  • slack.message.  │                                 │
                    │    received        │─────────────────────────────────┘
                    │  • requirement.    │          Consumed by
                    │    created         │          Slack Citizen
                    └────────┬───────────┘
                             │
                             │ Consumed by other services
                             ▼
                    ┌────────────────────┐
                    │ Requirement Service│
                    │ Pulse Engine       │
                    │ Other Consumers    │
                    └────────────────────┘
```

### Multi-Tenancy Flow

```
Webhook from Team A           Webhook from Team B
    (team_id: T111)               (team_id: T222)
         │                              │
         ▼                              ▼
    ┌────────────────────────────────────────┐
    │      TenantMiddleware                  │
    │                                         │
    │  team_id → tenant_id mapping:          │
    │  • T111 → tenant_org_alpha             │
    │  • T222 → tenant_org_beta              │
    └──────────┬─────────────────┬───────────┘
               │                 │
               ▼                 ▼
         tenant_org_alpha   tenant_org_beta
               │                 │
               ▼                 ▼
         ┌─────────────────────────────┐
         │  Kafka Topics               │
         │  (Partitioned by tenant_id) │
         └─────────────────────────────┘
               │                 │
               ▼                 ▼
         Isolated Processing
```

---

## Error Handling & Retry Logic

### Inbound Error Handling

```
Webhook Received
   │
   ├─▶ Signature Verification Failed
   │      └─▶ Return 401 Unauthorized
   │          Log warning
   │          Slack won't retry (auth issue)
   │
   ├─▶ Validation Error (Bad Payload)
   │      └─▶ Return 400 Bad Request
   │          Log error with details
   │          Slack may retry
   │
   ├─▶ Kafka Publish Failed
   │      └─▶ Still return 200 OK (to Slack)
   │          Retry internally (3 attempts)
   │          If exhausted → Publish to DLQ
   │          Log error with event details
   │
   └─▶ Success
          └─▶ Return 200 OK immediately
              Process asynchronously
```

### Outbound Error Handling

```
Event Consumed from Kafka
   │
   ├─▶ Event Validation Failed
   │      └─▶ Log error
   │          Don't commit offset
   │          Reprocess on restart
   │
   ├─▶ Slack Metadata Missing
   │      └─▶ Log warning (can't determine channel)
   │          Commit offset (skip event)
   │          Can't retry without destination
   │
   ├─▶ Slack API Call Failed
   │      │
   │      ├─▶ Retry with Exponential Backoff
   │      │      Attempt 1: Immediate
   │      │      Attempt 2: 1s delay
   │      │      Attempt 3: 2s delay
   │      │      Attempt 4: 4s delay
   │      │
   │      ├─▶ Slack Rate Limit (429)
   │      │      └─▶ Wait for Retry-After header
   │      │          Retry with backoff
   │      │
   │      └─▶ All Retries Exhausted
   │             └─▶ Publish to DLQ topic:
   │                 "slack.notifications.failed.dlq"
   │                 Include original event + error
   │                 Commit offset (processed, but failed)
   │                 Alert/monitor DLQ for manual review
   │
   └─▶ Success
          └─▶ Commit offset
              Track metrics
              Log success
```

### Dead Letter Queue Flow

```
Failed Event
   │
   ▼
┌───────────────────────────────────┐
│ Publish to DLQ Topic              │
│                                    │
│ Topic: {original_topic}.dlq       │
│ Payload: {                         │
│   original_topic: "...",          │
│   original_message: {...},        │
│   error: "Rate limit exceeded",   │
│   error_type: "SlackApiError",    │
│   tenant_id: "...",               │
│   timestamp: "...",               │
│   retry_count: 3                  │
│ }                                  │
└───────────────────────────────────┘
   │
   ▼
┌───────────────────────────────────┐
│ DLQ Monitoring & Alerts           │
│                                    │
│ • Dashboard shows DLQ message     │
│   count per tenant                │
│ • Alert if threshold exceeded     │
│ • Manual review required          │
│ • Replay or discard decision      │
└───────────────────────────────────┘
```

---

## Observability

### Logging Context

Every log entry includes:

```json
{
  "timestamp": "2026-01-07T10:30:00.000Z",
  "level": "info",
  "logger": "src.routes.webhooks",
  "event": "slack_message_processed",
  "tenant_id": "tenant_T123456",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_id": "650e8400-e29b-41d4-a716-446655440001",
  "message_id": "msg_a1b2c3d4e5f6",
  "channel": "C123456"
}
```

### Metrics Tracked

**Inbound Metrics:**
- `slack_messages_received_total{tenant_id, channel_type}` - Counter
- `slack_messages_processing_seconds{tenant_id}` - Histogram
- `kafka_messages_published_total{tenant_id, topic}` - Counter

**Outbound Metrics:**
- `kafka_messages_consumed_total{tenant_id, topic}` - Counter
- `event_processing_seconds{tenant_id, event_type}` - Histogram
- `slack_api_calls_total{tenant_id, endpoint, status}` - Counter
- `slack_api_errors_total{tenant_id, error_type}` - Counter

### Request Tracing

```
Correlation ID: 550e8400-e29b-41d4-a716-446655440000
   │
   ├─▶ Webhook received
   ├─▶ Middleware processing
   ├─▶ Event mapping
   ├─▶ Kafka publish
   ├─▶ Event consumed (different process)
   ├─▶ Slack API call
   └─▶ Response complete

All logs and spans linked by correlation_id
```

---

## Summary

The Slack Citizen service implements a clean event-driven architecture with clear separation of concerns:

1. **Inbound Flow**: Webhook → Middleware → Validation → Mapping → Event Bus
2. **Outbound Flow**: Event Bus → Consumer → Routing → Notification → External API
3. **Cross-Cutting**: Logging, metrics, retry logic, multi-tenancy throughout
4. **Resilience**: Signature verification, retry with backoff, DLQ for failures
5. **Observability**: Structured logs, Prometheus metrics, distributed tracing

This design ensures:
- ✅ **Scalability** - Stateless service, horizontal scaling
- ✅ **Reliability** - Retry logic, DLQ, idempotency
- ✅ **Observability** - Rich logs and metrics for debugging
- ✅ **Security** - Signature verification, tenant isolation
- ✅ **Maintainability** - Clear component boundaries, documented flows
