"""
Authentication router for login and user info endpoints.
"""

from fastapi import APIRouter, HTTPException, status

from app.dependencies import CurrentUserDep, DbSession
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.services.auth_service import (
    AuthenticationError,
    InactiveUserError,
    build_user_response,
    login_user,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="Authenticate with email and password to receive JWT access token.",
)
async def login(
    request: LoginRequest,
    db: DbSession,
) -> TokenResponse:
    """
    Authenticate user and return access token.

    - **email**: User's email address
    - **password**: User's password (min 8 characters)

    Returns JWT access token on successful authentication.
    """
    try:
        token_response, _ = await login_user(
            db,
            email=request.email,
            password=request.password,
        )
        return token_response
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InactiveUserError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get information about the currently authenticated user.",
)
async def get_me(
    current_user: CurrentUserDep,
) -> UserResponse:
    """
    Get current authenticated user information.

    Requires valid JWT access token in Authorization header.
    """
    return build_user_response(current_user.user)
