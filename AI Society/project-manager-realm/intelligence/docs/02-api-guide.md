# 02. API Guide

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
Currently supports API key authentication. Pass your API key in headers:
```
Authorization: Bearer YOUR_API_KEY
```

## Endpoints

### Agent Endpoints

#### 1. Clarify Requirement
Generate clarifying questions for a user requirement.

**Endpoint**: `POST /agents/clarify`

**Request**:
```json
{
  "user_description": "I need an e-commerce platform",
  "project_context": "B2C retail, target users are fashion enthusiasts",
  "conversation_history": []
}
```

**Response**:
```json
{
  "agent": "clarification-agent",
  "status": "success",
  "result": {
    "questions": [
      {
        "id": "q1",
        "text": "What is your target market size?",
        "category": "scope",
        "priority": "high"
      }
    ],
    "rationale": "These questions help define project scope",
    "estimated_confidence": 0.85
  },
  "duration_ms": 1523
}
```

---

#### 2. Generate PRD
Generate a Product Requirements Document from clarified requirements.

**Endpoint**: `POST /agents/generate-prd`

**Request**:
```json
{
  "requirement_description": "E-commerce platform for fashion",
  "clarification_answers": [
    {"question_id": "q1", "answer": "Target 50K users in first year"}
  ],
  "project_context": {"budget": "$50K", "timeline": "6 months"}
}
```

**Response**:
```json
{
  "agent": "prd-generator-agent",
  "status": "success",
  "result": {
    "prd": {
      "title": "Fashion E-commerce Platform",
      "overview": "...",
      "features": ["Product catalog", "Shopping cart", "Payment"],
      "success_metrics": ["50K users", "4.5 rating"]
    },
    "completeness_score": 0.92,
    "estimated_effort": "8 months"
  },
  "duration_ms": 2341
}
```

---

#### 3. Analyze Requirements
Analyze requirements for gaps, risks, and recommendations.

**Endpoint**: `POST /agents/analyze`

**Request**:
```json
{
  "requirements": {
    "features": ["Product catalog", "Shopping cart"],
    "constraints": ["Budget: $50K", "Timeline: 6 months"]
  },
  "analysis_depth": "standard"
}
```

**Response**:
```json
{
  "agent": "analysis-agent",
  "status": "success",
  "result": {
    "completeness_score": 0.78,
    "gaps": [
      "User authentication not specified",
      "Payment gateway not detailed"
    ],
    "risks": [
      "Timeline may be tight for MVP"
    ],
    "recommendations": [
      "Prioritize core features for MVP"
    ]
  },
  "duration_ms": 1834
}
```

---

### List Endpoints

#### List Available Agents
**Endpoint**: `GET /agents`

**Response**:
```json
{
  "agents": [
    {
      "name": "clarification-agent",
      "description": "Generates clarifying questions",
      "version": "1.0.0"
    },
    {
      "name": "prd-generator-agent",
      "description": "Generates PRDs from requirements",
      "version": "1.0.0"
    },
    {
      "name": "analysis-agent",
      "description": "Analyzes requirements for gaps",
      "version": "1.0.0"
    }
  ],
  "total": 3
}
```

---

#### List Available Prompts
**Endpoint**: `GET /prompts`

**Response**:
```json
{
  "prompts": [
    {"name": "clarification-v1"},
    {"name": "prd-generation-v1"},
    {"name": "analysis-v1"}
  ],
  "total": 3
}
```

---

#### Get Provider Configuration
**Endpoint**: `GET /config/providers`

**Response**:
```json
{
  "providers": [
    {
      "name": "gemini",
      "models": ["gemini-1.5-pro", "gemini-1.5-flash"],
      "routing": {
        "default": "gemini-1.5-pro",
        "clarification": "gemini-1.5-flash"
      }
    }
  ]
}
```

---

## Error Handling

All errors follow a consistent format:

```json
{
  "error": "Error type",
  "detail": "Detailed error message",
  "status_code": 400
}
```

### Common Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (validation error) |
| 401 | Unauthorized (missing API key) |
| 404 | Not found |
| 500 | Server error |

---

## Rate Limiting

- **Default**: 100 requests/minute per API key
- **Premium**: 1000 requests/minute

---

## Examples

### cURL
```bash
curl -X POST http://localhost:8000/api/v1/agents/clarify \
  -H "Content-Type: application/json" \
  -d '{
    "user_description": "Build an e-commerce site",
    "project_context": "Fashion retail"
  }'
```

### Python
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/agents/clarify",
    json={
        "user_description": "Build an e-commerce site",
        "project_context": "Fashion retail"
    }
)
print(response.json())
```

### JavaScript
```javascript
const response = await fetch('http://localhost:8000/api/v1/agents/clarify', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    user_description: "Build an e-commerce site",
    project_context: "Fashion retail"
  })
});
const data = await response.json();
console.log(data);
```

---

**Next**: See [Architecture](03-architecture.md) to understand how it works
