"""Application-specific exceptions."""

from typing import Optional, Dict, Any


class AppException(Exception):
    """Base application exception."""
    
    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize exception.
        
        Args:
            message: Error message
            code: Error code
            status_code: HTTP status code
            details: Additional error details
        """
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(AppException):
    """Configuration is invalid or incomplete."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message,
            code="CONFIGURATION_ERROR",
            status_code=500,
            details=details,
        )


class ProviderError(AppException):
    """LLM provider error."""
    
    def __init__(self, message: str, provider: str, details: Optional[Dict[str, Any]] = None):
        if details is None:
            details = {}
        details["provider"] = provider
        super().__init__(
            message,
            code="PROVIDER_ERROR",
            status_code=503,
            details=details,
        )


class AgentExecutionError(AppException):
    """Agent execution failed."""
    
    def __init__(
        self,
        message: str,
        agent_name: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        if details is None:
            details = {}
        details["agent"] = agent_name
        super().__init__(
            message,
            code="AGENT_EXECUTION_ERROR",
            status_code=500,
            details=details,
        )


class ValidationError(AppException):
    """Input validation failed."""
    
    def __init__(self, message: str, field: str, details: Optional[Dict[str, Any]] = None):
        if details is None:
            details = {}
        details["field"] = field
        super().__init__(
            message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details,
        )


class DatabaseError(AppException):
    """Database operation failed."""
    
    def __init__(self, message: str, operation: str, details: Optional[Dict[str, Any]] = None):
        if details is None:
            details = {}
        details["operation"] = operation
        super().__init__(
            message,
            code="DATABASE_ERROR",
            status_code=500,
            details=details,
        )


class ResourceNotFoundError(AppException):
    """Requested resource not found."""
    
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            f"{resource_type} not found: {resource_id}",
            code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id},
        )
