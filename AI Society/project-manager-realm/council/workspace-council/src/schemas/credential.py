from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any

class CredentialBase(BaseModel):
    key: str
    value: str
    metadata_json: Optional[Dict[str, Any]] = None

class CredentialCreate(CredentialBase):
    pass

class CredentialInfo(CredentialBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
