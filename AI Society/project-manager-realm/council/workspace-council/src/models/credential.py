from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.config.database import Base

class Credential(Base):
    __tablename__ = "credentials"

    id: Mapped[uuid4] = mapped_column(primary_key=True, default=uuid4)
    workspace_id: Mapped[uuid4] = mapped_column(ForeignKey("workspaces.id"))
    key: Mapped[str] = mapped_column(String(255))
    value: Mapped[str] = mapped_column(String(1024))  # Should be encrypted in production
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    workspace: Mapped["Workspace"] = relationship(back_populates="credentials")
