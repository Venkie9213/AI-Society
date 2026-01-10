from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import List
from src.models import WorkspaceType
from src.schemas.credential import CredentialCreate

class WorkspaceBase(BaseModel):
    type: WorkspaceType
    name: str
    external_id: str

class WorkspaceCreate(WorkspaceBase):
    tenant_id: UUID
    credentials: List[CredentialCreate] = []

class WorkspaceInfo(WorkspaceBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
