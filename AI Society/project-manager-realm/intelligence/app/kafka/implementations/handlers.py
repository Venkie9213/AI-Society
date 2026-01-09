# app/kafka/handlers.py
"""Message handlers for Kafka topics"""

import json
from typing import Dict, Any, Optional, List
import structlog
from datetime import datetime, timezone

logger = structlog.get_logger()

CONFIDENCE_THRESHOLD = 95.0  # Threshold to move to next agent


async def get_conversation_history(
    db_session: Any,
    conversation_id: str,
) -> List[Dict[str, str]]:
    """Get all messages in a conversation for context."""
    from sqlalchemy import text as sql_text
    
    result = await db_session.execute(
        sql_text("""
            SELECT role, content FROM messages 
            WHERE conversation_id = :conversation_id
            ORDER BY created_at ASC
        """),
        {"conversation_id": conversation_id}
    )
    
    messages = []
    for row in result:
        messages.append({
            "role": row[0],
            "content": row[1]
        })
    return messages


async def get_conversation_state(
    db_session: Any,
    conversation_id: str,
) -> Optional[Dict[str, Any]]:
    """Get the current state of a conversation."""
    from sqlalchemy import text as sql_text
    
    result = await db_session.execute(
        sql_text("""
            SELECT current_agent, confidence_score, turns_count, metadata
            FROM conversation_states
            WHERE conversation_id = :conversation_id
        """),
        {"conversation_id": conversation_id}
    )
    
    row = result.first()
    if row:
        return {
            "current_agent": row[0],
            "confidence_score": float(row[1]),
            "turns_count": row[2],
            "metadata": row[3] or {}
        }
    return None


async def update_conversation_state(
    db_session: Any,
    conversation_id: str,
    current_agent: str,
    confidence_score: float,
    turns_count: int,
    metadata: Dict[str, Any],
) -> None:
    """Update or create conversation state."""
    from sqlalchemy import text as sql_text
    import uuid
    from datetime import datetime as dt
    
    # Check if state exists
    existing = await get_conversation_state(db_session, conversation_id)
    
    if existing:
        # Update existing state
        await db_session.execute(
            sql_text("""
                UPDATE conversation_states
                SET current_agent = :agent, confidence_score = :score, 
                    turns_count = :turns, metadata = :metadata, updated_at = :updated_at
                WHERE conversation_id = :conversation_id
            """),
            {
                "agent": current_agent,
                "score": confidence_score,
                "turns": turns_count,
                "metadata": json.dumps(metadata),
                "conversation_id": conversation_id,
                "updated_at": dt.now(timezone.utc)
            }
        )
    else:
        # Create new state
        await db_session.execute(
            sql_text("""
                INSERT INTO conversation_states 
                (conversation_id, current_agent, confidence_score, turns_count, metadata)
                VALUES (:conversation_id, :agent, :score, :turns, :metadata)
            """),
            {
                "conversation_id": conversation_id,
                "agent": current_agent,
                "score": confidence_score,
                "turns": turns_count,
                "metadata": json.dumps(metadata)
            }
        )
    
    await db_session.commit()


async def handle_slack_message(
    message: Dict[str, Any],
    orchestrator: Any,  # AgentOrchestrator
    db_session: Any,  # AsyncSession
    producer: Any = None,  # KafkaMessageProducer (optional)
) -> None:
    """Handle Slack message received event.
    
    Args:
        message: Kafka message payload with Slack message data
        orchestrator: Agent orchestrator instance
        db_session: Database session
        producer: Kafka producer for publishing responses
    """
    try:
        # Extract payload
        payload = message.get("payload", {})
        event_id = message.get("event_id")
        occurred_at = message.get("occurred_at")
        tenant_id = message.get("tenant_id")
        
        # Extract Slack message details
        text = payload.get("text", "")
        slack_user_id = payload.get("slack_user_id", "")
        slack_channel_id = payload.get("slack_channel_id", "")
        slack_team_id = payload.get("slack_team_id", "")
        thread_ts = payload.get("thread_ts", "")
        message_ts = payload.get("message_ts", "")
        
        logger.info(
            "processing_slack_message",
            event_id=event_id,
            slack_user_id=slack_user_id,
            slack_channel_id=slack_channel_id,
            text=text[:100],  # Log first 100 chars
        )
        
        # Store conversation in database
        from sqlalchemy import text as sql_text
        import uuid
        
        conversation_id = str(uuid.uuid4())
        
        # Convert tenant_id to a valid UUID if it isn't already
        try:
            workspace_uuid = uuid.UUID(tenant_id)
        except (ValueError, AttributeError):
            # If not a valid UUID, hash it to create one
            workspace_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, tenant_id)
        
        # Parse the timestamp
        from datetime import datetime as dt
        try:
            # Parse ISO format timestamp and make it timezone-naive (remove timezone info)
            parsed_dt = dt.fromisoformat(occurred_at.replace('Z', '+00:00'))
            created_at = parsed_dt.replace(tzinfo=None)
        except (ValueError, AttributeError):
            created_at = dt.now(timezone.utc)
        
        # Ensure workspace exists
        try:
            await db_session.execute(
                sql_text("""
                    INSERT INTO workspaces (workspace_id, name, created_at)
                    VALUES (:workspace_id, :name, :created_at)
                    ON CONFLICT (workspace_id) DO NOTHING
                """),
                {
                    "workspace_id": str(workspace_uuid),
                    "name": f"Workspace {tenant_id}",
                    "created_at": created_at,
                }
            )
            await db_session.commit()
        except Exception as e:
            logger.warning("workspace_creation_failed", error=str(e))
            await db_session.rollback()
        
        # Create conversation
        conversation_result = await db_session.execute(
            sql_text("""
                INSERT INTO conversations 
                (conversation_id, workspace_id, channel_id, thread_ts, created_at) 
                VALUES (:conversation_id, :workspace_id, :channel_id, :thread_ts, :created_at)
                RETURNING id
            """),
            {
                "conversation_id": conversation_id,
                "workspace_id": str(workspace_uuid),
                "channel_id": slack_channel_id,
                "thread_ts": thread_ts,
                "created_at": created_at,
            }
        )
        
        returned_id = conversation_result.scalar()
        logger.info(
            "conversation_created",
            conversation_id=returned_id,
            event_id=event_id,
        )
        
        # Store message in database - use the UUID conversation_id, not the integer id
        message_id = str(uuid.uuid4())
        await db_session.execute(
            sql_text("""
                INSERT INTO messages 
                (message_id, conversation_id, role, content, created_at) 
                VALUES (:message_id, :conversation_id, :role, :content, :created_at)
            """),
            {
                "message_id": message_id,
                "conversation_id": conversation_id,
                "role": "user",
                "content": text,
                "created_at": created_at,
            }
        )
        
        await db_session.commit()
        logger.info("message_stored", event_id=event_id, conversation_id=conversation_id)
        
        # Get or initialize conversation state
        conv_state = await get_conversation_state(db_session, conversation_id)
        
        if conv_state is None:
            # First message - start with clarification agent
            conv_state = {
                "current_agent": "clarification",
                "confidence_score": 0.0,
                "turns_count": 0,
                "metadata": {}
            }
        
        logger.info(
            "conversation_state",
            conversation_id=conversation_id,
            current_agent=conv_state["current_agent"],
            confidence_score=conv_state["confidence_score"],
            turns=conv_state["turns_count"]
        )
        
        # Get conversation history for context
        history = await get_conversation_history(db_session, conversation_id)
        
        # Process based on current agent and confidence
        if orchestrator:
            try:
                if conv_state["current_agent"] == "clarification":
                    await handle_clarification_phase(
                        event_id=event_id,
                        conversation_id=conversation_id,
                        user_text=text,
                        history=history,
                        conv_state=conv_state,
                        orchestrator=orchestrator,
                        db_session=db_session,
                        producer=producer,
                        slack_channel_id=slack_channel_id,
                        thread_ts=thread_ts,
                    )
                
                elif conv_state["current_agent"] == "prd-generator":
                    await handle_prd_generation_phase(
                        event_id=event_id,
                        conversation_id=conversation_id,
                        user_text=text,
                        history=history,
                        conv_state=conv_state,
                        orchestrator=orchestrator,
                        db_session=db_session,
                        producer=producer,
                        slack_channel_id=slack_channel_id,
                        thread_ts=thread_ts,
                    )
                
                elif conv_state["current_agent"] == "analysis":
                    await handle_analysis_phase(
                        event_id=event_id,
                        conversation_id=conversation_id,
                        user_text=text,
                        history=history,
                        conv_state=conv_state,
                        orchestrator=orchestrator,
                        db_session=db_session,
                        producer=producer,
                        slack_channel_id=slack_channel_id,
                        thread_ts=thread_ts,
                    )
                
            except Exception as e:
                logger.error(
                    "agent_processing_failed",
                    event_id=event_id,
                    current_agent=conv_state["current_agent"],
                    error=str(e),
                )
        
    except Exception as e:
        logger.error(
            "slack_message_processing_failed",
            error=str(e),
            message_keys=list(message.keys()) if isinstance(message, dict) else "unknown",
        )
        await db_session.rollback()


async def handle_clarification_phase(
    event_id: str,
    conversation_id: str,
    user_text: str,
    history: List[Dict[str, str]],
    conv_state: Dict[str, Any],
    orchestrator: Any,
    db_session: Any,
    producer: Any = None,
    slack_channel_id: str = "",
    thread_ts: str = "",
) -> None:
    """Handle clarification agent phase with confidence-based progression."""
    from sqlalchemy import text as sql_text
    import uuid
    from datetime import datetime as dt
    
    logger.info("clarification_agent_start", event_id=event_id, turn=conv_state["turns_count"] + 1)
    
    # Get previous context if any
    previous_questions = conv_state["metadata"].get("questions", [])
    
    clarification_output = await orchestrator.execute_clarification_agent(
        user_description=user_text,
        project_context="",
        conversation_history=history,
    )
    
    # Extract confidence score from output
    confidence = float(clarification_output.estimated_confidence * 100) if hasattr(clarification_output, 'estimated_confidence') else 0.0
    new_confidence = min(100.0, conv_state["confidence_score"] + confidence)  # Accumulate confidence
    
    logger.info(
        "clarification_agent_completed",
        event_id=event_id,
        confidence=new_confidence,
        threshold=CONFIDENCE_THRESHOLD,
    )
    
    # Store agent response
    assistant_message_id = str(uuid.uuid4())
    now = dt.now(timezone.utc)
    
    # Safely serialize the output
    try:
        if hasattr(clarification_output, 'dict'):
            output_dict = clarification_output.dict()
        else:
            output_dict = vars(clarification_output) if hasattr(clarification_output, '__dict__') else {}
    except Exception as e:
        logger.warning("agent_output_dict_conversion_failed", error=str(e))
        output_dict = str(clarification_output)
    
    # Convert to string safely
    try:
        content = json.dumps(output_dict, default=str)
    except Exception as e:
        logger.warning("agent_output_json_serialization_failed", error=str(e))
        content = str(output_dict)
    
    await db_session.execute(
        sql_text("""
            INSERT INTO messages 
            (message_id, conversation_id, role, content, created_at) 
            VALUES (:message_id, :conversation_id, :role, :content, :created_at)
        """),
        {
            "message_id": assistant_message_id,
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": content,
            "created_at": now,
        }
    )
    
    await db_session.commit()
    logger.info("agent_response_stored", event_id=event_id, conversation_id=conversation_id)
    
    # Update conversation state - convert Pydantic objects to dicts
    questions_list = []
    if hasattr(clarification_output, 'questions') and clarification_output.questions:
        for q in clarification_output.questions:
            if hasattr(q, 'dict'):
                questions_list.append(q.dict())
            else:
                questions_list.append(vars(q) if hasattr(q, '__dict__') else str(q))
    
    metadata = {
        "questions": questions_list,
        "rationale": clarification_output.rationale if hasattr(clarification_output, 'rationale') else ""
    }
    
    # Determine next agent based on confidence
    # If confidence >= 95%, publish to requirement.clarification.completed and don't move to PRD
    if new_confidence >= CONFIDENCE_THRESHOLD:
        next_agent = "clarification"  # Stay in clarification, mark as completed via topic
        is_completed = True
    else:
        next_agent = "clarification"  # Ask more clarifying questions
        is_completed = False
    
    logger.info(
        "confidence_check",
        event_id=event_id,
        current_confidence=new_confidence,
        threshold=CONFIDENCE_THRESHOLD,
        is_completed=is_completed,
    )
    
    await update_conversation_state(
        db_session,
        conversation_id,
        current_agent=next_agent,
        confidence_score=new_confidence,
        turns_count=conv_state["turns_count"] + 1,
        metadata=metadata,
    )
    
    # Always publish clarification questions to Slack Citizen for display
    if producer and slack_channel_id:
        try:
            import uuid
            from datetime import datetime
            
            # Convert questions to dicts for publishing
            questions = []
            if hasattr(clarification_output, 'questions') and clarification_output.questions:
                for q in clarification_output.questions:
                    if hasattr(q, 'dict'):
                        questions.append(q.dict())
                    elif hasattr(q, '__dict__'):
                        questions.append(vars(q))
                    else:
                        questions.append({"text": str(q), "category": "", "priority": ""})
            
            # Publish clarification event with raw data for formatting by Slack Citizen
            clarification_event = {
                "event_id": str(uuid.uuid4()),
                "event_type": "requirement.clarification.completed",
                "source": "intelligence-service",
                "occurred_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "payload": {
                    "conversation_id": conversation_id,
                    "slack_channel_id": slack_channel_id,
                    "slack_thread_ts": thread_ts,
                    "questions": questions,
                    "rationale": metadata.get("rationale", ""),
                    "confidence_score": new_confidence,
                    "is_completed": new_confidence >= CONFIDENCE_THRESHOLD,  # Flag to indicate if requirements are locked
                },
            }
            
            await producer.producer.send_and_wait(
                "project-manager.requirement.clarification.completed",
                value=clarification_event,
            )
            
            logger.info(
                "clarification_questions_published",
                event_id=event_id,
                conversation_id=conversation_id,
                confidence=new_confidence,
                is_completed=new_confidence >= CONFIDENCE_THRESHOLD,
            )
        except Exception as e:
            logger.error(
                "clarification_questions_publish_failed",
                event_id=event_id,
                error=str(e),
            )


async def handle_prd_generation_phase(
    event_id: str,
    conversation_id: str,
    user_text: str,
    history: List[Dict[str, str]],
    conv_state: Dict[str, Any],
    orchestrator: Any,
    db_session: Any,
    producer: Any = None,
    slack_channel_id: str = "",
    thread_ts: str = "",
) -> None:
    """Handle PRD generation phase."""
    from sqlalchemy import text as sql_text
    import uuid
    from datetime import datetime as dt
    
    logger.info("prd_generation_start", event_id=event_id, confidence=conv_state["confidence_score"])
    
    # Extract user description from history
    user_description = ""
    clarification_answers = []
    for msg in history:
        if msg["role"] == "user":
            user_description = msg["content"]
            clarification_answers.append(msg["content"])
    
    prd_output = await orchestrator.execute_prd_generator_agent(
        requirement_description=user_description,
        clarification_answers=clarification_answers,
    )
    
    # Store PRD response
    assistant_message_id = str(uuid.uuid4())
    now = dt.now(timezone.utc)
    
    # Safely serialize the output
    try:
        if hasattr(prd_output, 'dict'):
            output_dict = prd_output.dict()
        else:
            output_dict = vars(prd_output) if hasattr(prd_output, '__dict__') else {}
    except Exception as e:
        logger.warning("prd_output_dict_conversion_failed", error=str(e))
        output_dict = str(prd_output)
    
    # Convert to string safely
    try:
        content = json.dumps(output_dict, default=str)
    except Exception as e:
        logger.warning("prd_output_json_serialization_failed", error=str(e))
        content = str(output_dict)
    
    await db_session.execute(
        sql_text("""
            INSERT INTO messages 
            (message_id, conversation_id, role, content, created_at) 
            VALUES (:message_id, :conversation_id, :role, :content, :created_at)
        """),
        {
            "message_id": assistant_message_id,
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": content,
            "created_at": now,
        }
    )
    
    await db_session.commit()
    logger.info("prd_response_stored", event_id=event_id, conversation_id=conversation_id)
    
    # Move to analysis phase
    metadata = conv_state["metadata"].copy()
    metadata["prd"] = prd_output.dict() if hasattr(prd_output, 'dict') else str(prd_output)
    
    await update_conversation_state(
        db_session,
        conversation_id,
        current_agent="analysis",
        confidence_score=100.0,
        turns_count=conv_state["turns_count"] + 1,
        metadata=metadata,
    )
    
    # Publish PRD response to Slack via Kafka
    if producer and slack_channel_id:
        try:
            from app.utils.slack_formatter import format_prd_for_slack
            
            prd_data = prd_output.dict() if hasattr(prd_output, 'dict') else {}
            message_text, message_blocks = format_prd_for_slack(prd_data)
            
            await producer.publish_slack_reply(
                channel_id=slack_channel_id,
                thread_ts=thread_ts,
                message_text=message_text,
                message_blocks=message_blocks,
            )
            logger.info("prd_slack_reply_published", event_id=event_id, channel=slack_channel_id)
        except Exception as e:
            logger.error("prd_slack_reply_publish_failed", event_id=event_id, error=str(e))


async def handle_analysis_phase(
    event_id: str,
    conversation_id: str,
    user_text: str,
    history: List[Dict[str, str]],
    conv_state: Dict[str, Any],
    orchestrator: Any,
    db_session: Any,
    producer: Any = None,
    slack_channel_id: str = "",
    thread_ts: str = "",
) -> None:
    """Handle requirements analysis phase."""
    from sqlalchemy import text as sql_text
    import uuid
    from datetime import datetime as dt
    
    logger.info("analysis_agent_start", event_id=event_id)
    
    # Extract requirements from metadata
    requirements = conv_state["metadata"].get("prd", {})
    
    analysis_output = await orchestrator.execute_analysis_agent(
        requirements=requirements,
        analysis_depth="standard",
    )
    
    # Store analysis response
    assistant_message_id = str(uuid.uuid4())
    now = dt.now(timezone.utc)
    
    # Safely serialize the output
    try:
        if hasattr(analysis_output, 'dict'):
            output_dict = analysis_output.dict()
        else:
            output_dict = vars(analysis_output) if hasattr(analysis_output, '__dict__') else {}
    except Exception as e:
        logger.warning("analysis_output_dict_conversion_failed", error=str(e))
        output_dict = str(analysis_output)
    
    # Convert to string safely
    try:
        content = json.dumps(output_dict, default=str)
    except Exception as e:
        logger.warning("analysis_output_json_serialization_failed", error=str(e))
        content = str(output_dict)
    
    await db_session.execute(
        sql_text("""
            INSERT INTO messages 
            (message_id, conversation_id, role, content, created_at) 
            VALUES (:message_id, :conversation_id, :role, :content, :created_at)
        """),
        {
            "message_id": assistant_message_id,
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": content,
            "created_at": now,
        }
    )
    
    await db_session.commit()
    logger.info("analysis_response_stored", event_id=event_id, conversation_id=conversation_id)
    
    # Mark conversation as complete
    await update_conversation_state(
        db_session,
        conversation_id,
        current_agent="complete",
        confidence_score=100.0,
        turns_count=conv_state["turns_count"] + 1,
        metadata=conv_state["metadata"],
    )
    
    # Publish analysis response to Slack via Kafka
    if producer and slack_channel_id:
        try:
            from app.utils.slack_formatter import format_analysis_for_slack
            
            analysis_data = analysis_output.dict() if hasattr(analysis_output, 'dict') else {}
            message_text, message_blocks = format_analysis_for_slack(analysis_data)
            
            await producer.publish_slack_reply(
                channel_id=slack_channel_id,
                thread_ts=thread_ts,
                message_text=message_text,
                message_blocks=message_blocks,
            )
            logger.info("analysis_slack_reply_published", event_id=event_id, channel=slack_channel_id)
        except Exception as e:
            logger.error("analysis_slack_reply_publish_failed", event_id=event_id, error=str(e))
