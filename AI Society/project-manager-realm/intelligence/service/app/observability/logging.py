# app/observability/logging.py
"""Structured logging setup"""

import sys
import json
from typing import Any
import structlog
from pythonjsonlogger import jsonlogger


def setup_logging(log_level: str = "INFO", structured_logs: bool = True) -> None:
    """Setup structured logging with structlog and python-json-logger"""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Setup console handler with JSON logging
    if structured_logs:
        handler = structlog.stdlib.logging.StreamHandler(sys.stdout)
        handler.setFormatter(jsonlogger.JsonFormatter())
        
        root_logger = structlog.stdlib.logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(getattr(structlog.stdlib.logging, log_level.upper()))


def get_logger():
    """Get a structlog logger instance"""
    return structlog.get_logger()


class JSONFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for Python logging"""
    
    def add_fields(self, log_record: dict, record: Any, message_dict: dict) -> None:
        """Add custom fields to log record"""
        super().add_fields(log_record, record, message_dict)
        
        # Add service context
        log_record["service"] = "intelligence-service"
        log_record["environment"] = "development"  # TODO: make configurable
        
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
