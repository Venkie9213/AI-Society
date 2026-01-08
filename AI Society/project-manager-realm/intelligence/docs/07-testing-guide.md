# 07. Testing Guide

## Testing Strategy

The Intelligence Service uses comprehensive testing across multiple levels:

- **Unit Tests** - Test individual components in isolation
- **Integration Tests** - Test component interactions
- **End-to-End Tests** - Test complete workflows
- **API Tests** - Test HTTP endpoints

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures
├── unit/
│   ├── test_config.py
│   ├── test_loaders.py
│   ├── test_agents.py
│   ├── test_schemas.py
│   └── test_orchestration.py
├── integration/
│   ├── test_agent_workflow.py
│   ├── test_api_endpoints.py
│   └── test_database.py
├── e2e/
│   ├── test_full_workflow.py
│   └── test_user_journey.py
└── fixtures/
    ├── mock_llm.py
    ├── mock_providers.py
    └── test_data.py
```

## Running Tests

### All Tests
```bash
pytest
```

### Specific Test File
```bash
pytest tests/unit/test_agents.py
```

### Specific Test
```bash
pytest tests/unit/test_agents.py::test_clarification_agent_execute
```

### With Coverage
```bash
pytest --cov=app --cov-report=html
```

### Watch Mode
```bash
ptw  # Requires pytest-watch
```

### Verbose Output
```bash
pytest -v
```

---

## Unit Tests

### Testing Loaders

```python
# tests/unit/test_loaders.py
import pytest
from app.loaders import get_provider_loader, get_agent_loader

@pytest.mark.asyncio
async def test_provider_loader_loads_providers():
    """Test that provider loader loads configuration"""
    loader = get_provider_loader()
    providers = loader.load_providers()
    
    assert providers is not None
    assert "gemini" in providers["providers"]

@pytest.mark.asyncio
async def test_agent_loader_caching():
    """Test that agent loader caches results"""
    loader = get_agent_loader()
    
    agents1 = loader.load_agents()
    agents2 = loader.load_agents()
    
    assert agents1 is agents2  # Same instance due to caching
```

### Testing Agents

```python
# tests/unit/test_agents.py
import pytest
from app.agents import ClarificationAgent
from app.schemas import ClarificationInput, ClarificationOutput

@pytest.mark.asyncio
async def test_clarification_agent_validation():
    """Test that agent validates inputs"""
    agent = ClarificationAgent(
        provider_loader=mock_provider_loader,
        prompt_loader=mock_prompt_loader,
        llm_client=mock_llm_client
    )
    
    # Should raise on missing required field
    with pytest.raises(ValueError):
        await agent.execute(
            ClarificationInput(
                user_description="",  # Empty
                project_context="Some context"
            )
        )

@pytest.mark.asyncio
async def test_clarification_agent_execute():
    """Test agent execution"""
    agent = ClarificationAgent(
        provider_loader=mock_provider_loader,
        prompt_loader=mock_prompt_loader,
        llm_client=mock_llm_client
    )
    
    result = await agent.execute(
        ClarificationInput(
            user_description="Build an e-commerce site",
            project_context="Fashion retail"
        )
    )
    
    assert isinstance(result, ClarificationOutput)
    assert len(result.questions) > 0
    assert 0 <= result.estimated_confidence <= 1
```

### Testing Schemas

```python
# tests/unit/test_schemas.py
from app.schemas import ClarificationInput, ClarificationOutput

def test_clarification_input_validation():
    """Test Pydantic validation for input"""
    # Valid input
    input = ClarificationInput(
        user_description="Build an app",
        project_context="Startup",
        conversation_history=[]
    )
    assert input.user_description == "Build an app"
    
    # Invalid input
    with pytest.raises(ValueError):
        ClarificationInput(
            user_description="",
            project_context=""
        )

def test_clarification_output_serialization():
    """Test output serialization"""
    output = ClarificationOutput(
        questions=[...],
        rationale="...",
        estimated_confidence=0.85
    )
    
    json_data = output.dict()
    assert "questions" in json_data
    assert json_data["estimated_confidence"] == 0.85
```

---

## Integration Tests

### Testing Orchestration

```python
# tests/integration/test_orchestration.py
import pytest
from app.orchestration import get_agent_orchestrator
from app.loaders import get_config_loader

@pytest.mark.asyncio
async def test_agent_orchestrator_execution():
    """Test that orchestrator can execute agents"""
    # Setup
    config_loader = get_config_loader()
    await config_loader.load_all_configs()
    
    orchestrator = get_agent_orchestrator()
    
    # Execute
    result = await orchestrator.execute_clarification_agent(
        user_description="Build a todo app",
        project_context="Personal productivity"
    )
    
    # Assert
    assert result is not None
    assert hasattr(result, 'questions')

@pytest.mark.asyncio
async def test_full_workflow_execution():
    """Test complete agent workflow"""
    orchestrator = get_agent_orchestrator()
    
    # Execute clarification
    clarification = await orchestrator.execute_clarification_agent(...)
    assert clarification is not None
    
    # Execute PRD generation
    prd = await orchestrator.execute_prd_generator_agent(
        requirement_description="Build a todo app",
        clarification_answers=[...]
    )
    assert prd is not None
    
    # Execute analysis
    analysis = await orchestrator.execute_analysis_agent(
        requirements=prd.prd
    )
    assert analysis is not None
```

### Testing API Endpoints

```python
# tests/integration/test_api_endpoints.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_clarify_endpoint(client):
    """Test clarify endpoint"""
    response = client.post(
        "/api/v1/agents/clarify",
        json={
            "user_description": "Build an e-commerce site",
            "project_context": "Fashion retail"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "agent" in data
    assert data["agent"] == "clarification-agent"

def test_clarify_endpoint_validation_error(client):
    """Test endpoint validation"""
    response = client.post(
        "/api/v1/agents/clarify",
        json={
            "user_description": "",
            "project_context": ""
        }
    )
    
    assert response.status_code == 400

def test_list_agents_endpoint(client):
    """Test list agents endpoint"""
    response = client.get("/api/v1/agents")
    
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert len(data["agents"]) > 0
```

---

## Fixtures

### Shared Fixtures

```python
# tests/conftest.py
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.fixture
def mock_llm_client():
    """Mock LLM client"""
    client = AsyncMock()
    client.generate_content = AsyncMock(
        return_value=Mock(text='{"questions": [...]}')
    )
    return client

@pytest.fixture
def mock_provider_loader():
    """Mock provider loader"""
    loader = Mock()
    loader.get_routing_config = Mock(
        return_value={"model": "gemini-1.5-pro"}
    )
    return loader

@pytest.fixture
def mock_prompt_loader():
    """Mock prompt loader"""
    loader = Mock()
    loader.get_prompt_template = Mock(
        return_value="Your prompt template..."
    )
    return loader

@pytest.fixture
async def setup_database():
    """Setup test database"""
    # Create tables
    await init_test_db()
    yield
    # Cleanup
    await cleanup_test_db()
```

---

## Mock Data

### Test Data Fixtures

```python
# tests/fixtures/test_data.py
CLARIFICATION_INPUT = {
    "user_description": "Build a todo app",
    "project_context": "Personal productivity",
    "conversation_history": []
}

CLARIFICATION_OUTPUT = {
    "questions": [
        {
            "id": "q1",
            "text": "What features are required?",
            "category": "features",
            "priority": "high"
        }
    ],
    "rationale": "To better understand scope",
    "estimated_confidence": 0.88
}

PROVIDER_CONFIG = {
    "providers": [
        {
            "name": "gemini",
            "models": ["gemini-1.5-pro", "gemini-1.5-flash"],
            "routing": {"default": "gemini-1.5-pro"}
        }
    ]
}
```

---

## Performance Tests

### Benchmarking

```python
# tests/performance/test_benchmarks.py
import pytest
import time

@pytest.mark.asyncio
async def test_clarification_agent_performance():
    """Benchmark agent execution"""
    agent = ClarificationAgent(...)
    
    start = time.time()
    result = await agent.execute(ClarificationInput(...))
    duration = time.time() - start
    
    assert duration < 5  # Should complete within 5 seconds

def test_config_loading_performance(benchmark):
    """Benchmark config loading"""
    loader = get_config_loader()
    
    result = benchmark(loader.load_all_configs)
    assert result is not None
```

---

## Coverage Reports

### Generate Coverage Report

```bash
# HTML report
pytest --cov=app --cov-report=html

# Terminal report
pytest --cov=app --cov-report=term-missing

# Minimum coverage threshold
pytest --cov=app --cov-fail-under=80
```

### View Coverage

```bash
# Open HTML report
open htmlcov/index.html

# Check coverage for specific file
pytest --cov=app.agents --cov-report=term-missing
```

---

## Test Best Practices

### 1. Use Descriptive Names
```python
# Good
def test_clarification_agent_returns_questions_on_valid_input():
    pass

# Bad
def test_agent():
    pass
```

### 2. Arrange, Act, Assert
```python
async def test_agent_execution():
    # Arrange
    agent = ClarificationAgent(...)
    input = ClarificationInput(...)
    
    # Act
    result = await agent.execute(input)
    
    # Assert
    assert result is not None
```

### 3. Mock External Dependencies
```python
async def test_agent_with_mocked_llm():
    mock_llm = AsyncMock()
    mock_llm.generate_content = AsyncMock(
        return_value=Mock(text='{"questions": [...]}')
    )
    
    agent = ClarificationAgent(llm_client=mock_llm)
    result = await agent.execute(input)
```

### 4. Use Fixtures for Setup
```python
@pytest.fixture
def mock_orchestrator():
    return Mock(spec=AgentOrchestrator)

def test_api_endpoint(mock_orchestrator):
    # Use fixture
    with patch('app.orchestration.get_agent_orchestrator',
               return_value=mock_orchestrator):
        ...
```

---

## Continuous Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: "3.9"
      - run: pip install -r requirements-dev.txt
      - run: pytest --cov=app --cov-fail-under=80
```

---

**Next**: See [LLM Integration](08-llm-integration.md) for provider details
