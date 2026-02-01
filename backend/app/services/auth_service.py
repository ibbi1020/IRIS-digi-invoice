"""
Authentication service for user login and validation.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.schemas.auth import TokenResponse, UserResponse
from app.utils.security import (
    create_access_token,
    verify_password,
)


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Invalid credentials"):
        self.message = message
        super().__init__(self.message)


class InactiveUserError(Exception):
    """Raised when user account is inactive."""

    def __init__(self, message: str = "User account is inactive"):
        self.message = message
        super().__init__(self.message)


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> User:
    """
    Authenticate a user by email and password.

    Args:
        db: Database session
        email: User email
        password: Plain text password

    Returns:
        Authenticated User object

    Raises:
        AuthenticationError: If credentials are invalid
        InactiveUserError: If user account is inactive
    """
    # Query user by email
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise AuthenticationError()

    # Verify password
    if not verify_password(password, user.password_hash):
        raise AuthenticationError()

    # Check if user is active
    if not user.is_active:
        raise InactiveUserError()

    return user


async def login_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> tuple[TokenResponse, User]:
    """
    Authenticate user and generate access token.

    Args:
        db: Database session
        email: User email
        password: Plain text password

    Returns:
        Tuple of (TokenResponse, User)

    Raises:
        AuthenticationError: If credentials are invalid
        InactiveUserError: If user account is inactive
    """
    # Authenticate
    user = await authenticate_user(db, email, password)

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)
    await db.flush()

    # Generate token
    token, expires_in = create_access_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        email=user.email,
    )

    token_response = TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
    )

    return token_response, user


def build_user_response(user: User) -> UserResponse:
    """
    Build UserResponse from User model.

    Args:
        user: User model instance

    Returns:
        UserResponse schema
    """
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        tenant_id=str(user.tenant_id),
        is_active=user.is_active,
    )
