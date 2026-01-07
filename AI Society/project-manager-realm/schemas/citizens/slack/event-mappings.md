# Slack Citizen Event Mappings

This document defines how Slack events are mapped to internal event schemas within the AI Society platform.

## Event Mapping Contracts

### 1. Slack Message → Internal Event

**Slack Event Type:** `message`

**Internal Event Topic:** `project-manager.slack.message.received`

**Mapping:**

| Slack Field | Internal Field | Transformation |
|-------------|---------------|----------------|
| `event.user` | `payload.slack_user_id` | Direct |
| `event.channel` | `payload.slack_channel_id` | Direct |
| `team_id` | `payload.slack_team_id` | Direct |
| `event.text` | `payload.text` | Direct |
| `event.thread_ts` | `payload.thread_ts` | Optional |
| `event.ts` | `payload.message_ts` | Direct |
| `event.channel_type` | `payload.channel_type` | Default: "channel" |
| N/A | `payload.message_id` | Generated: `msg_{uuid}` |
| `team_id` | `tenant_id` | Mapped via tenant service |
| `event_time` | `occurred_at` | Unix timestamp → ISO 8601 |
| N/A | `event_id` | Generated: UUID |
| N/A | `source` | Static: "slack-citizen" |
| N/A | `payload_version` | Static: "v1" |

**Example Internal Event:**

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "occurred_at": "2026-01-07T10:30:00.000Z",
  "tenant_id": "tenant_T01234567",
  "source": "slack-citizen",
  "payload_version": "v1",
  "payload": {
    "message_id": "msg_a1b2c3d4e5f6",
    "slack_user_id": "U01234567",
    "slack_channel_id": "C01234567",
    "slack_team_id": "T01234567",
    "text": "I need a feature to export reports to PDF",
    "thread_ts": null,
    "message_ts": "1704621000.123456",
    "channel_type": "channel",
    "metadata": {
      "slack_event_id": "Ev01234567",
      "slack_event_time": 1704621000,
      "message_subtype": null
    }
  }
}
```

---

### 2. Slack Slash Command → Internal Event

**Slack Event Type:** Slash Command POST

**Internal Event Topic:** `project-manager.slack.command.invoked`

**Mapping:**

| Slack Field | Internal Field | Transformation |
|-------------|---------------|----------------|
| `user_id` | `payload.slack_user_id` | Direct |
| `team_id` | `payload.slack_team_id` | Direct |
| `channel_id` | `payload.slack_channel_id` | Direct |
| `command` | `payload.command` | Direct |
| `text` | `payload.arguments` | Direct |
| `response_url` | `payload.response_url` | Direct |
| `trigger_id` | `payload.trigger_id` | Direct |
| N/A | `payload.command_id` | Generated: `cmd_{uuid}` |
| `team_id` | `tenant_id` | Mapped via tenant service |

**Example Internal Event:**

```json
{
  "event_id": "650e8400-e29b-41d4-a716-446655440001",
  "occurred_at": "2026-01-07T10:35:00.000Z",
  "tenant_id": "tenant_T01234567",
  "source": "slack-citizen",
  "payload_version": "v1",
  "payload": {
    "command_id": "cmd_b2c3d4e5f6g7",
    "slack_user_id": "U01234567",
    "slack_team_id": "T01234567",
    "slack_channel_id": "C01234567",
    "command": "/create-requirement",
    "arguments": "Build user authentication system",
    "response_url": "https://hooks.slack.com/commands/...",
    "trigger_id": "123456789.987654321.abcdef"
  }
}
```

---

### 3. Slack Interaction → Internal Event

**Slack Event Type:** Interactive Component (button, modal, etc.)

**Internal Event Topic:** `project-manager.slack.interaction.triggered`

**Mapping:**

| Slack Field | Internal Field | Transformation |
|-------------|---------------|----------------|
| `user.id` | `payload.slack_user_id` | Direct |
| `team.id` | `payload.slack_team_id` | Direct |
| `channel.id` | `payload.slack_channel_id` | Optional |
| `type` | `payload.interaction_type` | Direct |
| `actions` | `payload.actions` | Direct array |
| `response_url` | `payload.response_url` | Optional |
| `trigger_id` | `payload.trigger_id` | Direct |
| N/A | `payload.interaction_id` | Generated: `int_{uuid}` |
| `team.id` | `tenant_id` | Mapped via tenant service |

---

## Consumed Events (Outbound to Slack)

### 1. Requirement Created → Slack Notification

**Internal Event Topic:** `project-manager.requirement.requirement.created`

**Slack Action:** Post message to channel

**Metadata Required:**
- `slack_channel_id` - Channel to post to
- `slack_thread_ts` - Thread to reply to (optional)

**Slack Message Format:**

```json
{
  "channel": "{slack_channel_id}",
  "thread_ts": "{slack_thread_ts}",
  "text": "✅ Requirement created: {title}",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*New Requirement Created*\n\n*Title:* {title}\n*ID:* `{requirement_id}`"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Description:*\n{description}"
      }
    }
  ]
}
```

---

### 2. Clarification Completed → Slack PRD

**Internal Event Topic:** `project-manager.requirement.clarification.completed`

**Slack Action:** Post PRD to channel/thread

**Metadata Required:**
- `slack_channel_id` - Channel to post to
- `slack_thread_ts` - Thread to reply to (optional)

**Slack Message Format:**

```json
{
  "channel": "{slack_channel_id}",
  "thread_ts": "{slack_thread_ts}",
  "text": "📋 PRD completed for requirement {requirement_id}",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Product Requirements Document*"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Summary:* {clarification_summary}"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*PRD:*\n```\n{prd_content}\n```"
      }
    }
  ]
}
```

---

### 3. Pulse Execution Failed → Slack Alert

**Internal Event Topic:** `project-manager.pulse.execution.failed`

**Slack Action:** Post alert to channel

**Metadata Required:**
- `slack_channel_id` - Channel to post to (fallback to default alerts channel)

**Slack Message Format:**

```json
{
  "channel": "{slack_channel_id}",
  "text": "❌ Pulse execution failed: {pulse_name}",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*⚠️ Pulse Execution Failed*\n\n*Pulse:* {pulse_name}\n*Execution ID:* `{execution_id}`"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Error:* {error_message}"
      }
    }
  ]
}
```

---

## Event Envelope Standard

All internal events MUST follow this envelope structure:

```typescript
{
  event_id: string;          // UUID
  occurred_at: datetime;     // ISO 8601 timestamp
  tenant_id: string;         // Tenant identifier
  source: string;            // Service that emitted the event
  payload_version: string;   // Schema version (e.g., "v1")
  payload: object;           // Event-specific data
}
```

## Metadata Conventions

To enable bidirectional communication, internal events that originate from Slack should include these metadata fields in the payload:

- `slack_channel_id` - Slack channel ID for notifications
- `slack_thread_ts` - Thread timestamp for threaded replies
- `slack_message_ts` - Original message timestamp
- `slack_team_id` - Slack workspace ID
- `slack_event_id` - Original Slack event ID for deduplication

## Idempotency

- **Inbound**: Slack event IDs are logged to prevent duplicate processing
- **Outbound**: Use Kafka's exactly-once semantics and message keys for deduplication

## Error Handling

Failed messages are published to Dead Letter Queue (DLQ) topics:

- `{original_topic}.dlq` - Contains failed messages with error context
- DLQ messages include: `original_topic`, `original_message`, `error`, `error_type`, `tenant_id`
