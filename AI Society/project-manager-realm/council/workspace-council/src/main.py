from fastapi import FastAPI
from src.api.v1 import tenants, workspaces
from src.config.database import db_manager, Base
from src.utils.observability import setup_logging, get_logger
from src.config.settings import settings

# Initialize Logging
setup_logging()
logger = get_logger("workspace_council")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

# Register API routers
app.include_router(tenants.router, prefix="/api/v1")
app.include_router(workspaces.router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    logger.info("workspace_council_starting", version=settings.app_version)
    
    # Create tables automatically for development
    # In a production environment, use Alembic migrations
    async with db_manager.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("workspace_council_started")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.app_name}
