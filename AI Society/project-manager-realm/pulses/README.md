# Pulses

Purpose
- Define and run orchestrated workflows (Pulses) for product management flows.

Responsibilities
- Store pulse definitions in `pulse.yaml` files.
- Provide a runtime in `_engine/` that executes pulse steps, respects retry/compensation, and emits events.
- Instrument pulse executions for observability and metrics.

Event-driven details
- Pulses implement long-running workflows and may act as saga orchestrators by listening to events and emitting compensating events when necessary.
- Prefer event choreography (services emitting events in response to state changes) and use pulses for cross-cutting workflows that require coordination.
- Pulses should publish status events (e.g., `pulse.execution.started`, `pulse.execution.succeeded`, `pulse.execution.failed`) and include correlation IDs for tracing.

Directory contents
- `_engine/` - runtime executor (README and later code)
- `requirement-clarification/` - example pulse

Next steps
- Implement a small pulse executor that can run HTTP-triggered pulses and log step execution.
- Add tests for retry and compensation behaviors.
