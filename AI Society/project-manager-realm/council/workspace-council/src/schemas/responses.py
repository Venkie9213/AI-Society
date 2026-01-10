from pydantic import BaseModel
from typing import Dict

class WorkspaceConfigResponse(BaseModel):
    tenant_id: str
    workspace_type: str
    config: Dict[str, str]
