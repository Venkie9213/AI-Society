"""Pydantic schemas for Slack event payloads."""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class SlackUser(BaseModel):
    """Slack user information."""

    id: str = Field(..., description="Slack user ID")
    username: Optional[str] = Field(None, description="Slack username")
    name: Optional[str] = Field(None, description="Display name")
    team_id: Optional[str] = Field(None, description="Slack team/workspace ID")


class SlackChannel(BaseModel):
    """Slack channel information."""

    id: str = Field(..., description="Slack channel ID")
    name: Optional[str] = Field(None, description="Channel name")
    is_private: Optional[bool] = Field(False, description="Whether channel is private")


class SlackMessage(BaseModel):
    """Slack message event."""

    type: Literal["message"] = "message"
    subtype: Optional[str] = Field(None, description="Message subtype")
    user: str = Field(..., description="User ID who sent the message")
    text: str = Field(..., description="Message text")
    ts: str = Field(..., description="Timestamp of the message")
    channel: str = Field(..., description="Channel ID")
    thread_ts: Optional[str] = Field(None, description="Thread timestamp if in thread")
    channel_type: Optional[str] = Field(None, description="Type of channel")


class SlackEventWrapper(BaseModel):
    """Slack event API wrapper."""

    token: str = Field(..., description="Verification token")
    team_id: str = Field(..., description="Slack workspace/team ID")
    api_app_id: str = Field(..., description="App ID")
    event: dict[str, Any] = Field(..., description="Event payload")
    type: Literal["event_callback", "url_verification"] = Field(
        ..., description="Event type"
    )
    event_id: str = Field(..., description="Unique event ID")
    event_time: int = Field(..., description="Unix timestamp of event")
    challenge: Optional[str] = Field(None, description="Challenge for URL verification")


class SlackCommand(BaseModel):
    """Slack slash command payload."""

    token: str = Field(..., description="Verification token")
    team_id: str = Field(..., description="Slack workspace ID")
    team_domain: str = Field(..., description="Workspace domain")
    channel_id: str = Field(..., description="Channel ID where command was invoked")
    channel_name: str = Field(..., description="Channel name")
    user_id: str = Field(..., description="User ID who invoked command")
    user_name: str = Field(..., description="Username")
    command: str = Field(..., description="The slash command")
    text: str = Field(..., description="Arguments passed to command")
    response_url: str = Field(..., description="URL to post delayed responses")
    trigger_id: str = Field(..., description="ID for opening modals")


class SlackInteraction(BaseModel):
    """Slack interactive component payload."""

    type: Literal["block_actions", "view_submission", "shortcut"] = Field(
        ..., description="Type of interaction"
    )
    team: dict[str, str] = Field(..., description="Team/workspace info")
    user: dict[str, str] = Field(..., description="User who triggered interaction")
    channel: Optional[dict[str, str]] = Field(None, description="Channel info")
    message: Optional[dict[str, Any]] = Field(None, description="Associated message")
    actions: Optional[list[dict[str, Any]]] = Field(
        None, description="Actions performed"
    )
    view: Optional[dict[str, Any]] = Field(None, description="View submission data")
    trigger_id: str = Field(..., description="Trigger ID")
    response_url: Optional[str] = Field(None, description="Response URL")


class SlackApiError(BaseModel):
    """Slack API error response."""

    ok: Literal[False] = False
    error: str = Field(..., description="Error code")
    warning: Optional[str] = Field(None, description="Warning message")
