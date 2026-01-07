# Intelligence Layer

Purpose
- Provide a centralized place for prompt templates, agent definitions, model/provider routing, memory adapters, evaluation datasets, and guardrails.

Responsibilities
- Versioned prompts under `prompts/v1/` with metadata and metrics.
- Agent definitions for routing requests to models and applying policies.
- Provider configs and routing/fallback rules in `models/`.
- Memory adapters and vector-store integration in `memory/`.
- Evaluation datasets and scripts in `evals/` for A/B testing and regressions.
- Guardrails and safety checks under `guardrails/` (PII masking, toxicity, factuality verification).

Directory contents
- `prompts/v1/` - production and draft prompts (YAML files)
- `agents/` - agent configs and orchestration policies
- `models/` - model provider configs
- `memory/` - vector store adapters and schema
- `evals/` - test datasets and evaluation scripts
- `guardrails/` - guardrail policies and checkers

Next steps
- Add prompt authoring guidelines and templates.
- Add example vector-store config for Qdrant/Pinecone.
- Add evaluation harness and CI job to run prompt evals.
