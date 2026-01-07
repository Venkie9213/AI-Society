# AI Society

AI Society is a SaaS platform to automate product management workflows using LLMs and workflow orchestration (Pulses).

Repository structure (scaffold):

- intelligence/: LLM layer, prompts, agents, models, memory, evals, guardrails
- gateway/: API gateway, webhooks, auth
- pulses/: workflow definitions and runtime engine
- services/: domain services (requirement-service, planning-service, ...)
- libraries/project-manager-identity/: tenant/workspace and RBAC helpers
- citizens/: integration adapters (Jira, GitHub, Slack, etc.)
- schemas/: contract-first schemas for events, APIs, pulses
- infrastructure/: Docker/K8s/CI/CD and monitoring artifacts

Next steps:
1. Implement `requirement-service` API and `intent extraction` pulse.
2. Add intelligence prompt templates and a minimal pulse engine.

Runbook:
- Add code under `services/` and `intelligence/` per roadmap.

