"""
Authentication schemas for login request and response.
"""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Request schema for user login."""

    email: EmailStr = Field(
        ...,
        description="User email address",
        examples=["user@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password",
    )


class TokenResponse(BaseModel):
    """Response schema containing JWT access token."""

    access_token: str = Field(
        ...,
        description="JWT access token for authentication",
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')",
    )
    expires_in: int = Field(
        ...,
        description="Token expiration time in seconds",
    )


class TokenPayload(BaseModel):
    """JWT token payload (claims)."""

    sub: str = Field(
        ...,
        description="Subject (user ID)",
    )
    tenant_id: str = Field(
        ...,
        description="Tenant ID for multi-tenancy",
    )
    email: str = Field(
        ...,
        description="User email",
    )
    exp: int = Field(
        ...,
        description="Expiration timestamp (Unix epoch)",
    )
    iat: int = Field(
        ...,
        description="Issued at timestamp (Unix epoch)",
    )


class UserResponse(BaseModel):
    """Response schema for authenticated user info."""

    id: str = Field(
        ...,
        description="User ID",
    )
    email: str = Field(
        ...,
        description="User email",
    )
    full_name: str | None = Field(
        None,
        description="User's full name",
    )
    tenant_id: str = Field(
        ...,
        description="Tenant ID",
    )
    is_active: bool = Field(
        ...,
        description="Whether user account is active",
    )
