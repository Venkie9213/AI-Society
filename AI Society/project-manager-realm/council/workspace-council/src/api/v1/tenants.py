from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.database import db_manager
from src.schemas import TenantCreate, TenantInfo
from src.services.council_service import CouncilService
from typing import List

router = APIRouter(prefix="/tenants", tags=["Tenants"])

@router.post("/", response_model=TenantInfo)
async def create_tenant(tenant_in: TenantCreate, session: AsyncSession = Depends(db_manager.get_session)):
    existing = await CouncilService.get_tenant_by_external_id(session, tenant_in.external_id)
    if existing:
        raise HTTPException(status_code=400, detail="Tenant with this external_id already exists")
    return await CouncilService.create_tenant(session, tenant_in)

@router.get("/{external_id}", response_model=TenantInfo)
async def get_tenant(external_id: str, session: AsyncSession = Depends(db_manager.get_session)):
    tenant = await CouncilService.get_tenant_by_external_id(session, external_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant
