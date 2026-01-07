# Project Manager Identity Library

Purpose
- Tenant and workspace identity models, RBAC, and middleware to enforce multi-tenancy.

Responsibilities
- Define `Tenant`, `Workspace`, `User`, and `Role` models and seed scripts.
- Provide middleware for extracting `tenant_id` from requests and verifying access.
- Export shared DB types used across services.

Directory contents
- `README.md` - this file

Next steps
- Add model definitions and migration scripts.
- Add example middleware for Express/Fastify.
