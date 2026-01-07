# Requirement Service

Purpose
- Intake product requirements, start the `requirement-clarification` pulse, and persist conversation state.

Responsibilities
- Provide endpoints:
	- `POST /requirements` - create intake and trigger pulse
	- `GET /requirements/:id` - retrieve requirement and conversation state
- Publish events to the event bus when new requirements are created or PRDs are generated.
- Integrate with `intelligence/` for intent extraction and `pulses/` for orchestration.

Directory contents
- `README.md` - this file

Next steps
- Scaffold a minimal Node.js service with Express/Fastify that accepts requirement intake and logs a pulse start.
- Add DB schema for `requirements` and `intent_conversations`.
