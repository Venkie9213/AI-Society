"""Pydantic schemas for internal event payloads."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class EventEnvelope(BaseModel):
    """Standard event envelope for all internal events."""

    event_id: str = Field(..., description="Unique event identifier")
    occurred_at: datetime = Field(..., description="When the event occurred")
    tenant_id: str = Field(..., description="Tenant identifier for multi-tenancy")
    source: str = Field(..., description="Source service that emitted the event")
    payload_version: str = Field(..., description="Schema version of the payload")
    payload: dict[str, Any] = Field(..., description="Event payload data")


class SlackMessageReceivedPayload(BaseModel):
    """Payload for slack.message.received event."""

    message_id: str = Field(..., description="Internal message identifier")
    slack_user_id: str = Field(..., description="Slack user ID")
    slack_channel_id: str = Field(..., description="Slack channel ID")
    slack_team_id: str = Field(..., description="Slack workspace ID")
    text: str = Field(..., description="Message text content")
    thread_ts: Optional[str] = Field(None, description="Thread timestamp if in thread")
    message_ts: str = Field(..., description="Slack message timestamp")
    channel_type: str = Field(..., description="Type of channel (channel, im, group)")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class SlackCommandInvokedPayload(BaseModel):
    """Payload for slack.command.invoked event."""

    command_id: str = Field(..., description="Internal command identifier")
    slack_user_id: str = Field(..., description="User who invoked the command")
    slack_team_id: str = Field(..., description="Slack workspace ID")
    slack_channel_id: str = Field(..., description="Channel where command was invoked")
    command: str = Field(..., description="The slash command")
    arguments: str = Field(..., description="Command arguments")
    response_url: str = Field(..., description="URL for delayed responses")
    trigger_id: str = Field(..., description="Trigger ID for opening modals")


class SlackInteractionTriggeredPayload(BaseModel):
    """Payload for slack.interaction.triggered event."""

    interaction_id: str = Field(..., description="Internal interaction identifier")
    interaction_type: str = Field(..., description="Type of interaction")
    slack_user_id: str = Field(..., description="User who triggered interaction")
    slack_team_id: str = Field(..., description="Slack workspace ID")
    slack_channel_id: Optional[str] = Field(
        None, description="Channel ID if applicable"
    )
    actions: list[dict[str, Any]] = Field(
        default_factory=list, description="Actions performed"
    )
    response_url: Optional[str] = Field(None, description="Response URL")
    trigger_id: str = Field(..., description="Trigger ID")


class RequirementCreatedPayload(BaseModel):
    """Payload for requirement.created event (consumed by Slack citizen)."""

    requirement_id: str = Field(..., description="Requirement identifier")
    creator_id: str = Field(..., description="User who created the requirement")
    title: str = Field(..., description="Requirement title")
    description: str = Field(..., description="Requirement description")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata including Slack channel/thread info",
    )


class RequirementClarificationCompletedPayload(BaseModel):
    """Payload for requirement.clarification.completed event."""

    requirement_id: str = Field(..., description="Requirement identifier")
    prd_content: str = Field(..., description="Product Requirements Document content")
    clarification_summary: str = Field(..., description="Summary of clarifications")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata including original Slack message info",
    )


class PulseExecutionFailedPayload(BaseModel):
    """Payload for pulse.execution.failed event."""

    pulse_id: str = Field(..., description="Pulse identifier")
    pulse_name: str = Field(..., description="Name of the pulse")
    execution_id: str = Field(..., description="Execution identifier")
    error_message: str = Field(..., description="Error description")
    failed_step: Optional[str] = Field(None, description="Step that failed")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional context"
    )


class SlackReplyRequestedPayload(BaseModel):
    """Payload for slack.reply.requested event (from Intelligence Service)."""

    message_text: str = Field(..., description="Reply message text")
    slack_channel_id: str = Field(..., description="Channel to reply in")
    slack_thread_ts: Optional[str] = Field(
        None, description="Thread timestamp to reply to"
    )
    slack_user_id: Optional[str] = Field(
        None, description="User who triggered the reply"
    )
    blocks: Optional[list[dict[str, Any]]] = Field(
        None, description="Slack Block Kit blocks for rich formatting"
    )
