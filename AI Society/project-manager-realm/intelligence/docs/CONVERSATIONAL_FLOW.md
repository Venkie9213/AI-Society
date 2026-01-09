# Conversational Agent Flow Implementation

## Overview

The intelligence service now implements a **multi-turn conversational flow** instead of one-shot agent calls. The system automatically progresses through agents based on a **confidence threshold of 95%**.

## Flow Architecture

### Agent Progression Chain

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER MESSAGE                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
        ┌─────────────────────────────────┐
        │  CLARIFICATION AGENT (Phase 1)  │
        │  Asks clarifying questions      │
        └────────────┬────────────────────┘
                     │
         ┌───────────┴────────────┐
         │ Confidence < 95%?      │ Confidence >= 95%?
         ↓                        ↓
    ASK MORE QUESTIONS    ┌──────────────────────┐
    (Conversational)      │ PRD GENERATOR (Phase 2)
                          │ Generates PRD sections
                          └──────────┬───────────┘
                                     │
                          ┌──────────┴───────────┐
                          │ ANALYSIS AGENT       │
                          │ (Phase 3)            │
                          │ Analyzes requirements
                          └──────────┬───────────┘
                                     │
                                     ↓
                          ┌──────────────────────┐
                          │ CONVERSATION COMPLETE
                          │ (All responses stored)
                          └──────────────────────┘
```

## Key Features

### 1. Confidence-Based Progression
- **Confidence Score**: Accumulates with each turn (0-100%)
- **Threshold**: 95% required to move to next agent
- **Tracking**: Stored in `conversation_states` table
- **Turns**: Counts multi-turn interactions for same agent

### 2. Conversation State Management

**Database Table**: `conversation_states`
```sql
CREATE TABLE conversation_states (
    conversation_id UUID PRIMARY KEY,
    current_agent VARCHAR(100),           -- clarification, prd-generator, analysis, complete
    confidence_score DECIMAL(5, 2),       -- 0.0 to 100.0
    turns_count INTEGER,                  -- Number of turns in current agent
    metadata JSONB                        -- Agent-specific data
);
```

### 3. Multi-Turn Support

**Clarification Phase (Conversational)**
1. User sends message #1
2. Clarification agent generates questions
3. Confidence increases
4. If confidence < 95%, wait for user response
5. User sends message #2 (answer to questions)
6. Clarification agent processes answer, increases confidence
7. When confidence >= 95%, move to PRD generation

**Example Flow**:
```
Turn 1:
  User: "I want to build an AI project manager"
  Agent: Ask 5 clarifying questions
  Confidence: 50%
  Status: Ask follow-up

Turn 2:
  User: "It should help with task scheduling and team management"
  Agent: Process answer, ask 3 more questions
  Confidence: 75%
  Status: Ask follow-up

Turn 3:
  User: "For software development teams, 10-50 people"
  Agent: Process answer
  Confidence: 98%
  Status: Move to PRD Generation ✓
```

## Implementation Details

### 1. Conversation History Tracking

All messages are stored:
- User messages
- Agent responses (questions, PRD sections, analysis)
- Conversation history used for context on next turn

### 2. Agent Handlers

**`handle_clarification_phase()`**
- Calls clarification agent with history
- Extracts confidence score
- Accumulates scores across turns
- Checks threshold for progression
- Stores state for next message

**`handle_prd_generation_phase()`**
- Auto-triggered when confidence >= 95%
- Uses conversation history for context
- Generates complete PRD
- Moves to analysis phase

**`handle_analysis_phase()`**
- Analyzes generated PRD
- Identifies gaps, risks, recommendations
- Marks conversation as complete

### 3. State Persistence

```python
# For each incoming message:
1. Get conversation state
   - If new: Initialize with clarification agent
   - If existing: Get current agent and confidence

2. Get full conversation history
   - All user messages
   - All assistant responses

3. Process message through current agent
   - Pass history for context
   - Update confidence score

4. Check threshold:
   - If confidence >= 95%: Move to next agent
   - If < 95%: Stay on current agent (conversational)

5. Update state for next message
```

## Database Schema Addition

```sql
CREATE TABLE conversation_states (
    id SERIAL PRIMARY KEY,
    conversation_id UUID UNIQUE NOT NULL REFERENCES conversations(conversation_id),
    current_agent VARCHAR(100),
    confidence_score DECIMAL(5, 2) DEFAULT 0.0,
    turns_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Configuration

**Confidence Threshold**:
```python
# In app/kafka/handlers.py
CONFIDENCE_THRESHOLD = 95.0  # Percentage required to advance
```

Adjust this value to change how "confident" the system needs to be before progressing to the next agent.

## Logging

All transitions are logged with details:

```
✓ conversation_state: Logs current agent, confidence, turns
✓ confidence_check: When threshold is checked
✓ clarification_agent_start: Turn #N started
✓ clarification_agent_completed: Confidence increased to X%
✓ prd_generation_start: Auto-triggered when ready
✓ analysis_agent_start: Final phase initiated
```

## Message Flow Example

```
User sends: "Build a customer loyalty program"
├─ Message stored (role=user)
├─ Conversation state created (agent=clarification, confidence=0%)
├─ Clarification agent runs
│  └─ Generates 5 questions
│  └─ Confidence: 50%
├─ Response stored (role=assistant, content=questions)
├─ State updated: confidence=50%, turns=1
└─ Waiting for user response...

User responds with answer
├─ Message stored (role=user)
├─ Retrieve state: agent=clarification, confidence=50%
├─ Clarification agent runs (with history)
│  └─ Processes answer, asks 2 more questions
│  └─ Confidence: 80%
├─ Response stored (role=assistant)
├─ State updated: confidence=80%, turns=2
└─ Still in clarification...

User provides more details
├─ Message stored (role=user)
├─ Retrieve state: agent=clarification, confidence=80%
├─ Clarification agent runs (with full history)
│  └─ Confidence now: 96%
├─ Response stored
├─ Check threshold: 96% >= 95% ✓
├─ State updated: agent=prd-generator, confidence=96%
├─ PRD generator auto-triggers
│  └─ Generates complete PRD (10 sections)
├─ PRD response stored (role=assistant)
├─ State updated: agent=analysis, confidence=100%
├─ Analysis agent auto-triggers
│  └─ Analyzes PRD, identifies gaps & risks
└─ Analysis response stored → DONE
```

## Benefits

1. **Conversational UX**: Users can clarify incrementally instead of one big info dump
2. **Confidence Tracking**: System knows when it has enough info to proceed
3. **Full Context**: Each agent sees all previous messages
4. **Automated Chaining**: No manual triggering of next agent
5. **State Persistence**: Can resume conversation later
6. **Multi-turn Safety**: Won't move forward prematurely

## Files Modified

- `app/kafka/handlers.py`: Complete rewrite with multi-turn support
- `db/init/01-init-schema.sql`: Added `conversation_states` table
- `app/kafka/consumer.py`: Changed to `auto_offset_reset="earliest"`

## Testing

Send messages to Slack and watch:
1. First message: Clarification questions appear
2. Follow-up messages: Confidence increases
3. When confidence >= 95%: PRD auto-generates
4. Next message: Analysis auto-runs
5. Check database: All messages and state tracked

Check database:
```sql
SELECT conversation_id, current_agent, confidence_score, turns_count 
FROM conversation_states
ORDER BY updated_at DESC
LIMIT 10;
```

View full conversation:
```sql
SELECT role, content, created_at FROM messages
WHERE conversation_id = '<id>'
ORDER BY created_at ASC;
```
