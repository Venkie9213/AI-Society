from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.database import db_manager
from src.schemas import WorkspaceCreate, WorkspaceInfo, WorkspaceConfigResponse
from src.services.council_service import CouncilService
from src.models import WorkspaceType
from typing import List

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

@router.post("/", response_model=WorkspaceInfo)
async def create_workspace(workspace_in: WorkspaceCreate, session: AsyncSession = Depends(db_manager.get_session)):
    return await CouncilService.create_workspace(session, workspace_in)

@router.get("/{tenant_id}/{type}/config", response_model=WorkspaceConfigResponse)
async def get_workspace_config(
    tenant_id: str, 
    type: WorkspaceType, 
    session: AsyncSession = Depends(db_manager.get_session)
):
    config = await CouncilService.get_workspace_config(session, tenant_id, type)
    if config is None:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    return WorkspaceConfigResponse(
        tenant_id=tenant_id,
        workspace_type=type.value,
        config=config
    )
