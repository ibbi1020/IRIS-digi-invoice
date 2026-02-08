"""
FastAPI dependencies for authentication and database access.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Tenant, User
from app.utils.security import decode_access_token

# HTTP Bearer token scheme
security = HTTPBearer()


class CurrentUser:
    """Container for authenticated user context."""

    def __init__(self, user: User, tenant: Tenant):
        self.user = user
        self.tenant = tenant

    @property
    def user_id(self) -> str:
        return str(self.user.id)

    @property
    def tenant_id(self) -> str:
        return str(self.tenant.id)

    @property
    def email(self) -> str:
        return self.user.email


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CurrentUser:
    """
    Dependency to get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        CurrentUser with user and tenant context

    Raises:
        HTTPException 401: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Decode token
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")

    if user_id is None or tenant_id is None:
        raise credentials_exception

    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch tenant
    result = await db.execute(
        select(Tenant).where(Tenant.id == user.tenant_id)
    )
    tenant = result.scalar_one_or_none()

    if tenant is None or not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return CurrentUser(user=user, tenant=tenant)


# Type alias for dependency injection
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db)]


# FBR Service dependency
from app.services.fbr_service import FBRService


def get_fbr_service() -> FBRService:
    """Provide FBR service instance for dependency injection."""
    return FBRService()


FBRServiceDep = Annotated[FBRService, Depends(get_fbr_service)]

