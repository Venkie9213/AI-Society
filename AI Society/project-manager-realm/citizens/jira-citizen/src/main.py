from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.config.settings import settings
from src.events.consumer import KafkaConsumerService
from src.utils.discovery import DiscoveryClient
from src.events.router import EventRouter
from src.utils.observability import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

# Global instances
consumer_service: KafkaConsumerService | None = None
discovery_client: DiscoveryClient | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("service_startup", app_name=settings.app_name, version=settings.app_version)
    
    # Register with Gateway
    global discovery_client
    discovery_client = DiscoveryClient("jira-citizen", port=8001)
    await discovery_client.register()
    
    # Initialize Kafka Consumer
    topics = [
        settings.topic_epic_create,
        settings.topic_story_create,
        settings.topic_story_assign,
        settings.topic_sprint_start
    ]
    
    global consumer_service
    consumer_service = KafkaConsumerService(topics=topics, handler=EventRouter.route_event)
    await consumer_service.start()
    
    yield
    
    # Shutdown
    if consumer_service:
        await consumer_service.stop()
        
    if discovery_client:
        await discovery_client.unregister()
    
    logger.info("service_shutdown")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "jira-citizen"}
