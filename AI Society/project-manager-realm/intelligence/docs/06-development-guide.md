# 06. Development Guide

## Local Development Setup

### Prerequisites
- Python 3.9+
- PostgreSQL 15+
- Git
- Virtual environment manager (venv or conda)

### Step 1: Clone and Setup

```bash
cd project-manager-realm/intelligence/service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### Step 2: Environment Setup

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

Example `.env` for development:
```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

DATABASE_URL=postgresql://localhost:5432/intelligence
GEMINI_API_KEY=your-dev-key

INTELLIGENCE_ROOT=./intelligence
```

### Step 3: Database Setup

```bash
# Create database
createdb intelligence

# Run migrations
python -m alembic upgrade head

# (Optional) Seed with test data
python scripts/seed_db.py
```

### Step 4: Run Development Server

```bash
# Option 1: Using uvicorn directly
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Option 2: Using Python module
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Option 3: Using Makefile
make run-dev
```

Server runs at: `http://localhost:8000`

API docs at: `http://localhost:8000/docs`

---

## Project Structure

```
intelligence/service/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Application entry point
│   ├── config/                    # Configuration management
│   │   ├── settings.py
│   │   ├── app_config.py
│   │   └── ...
│   ├── loaders/                   # Configuration loaders
│   │   ├── base_loader.py
│   │   ├── provider_loader.py
│   │   └── ...
│   ├── agents/                    # Agent implementations
│   │   ├── base.py
│   │   ├── clarification_agent.py
│   │   └── ...
│   ├── orchestration/             # Agent coordination
│   │   └── agent_orchestrator.py
│   ├── schemas/                   # Pydantic models
│   │   └── agent_schemas.py
│   ├── api/                       # API routes
│   │   ├── agents.py
│   │   └── health.py
│   ├── database/                  # Database setup
│   ├── observability/             # Logging and metrics
│   └── providers/                 # LLM provider interfaces
│
├── tests/                         # Test suite
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── scripts/                       # Utility scripts
│   └── seed_db.py
│
├── migrations/                    # Database migrations
├── Dockerfile
├── docker-compose.yml
├── requirements.txt               # Production dependencies
├── requirements-dev.txt           # Development dependencies
├── .env.example
├── Makefile
└── README.md
```

---

## Common Development Tasks

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/unit/test_clarification_agent.py

# Run tests matching pattern
pytest -k "test_load" -v

# Watch mode (auto-rerun on file changes)
ptw
```

### Code Quality

```bash
# Format code
black app/

# Sort imports
isort app/

# Lint
flake8 app/

# Type checking
mypy app/

# All checks
make lint
```

### Database Operations

```bash
# Create migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration status
alembic current

# View history
alembic history
```

### Working with Agents

#### Test an Agent

```python
# test_clarification_agent.py
import asyncio
from app.agents import ClarificationAgent
from app.schemas import ClarificationInput

async def test_agent():
    agent = ClarificationAgent()
    result = await agent.execute(
        ClarificationInput(
            user_description="Build an e-commerce site",
            project_context="Fashion retail"
        )
    )
    print(result)

asyncio.run(test_agent())
```

#### Debug LLM Calls

```python
import structlog

logger = structlog.get_logger()

# Logs will show:
# - Input to agent
# - Rendered prompt
# - LLM response
# - Parsed output

logger.debug("agent_input", input=input)
logger.debug("rendered_prompt", prompt=prompt)
logger.debug("llm_response", response=response)
logger.debug("parsed_output", output=output)
```

#### Add New Agent

1. Create `app/agents/new_agent.py`:
```python
from app.agents.base import BaseAgent
from app.schemas import NewInput, NewOutput

class NewAgent(BaseAgent):
    def _validate_inputs(self, inputs: NewInput):
        # Validation logic
        pass
    
    def _parse_response(self, raw: str) -> NewOutput:
        # Parse LLM response
        pass
```

2. Add schema to `app/schemas/agent_schemas.py`:
```python
class NewInput(BaseModel):
    field1: str
    field2: Optional[str] = None

class NewOutput(BaseModel):
    result: str
```

3. Add agent config to `agents/new-agent.yaml`:
```yaml
name: new-agent
version: 1.0.0
routing:
  model: gemini-1.5-pro
```

4. Register in orchestrator:
```python
# app/orchestration/agent_orchestrator.py
self.new_agent = NewAgent(...)
```

---

## Debugging

### Enable Debug Logging

```python
# In app/main.py
import logging
logging.basicConfig(level=logging.DEBUG)

# Or via environment
LOG_LEVEL=DEBUG
```

### Use Python Debugger

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use breakpoint() in Python 3.7+
breakpoint()
```

### VS Code Debug Configuration

Create `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastAPI",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": [
                "app.main:app",
                "--reload",
                "--host=127.0.0.1",
                "--port=8000"
            ],
            "jinja": true
        }
    ]
}
```

### Check Logs

```bash
# View real-time logs
tail -f logs/app.log

# Search logs
grep "error" logs/app.log

# Parse JSON logs
cat logs/app.log | jq '.level, .message'
```

---

## API Testing

### Using curl

```bash
# Test clarification agent
curl -X POST http://localhost:8000/api/v1/agents/clarify \
  -H "Content-Type: application/json" \
  -d '{
    "user_description": "Build a todo app",
    "project_context": "Personal productivity tool"
  }'
```

### Using Postman

1. Import collection from `postman/intelligence-service.json`
2. Set environment variables
3. Run requests

### Using Python requests

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/agents/clarify",
    json={
        "user_description": "Build a todo app",
        "project_context": "Personal productivity"
    }
)
print(response.json())
```

---

## Performance Profiling

### Profile Code

```bash
# Install profiler
pip install py-spy

# Profile application
py-spy record -o profile.svg -- python -m uvicorn app.main:app
```

### Memory Usage

```bash
# Install memory profiler
pip install memory-profiler

# Add decorator
@profile
def my_function():
    pass

# Run
python -m memory_profiler script.py
```

---

## Common Issues

### Issue: `ModuleNotFoundError: No module named 'app'`

**Solution**: Make sure you're in the correct directory and have installed dependencies:
```bash
cd intelligence/service
pip install -r requirements.txt
```

### Issue: `psycopg2.OperationalError: cannot connect to server`

**Solution**: Ensure PostgreSQL is running:
```bash
# On macOS
brew services start postgresql

# On Linux
sudo systemctl start postgresql

# Check connection
psql -U postgres -h localhost
```

### Issue: `RuntimeError: database connection error`

**Solution**: Ensure DATABASE_URL is correct and database exists:
```bash
# Check .env
cat .env | grep DATABASE_URL

# Create database if missing
createdb intelligence

# Run migrations
alembic upgrade head
```

### Issue: `google.auth.exceptions.DefaultCredentialsError`

**Solution**: Set your Gemini API key:
```bash
# Add to .env
GEMINI_API_KEY=your-key-here

# Or export environment variable
export GEMINI_API_KEY="your-key-here"
```

---

## Useful Commands

```bash
# Start development server
make run-dev

# Run tests
make test

# Run tests with coverage
make coverage

# Format code
make format

# Lint code
make lint

# Type check
make type-check

# Run all quality checks
make check-all

# Clean build artifacts
make clean
```

---

## IDE Setup

### VS Code

Install extensions:
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- FastAPI (dameng.fastapi-offical)
- SQLTools (mtxr.sqltools)

### PyCharm

1. Set Python interpreter to virtual environment
2. Mark `app` directory as Sources Root
3. Enable Django support (optional)

---

## Next Steps

1. Read [Testing Guide](07-testing-guide.md)
2. Check [LLM Integration](08-llm-integration.md)
3. See [API Guide](02-api-guide.md) for endpoint examples

---

**Need help?** Check the troubleshooting section or create an issue.
