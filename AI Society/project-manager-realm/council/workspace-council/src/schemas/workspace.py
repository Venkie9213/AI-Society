from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from src.models import WorkspaceType
from src.schemas.credential import CredentialCreate
from pydantic import model_validator

class WorkspaceBase(BaseModel):
    type: WorkspaceType
    name: str
    external_id: str

class WorkspaceCreate(WorkspaceBase):
    tenant_id: Optional[UUID] = None
    tenant_external_id: Optional[str] = None
    credentials: List[CredentialCreate] = []

    @model_validator(mode="after")
    def check_tenant_identifier(self) -> "WorkspaceCreate":
        if not self.tenant_id and not self.tenant_external_id:
            raise ValueError("Either tenant_id (UUID) or tenant_external_id (string) must be provided")
        return self

class WorkspaceInfo(WorkspaceBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
