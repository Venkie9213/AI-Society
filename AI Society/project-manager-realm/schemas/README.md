# Schemas

Purpose
- Contract-first design for events, APIs, and pulses. Store JSON Schema and OpenAPI specs here.

Responsibilities
- Host JSON Schemas for Kafka events under `schemas/events/`.
- Host OpenAPI specs or API contract stubs under `schemas/api/`.
- Host pulse schemas under `schemas/pulses/`.

Next steps
- Add `schemas/events/` and `schemas/api/` directories and example schemas.

Event schema guidance
- Put event JSON Schema definitions in `schemas/events/` and name files `{entity}.{event}.schema.yaml` (e.g., `requirement.created.schema.yaml`).
- Include standard event envelope fields: `event_id`, `occurred_at`, `tenant_id`, `source`, `payload_version`, and `payload`.
- Consumers must validate incoming events against these schemas before processing.
