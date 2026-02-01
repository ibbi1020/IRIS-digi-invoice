"""
Common schema utilities and types.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field
from pydantic.functional_validators import BeforeValidator


def coerce_decimal(value: str | int | float | Decimal) -> Decimal:
    """Convert various numeric types to Decimal."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


# Type alias for Decimal fields that accept various input types
DecimalField = Annotated[Decimal, BeforeValidator(coerce_decimal)]


class PaginatedResponse(BaseModel):
    """Base schema for paginated responses."""

    model_config = ConfigDict(from_attributes=True)

    total: int = Field(..., description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")


class PaginationParams(BaseModel):
    """Query parameters for pagination."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset for SQL queries."""
        return (self.page - 1) * self.page_size


class TimestampMixin(BaseModel):
    """Mixin for created/updated timestamps."""

    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    updated_at: datetime


def to_camel_case(string: str) -> str:
    """Convert snake_case to camelCase for JSON serialization."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])
