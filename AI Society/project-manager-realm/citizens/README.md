# Citizens

Purpose
- Integration adapters to external systems (Jira, GitHub, Slack, Google Workspace, DataDog, Figma).

Responsibilities
- Provide inbound webhook handlers that validate signatures and map events to internal schemas.
- Provide outbound clients for making authenticated API calls to external systems.
- Implement retry and DLQ strategies for failed outbound calls.

Next steps
- Create example adapters for Jira and GitHub.
- Define event mapping contracts under `schemas/citizens/`.
