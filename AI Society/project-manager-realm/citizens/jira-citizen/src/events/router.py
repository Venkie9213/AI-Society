from aiokafka import ConsumerRecord
from src.utils.observability import get_logger
from src.services.auth import AuthService
from src.clients.jira import JiraClient
from typing import Dict, Any

logger = get_logger(__name__)

class EventRouter:
    """Routes Kafka events to the appropriate handler logic."""
    
    @staticmethod
    async def route_event(msg: ConsumerRecord):
        """
        Route the event based on the topic or event type.
        """
        try:
            topic = msg.topic
            payload = msg.value
            
            # Extract tenant context
            # Assuming payload follows a standard envelope: { "tenant_id": "...", "data": ... }
            tenant_id = payload.get("tenant_id")
            if not tenant_id:
                logger.error("missing_tenant_id", topic=topic)
                return

            # Fetch Config
            config = await AuthService.get_jira_credentials(tenant_id)
            if not config:
                logger.error("jira_config_missing", tenant_id=tenant_id)
                return

            client = JiraClient(config)
            
            # Dispatch
            # This logic should be cleaner in a real app (Registration Pattern), but if/else ok for now
            data = payload.get("data", {})
            
            if "epic.create" in topic:
                await client.create_epic(
                    project_key=data.get("project_key"),
                    summary=data.get("summary"),
                    description=data.get("description")
                )
                logger.info("epic_created_via_event", tenant_id=tenant_id, project=data.get("project_key"))
                
            elif "story.create" in topic:
                await client.create_story(
                    project_key=data.get("project_key"),
                    summary=data.get("summary"),
                    description=data.get("description"),
                    epic_key=data.get("epic_key")
                )
                logger.info("story_created_via_event", tenant_id=tenant_id, project=data.get("project_key"))

            elif "story.assign" in topic:
                await client.assign_issue(
                    issue_key=data.get("issue_key"),
                    account_id=data.get("account_id")
                )
                logger.info("story_assigned_via_event", tenant_id=tenant_id, issue=data.get("issue_key"))
                
            else:
                logger.warning("unhandled_topic", topic=topic)
                
        except Exception as e:
            logger.error("event_routing_failed", error=str(e), topic=msg.topic)
            # In a robust system, we might DLQ this message
