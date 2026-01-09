# Event-Driven Architecture: Slack → Intelligence → Slack Response

## Overview

The Intelligence Service now implements a complete event-driven response architecture that enables seamless two-way communication between Slack and the AI agents.

**Architecture Pattern:**
```
Slack User
    ↓
Slack App (webhook)
    ↓
Slack Citizen (consumer)
    ↓
Kafka Topic: project-manager.message.received
    ↓
Intelligence Service (consumer)
    ↓
Agent Pipeline (Clarification → PRD → Analysis)
    ↓
Kafka Topic: project-manager.reply.requested
    ↓
Slack Citizen (consumer)
    ↓
Slack API (bot.postMessage / chat.postMessage)
    ↓
Slack User (response in thread)
```

## Components

### 1. Message Ingestion (Intelligence Service)
**File:** `app/kafka/consumer.py`

- **Topic:** `project-manager.slack.message.received`
- **Consumer Group:** `intelligence-service-group`
- **Offset Reset:** `earliest` (reprocess all historical messages)
- **Handler:** `handle_slack_message()` in `app/kafka/handlers.py`

**Payload Structure:**
```json
{
  "event_id": "evt_xyz",
  "event_type": "slack.message.received",
  "occurred_at": "2026-01-08T18:30:00Z",
  "payload": {
    "tenant_id": "workspace-123",
    "slack_user_id": "U123456",
    "slack_channel_id": "C123456",
    "thread_ts": "1234567890.000100",
    "text": "How do we implement real-time notifications?"
  }
}
```

### 2. Message Processing Pipeline

**Location:** `app/kafka/handlers.py`

**Entry Point:** `handle_slack_message()`
1. Extract Slack context (channel, thread, user)
2. Store user message in database
3. Get or create conversation state
4. Retrieve conversation history
5. Route to appropriate agent based on state
6. **NEW:** Publish agent response to Kafka

**Conversation State Machine:**
```
clarification (0-95% confidence)
    ↓
prd-generator (95-100% confidence)
    ↓
analysis (100% confidence)
    ↓
complete
```

**Confidence Scoring:**
- Clarification agent contributes to confidence
- Each turn accumulates confidence (0-100%)
- At 95% threshold: Auto-progression to PRD generator
- After PRD: Analysis phase with 100% completion
- Response published after each phase

### 3. Agent Response Publishing

**File:** `app/kafka/producer.py`

**Class:** `KafkaMessageProducer`
```python
class KafkaMessageProducer:
    async def __init__(brokers: List[str]) -> None
    async def start() -> None           # Initialize AIOKafkaProducer
    async def stop() -> None            # Cleanup
    async def publish_slack_reply(
        channel_id: str,                # Slack channel ID
        thread_ts: str,                 # Thread timestamp
        message_text: str,              # Plain text message
        message_blocks: List[Dict] = None  # Rich formatting blocks
    ) -> None
```

**Response Publishing Workflow:**

For each phase:

1. **Clarification Phase** (`app/kafka/handlers.py:410-430`)
   ```python
   questions, rationale = clarification_output
   text, blocks = format_clarification_questions_for_slack(questions, rationale)
   await producer.publish_slack_reply(channel_id, thread_ts, text, blocks)
   ```

2. **PRD Generation Phase** (`app/kafka/handlers.py:497-515`)
   ```python
   prd = prd_output.dict()
   text, blocks = format_prd_for_slack(prd)
   await producer.publish_slack_reply(channel_id, thread_ts, text, blocks)
   ```

3. **Analysis Phase** (`app/kafka/handlers.py:577-597`)
   ```python
   analysis = analysis_output.dict()
   text, blocks = format_analysis_for_slack(analysis)
   await producer.publish_slack_reply(channel_id, thread_ts, text, blocks)
   ```

**Message Format to Slack:**
```json
{
  "event_type": "slack.reply.requested",
  "payload": {
    "slack_channel_id": "C123456",
    "thread_ts": "1234567890.000100",
    "text": "Here are clarifying questions...",
    "blocks": [
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": "*Clarification Questions*"
        }
      }
    ]
  }
}
```

### 4. Message Formatting

**File:** `app/utils/slack_formatter.py`

Converts agent outputs to Slack-friendly format with rich formatting:

#### `format_clarification_questions_for_slack(questions, rationale)`
- Returns: `(text: str, blocks: List[Dict])`
- Formats questions with categories and priorities
- Rich blocks with emoji and formatting
- Example: ❓ Question 1: ... [category • priority]

#### `format_prd_for_slack(prd: Dict)`
- Returns: `(text: str, blocks: List[Dict])`
- Includes title, overview, objectives, user stories, acceptance criteria
- Dividers between sections
- Emoji indicators (📋, 🎯, 👥, etc.)

#### `format_analysis_for_slack(analysis: Dict)`
- Returns: `(text: str, blocks: List[Dict])`
- Completeness score with color indicator (🟢🟡🔴)
- Gaps, risks, recommendations with counts
- Effort estimation

### 5. Response Consumption (Slack Citizen)

**Expected Location:** `../../citizens/slack-citizen/app/kafka/`

**Consumer Topic:** `project-manager.slack.reply.requested`

**Consumer Group:** `slack-citizen-group`

**Handler Responsibilities:**
1. Receive message from Kafka topic
2. Extract channel, thread_ts, text, blocks
3. Call Slack API: `client.chat_postMessage()`
   - `channel`: slack_channel_id
   - `thread_ts`: thread_ts
   - `text`: message_text
   - `blocks`: message_blocks
4. Log success/failure

**Example Implementation Needed:**
```python
# In slack-citizen: app/kafka/handlers.py
async def handle_slack_reply_requested(message: Dict) -> None:
    payload = message["payload"]
    
    try:
        response = await slack_client.chat_postMessage(
            channel=payload["slack_channel_id"],
            thread_ts=payload["thread_ts"],
            text=payload["text"],
            blocks=payload.get("blocks", [])
        )
        logger.info("slack_reply_posted", response_ts=response["ts"])
    except Exception as e:
        logger.error("slack_reply_post_failed", error=str(e))
```

## Database Integration

### Conversation State Tracking
**Table:** `conversation_states`

```sql
CREATE TABLE conversation_states (
    conversation_id UUID PRIMARY KEY,
    current_agent VARCHAR(100),              -- clarification|prd-generator|analysis|complete
    confidence_score DECIMAL(5, 2),          -- 0-100%
    turns_count INTEGER,                     -- Multi-turn counter
    metadata JSONB,                          -- Agent-specific data
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Metadata Structure:**
- **Clarification:** `{ "questions": [...], "rationale": "..." }`
- **PRD:** `{ "title": "...", "objectives": [...], ... }`
- **Analysis:** `{ "gaps": [...], "risks": [...], ... }`

### Message Storage
**Table:** `messages`

All messages (user + assistant) stored with conversation context:
```sql
INSERT INTO messages (
    message_id,          -- UUID
    conversation_id,     -- Links to conversation_states
    role,                -- "user" or "assistant"
    content,             -- JSON for assistant, text for user
    created_at
)
```

## Data Flow Example

### Scenario: User asks about real-time notifications

**Step 1: Slack Message Received**
```
User: "How do we implement real-time notifications?"
Channel: #project-discussion
Thread: 1234567890.000100
```

**Step 2: Intelligence Consumer Processes**
- Extract message from Kafka topic
- Store as user message in DB
- Check conversation state → "clarification" (first message)
- Get empty conversation history

**Step 3: Clarification Agent Runs**
- Input: User description + empty history
- Output: 3 clarification questions, 45% confidence
- Store assistant message in DB
- **Publish to Kafka:** Clarification questions
- Update state: confidence = 45%, turns = 1

**Step 4: Slack Citizen Receives Reply**
- Consume from `slack.reply.requested` topic
- Format: Blocks with questions
- Post to Slack channel in thread

**Step 5: User Responds in Thread**
- New message in same thread
- Slack Citizen publishes to `slack.message.received`
- Intelligence Consumer processes (2nd turn)
- Confidence accumulates: 45% + 60% = 100% → Move to PRD

**Step 6: PRD Generation Agent Runs**
- Input: Original question + clarifications + history (3 messages)
- Output: PRD with structure, objectives, user stories
- **Publish to Kafka:** PRD document
- Update state: confidence = 100%, current_agent = "analysis"

**Step 7: Analysis Agent Runs**
- Input: Full context + clarifications + PRD
- Output: Gap analysis, risks, recommendations
- **Publish to Kafka:** Analysis report
- Update state: current_agent = "complete"

**Step 8: User Sees Full Response Thread**
```
Slack Thread:
├─ User: "How do we implement real-time notifications?"
├─ Bot: "Clarification Questions" (block-formatted)
├─ User: "[Response with context]"
├─ Bot: "PRD: Real-Time Notification System" (detailed)
└─ Bot: "Analysis: Gaps & Recommendations" (comprehensive)
```

## Integration Checklist

- ✅ Intelligence Service Producer: `KafkaMessageProducer` created and initialized
- ✅ Producer integrated into all 3 phase handlers (clarification, prd, analysis)
- ✅ Slack message formatters: `slack_formatter.py` with 3 format functions
- ✅ Consumer receives messages and processes
- 🟡 Slack Citizen needs consumer for `project-manager.slack.reply.requested` topic
- 🟡 Slack Citizen needs to post to Slack API with formatted messages
- 🟡 Error handling and retry logic for failed Kafka publishes
- 🟡 Thread tracking to ensure responses appear in correct thread

## Testing the Flow

### Manual Test Steps

1. **Start Services**
   ```bash
   cd intelligence/service && docker-compose up -d
   cd citizens/slack-citizen && docker-compose up -d
   ```

2. **Send Test Message to Slack**
   - Mention bot: "@Project Manager: How do we build real-time features?"
   - Observe Slack Citizen publishes to Kafka
   - Check Intelligence Service logs for message processing
   - Verify database has user message

3. **Monitor Kafka Topics**
   ```bash
   # Watch incoming messages
   docker exec kafka kafka-console-consumer \
     --bootstrap-server localhost:9092 \
     --topic project-manager.slack.message.received \
     --from-beginning
   
   # Watch outgoing responses
   docker exec kafka kafka-console-consumer \
     --bootstrap-server localhost:9092 \
     --topic project-manager.slack.reply.requested \
     --from-beginning
   ```

4. **Verify Database**
   ```sql
   SELECT * FROM conversations ORDER BY created_at DESC LIMIT 1;
   SELECT * FROM messages WHERE conversation_id = '...' ORDER BY created_at;
   SELECT * FROM conversation_states WHERE conversation_id = '...';
   ```

5. **Check Slack Response**
   - Response should appear in thread
   - Rich formatting (blocks) should render properly
   - Multiple agent responses should appear sequentially

## Architecture Benefits

✅ **Decoupled:** Intelligence Service doesn't call Slack API directly
✅ **Scalable:** Multiple consumers can handle Slack replies independently
✅ **Reliable:** Kafka provides message durability and replay capability
✅ **Observable:** All messages logged and persisted in database
✅ **Extensible:** Easy to add new reply handlers or processors
✅ **Testable:** Can replay messages for debugging and testing

## Known Limitations

- ⚠️ Slack Citizen consumer for outgoing topic not yet implemented
- ⚠️ No retry logic for failed Kafka publishes (could lose responses)
- ⚠️ No error response messaging (if agent fails, user doesn't know)
- ⚠️ Rich formatting relies on Slack blocks (fallback text provided)

## Next Steps

1. Implement Slack Citizen consumer for `project-manager.slack.reply.requested`
2. Add Slack API posting in Slack Citizen handler
3. Test end-to-end: Send message via Slack → See response in thread
4. Add retry/DLQ logic for failed publishes
5. Implement error response messaging for failed agent processing
