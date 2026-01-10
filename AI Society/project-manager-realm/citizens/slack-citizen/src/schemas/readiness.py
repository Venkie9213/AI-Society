from pydantic import BaseModel

class ReadinessResponse(BaseModel):
    """Readiness check response model."""

    ready: bool
    service: str
    checks: dict[str, bool]
