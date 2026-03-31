"""
JWT authentication dependency.
Extracts and validates Bearer token from the Authorization header.
"""

from typing import TypedDict
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings

_bearer_scheme = HTTPBearer()


class CurrentUser(TypedDict):
    sub: str
    email: str
    name: str
    role: str
    advisor_id: UUID
    firm_id: UUID


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> CurrentUser:
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return CurrentUser(
            sub=payload["sub"],
            email=payload["email"],
            name=payload.get("name", ""),
            role=payload.get("role", "advisor"),
            advisor_id=UUID(payload["advisor_id"]),
            firm_id=UUID(payload["firm_id"]),
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token missing required claims: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )
