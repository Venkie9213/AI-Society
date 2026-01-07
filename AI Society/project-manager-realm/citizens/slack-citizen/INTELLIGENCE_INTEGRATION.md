# Intelligence Service Integration

## Overview

The Slack Citizen has been updated to integrate with the Intelligence Service for LLM processing. The Slack Citizen acts as a **thin adapter** between Slack and the platform's event bus, while all LLM logic resides in the Intelligence Service.

## Architecture Changes

### Before (Incorrect)
```
Slack → Slack Citizen (with LLM logic) → Slack
```

### After (Correct - Microservices)
```
Slack → Slack Citizen → Kafka → Intelligence Service → Kafka → Slack Citizen → Slack
```

## Event Flow

### 1. Inbound: User Message from Slack

```
User sends message in Slack
   ↓
Slack Citizen receives webhook
   ↓
Validates signature & extracts tenant
   ↓
Publishes to Kafka topic: "slack.message.received"
   ↓
Adds 👀 reaction to acknowledge
```

**Event Schema: slack.message.received**
```json
{
  "event_id": "uuid",
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

### 2. Processing: Intelligence Service

```
Intelligence Service consumes "slack.message.received"
   ↓
Routes to appropriate LLM agent (OpenAI, Claude, etc.)
   ↓
Processes message through LLM
   ↓
Formats response (text + optional Slack blocks)
   ↓
Publishes to Kafka topic: "slack.reply.requested"
```

**Event Schema: slack.reply.requested**
```json
{
  "event_id": "uuid",
  "occurred_at": "2024-01-07T12:00:05Z",
  "tenant_id": "tenant_123",
  "source": "intelligence-service",
  "payload_version": "1.0",
  "payload": {
    "message_text": "To export reports, go to Reports > Export...",
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

### 3. Outbound: Reply to Slack

```
Slack Citizen consumes "slack.reply.requested"
   ↓
Validates SlackReplyRequestedPayload
   ↓
Calls Slack Web API to post message
   ↓
Posts to same channel/thread
   ↓
User sees reply in Slack
```

## Code Changes

### 1. New Schema: SlackReplyRequestedPayload

**File:** `/src/schemas/internal_schemas.py`

```python
class SlackReplyRequestedPayload(BaseModel):
    """Payload for slack.reply.requested event (from Intelligence Service)."""
    message_text: str
    slack_channel_id: str
    slack_thread_ts: Optional[str] = None
    slack_user_id: str
    blocks: Optional[List[Dict[str, Any]]] = None
```

### 2. Updated Consumer Topics

**File:** `/src/main.py` - `lifespan()` function

Added `"slack.reply.requested"` to the consumer topics list:

```python
consumer_topics = [
    "requirement.requirement.created",
    "requirement.clarification.completed",
    "pulse.execution.failed",
    "slack.reply.requested",  # NEW
]
```

### 3. New Event Router

**File:** `/src/main.py` - `handle_internal_event()` function

Added routing for intelligence-service source:

```python
elif source == "intelligence-service":
    await handle_intelligence_event(envelope)
```

### 4. New Handler Functions

**File:** `/src/main.py`

```python
async def handle_intelligence_event(envelope: EventEnvelope) -> None:
    """Handle intelligence-related events."""
    payload = envelope.payload
    
    # Check if this is a slack.reply.requested event
    if "message_text" in payload and "slack_channel_id" in payload:
        reply = SlackReplyRequestedPayload(**payload)
        await send_slack_reply(reply, envelope.tenant_id)


async def send_slack_reply(
    reply: SlackReplyRequestedPayload,
    tenant_id: str,
) -> None:
    """Send a reply message to Slack (from Intelligence Service)."""
    slack_client = get_slack_client()
    
    logger.info(
        "sending_slack_reply",
        channel=reply.slack_channel_id,
        thread_ts=reply.slack_thread_ts,
        tenant_id=tenant_id,
    )
    
    # Post reply to Slack
    await slack_client.post_message(
        channel=reply.slack_channel_id,
        text=reply.message_text,
        blocks=reply.blocks,
        thread_ts=reply.slack_thread_ts,
        tenant_id=tenant_id,
    )
    
    logger.info(
        "slack_reply_sent",
        channel=reply.slack_channel_id,
        thread_ts=reply.slack_thread_ts,
        tenant_id=tenant_id,
    )
```

## Separation of Concerns

### Slack Citizen (Thin Adapter)

**Responsibilities:**
- ✅ Webhook validation & security (signature verification)
- ✅ Slack API integration (post messages, reactions)
- ✅ Event transformation (Slack format ↔ Internal format)
- ✅ Rate limiting & retry logic for Slack API
- ✅ Multi-tenancy (tenant ID extraction)

**Does NOT Do:**
- ❌ Business logic
- ❌ LLM integration
- ❌ Intent detection
- ❌ Conversation context management

### Intelligence Service (Smart Core)

**Responsibilities:**
- ✅ LLM integration (OpenAI, Claude, etc.)
- ✅ Intent detection & routing
- ✅ Conversation context management
- ✅ Response generation & formatting
- ✅ Business logic & decision making

**Does NOT Do:**
- ❌ Slack-specific code
- ❌ Direct Slack API calls
- ❌ Webhook handling

## Testing the Integration

### 1. Verify Service is Running

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "slack-citizen",
  "version": "1.0.0"
}
```

### 2. Check Kafka Topics

```bash
# Access Kafka UI
open http://localhost:8080

# Or use CLI
docker exec slack-citizen-kafka kafka-topics --list --bootstrap-server localhost:9092
```

Expected topics:
- `slack.message.received` (Slack Citizen → Intelligence Service)
- `slack.reply.requested` (Intelligence Service → Slack Citizen)

### 3. Monitor Logs

```bash
# Slack Citizen logs
docker logs -f slack-citizen

# Look for events:
# - message_received (inbound from Slack)
# - event_published (to Kafka)
# - event_consumed (from Kafka)
# - sending_slack_reply (outbound to Slack)
```

### 4. Test with Slack

1. Send a message in Slack channel
2. Slack Citizen adds 👀 reaction (acknowledgment)
3. Intelligence Service processes and publishes reply
4. Slack Citizen posts reply to thread

## Next Steps

### Intelligence Service Implementation

The Intelligence Service needs to be implemented in the `intelligence/` folder:

1. **Create Intelligence Service structure:**
   ```
   intelligence/
   ├── src/
   │   ├── main.py
   │   ├── agents/
   │   │   └── slack_agent.py
   │   ├── llm/
   │   │   ├── openai_client.py
   │   │   └── claude_client.py
   │   └── events/
   │       ├── consumer.py
   │       └── producer.py
   ├── Dockerfile
   ├── docker-compose.yml
   └── requirements.txt
   ```

2. **Consumer Setup:**
   - Subscribe to: `slack.message.received`
   - Process messages through LLM
   - Publish to: `slack.reply.requested`

3. **LLM Integration:**
   - OpenAI API client
   - Claude API client
   - Intent detection
   - Context management

4. **Update Docker Compose:**
   - Add intelligence-service to network
   - Share Kafka with slack-citizen

## Documentation Updates

- ✅ `CONTROL_FLOW.md` - Updated with Intelligence Service flow
- ✅ `INTELLIGENCE_INTEGRATION.md` - This document (new)
- ⏳ Intelligence Service documentation (pending implementation)

## Summary

The Slack Citizen is now ready to work with the Intelligence Service. It:
1. Publishes user messages to `slack.message.received`
2. Consumes LLM replies from `slack.reply.requested`
3. Posts replies back to Slack

The Intelligence Service (to be implemented) will:
1. Consume messages from `slack.message.received`
2. Process through LLM
3. Publish replies to `slack.reply.requested`

This architecture maintains clean separation of concerns and follows microservices best practices.
