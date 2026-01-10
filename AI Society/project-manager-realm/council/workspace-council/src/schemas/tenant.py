from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class TenantBase(BaseModel):
    name: str
    external_id: str

class TenantCreate(TenantBase):
    pass

class TenantInfo(TenantBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
