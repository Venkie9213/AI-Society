"""Input validation utilities."""

from typing import Optional
import re
from app.exceptions import ValidationError


class InputValidator:
    """Validates user inputs and API requests."""
    
    @staticmethod
    def validate_non_empty(value: str, field_name: str) -> str:
        """Validate string is not empty.
        
        Args:
            value: String to validate
            field_name: Field name for error message
            
        Returns:
            Validated string
            
        Raises:
            ValidationError: If validation fails
        """
        if not value or not value.strip():
            raise ValidationError(
                f"{field_name} cannot be empty",
                field=field_name,
            )
        return value.strip()
    
    @staticmethod
    def validate_uuid(value: str, field_name: str) -> str:
        """Validate UUID format.
        
        Args:
            value: UUID string to validate
            field_name: Field name for error message
            
        Returns:
            Validated UUID string
            
        Raises:
            ValidationError: If not valid UUID
        """
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE,
        )
        if not uuid_pattern.match(value):
            raise ValidationError(
                f"{field_name} is not a valid UUID",
                field=field_name,
            )
        return value
    
    @staticmethod
    def validate_confidence_score(value: float, field_name: str) -> float:
        """Validate confidence score is between 0-100.
        
        Args:
            value: Score value
            field_name: Field name for error message
            
        Returns:
            Validated score
            
        Raises:
            ValidationError: If not in valid range
        """
        if not isinstance(value, (int, float)):
            raise ValidationError(
                f"{field_name} must be a number",
                field=field_name,
            )
        if value < 0 or value > 100:
            raise ValidationError(
                f"{field_name} must be between 0 and 100",
                field=field_name,
            )
        return value
    
    @staticmethod
    def validate_max_length(value: str, max_length: int, field_name: str) -> str:
        """Validate string doesn't exceed max length.
        
        Args:
            value: String to validate
            max_length: Maximum allowed length
            field_name: Field name for error message
            
        Returns:
            Validated string
            
        Raises:
            ValidationError: If exceeds max length
        """
        if len(value) > max_length:
            raise ValidationError(
                f"{field_name} exceeds maximum length of {max_length}",
                field=field_name,
            )
        return value
