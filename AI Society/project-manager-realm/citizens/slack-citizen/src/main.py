"""Main ASGI application entry point for Slack Citizen service."""

from src.app import create_app

# Create and expose the ASGI app
app = create_app()
