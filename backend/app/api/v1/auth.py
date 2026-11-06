"""
CivicTrack — Authentication API Router (FR-001, FR-002, FR-005, TRD §8.3)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import PublicUser
from app.services.auth_service import authenticate_user, register_citizen

router = APIRouter(tags=["Authentication"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=TokenResponse,
    summary="Register a new Citizen account",
)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Register a new Citizen account (FR-001).
    Returns 201 with access token and public user profile.
    """
    user, token, expires_in = register_citizen(
        db=db,
        full_name=data.full_name,
        email=data.email,
        password=data.password,
        phone=data.phone,
    )
    return TokenResponse(
        token=token,
        token_type="bearer",
        expires_in=expires_in,
        user=PublicUser.model_validate(user),
    )


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=TokenResponse,
    summary="Authenticate user and return JWT",
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate active user with email and password (FR-002).
    Returns 401 with generic message on any failure.
    """
    user, token, expires_in = authenticate_user(
        db=db,
        email=data.email,
        password=data.password,
    )
    return TokenResponse(
        token=token,
        token_type="bearer",
        expires_in=expires_in,
        user=PublicUser.model_validate(user),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Logout user (client discards token)",
)
def logout() -> Response:
    """
    Client-side token disposal acknowledgment (FR-002).
    Returns HTTP 204.
    """
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=PublicUser,
    summary="Retrieve current user's profile",
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> PublicUser:
    """
    Retrieve profile of the currently authenticated user (FR-005).
    Exposes no password hash or other users' PII.
    """
    return PublicUser.model_validate(current_user)
