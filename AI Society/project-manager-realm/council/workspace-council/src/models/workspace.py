from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.config.database import Base
from src.models.enums import WorkspaceType

class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"))
    type: Mapped[WorkspaceType] = mapped_column(Enum(WorkspaceType))
    name: Mapped[str] = mapped_column(String(255))
    external_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    tenant: Mapped["Tenant"] = relationship(back_populates="workspaces")
    credentials: Mapped[list["Credential"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
