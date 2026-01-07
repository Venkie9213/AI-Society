"""Tests for Slack client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.clients import SlackClient


@pytest.fixture
def slack_client():
    """Create Slack client with mocked token."""
    return SlackClient(bot_token="xoxb-test-token")


@pytest.mark.asyncio
async def test_post_message_success(slack_client):
    """Test successful message posting."""
    with patch.object(slack_client.client, "chat_postMessage", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            data={"ok": True, "ts": "1234567890.123456"}
        )
        
        result = await slack_client.post_message(
            channel="C123456",
            text="Test message",
            tenant_id="test_tenant",
        )
        
        assert result["ok"] is True
        assert "ts" in result
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_post_message_with_thread(slack_client):
    """Test posting message in thread."""
    with patch.object(slack_client.client, "chat_postMessage", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(
            data={"ok": True, "ts": "1234567890.123456"}
        )
        
        result = await slack_client.post_message(
            channel="C123456",
            text="Test reply",
            thread_ts="1234567890.000000",
            tenant_id="test_tenant",
        )
        
        assert result["ok"] is True
        call_args = mock_post.call_args
        assert call_args[1]["thread_ts"] == "1234567890.000000"


@pytest.mark.asyncio
async def test_add_reaction(slack_client):
    """Test adding reaction to message."""
    with patch.object(slack_client.client, "reactions_add", new_callable=AsyncMock) as mock_reaction:
        mock_reaction.return_value = MagicMock(data={"ok": True})
        
        result = await slack_client.add_reaction(
            channel="C123456",
            timestamp="1234567890.123456",
            emoji="thumbsup",
            tenant_id="test_tenant",
        )
        
        assert result.get("ok") is True
        mock_reaction.assert_called_once()
