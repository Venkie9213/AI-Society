# Gateway

Purpose
- Edge layer: ingress for HTTP APIs and webhooks into the realm.

Responsibilities
- Validate and authenticate requests, extract `tenant_id`/`workspace_id`.
- Route requests to pulses or services.
- Verify webhook signatures and provide DLQ/retry behavior for citizen webhooks.
- Rate limiting, caching, and basic request transformations.

Event-driven details
- The gateway should translate inbound HTTP/webhook requests into domain events and publish them to the event bus (e.g., `project-manager.requirement.requirement.created`).
- For synchronous request-response flows, the gateway may call a service HTTP API; prefer emitting events for asynchronous workflows.
- Implement request validation, idempotency keys, and correlation IDs (`X-Correlation-ID`) to trace events across services.
- Provide an HTTP endpoint to receive event callbacks or implement a lightweight consumer to handle critical events if needed.

Directory contents
- `README.md` - this file

Next steps
- Add example webhook handlers and signature verification samples.
- Add a small API gateway reference implementation (Express/Fastify) under `gateway/service/`.
