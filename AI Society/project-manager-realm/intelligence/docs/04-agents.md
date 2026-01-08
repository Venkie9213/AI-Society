# 04. Agent System

## Overview

The Intelligence Service uses a modular agent system where each agent is a specialized LLM-powered worker that performs a specific task.

## Agents

### 1. Clarification Agent

**Purpose**: Generate clarifying questions for ambiguous requirements

**Input**:
```python
ClarificationInput(
    user_description: str,
    project_context: str,
    conversation_history: Optional[List[Dict[str, str]]]
)
```

**Output**:
```python
ClarificationOutput(
    questions: List[ClarificationQuestion],
    rationale: str,
    estimated_confidence: float
)
```

**Example**:
```bash
Input:
  user_description: "Build an e-commerce platform"
  project_context: "Fashion retail startup"

Output:
  questions: [
    {id: "q1", text: "What's your target market size?", category: "scope"},
    {id: "q2", text: "What payment methods?", category: "features"},
    {id: "q3", text: "What's your budget?", category: "resources"}
  ]
  estimated_confidence: 0.88
```

**Use Cases**:
- Clarify vague requirements
- Fill in missing details
- Validate project scope
- Gather customer requirements

---

### 2. PRD Generator Agent

**Purpose**: Generate formal Product Requirements Documents from clarified requirements

**Input**:
```python
PRDGeneratorInput(
    requirement_description: str,
    clarification_answers: List[Dict[str, str]],
    project_context: Optional[Dict[str, Any]]
)
```

**Output**:
```python
PRDGeneratorOutput(
    prd: Dict[str, Any],
    completeness_score: float,
    estimated_effort: str
)
```

**Generated PRD includes**:
- Product overview
- Features and functionality
- User stories
- Acceptance criteria
- Non-functional requirements
- Success metrics
- Timeline estimates

**Example**:
```bash
Input:
  requirement_description: "E-commerce for fashion"
  clarification_answers: {
    "q1": "50,000 users in year 1",
    "q2": "Credit card, PayPal",
    "q3": "$50,000 budget"
  }

Output:
  prd: {
    title: "Fashion E-commerce Platform",
    overview: "...",
    features: [...],
    timeline: "8 months"
  }
  completeness_score: 0.92
  estimated_effort: "8 person-months"
```

**Use Cases**:
- Create formal product specs
- Generate documentation
- Plan development sprints
- Estimate project effort

---

### 3. Analysis Agent

**Purpose**: Analyze requirements for gaps, risks, and recommendations

**Input**:
```python
AnalysisInput(
    requirements: Dict[str, Any],
    analysis_depth: str  # "quick", "standard", "deep"
)
```

**Output**:
```python
AnalysisOutput(
    completeness_score: float,
    gaps: List[str],
    risks: List[str],
    recommendations: List[str],
    missing_details: List[str]
)
```

**Example**:
```bash
Input:
  requirements: {PRD document}
  analysis_depth: "standard"

Output:
  completeness_score: 0.78
  gaps: [
    "User authentication not specified",
    "Error handling strategies unclear",
    "Data backup plan missing"
  ]
  risks: [
    "Timeline may be tight",
    "Scope creep potential",
    "Integration complexity"
  ]
  recommendations: [
    "Prioritize MVP features",
    "Add acceptance testing phase",
    "Include buffer time"
  ]
```

**Use Cases**:
- Validate requirements completeness
- Identify project risks
- Provide recommendations
- Quality assurance

---

## Agent Architecture

### Base Agent Class

All agents inherit from `BaseAgent`:

```python
class BaseAgent(ABC):
    async def execute(self, inputs: BaseModel) -> BaseModel:
        """Main execution method"""
        # Validate inputs
        self._validate_inputs(inputs)
        
        # Get prompt and config
        prompt_name = self._get_prompt_name()
        routing_config = self._get_routing_config()
        
        # Render prompt
        prompt = self._render_prompt(prompt_name, inputs.dict())
        
        # Call LLM
        response = await self._call_llm(prompt, routing_config)
        
        # Parse and return
        return self._parse_response(response)
    
    @abstractmethod
    def _validate_inputs(self, inputs: BaseModel): ...
    
    @abstractmethod
    def _parse_response(self, raw: str) -> BaseModel: ...
    
    def _get_prompt_name(self) -> str: ...
    def _get_routing_config(self) -> Dict: ...
```

### Concrete Agent Implementation

Example: `ClarificationAgent`

```python
class ClarificationAgent(BaseAgent):
    def _validate_inputs(self, inputs: ClarificationInput):
        if not inputs.user_description:
            raise ValueError("user_description required")
        if not inputs.project_context:
            raise ValueError("project_context required")
    
    def _parse_response(self, raw: str) -> ClarificationOutput:
        data = json.loads(raw)
        return ClarificationOutput(
            questions=[
                ClarificationQuestion(**q) for q in data['questions']
            ],
            rationale=data['rationale'],
            estimated_confidence=data['confidence']
        )
    
    def _get_prompt_name(self) -> str:
        return "clarification-v1"
```

---

## Execution Flow

### Step 1: Input Validation
```python
# User provides input
input = ClarificationInput(
    user_description="...",
    project_context="..."
)

# Agent validates
agent._validate_inputs(input)  # Raises if invalid
```

### Step 2: Configuration Loading
```python
# Get prompt template
prompt_name = agent._get_prompt_name()  # "clarification-v1"
prompt_template = prompt_loader.get_prompt_template(prompt_name)

# Get LLM routing
routing = provider_loader.get_routing_config("clarification")
# Returns: {"model": "gemini-1.5-flash", "temperature": 0.7}
```

### Step 3: Prompt Rendering
```python
# Render Jinja2 template with inputs
prompt = template_renderer.render_prompt(
    prompt_template,
    {
        "user_description": "...",
        "project_context": "...",
        "conversation_history": [...]
    }
)
```

### Step 4: LLM Call
```python
# Call Gemini API with rendered prompt
response = await llm_client.generate_content(
    model="gemini-1.5-flash",
    prompt=prompt,
    temperature=0.7
)
```

### Step 5: Response Parsing
```python
# Parse LLM response
parsed = agent._parse_response(response.text)
# Returns: ClarificationOutput(questions=[], rationale="", ...)
```

---

## Error Handling

### Validation Errors
```python
try:
    result = await agent.execute(invalid_input)
except ValueError as e:
    # Input validation failed
    error_response = {
        "status": "failed",
        "error": str(e)
    }
```

### LLM Errors
```python
try:
    response = await llm_client.generate_content(prompt)
except APIError as e:
    # LLM API failed
    logger.error("llm_call_failed", error=str(e))
    raise
```

### Parsing Errors
```python
try:
    result = agent._parse_response(raw)
except json.JSONDecodeError as e:
    # LLM response not valid JSON
    logger.error("response_parse_failed", error=str(e))
    raise
```

---

## Configuration

Each agent configuration in `agents/*.yaml`:

```yaml
# agents/clarification-agent.yaml
name: clarification-agent
version: 1.0.0
description: Generates clarifying questions for requirements

prompt:
  name: clarification-v1
  version: 1.0.0
  
routing:
  default_model: gemini-1.5-flash
  temperature: 0.7
  max_tokens: 1000
  
validation:
  required_fields:
    - user_description
    - project_context
```

---

## Performance Considerations

### Caching
- Loaded agents cached in memory
- Prompt templates cached
- Configuration cached
- Clear cache on need

### Concurrency
- All agent calls async
- Multiple agents can run concurrently
- Database connection pooling
- LLM API rate limiting

### Timeouts
- Default: 30 seconds per agent execution
- Configurable per agent
- Automatic retry on timeout

---

## Testing Agents

### Unit Test Example
```python
async def test_clarification_agent():
    # Setup
    mock_provider = MockProviderLoader()
    mock_prompt = MockPromptLoader()
    agent = ClarificationAgent(mock_provider, mock_prompt, mock_llm)
    
    # Execute
    result = await agent.execute(
        ClarificationInput(
            user_description="Build an app",
            project_context="Startup"
        )
    )
    
    # Assert
    assert isinstance(result, ClarificationOutput)
    assert len(result.questions) > 0
    assert 0 <= result.estimated_confidence <= 1
```

---

## Extending the System

### Adding a New Agent

1. **Create agent file**: `agents/new_agent.py`
```python
class NewAgent(BaseAgent):
    def _validate_inputs(self, inputs: NewInput): ...
    def _parse_response(self, raw: str) -> NewOutput: ...
```

2. **Create schema**: Update `schemas/agent_schemas.py`
```python
class NewInput(BaseModel): ...
class NewOutput(BaseModel): ...
```

3. **Create config**: `agents/new-agent.yaml`
```yaml
name: new-agent
version: 1.0.0
routing:
  default_model: gemini-1.5-pro
```

4. **Create prompt**: `prompts/v1/new-agent.prompt.yaml`
```yaml
name: new-agent-v1
template: |
  {{input_field}}: {{value}}
```

5. **Register agent** in orchestrator
```python
# orchestration/agent_orchestrator.py
self.new_agent = NewAgent(...)
```

---

**Next**: See [Configuration](05-configuration.md) for setting up agents
