"""Event ID generation utilities."""

import uuid


def generate_event_id() -> str:
    """Generate a unique event ID."""
    return str(uuid.uuid4())


def generate_entity_id(prefix: str) -> str:
    """Generate a unique entity ID with a prefix."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"
