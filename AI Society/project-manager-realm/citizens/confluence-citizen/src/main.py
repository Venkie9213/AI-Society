from fastapi import FastAPI
import uvicorn
from src.config.settings import settings
from src.utils.observability import setup_logging
from src.utils.discovery import DiscoveryClient
import structlog

logger = structlog.get_logger()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

from src.services.workspace_service import WorkspaceService
from src.services.document_handler import DocumentHandler
from src.events.consumer import KafkaConsumerService


# Initialize Logging
setup_logging()
logger = structlog.get_logger()

discovery_client = DiscoveryClient("confluence-citizen")

@app.on_event("startup")
async def startup_event():
    await discovery_client.register()
    logger.info("confluence_citizen_starting", version=settings.app_version)
    
    # Initialize Workspace Service
    workspace_service = WorkspaceService()
    
    # Initialize Document Handler with Workspace Service for dynamic config
    doc_handler = DocumentHandler(workspace_service)
    
    # Initialize and Start Kafka Consumer
    consumer_service = KafkaConsumerService(
        topic=settings.kafka_topic_prd_generated,
        handler=doc_handler.handle_document_event
    )
    
    # Store in app state for cleanup
    app.state.consumer_service = consumer_service
    await consumer_service.start()
    
    logger.info("confluence_citizen_started")

@app.on_event("shutdown")
async def shutdown_event():
    await discovery_client.unregister()
    logger.info("confluence_citizen_shutting_down")
    if hasattr(app.state, "consumer_service"):
        await app.state.consumer_service.stop()

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
