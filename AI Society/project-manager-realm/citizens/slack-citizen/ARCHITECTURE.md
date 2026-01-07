# Slack Citizen - Architecture Overview

## Layered Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                       │
│                          (main.py/app.py)                        │
└──────────────────────┬──────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼─────┐ ┌─────▼──────┐ ┌────▼──────────┐
│   Routes    │ │ Middleware │ │   Webhooks   │
├─────────────┤ ├────────────┤ ├──────────────┤
│health.py    │ │auth.py     │ │webhooks.py   │
│             │ │tenant.py   │ │              │
│handlers.py  │ │correlation │ │handlers.py   │
└──────┬──────┘ └────────────┘ └──────┬───────┘
       │                              │
       └──────────────┬───────────────┘
                      │
         ┌────────────▼────────────┐
         │    Services Layer       │
         ├────────────────────────┤
         │ • SlackNotifier        │
         │ • InternalEventRouter  │
         │ • EventRouterChain     │
         │ • KafkaConsumerService │
         └────────────┬───────────┘
                      │
         ┌────────────▼────────────┐
         │   Clients/Repositories  │
         ├────────────────────────┤
         │ • SlackClient          │
         │ • SlackRepository      │
         │ • MessageBuilders      │
         │ • EventFactories       │
         └────────────┬───────────┘
                      │
         ┌────────────▼────────────┐
         │  Configuration & Utils  │
         ├────────────────────────┤
         │ • Config modules       │
         │ • Observability        │
         │ • ID Generators        │
         │ • Retry utilities      │
         └────────────────────────┘
```

## Dependency Flow (Dependency Inversion)

```
HIGH LEVEL MODULES
    ↓ depends on
ABSTRACTIONS (Interfaces)
    ↑ implemented by
LOW LEVEL MODULES

Example: Event Routing
┌─────────────────────────────┐
│ InternalEventRouter         │
│ (high level)                │
└────────────┬────────────────┘
             │ depends on
    ┌────────▼─────────┐
    │ EventHandler     │
    │ (abstract)       │
    └────┬────────┬────┘
         │        │
    ┌────▼──┐ ┌──▼──────────┐
    │Req    │ │Pulse  │Intel │
    │Handler│ │Handler│Handler│
    └───────┘ └───────┴──────┘
    (low level)
```

## Design Pattern Application

### 1. Factory Pattern - Event Creation
```
Event Source (Slack)
    ↓
SlackMessageEventFactory
    ↓
Internal EventEnvelope
    ↓
Kafka Topic
```

### 2. Strategy Pattern - Tenant Extraction
```
Request comes in
    ↓
TenantExtractorChain
    ├→ SlackTeamTenantExtractor (Try first)
    ├→ HeaderTenantExtractor (Fallback)
    └→ Default tenant_id (Last resort)
```

### 3. Repository Pattern - Data Access
```
SlackClient (Business Logic)
    ↓ uses
SlackClientRepository (Interface)
    ↓ uses
SlackSDK (External Library)
```

### 4. Chain of Responsibility - Event Routing
```
EventRouterChain
    ├→ RequirementEventHandler
    ├→ PulseEventHandler
    └→ IntelligenceEventHandler
```

### 5. Builder Pattern - Message Formatting
```
RequirementNotificationBuilder
    ├→ build_creation_blocks() → [Block1, Block2, Block3]
    └→ get_creation_text() → "✅ Requirement created..."
```

## Configuration Structure

```
Config Domains:
├── AppConfig (environment, port, version)
├── SlackConfig (API keys, signing secrets)
├── KafkaConfig (brokers, topics, consumer groups)
├── TenancyConfig (tenant mapping, multi-tenancy)
├── ObservabilityConfig (logging, tracing, metrics)
├── RetryConfig (retry attempts, DLQ, backoff)
└── RateLimitConfig (rate limits per tenant)

All composed into:
    ↓
Settings (Composite)
    ↓ provides
Global settings instance
```

## Event Flow

```
┌─────────────────────────────────────────┐
│         Slack Webhook                   │
│    /webhooks/slack/events               │
└──────────────┬──────────────────────────┘
               │
      ┌────────▼────────┐
      │ Signature       │
      │ Verification    │
      │ (Strategy)      │
      └────────┬────────┘
               │
      ┌────────▼────────┐
      │ Tenant          │
      │ Extraction      │
      │ (Chain)         │
      └────────┬────────┘
               │
      ┌────────▼─────────────┐
      │ Event Handler        │
      │ (Command Pattern)    │
      └────────┬─────────────┘
               │
      ┌────────▼─────────────┐
      │ Event Factory        │
      │ (Map to Internal)    │
      └────────┬─────────────┘
               │
      ┌────────▼─────────────┐
      │ Kafka Producer       │
      │ (Publish Event)      │
      └──────────────────────┘
               ↓
      ┌──────────────────────┐
      │ Internal Event Bus   │
      │ (Kafka Topics)       │
      └──────────┬───────────┘
               │
      ┌────────▼───────────────┐
      │ Kafka Consumer Service │
      │ (Event Listener)       │
      └────────┬───────────────┘
               │
      ┌────────▼──────────────┐
      │ Event Router Chain    │
      │ (Route to handler)    │
      └────────┬──────────────┘
               │
      ┌────────▼──────────────┐
      │ Slack Notifier        │
      │ (Send to Slack)       │
      └────────┬──────────────┘
               │
      ┌────────▼──────────────┐
      │ Message Builder       │
      │ (Format message)      │
      └────────┬──────────────┘
               │
      ┌────────▼──────────────┐
      │ Slack Repository      │
      │ (Abstract access)     │
      └────────┬──────────────┘
               │
      ┌────────▼──────────────┐
      │ Slack SDK             │
      │ (Send to Slack)       │
      └───────────────────────┘
```

## Observability Architecture

```
Application Code
    │
    ├─→ Logger.info/debug/error
    │       ↓
    │   structlog (Context vars)
    │       ↓
    │   Formatted JSON logs → stdout
    │
    ├─→ Metrics.labels().inc()
    │       ↓
    │   Prometheus Counter/Histogram
    │       ↓
    │   /metrics endpoint
    │
    └─→ Tracing (OpenTelemetry)
            ↓
        Jaeger Agent
```

## Testing Strategy

```
Unit Tests (Isolated)
├── Event Factories (no Kafka)
├── Message Builders (no Slack API)
├── Config Classes (no environment)
├── Handlers (mocked dependencies)
└── Strategies (strategy pattern)

Integration Tests (Local Services)
├── Slack Client ↔ Repository
├── Config ↔ Settings
├── Event Router ↔ Handlers
└── Middleware ↔ Request

E2E Tests (Full Stack)
├── Slack Webhook → Event → Kafka → Handler → Slack
└── Full request/response cycle
```

## Extensibility Points

### Adding New Event Type
```
1. Create EventHandler subclass
2. Add _can_handle() and _do_handle()
3. Add to EventRouterChain
4. Register in router initialization
```

### Adding New Notification Type
```
1. Create NotificationBuilder class
2. Implement build_*_blocks() methods
3. Call from SlackNotifier
4. No changes to routing needed
```

### Adding New Signature Strategy
```
1. Create SignatureVerifier subclass
2. Implement verify() method
3. Use in SlackSignatureMiddleware
4. No changes to other middleware needed
```

### Adding New Tenant Extractor
```
1. Create TenantExtractor subclass
2. Implement extract() method
3. Add to TenantExtractorChain
4. Automatic chain integration
```

## Performance Characteristics

```
Startup:
├── Configuration load: O(1)
├── Middleware setup: O(n) handlers
└── Consumer start: O(1)

Per Message:
├── Signature verification: O(n) where n=body size
├── Tenant extraction: O(1) with caching
├── Event routing: O(h) where h=handlers in chain
├── Message building: O(b) where b=blocks
└── Slack API call: O(network latency)

Memory:
├── Config objects: ~1KB each
├── Handler instances: ~100B each
├── In-flight messages: 10 * msg_size
└── Tenant cache: O(distinct tenants)
```

## Error Handling Strategy

```
Level 1: Request Level
├── Signature verification fail → 401
├── Parsing error → 400
└── Unhandled error → 500

Level 2: Event Processing
├── Slack API error → Log + Retry + DLQ
├── Handler error → Log + Retry
└── Unhandled → Error log + continue

Level 3: Infrastructure
├── Kafka unavailable → Backoff + retry
└── Slack API down → DLQ + exponential backoff
```

---

This architecture provides:
- ✅ Loose coupling between components
- ✅ High cohesion within modules
- ✅ Easy to test each component
- ✅ Easy to extend with new functionality
- ✅ Clear separation of concerns
- ✅ SOLID principle compliance
- ✅ Industry-standard design patterns
- ✅ Maintainable codebase
