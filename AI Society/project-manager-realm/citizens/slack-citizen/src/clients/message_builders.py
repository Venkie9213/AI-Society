"""Slack message block builders for rich formatting."""

from typing import Any, Optional


class MessageBlockBuilder:
    """Base builder for Slack message blocks."""

    @staticmethod
    def section(text: str, markdown: bool = True) -> dict[str, Any]:
        """Create a section block with text."""
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn" if markdown else "plain_text",
                "text": text,
            },
        }

    @staticmethod
    def divider() -> dict[str, Any]:
        """Create a divider block."""
        return {"type": "divider"}

    @staticmethod
    def context(text: str) -> dict[str, Any]:
        """Create a context block."""
        return {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": text,
                },
            ],
        }


class RequirementNotificationBuilder:
    """Builder for requirement notification messages."""

    @staticmethod
    def build_creation_blocks(requirement_id: str, title: str, description: str) -> list[dict[str, Any]]:
        """Build blocks for requirement.created notification."""
        return [
            MessageBlockBuilder.section(
                f"*New Requirement Created*\n\n*Title:* {title}\n*ID:* `{requirement_id}`"
            ),
            MessageBlockBuilder.section(f"*Description:*\n{description}"),
            MessageBlockBuilder.context("From: Requirement Service"),
        ]

    @staticmethod
    def get_creation_text(title: str) -> str:
        """Get fallback text for requirement creation."""
        return f"✅ Requirement created: {title}"


class ClarificationNotificationBuilder:
    """Builder for clarification completion notifications."""

    @staticmethod
    def build_completion_blocks(
        requirement_id: str,
        summary: str,
        prd_content: str,
    ) -> list[dict[str, Any]]:
        """Build blocks for requirement.clarification.completed notification."""
        # Truncate PRD content to avoid exceeding Slack limits
        prd_preview = prd_content[:2000] if len(prd_content) > 2000 else prd_content
        prd_with_ellipsis = prd_preview + ("\n..." if len(prd_content) > 2000 else "")

        return [
            MessageBlockBuilder.section("*Product Requirements Document*"),
            MessageBlockBuilder.section(f"*Summary:* {summary}"),
            MessageBlockBuilder.section(f"*PRD:*\n```\n{prd_with_ellipsis}\n```"),
            MessageBlockBuilder.context("From: Requirement Service"),
        ]

    @staticmethod
    def get_completion_text(requirement_id: str) -> str:
        """Get fallback text for clarification completion."""
        return f"📋 PRD completed for requirement {requirement_id}"


class PulseNotificationBuilder:
    """Builder for pulse execution failure notifications."""

    @staticmethod
    def build_failure_blocks(
        pulse_name: str,
        execution_id: str,
        error_message: str,
    ) -> list[dict[str, Any]]:
        """Build blocks for pulse.execution.failed notification."""
        return [
            MessageBlockBuilder.section(
                f"*⚠️ Pulse Execution Failed*\n\n*Pulse:* {pulse_name}\n*Execution ID:* `{execution_id}`"
            ),
            MessageBlockBuilder.section(f"*Error:* {error_message}"),
            MessageBlockBuilder.context("From: Pulse Engine"),
        ]

    @staticmethod
    def get_failure_text(pulse_name: str) -> str:
        """Get fallback text for pulse failure."""
        return f"❌ Pulse execution failed: {pulse_name}"
