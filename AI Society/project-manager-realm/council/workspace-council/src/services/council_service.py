from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import Tenant, Workspace, Credential, WorkspaceType
from src.schemas import TenantCreate, WorkspaceCreate, CredentialCreate
from src.utils.observability import get_logger
from typing import List, Optional, Dict

logger = get_logger(__name__)

class CouncilService:
    @staticmethod
    async def create_tenant(session: AsyncSession, tenant_in: TenantCreate) -> Tenant:
        tenant = Tenant(name=tenant_in.name, external_id=tenant_in.external_id)
        session.add(tenant)
        await session.flush()
        logger.info("tenant_created", id=str(tenant.id), external_id=tenant.external_id)
        return tenant

    @staticmethod
    async def get_tenant_by_external_id(session: AsyncSession, external_id: str) -> Optional[Tenant]:
        stmt = select(Tenant).where(Tenant.external_id == external_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def create_workspace(session: AsyncSession, workspace_in: WorkspaceCreate) -> Workspace:
        tenant_id = workspace_in.tenant_id

        # Resolve tenant_id from external_id if missing
        if not tenant_id and workspace_in.tenant_external_id:
            tenant = await CouncilService.get_tenant_by_external_id(session, workspace_in.tenant_external_id)
            if not tenant:
                logger.error("tenant_not_found_by_external_id", external_id=workspace_in.tenant_external_id)
                raise ValueError(f"Tenant with external_id '{workspace_in.tenant_external_id}' not found")
            tenant_id = tenant.id

        if not tenant_id:
             raise ValueError("Valid tenant identifier (ID or External ID) is required")

        workspace = Workspace(
            tenant_id=tenant_id,
            type=workspace_in.type,
            name=workspace_in.name,
            external_id=workspace_in.external_id
        )
        session.add(workspace)
        await session.flush()

        for cred_in in workspace_in.credentials:
            cred = Credential(
                workspace_id=workspace.id,
                key=cred_in.key,
                value=cred_in.value,
                metadata_json=cred_in.metadata_json
            )
            session.add(cred)
        
        await session.flush()
        logger.info("workspace_created", id=str(workspace.id), type=workspace.type.value, tenant_id=str(workspace.tenant_id))
        return workspace

    @staticmethod
    async def get_workspace_config(
        session: AsyncSession, 
        tenant_external_id: str, 
        workspace_type: WorkspaceType
    ) -> Optional[Dict[str, str]]:
        # Find tenant first
        tenant = await CouncilService.get_tenant_by_external_id(session, tenant_external_id)
        if not tenant:
            logger.warning("config_lookup_failed_tenant_not_found", tenant_id=tenant_external_id)
            return None

        # Find workspace of specific type for this tenant
        stmt = select(Workspace).where(
            Workspace.tenant_id == tenant.id,
            Workspace.type == workspace_type
        )
        result = await session.execute(stmt)
        workspace = result.scalars().first()

        if not workspace:
            logger.warning("config_lookup_failed_workspace_not_found", tenant_id=tenant_external_id, type=workspace_type.value)
            return None

        # Fetch credentials
        stmt = select(Credential).where(Credential.workspace_id == workspace.id)
        result = await session.execute(stmt)
        credentials = result.scalars().all()

        config = {cred.key: cred.value for cred in credentials}
        logger.info("workspace_config_resolved", tenant_id=tenant_external_id, type=workspace_type.value)
        return config
