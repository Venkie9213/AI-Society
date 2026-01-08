# 03. Architecture Overview

## System Design

The Intelligence Service follows a modular, layered architecture with clear separation of concerns.

```
┌─────────────────────────────────────────────────────────┐
│                     HTTP Layer                          │
│              (FastAPI + Middleware)                     │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                  API Routes Layer                       │
│         (app/api/agents.py - Thin Handlers)            │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              Orchestration Layer                        │
│         (AgentOrchestrator - Coordinator)              │
└──────────────────────┬──────────────────────────────────┘
                       │
    ┌──────────────────┼──────────────────┐
    │                  │                  │
┌───▼───────┐   ┌─────▼──────┐   ┌──────▼──────┐
│   Agent   │   │   Agent    │   │   Agent     │
│ System    │   │ Loader     │   │ Orchestr.  │
│           │   │            │   │            │
└───────────┘   └────────────┘   └────────────┘
    │                  │                  │
┌───▼───────────────────▼──────────────────▼────────────┐
│           Cross-Cutting Services                      │
├─────────────┬──────────────┬────────────┬──────────────┤
│  Config     │  Loaders     │  Schemas   │  Prompt      │
│  System     │  (Providers, │  (Pydantic)│  Engine      │
│  (Settings) │   Agents,    │            │  (Jinja2)    │
│             │   Prompts)   │            │              │
└─────────────┴──────────────┴────────────┴──────────────┘
    │              │              │            │
┌───▴──────────────┴──────────────┴────────────┴──────────┐
│                  Data & External                        │
│    (Database, LLM Providers, File System)              │
└────────────────────────────────────────────────────────┘
```

## Core Modules

### 1. **config/** - Application Configuration
**Purpose**: Centralized settings management

**Components**:
- `AppConfig` - FastAPI, server, CORS settings
- `IntelligenceConfig` - Service paths, routing, defaults
- `ProviderConfig` - LLM API keys, endpoints, timeouts
- `ObservabilityConfig` - Logging, metrics, tracing
- `Settings` - Composite class combining all configs

**Usage**:
```python
from app.config import get_settings

settings = get_settings()
print(settings.app_name)
```

---

### 2. **loaders/** - Configuration Loading
**Purpose**: Load and cache YAML configurations

**Components**:
- `BaseLoader` - Common caching and error handling
- `ProviderLoader` - Load LLM provider configurations
- `AgentLoader` - Load agent definitions
- `PromptLoader` - Load prompt templates
- `ConfigLoader` - Orchestrate all loaders

**Usage**:
```python
from app.loaders import get_config_loader

loader = get_config_loader()
await loader.load_all_configs()
```

---

### 3. **agents/** - Agent Implementations
**Purpose**: LLM-powered conversational agents

**Components**:
- `BaseAgent` - Abstract base class with common logic
- `ClarificationAgent` - Generate clarifying questions
- `PRDGeneratorAgent` - Generate PRDs
- `AnalysisAgent` - Analyze requirements

**Pattern**: Inheritance with template method

**Usage**:
```python
from app.agents import ClarificationAgent

agent = ClarificationAgent(provider, prompt, llm)
result = await agent.execute(input)
```

---

### 4. **orchestration/** - Agent Coordination
**Purpose**: Coordinate agent execution and workflows

**Components**:
- `AgentOrchestrator` - Execute individual agents and workflows

**Usage**:
```python
from app.orchestration import get_agent_orchestrator

orchestrator = get_agent_orchestrator()
result = await orchestrator.execute_clarification_agent(...)
```

---

### 5. **prompt_engine/** - Template Rendering
**Purpose**: Render Jinja2 prompts with variables

**Components**:
- `TemplateRenderer` - Render and validate templates

**Usage**:
```python
from app.prompt_engine import get_template_renderer

renderer = get_template_renderer()
prompt = renderer.render_prompt("clarification", context)
```

---

### 6. **schemas/** - Type Validation
**Purpose**: Pydantic models for type-safe I/O

**Components**:
- Input/Output models for each agent
- Generic request/response models
- Automatic OpenAPI integration

**Usage**:
```python
from app.schemas import ClarificationInput, ClarificationOutput

input = ClarificationInput(user_description="...", ...)
output: ClarificationOutput = await agent.execute(input)
```

---

## Request Flow

### Example: Clarify Requirement

1. **HTTP Request**
   ```
   POST /api/v1/agents/clarify
   {user_description: "...", project_context: "..."}
   ```

2. **API Handler** (`api/agents.py`)
   - Validates input
   - Logs request start
   - Calls orchestrator

3. **Orchestrator** (`orchestration/agent_orchestrator.py`)
   - Loads clarification agent
   - Executes agent

4. **Agent** (`agents/clarification_agent.py`)
   - Validates inputs
   - Gets prompt template (via `PromptLoader`)
   - Gets LLM routing config (via `ProviderLoader`)
   - Renders prompt with Jinja2
   - Calls LLM API
   - Parses JSON response

5. **API Handler** (returns response)
   - Formats response
   - Returns `AgentExecutionResponse`

---

## Data Flow

```
User Input
    ↓
[Schemas] - Validate input
    ↓
[Config] - Load settings
    ↓
[Loaders] - Load agent/prompt configs
    ↓
[Agent] - Execute agent logic
    ↓
[LLM Provider] - Call Gemini API
    ↓
[Agent] - Parse response
    ↓
[Schemas] - Validate output
    ↓
HTTP Response
```

---

## Dependency Injection

All modules use singleton factory functions:

```python
# In each module's __init__.py
_instance = None

def get_module():
    global _instance
    if _instance is None:
        _instance = Module()
    return _instance
```

**Benefits**:
- Single instance per lifecycle
- Thread-safe initialization
- Easy to mock for testing
- Lazy initialization

---

## Design Patterns

| Pattern | Location | Purpose |
|---------|----------|---------|
| Composite | `config/` | Aggregate configurations |
| Singleton | All modules | Single instance per app |
| Factory | Module init functions | Create instances |
| Template Method | `agents/base.py` | Define agent contract |
| Strategy | Different agents | Different execution strategies |
| Adapter | `loaders/` | Adapt to different formats |
| Decorator | Middleware | Add cross-cutting concerns |

---

## Scalability Considerations

### Horizontal Scaling
- Stateless API servers
- Load balance across instances
- Shared database
- Shared cache (Redis for production)

### Vertical Scaling
- Async/await for concurrency
- Database connection pooling
- Prompt/config caching
- Rate limiting per agent

---

**Next**: See [Agents](04-agents.md) for detailed agent information
