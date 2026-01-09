"""Main message processing orchestrator.

Coordinates conversation management, agent execution, and event publishing.
Implements the Orchestrator pattern to reduce cognitive complexity.
"""

import uuid
from typing import Any, Optional
import structlog

from sqlalchemy.ext.asyncio import AsyncSession

from app.message_processing.conversation_manager import ConversationManager
from app.message_processing.agent_runner import AgentRunner
from app.message_processing.event_publisher import EventPublisher

logger = structlog.get_logger()


class MessageProcessingOrchestrator:
    """Orchestrates message processing workflow.
    
    Responsibilities:
    - Coordinate conversation management
    - Trigger agent execution
    - Publish events
    - Handle errors and logging
    """
    
    def __init__(
        self,
        db_session: AsyncSession,
        agent_orchestrator: Any,  # AgentOrchestrator
        producer: Any,  # KafkaMessageProducer
    ):
        self.conversation_mgr = ConversationManager(db_session)
        self.agent_runner = AgentRunner(agent_orchestrator)
        self.event_publisher = EventPublisher(producer)
        self.db_session = db_session
    
    async def process_slack_message(
        self,
        text: str,
        slack_user_id: str,
        slack_channel_id: str,
        slack_team_id: str,
        thread_ts: str,
        message_ts: Optional[str] = None,
    ) -> None:
        """Process incoming Slack message end-to-end.
        
        Args:
            text: User message text
            slack_user_id: Slack user ID
            slack_channel_id: Slack channel ID
            slack_team_id: Slack team/workspace ID
            thread_ts: Thread timestamp for replies
            message_ts: Message timestamp
        """
        try:
            # Generate IDs
            conversation_id = str(uuid.uuid4())
            workspace_id = str(uuid.uuid4())
            
            logger.info(
                "message_processing_started",
                conversation_id=conversation_id,
                channel=slack_channel_id,
            )
            
            # Step 1: Create/get conversation
            await self.conversation_mgr.get_or_create_conversation(
                conversation_id=conversation_id,
                workspace_id=workspace_id,
                slack_channel_id=slack_channel_id,
                thread_ts=thread_ts,
            )
            
            # Step 2: Store user message
            await self.conversation_mgr.store_message(
                conversation_id=conversation_id,
                role="user",
                content=text,
            )
            
            # Step 3: Get conversation state
            conv_state = await self.conversation_mgr.get_state(conversation_id)
            if not conv_state:
                # Initialize new conversation state
                await self.conversation_mgr.update_state(
                    conversation_id=conversation_id,
                    current_agent="clarification",
                    confidence_score=0.0,
                    turns_count=0,
                    metadata={},
                )
                conv_state = await self.conversation_mgr.get_state(conversation_id)
            
            logger.info(
                "conversation_state_loaded",
                conversation_id=conversation_id,
                current_agent=conv_state.current_agent,
                confidence=conv_state.confidence_score,
            )
            
            # Step 4: Execute agent based on current state
            if conv_state.current_agent == "clarification":
                await self._process_clarification_phase(
                    conversation_id=conversation_id,
                    slack_channel_id=slack_channel_id,
                    thread_ts=thread_ts,
                    conv_state=conv_state,
                )
            else:
                logger.info(
                    "unsupported_agent_phase",
                    agent=conv_state.current_agent,
                )
            
            logger.info("message_processing_completed", conversation_id=conversation_id)
        
        except Exception as e:
            logger.error("message_processing_failed", error=str(e), exc_info=True)
            raise
    
    async def _process_clarification_phase(
        self,
        conversation_id: str,
        slack_channel_id: str,
        thread_ts: str,
        conv_state: Any,  # ConversationState
    ) -> None:
        """Process clarification phase with extracted logic."""
        try:
            # Get conversation history
            history = await self.conversation_mgr.get_conversation_history(
                conversation_id=conversation_id,
            )
            
            # Get latest user message
            user_messages = [m for m in history if m["role"] == "user"]
            if not user_messages:
                logger.warning("no_user_messages_found", conversation_id=conversation_id)
                return
            
            user_text = user_messages[-1]["content"]
            
            # Run agent
            agent_output = await self.agent_runner.run_clarification_agent(
                user_text=user_text,
                conversation_history=history,
            )
            
            # Extract data
            questions = agent_output.get_questions()
            rationale = agent_output.get_rationale()
            confidence = agent_output.get_confidence()
            
            # Store agent response
            response_content = agent_output.to_dict()
            import json
            await self.conversation_mgr.store_message(
                conversation_id=conversation_id,
                role="assistant",
                content=json.dumps(response_content, default=str),
            )
            
            # Update conversation state
            metadata = {
                "questions": questions,
                "rationale": rationale,
            }
            
            await self.conversation_mgr.update_state(
                conversation_id=conversation_id,
                current_agent="clarification",
                confidence_score=confidence,
                turns_count=conv_state.turns_count + 1,
                metadata=metadata,
            )
            
            logger.info(
                "clarification_phase_completed",
                conversation_id=conversation_id,
                confidence=confidence,
                is_confident=confidence >= self.event_publisher.CONFIDENCE_THRESHOLD,
            )
            
            # Publish event
            await self.event_publisher.publish_clarification_event(
                conversation_id=conversation_id,
                slack_channel_id=slack_channel_id,
                slack_thread_ts=thread_ts,
                questions=questions,
                rationale=rationale,
                confidence_score=confidence,
            )
        
        except Exception as e:
            logger.error(
                "clarification_phase_failed",
                conversation_id=conversation_id,
                error=str(e),
                exc_info=True,
            )
            raise
