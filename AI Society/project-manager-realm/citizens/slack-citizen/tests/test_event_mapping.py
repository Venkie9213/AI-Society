"""Tests for event mapping utilities."""

from datetime import datetime, timezone

import pytest

from src.schemas import SlackCommand, SlackEventWrapper, SlackMessage
from src.utils.mapping import (
    generate_entity_id,
    generate_event_id,
    map_slack_command_to_internal_event,
    map_slack_message_to_internal_event,
)


def test_generate_event_id():
    """Test event ID generation."""
    event_id = generate_event_id()
    assert isinstance(event_id, str)
    assert len(event_id) == 36  # UUID format


def test_generate_entity_id():
    """Test entity ID generation with prefix."""
    entity_id = generate_entity_id("msg")
    assert entity_id.startswith("msg_")
    assert len(entity_id) == 16  # msg_ + 12 hex chars


def test_map_slack_message_to_internal_event():
    """Test mapping Slack message to internal event."""
    slack_event = SlackEventWrapper(
        token="test_token",
        team_id="T123456",
        api_app_id="A123456",
        event={
            "type": "message",
            "user": "U123456",
            "text": "Test message",
            "ts": "1234567890.123456",
            "channel": "C123456",
        },
        type="event_callback",
        event_id="Ev123456",
        event_time=1704621000,
    )
    
    message = SlackMessage(**slack_event.event)
    
    internal_event = map_slack_message_to_internal_event(
        slack_event=slack_event,
        message=message,
        tenant_id="tenant_T123456",
    )
    
    assert internal_event.tenant_id == "tenant_T123456"
    assert internal_event.source == "slack-citizen"
    assert internal_event.payload_version == "v1"
    assert internal_event.payload["slack_user_id"] == "U123456"
    assert internal_event.payload["text"] == "Test message"
    assert internal_event.payload["message_id"].startswith("msg_")


def test_map_slack_command_to_internal_event():
    """Test mapping Slack command to internal event."""
    command = SlackCommand(
        token="test_token",
        team_id="T123456",
        team_domain="test-team",
        channel_id="C123456",
        channel_name="general",
        user_id="U123456",
        user_name="testuser",
        command="/test-command",
        text="command arguments",
        response_url="https://hooks.slack.com/...",
        trigger_id="123.456.abc",
    )
    
    internal_event = map_slack_command_to_internal_event(
        slack_command=command,
        tenant_id="tenant_T123456",
    )
    
    assert internal_event.tenant_id == "tenant_T123456"
    assert internal_event.source == "slack-citizen"
    assert internal_event.payload["command"] == "/test-command"
    assert internal_event.payload["arguments"] == "command arguments"
    assert internal_event.payload["command_id"].startswith("cmd_")
