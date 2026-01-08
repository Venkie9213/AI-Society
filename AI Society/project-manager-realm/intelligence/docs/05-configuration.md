# 05. Configuration

## Settings Management

The Intelligence Service uses a composite configuration pattern that brings together settings from multiple domains.

## Configuration Structure

### Settings Class Hierarchy

```
Settings
├── AppConfig (app_config.py)
│   ├── app_name
│   ├── app_version
│   ├── environment
│   ├── debug
│   ├── host
│   ├── port
│   └── CORS settings
│
├── IntelligenceConfig (intelligence_config.py)
│   ├── intelligence_root
│   ├── models_path
│   ├── agents_path
│   ├── prompts_path
│   └── defaults
│
├── ProviderConfig (provider_config.py)
│   ├── gemini_api_key
│   ├── claude_api_key
│   ├── openai_api_key
│   ├── rate_limits
│   └── timeouts
│
└── ObservabilityConfig (observability_config.py)
    ├── log_level
    ├── structured_logs
    ├── metrics_port
    └── correlation_ids
```

## Environment Variables

Create a `.env` file in the service root:

### Application Configuration
```bash
# App settings
APP_NAME=intelligence-service
APP_VERSION=1.0.0
ENVIRONMENT=production        # development, staging, production
DEBUG=false                    # true/false

# Server
HOST=0.0.0.0
PORT=8000

# CORS
CORS_ORIGINS=http://localhost:3000,https://example.com
CORS_CREDENTIALS=true
CORS_METHODS=GET,POST,PUT,DELETE
CORS_HEADERS=*
```

### Database Configuration
```bash
# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/intelligence
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30
```

### LLM Provider Configuration
```bash
# Gemini (Primary)
GEMINI_API_KEY=your-gemini-key

# Claude (Optional)
CLAUDE_API_KEY=your-claude-key

# OpenAI (Optional)
OPENAI_API_KEY=your-openai-key
```

### Intelligence Service Configuration
```bash
# Paths
INTELLIGENCE_ROOT=./intelligence
MODELS_PATH=models/providers.yaml
AGENTS_PATH=agents/
PROMPTS_PATH=prompts/

# Defaults
DEFAULT_PROVIDER=gemini
DEFAULT_MODEL=gemini-1.5-pro
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=2000
```

### Observability Configuration
```bash
# Logging
LOG_LEVEL=INFO                 # DEBUG, INFO, WARNING, ERROR
STRUCTURED_LOGS=true           # Use JSON structured logs
LOG_FORMAT=json               # json or text

# Metrics
METRICS_PORT=9090
ENABLE_METRICS=true
ENABLE_TRACING=false
CORRELATION_ID_ENABLED=true
```

## Usage

### Accessing Settings

```python
from app.config import get_settings

# Get settings instance
settings = get_settings()

# Access settings
print(settings.app_name)          # From AppConfig
print(settings.gemini_api_key)    # From ProviderConfig
print(settings.log_level)         # From ObservabilityConfig
```

### In a Route Handler

```python
from fastapi import FastAPI
from app.config import get_settings

app = FastAPI()

@app.get("/config/info")
def get_config_info():
    settings = get_settings()
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "debug": settings.debug
    }
```

### In an Agent

```python
from app.config import get_settings
from app.agents import ClarificationAgent

settings = get_settings()
agent = ClarificationAgent(
    timeout=settings.llm_timeout,
    temperature=settings.default_temperature
)
```

## Provider Configuration

The provider configuration is loaded from `models/providers.yaml`:

```yaml
# models/providers.yaml
providers:
  - name: gemini
    type: google-genai
    api_key: ${GEMINI_API_KEY}
    
    models:
      - name: gemini-1.5-pro
        context_window: 1000000
        cost:
          input: 0.0075
          output: 0.03
      
      - name: gemini-1.5-flash
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
      
      fallback: gemini-1.5-flash

  - name: claude
    type: anthropic
    api_key: ${CLAUDE_API_KEY}
    models:
      - name: claude-3-opus
        context_window: 200000

  - name: openai
    type: openai
    api_key: ${OPENAI_API_KEY}
    models:
      - name: gpt-4
        context_window: 128000
```

## Agent Configuration

Agent configurations are in `agents/*.yaml`:

```yaml
# agents/clarification-agent.yaml
name: clarification-agent
version: 1.0.0
description: Generates clarifying questions

enabled: true

prompt:
  name: clarification-v1
  version: 1.0.0

routing:
  provider: gemini
  model: gemini-1.5-flash
  temperature: 0.7
  max_tokens: 1000
  top_p: 0.95

timeout_seconds: 30

validation:
  required_fields:
    - user_description
    - project_context
  
  max_length:
    user_description: 5000
    project_context: 2000
```

## Prompt Configuration

Prompts are in `prompts/v1/*.prompt.yaml`:

```yaml
# prompts/v1/clarification.prompt.yaml
name: clarification-v1
version: 1.0.0
description: Generates clarifying questions

template: |
  You are a requirements clarification expert.
  
  User Description: {{user_description}}
  Project Context: {{project_context}}
  
  Generate 5-7 clarifying questions that help define project scope.
  
  Return as JSON:
  {
    "questions": [
      {"id": "q1", "text": "...", "category": "scope", "priority": "high"}
    ],
    "rationale": "...",
    "confidence": 0.85
  }

variables:
  - name: user_description
    type: string
    required: true
  
  - name: project_context
    type: string
    required: true
  
  - name: conversation_history
    type: array
    required: false

output_format: json
```

## Configuration Loading

### Startup

Configuration is loaded during application startup:

```python
# app/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    settings = get_settings()
    config_loader = get_config_loader()
    await config_loader.load_all_configs()
    
    yield
    
    # Shutdown
    config_loader.clear_caches()
```

### Runtime Access

```python
from app.loaders import get_provider_loader

provider_loader = get_provider_loader()

# Get provider config
providers = provider_loader.load_providers()

# Get specific model config
model_config = provider_loader.get_model_config("gemini-1.5-pro")

# Get routing for use case
routing = provider_loader.get_routing_config("clarification")
```

## Environment-Based Configuration

Different environments can have different settings:

```bash
# .env.development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://localhost:5432/intelligence_dev

# .env.staging
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://staging-db:5432/intelligence

# .env.production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://prod-db:5432/intelligence
```

### Load Specific Environment

```bash
# Using Python-dotenv
from dotenv import load_dotenv
load_dotenv('.env.production')
```

## Validation

### Configuration Validation

```python
from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    app_name: str
    
    @validator('app_name')
    def app_name_not_empty(cls, v):
        if not v:
            raise ValueError('app_name cannot be empty')
        return v
    
    class Config:
        env_file = ".env"
```

### Required Variables

If a required environment variable is missing, the application will fail to start:

```
pydantic_core._pydantic_core.ValidationError: 
  1 validation error for Settings
  gemini_api_key
    Field required [type=missing, input_value={...}, input_type=dict, ...]
```

## Secrets Management

### Development
Use `.env` file (add to `.gitignore`):
```bash
GEMINI_API_KEY=sk-...
DATABASE_PASSWORD=secret
```

### Production
Use environment variables:
```bash
export GEMINI_API_KEY="your-production-key"
export DATABASE_PASSWORD="production-password"
```

Or use a secrets manager:
- AWS Secrets Manager
- HashiCorp Vault
- Google Cloud Secret Manager

## Configuration Examples

### Local Development
```bash
APP_NAME=intelligence-service
ENVIRONMENT=development
DEBUG=true
HOST=127.0.0.1
PORT=8000
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://localhost:5432/intelligence
GEMINI_API_KEY=test-key
INTELLIGENCE_ROOT=./intelligence
```

### Docker Development
```bash
APP_NAME=intelligence-service
ENVIRONMENT=development
DEBUG=true
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://db:5432/intelligence
GEMINI_API_KEY=${GEMINI_API_KEY}
INTELLIGENCE_ROOT=/app/intelligence
```

### Production
```bash
APP_NAME=intelligence-service
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://prod-db:5432/intelligence
GEMINI_API_KEY=${GEMINI_API_KEY}
INTELLIGENCE_ROOT=/opt/intelligence
```

---

**Next**: See [Development Guide](06-development-guide.md) for local setup
