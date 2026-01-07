# Services

Purpose
- Contain domain services grouped by product workflow stage (discovery, planning, execution, quality, insights).

Responsibilities
- Each service implements HTTP APIs, event publishers/subscribers, and domain logic.
- Services should be small, focused, and own their data.

Microservices & Event-driven guidance
- Each service is responsible for a single bounded context and owns its database (schema-per-service). Do not perform cross-service joins.
- Emit events for every state change and subscribe to other services' events to react and update local state.
- Use the `schemas/events/` contracts; version events and include `event_id`, `occurred_at`, `tenant_id`, and `payload_version` fields.
- For long-running business flows, implement sagas using pulses or event-based choreography; document compensating actions when applicable.
- Provide health endpoints, metrics (Prometheus), tracing (Jaeger), and structured logs including `tenant_id` and `correlation_id`.

Service layout (recommended)
- `src/` - service source code
- `src/routes/` - HTTP handlers
- `src/events/` - event producers and consumers
- `migrations/` - DB migrations
- `Dockerfile` and `docker-compose.yml` for local dev
- `ci/` - CI workflows

Directory contents
- `requirement-service/` - intake and intent extraction (see its README)

Next steps
- Add service templates (Node/NestJS + TypeORM or Python + FastAPI) with CI tests and local dev Dockerfiles.
