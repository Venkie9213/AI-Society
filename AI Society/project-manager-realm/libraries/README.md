# Libraries

Purpose
- Shared libraries and utilities used across services and the intelligence layer.

Responsibilities
- Host common code: `project-manager-identity` (tenant/workspace models, RBAC), SDKs for internal RPC, and shared types/schemas.

Event-driven libraries
- Provide a shared event-bus client library (Kafka producer/consumer helpers) under `libraries/` and shared event types to ensure consistent serialization and retries.
- Provide helpers for generating idempotency keys, correlation IDs, and consumer offset handling.

Directory contents
- `project-manager-identity/` - identity library (see README)

Next steps
- Add utility templates and a monorepo setup (pnpm/workspaces or yarn workspaces) if desired.
