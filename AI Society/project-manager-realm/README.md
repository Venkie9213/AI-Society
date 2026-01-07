# Project Manager Realm

This folder contains the `project-manager-realm` scoped scaffold for the AI Society project — the Product Management/PM automation product.

Overview
- Purpose: Automate product management workflows (PRDs, story decomposition, sprint planning, risk detection, reporting) using LLMs and orchestrated Pulses.
- Audience: Engineers implementing services, data engineers building pipelines, ML engineers managing prompts/models, and SRE/security owners.

Top-level layout
- `intelligence/` — LLM prompts, agents, model routing, memory and evals.
- `gateway/` — API gateway, webhooks, auth extraction, request validation.
- `pulses/` — workflow definitions and runtime engine (`_engine/`).
- `services/` — domain services (e.g., `requirement-service/`).
- `libraries/` — shared libraries (identity, multi-tenancy, SDKs).
- `citizens/` — adapters to external systems (Jira, GitHub, Slack, Google Workspace).
- `schemas/` — contract-first schemas (events, APIs, pulses).
- `infrastructure/` — Docker/K8s/CI, DB migrations, monitoring manifests.

Microservices & Event-Driven Architecture
- Each domain service under `services/` is a small, independently deployable microservice and owns its data (database-per-service).
- Services communicate asynchronously via an event bus (Kafka recommended). Use events for state changes and cross-service integration.
- Follow the contract-first approach: define events and API schemas under `schemas/` and version them.
- Use sagas/pulses for long-running transactions and compensating actions; prefer event choreography when possible and orchestration only when necessary.
- Ensure idempotency, message keys, and consumer-side deduplication for event handlers.

Conventions
- Kafka topic naming: `realm.service.entity.event` e.g. `project-manager.requirement.requirement.created`.
- Event schemas live in `schemas/events/` and must include `event_id`, `occurred_at`, `tenant_id`, `payload_version`.
- Add a consumer contract and a running contract test for critical flows.

Getting started
1. Read the README within each folder for intent and next steps.
2. Implement MVP features under `services/requirement-service` and `pulses/requirement-clarification`.
3. Use `intelligence/prompts/v1` to author and version prompt templates.

Contributing
- Follow the repository ADRs (add ADRs under `docs/adr/` when adding architecture decisions).
- Keep prompts versioned and add eval datasets under `intelligence/evals/` when updating prompts.

Contact
- For questions about scope, ask the architecture owner listed in the project docs. (Add owner metadata here when known.)
