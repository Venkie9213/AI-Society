from src.config import settings
from src.events import get_event_producer, shutdown_event_producer
from src.utils.observability import get_logger, start_metrics_server
from src.services.slack_notifier import SlackNotifier
from src.services.internal_event_router import InternalEventRouter
from src.services.consumer import KafkaConsumerService

logger = get_logger(__name__)

class ServiceManager:
    """Manages the lifecycle of core application services."""
    
    def __init__(self):
        self.notifier = SlackNotifier()
        self.router = InternalEventRouter(self.notifier)
        self.consumer_service = KafkaConsumerService(
            topics=[
                "requirement.requirement.created",
                "requirement.clarification.completed",
                "pulse.execution.failed",
                "reply.requested",
            ],
            handler=self.router.handle_event,
        )

    async def start(self):
        """Startup logic for all services."""
        logger.info(
            "starting_slack_citizen_services",
            version=settings.app_version,
            environment=settings.environment,
        )
        start_metrics_server()
        await get_event_producer()
        
        if settings.environment != "test":
            await self.consumer_service.start()
            
        logger.info("slack_citizen_services_started")

    async def stop(self):
        """Shutdown logic for all services."""
        logger.info("shutting_down_slack_citizen_services")
        
        if settings.environment != "test":
            await self.consumer_service.stop()
            
        await shutdown_event_producer()
        logger.info("slack_citizen_services_stopped")
