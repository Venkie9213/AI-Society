# 08. LLM Integration

## Supported Providers

### Gemini (Primary)
- **Status**: Production ready
- **Models**: gemini-1.5-pro, gemini-1.5-flash
- **Documentation**: [Google Gemini Docs](https://ai.google.dev)

### Claude (Optional)
- **Status**: Available
- **Models**: claude-3-opus, claude-3-sonnet
- **Documentation**: [Anthropic Docs](https://docs.anthropic.com)

### OpenAI (Optional)
- **Status**: Available
- **Models**: gpt-4, gpt-4-turbo
- **Documentation**: [OpenAI Docs](https://platform.openai.com/docs)

---

## Gemini Setup

### 1. Get API Key

1. Visit [Google AI Studio](https://aistudio.google.com)
2. Click "Get API key"
3. Create new API key
4. Copy the key

### 2. Configure Environment

```bash
# .env
GEMINI_API_KEY=your-api-key-here
```

### 3. Verify Setup

```bash
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key=YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{
      "parts": [{"text": "Hello!"}]
    }]
  }'
```

---

## Model Selection

### Gemini 1.5 Pro
- **Context Window**: 1M tokens
- **Cost**: Higher
- **Best For**: Complex tasks, long context

**Usage**:
```yaml
# models/providers.yaml
routing:
  use_cases:
    prd_generation: gemini-1.5-pro
    analysis: gemini-1.5-pro
```

### Gemini 1.5 Flash
- **Context Window**: 1M tokens
- **Cost**: Lower
- **Best For**: Simple tasks, quick responses

**Usage**:
```yaml
routing:
  use_cases:
    clarification: gemini-1.5-flash
```

---

## Provider Configuration

### Provider Configuration File

```yaml
# models/providers.yaml
providers:
  - name: gemini
    type: google-genai
    enabled: true
    api_key: ${GEMINI_API_KEY}
    base_url: https://generativelanguage.googleapis.com/v1beta
    timeout_seconds: 30
    
    models:
      - name: gemini-1.5-pro
        version: latest
        context_window: 1000000
        input_token_limit: 1000000
        output_token_limit: 8192
        
        cost:
          input: 0.0075      # per 1M tokens
          output: 0.03       # per 1M tokens
        
        capabilities:
          - text
          - vision
          - function_calling
      
      - name: gemini-1.5-flash
        version: latest
        context_window: 1000000
        cost:
          input: 0.00075
          output: 0.003
    
    routing:
      default: gemini-1.5-pro
      
      use_cases:
        clarification: gemini-1.5-flash
        prd_generation: gemini-1.5-pro
        analysis: gemini-1.5-pro
        quick_check: gemini-1.5-flash
      
      fallback: gemini-1.5-flash
    
    retry_policy:
      max_retries: 3
      backoff_factor: 2
      timeout_seconds: 30
```

---

## Using Different Providers

### Configuration-Based Routing

```python
# app/loaders/provider_loader.py
def get_routing_config(self, use_case: str) -> Dict:
    """Get routing config for specific use case"""
    providers_config = self.load_providers()
    
    for provider in providers_config['providers']:
        if 'routing' in provider:
            routing = provider['routing']
            if use_case in routing['use_cases']:
                model = routing['use_cases'][use_case]
                return {
                    'provider': provider['name'],
                    'model': model,
                    'temperature': 0.7
                }
    
    # Return default
    return {
        'provider': 'gemini',
        'model': 'gemini-1.5-pro'
    }
```

### Agent-Specific Configuration

```python
# agents/clarification_agent.py
def _get_routing_config(self) -> Dict:
    """Get routing for clarification agent"""
    routing = self.provider_loader.get_routing_config("clarification")
    return {
        **routing,
        'temperature': 0.7,
        'top_p': 0.95,
        'max_tokens': 1000
    }
```

---

## Making LLM Calls

### Basic Call

```python
from app.providers.manager import get_llm_client

client = get_llm_client()
response = await client.generate_content(
    model="gemini-1.5-pro",
    prompt="Your prompt here",
    temperature=0.7
)
print(response.text)
```

### With Configuration

```python
routing = provider_loader.get_routing_config("clarification")

response = await llm_client.generate_content(
    model=routing['model'],
    prompt=rendered_prompt,
    temperature=routing.get('temperature', 0.7),
    max_tokens=routing.get('max_tokens', 2000)
)
```

### With Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def call_llm_with_retry(prompt: str) -> str:
    response = await llm_client.generate_content(
        model="gemini-1.5-pro",
        prompt=prompt
    )
    return response.text
```

---

## Cost Tracking

### Token Counting

```python
# Count tokens before making API call
def count_tokens(prompt: str, model: str) -> int:
    """Estimate token count for cost calculation"""
    # Approximate: 1 token ~= 4 characters
    estimated_tokens = len(prompt) / 4
    return int(estimated_tokens)
```

### Cost Calculation

```python
def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate API call cost"""
    pricing = {
        "gemini-1.5-pro": {
            "input": 0.0075,
            "output": 0.03
        },
        "gemini-1.5-flash": {
            "input": 0.00075,
            "output": 0.003
        }
    }
    
    if model not in pricing:
        return 0.0
    
    input_cost = (input_tokens / 1_000_000) * pricing[model]["input"]
    output_cost = (output_tokens / 1_000_000) * pricing[model]["output"]
    
    return input_cost + output_cost
```

---

## Prompt Engineering

### Best Practices

1. **Be Specific**
```
❌ Bad: "Generate questions"
✅ Good: "Generate 5-7 clarifying questions that help define project scope"
```

2. **Provide Context**
```
❌ Bad: "What are the features?"
✅ Good: "Given this requirement, what features would be essential for MVP?"
```

3. **Specify Output Format**
```
❌ Bad: "Return questions"
✅ Good: "Return as JSON with fields: id, text, category, priority"
```

### Template Variables

```yaml
# prompts/v1/clarification.prompt.yaml
template: |
  You are a {{role}}.
  
  User Input: {{user_description}}
  Context: {{project_context}}
  
  {{instructions}}
  
  Return as JSON with this structure:
  {{output_schema}}

variables:
  - name: role
    default: "requirements clarification expert"
  - name: user_description
    required: true
  - name: project_context
    required: true
  - name: instructions
    default: "Generate 5-7 clarifying questions"
  - name: output_schema
    default: "..."
```

---

## Handling Errors

### Rate Limiting

```python
from tenacity import retry, stop_after_attempt, wait_random_exponential

@retry(wait=wait_random_exponential(min=1, max=60))
async def call_with_rate_limit(prompt: str):
    try:
        response = await llm_client.generate_content(prompt)
        return response
    except RateLimitError:
        raise  # Tenacity will retry
```

### API Errors

```python
async def safe_llm_call(prompt: str) -> Optional[str]:
    try:
        response = await llm_client.generate_content(prompt)
        return response.text
    except APIError as e:
        logger.error("llm_api_error", error=str(e))
        return None
    except ValueError as e:
        logger.error("invalid_request", error=str(e))
        return None
```

### Timeout Handling

```python
import asyncio

async def call_with_timeout(prompt: str, timeout: int = 30) -> str:
    try:
        response = await asyncio.wait_for(
            llm_client.generate_content(prompt),
            timeout=timeout
        )
        return response.text
    except asyncio.TimeoutError:
        logger.error("llm_timeout", timeout_seconds=timeout)
        raise
```

---

## Monitoring & Logging

### Log API Calls

```python
import structlog

logger = structlog.get_logger()

async def monitored_llm_call(prompt: str, model: str) -> str:
    logger.info("llm_call_start", model=model)
    
    start_time = time.time()
    try:
        response = await llm_client.generate_content(
            model=model,
            prompt=prompt
        )
        duration = time.time() - start_time
        
        logger.info(
            "llm_call_success",
            model=model,
            duration_ms=int(duration * 1000),
            output_tokens=len(response.text.split())
        )
        
        return response.text
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            "llm_call_failed",
            model=model,
            error=str(e),
            duration_ms=int(duration * 1000)
        )
        raise
```

### Metrics

```python
# Track API calls with Prometheus
from prometheus_client import Counter, Histogram

llm_calls = Counter(
    'llm_calls_total',
    'Total LLM API calls',
    ['model', 'status']
)

llm_duration = Histogram(
    'llm_call_duration_seconds',
    'LLM call duration',
    ['model']
)

@llm_duration.labels(model='gemini-1.5-pro').time()
async def call_gemini():
    response = await llm_client.generate_content(...)
    llm_calls.labels(model='gemini-1.5-pro', status='success').inc()
    return response
```

---

## Testing with Mocked LLMs

### Mock LLM Client

```python
from unittest.mock import AsyncMock, Mock

mock_llm = AsyncMock()
mock_llm.generate_content = AsyncMock(
    return_value=Mock(text='{"questions": [{"id": "q1", "text": "..."}]}')
)

# Use in tests
agent = ClarificationAgent(llm_client=mock_llm)
result = await agent.execute(input)
```

### Fixture for Testing

```python
# tests/conftest.py
@pytest.fixture
def mock_llm_client():
    client = AsyncMock()
    client.generate_content = AsyncMock(
        return_value=Mock(text='{"questions": [...]}')
    )
    return client
```

---

## Gemini-Specific Features

### Vision Capabilities

```python
# Future: Support for images
response = await llm_client.generate_content(
    model="gemini-1.5-pro",
    content=[
        {"type": "text", "text": "What's in this image?"},
        {"type": "image", "data": image_data}
    ]
)
```

### Function Calling

```python
# Define functions
tools = [
    {
        "name": "generate_schema",
        "description": "Generate a JSON schema",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "fields": {"type": "array"}
            }
        }
    }
]

response = await llm_client.generate_content(
    model="gemini-1.5-pro",
    prompt="Generate a schema for users",
    tools=tools
)
```

---

## Pricing & Optimization

### Cost Optimization

1. **Use Flash for Simple Tasks**
   - Clarification questions (cheaper, faster)
   
2. **Use Pro for Complex Tasks**
   - PRD generation (needs reasoning)
   - Analysis (needs depth)

3. **Batch Requests**
   - Process multiple requests together
   - Reduce number of API calls

4. **Cache Results**
   - Cache common prompts
   - Cache frequently asked questions

### Pricing Examples

```
Gemini 1.5 Flash:
- Input: $0.075 per million tokens
- Output: $0.3 per million tokens

Gemini 1.5 Pro:
- Input: $7.5 per million tokens
- Output: $30 per million tokens

Example cost:
- 100K input tokens (Flash): $0.0075
- 50K output tokens (Flash): $0.015
- Total: ~$0.023 per request
```

---

**Next**: See [Deployment Guide](09-deployment-guide.md) for production setup
