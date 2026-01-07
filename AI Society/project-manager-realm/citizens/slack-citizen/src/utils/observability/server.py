"""Metrics server startup."""

from prometheus_client import start_http_server

from src.config import settings
from src.utils.observability.logging import get_logger

logger = get_logger(__name__)


def start_metrics_server() -> None:
    """Start the Prometheus metrics HTTP server."""
    if settings.enable_metrics:
        try:
            start_http_server(settings.prometheus_port)
            logger.info(
                "prometheus_metrics_server_started",
                port=settings.prometheus_port,
            )
        except Exception as e:
            logger.warning(
                "failed_to_start_prometheus_server",
                port=settings.prometheus_port,
                error=str(e),
            )
