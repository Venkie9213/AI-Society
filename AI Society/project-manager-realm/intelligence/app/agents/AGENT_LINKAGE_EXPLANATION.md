# Agent Linkage: Python Code & YAML Configuration

## Overview
The `clarification_agent.py` (Python class) and `clarification-agent.yaml` (configuration file) work together as a complete agent system.

## Detailed Linkage Map

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXECUTION FLOW                               │
└─────────────────────────────────────────────────────────────────┘

1. INITIALIZATION (Python Code)
   ↓
   ClarificationAgent.__init__()
   ├─ agent_name = "clarification-agent"
   └─ Loads YAML config via BaseAgent.__init__()
      └─ self.config = agent_loader.get_agent_config("clarification-agent")
         └─ Loads: clarification-agent.yaml ✓

2. CONFIGURATION MAPPING
   ↓
   YAML File: clarification-agent.yaml
   ├─ inputs: defines required/optional inputs
   ├─ outputs: defines output schema
   ├─ config: agent-specific settings
   ├─ routing: provider/model/temperature settings
   ├─ prompt_template: specifies which prompt to use
   └─ metrics: success criteria

   Python Code: clarification_agent.py
   ├─ _validate_inputs(): validates against input schema
   ├─ _get_prompt_name(): returns prompt template name
   ├─ _parse_response(): parses output to match output schema
   └─ Execute flow: uses config loaded from YAML

3. EXECUTION PIPELINE
   ↓
   BaseAgent.execute() → calls ClarificationAgent methods
   ├─ _validate_inputs() ← Checks inputs match YAML schema
   ├─ _get_prompt_name() ← Returns from Python override
   ├─ _get_routing_config() ← Reads from YAML routing section
   ├─ Call LLM via provider_router ← Uses YAML routing settings
   ├─ _parse_response() ← Normalizes output to match YAML schema
   └─ Return structured output ← Matches YAML outputs section
```

## Specific Linkages

### 1. **Agent Name Linking**
```
Python Code (clarification_agent.py):
    super().__init__("clarification-agent")  ← Name passed to BaseAgent
                         ↑
                         └─ MUST match YAML filename
                            (clarification-agent.yaml)
```

### 2. **Input Validation Linking**
```
YAML (clarification-agent.yaml):
    inputs:
      user_description:  ← Required input
        type: string
      project_context:   ← Required input
        type: string
      conversation_history:  ← Optional input
        type: array
         ↓
Python (clarification_agent.py):
    def _validate_inputs(self, inputs):
        required_fields = ["user_description", "project_context"]
        └─ Validates only required fields
           (conversation_history is optional but validated if present)
```

### 3. **Prompt Template Linking**
```
YAML (clarification-agent.yaml):
    prompt_template: v1_requirement-question-generator.prompt
         ↓
Python (clarification_agent.py):
    def _get_prompt_name(self):
        return "v1_requirement-question-generator.prompt"
         ↓
BaseAgent.execute():
    rendered_prompt = self.template_renderer.render_prompt(
        prompt_name=prompt_name,  ← Uses the prompt template
        context=inputs
    )
```

### 4. **Routing Configuration Linking**
```
YAML (clarification-agent.yaml):
    routing:
      provider: gemini
      model: gemini-3-flash-preview
      temperature: 0.7
      max_tokens: 1000
         ↓
Python (BaseAgent._get_routing_config):
    routing = self.config.get("routing", {})
    return {
        "provider": routing.get("provider", "gemini"),
        "model": routing.get("model", "gemini-3-flash-preview"),
        "temperature": routing.get("temperature", 0.7),
        "max_tokens": routing.get("max_tokens", 1000),
    }
         ↓
BaseAgent.execute():
    response = await self.provider_router.generate(
        provider=routing["provider"],     ← From YAML
        temperature=routing["temperature"],  ← From YAML
        max_tokens=routing["max_tokens"],   ← From YAML
    )
```

### 5. **Output Schema Linking**
```
YAML (clarification-agent.yaml):
    outputs:
      questions:
        type: array
        items:
          properties:
            id: {type: integer}
            text: {type: string}
            category: {type: string}
            priority: {type: string, enum: [high, medium, low]}
      rationale: {type: string}
      estimated_confidence: {type: number, minimum: 0, maximum: 1}
         ↓
Python (clarification_agent.py):
    def _parse_response(self, response_content: str):
        output = json.loads(content)
        # Normalize to match output schema
        normalized_questions = []
        for q in output.get("questions", []):
            normalized_q = {
                "id": str(q.get("id", "")),
                "text": q.get("text", ""),
                "category": q.get("category", "Requirements"),
                "priority": q.get("priority", "Medium"),
            }
            normalized_questions.append(normalized_q)
        
        output["questions"] = normalized_questions
        output["rationale"] = ...  ← Ensures all YAML fields present
        output["estimated_confidence"] = ...
        return output  ← Returns structured data matching YAML schema
```

## Data Flow Example

```
User Input:
{
    "user_description": "Build a mobile app",
    "project_context": "Startup project"
}
    ↓
ClarificationAgent.execute(inputs)
    ↓
BaseAgent.execute():
    1. _validate_inputs()
       └─ Checks user_description & project_context exist ✓
    2. _get_prompt_name()
       └─ Returns "v1_requirement-question-generator.prompt"
    3. Load config from YAML
       └─ Gets routing settings (provider: gemini, model: ..., temp: 0.7, ...)
    4. Render prompt template with inputs
    5. Call LLM:
       LLMProvider.generate(
           messages=[prompt],
           provider="gemini",      ← From YAML
           temperature=0.7,        ← From YAML
           max_tokens=1000         ← From YAML
       )
    6. LLM Response:
       {
           "questions": [...],
           "reasoning": "...",
           "confidence": 0.8
       }
    7. _parse_response(llm_response)
       └─ Normalizes to match YAML output schema ✓
    ↓
Output:
{
    "questions": [
        {
            "id": "1",
            "text": "What features?",
            "category": "Requirements",
            "priority": "High"
        },
        ...
    ],
    "rationale": "Questions generated",
    "estimated_confidence": 0.8
}
```

## Key Connection Points

| Aspect | YAML | Python | Purpose |
|--------|------|--------|---------|
| **Agent Identity** | `name: clarification-agent` | `super().__init__("clarification-agent")` | Register agent & load config |
| **Inputs** | `inputs: {...}` | `_validate_inputs()` | Define & validate inputs |
| **Outputs** | `outputs: {...}` | `_parse_response()` | Define & normalize outputs |
| **Routing** | `routing: {...}` | `_get_routing_config()` | Configure LLM provider |
| **Prompt** | `prompt_template: ...` | `_get_prompt_name()` | Specify which prompt to use |
| **Config** | `config: {...}` | `self.config` | Agent-specific settings |
| **Metrics** | `metrics: [...]` | Logged during execution | Track performance |

## Summary

**The relationship is:**
- **YAML file** = Configuration contract (what inputs/outputs, which provider, which prompt)
- **Python class** = Implementation (how to validate, how to parse, custom logic)
- **BaseAgent** = Orchestrator (loads YAML, calls methods, manages execution flow)

When you create an agent:
1. **YAML** declares the contract
2. **Python** implements the contract
3. **BaseAgent** ensures they work together
4. The agent name in Python MUST match the YAML filename for automatic loading

**Example:** `clarification-agent.yaml` ↔ `ClarificationAgent("clarification-agent")` ✓
