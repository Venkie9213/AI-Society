"""Clients module initialization."""

from src.clients.slack_client import SlackClient, get_slack_client

__all__ = [
    "SlackClient",
    "get_slack_client",
]
