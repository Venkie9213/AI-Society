# Intelligence Agents

Collection of specialized agents for requirement clarification and PRD generation.

## Agents

### Clarification Agent (`clarification-agent.yaml`)
- **Purpose**: Generate clarifying questions to resolve requirement ambiguity
- **Input**: Partial requirement description, project context
- **Output**: Structured clarifying questions with rationale
- **Success Criteria**: Achieve >=95% intent confidence
- **Used by**: Requirement intake process

### PRD Generation Agent (`prd-generator-agent.yaml`)
- **Purpose**: Convert clarified requirements into formal PRD
- **Input**: Requirement description, clarification answers
- **Output**: Structured PRD document with sections
- **Used by**: Requirement formalization process

### Analysis Agent (`analysis-agent.yaml`)
- **Purpose**: Analyze requirements for completeness and feasibility
- **Input**: Requirements or PRD
- **Output**: Gap analysis, risk assessment, recommendations
- **Used by**: Requirement validation process

## Agent Lifecycle

```
User Input
    ↓
[Clarification Agent] → Generate Questions
    ↓
User Answers
    ↓
[PRD Generation Agent] → Generate PRD
    ↓
[Analysis Agent] → Validate & Analyze
    ↓
Formal PRD
```

## Implementation

Agents are defined in YAML and loaded by the Intelligence Service.

Each agent specifies:
- Input schema (required fields)
- Processing instructions (prompts)
- Output schema
- Routing configuration (which LLM provider to use)

## Adding New Agents

1. Create `{agent-name}-agent.yaml` in this directory
2. Define input/output schemas
3. Reference prompts from `prompts/v1/`
4. Register in Intelligence Service config
