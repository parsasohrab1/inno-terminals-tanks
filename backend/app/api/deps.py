"""Shared FastAPI dependencies: DB session, auth, RBAC guards."""
from __future__ import annotations

from collections.abc import Iterable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.config import settings
from app.core.security import decode_token
from app.database import get_session
from app.models.user import Role, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/login", auto_error=False)

SessionDep = Depends(get_session)


def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    if settings.require_mfa and not payload.get("mfa"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "MFA required")
    user = session.exec(select(User).where(User.username == payload["sub"])).first()
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User inactive")
    request.state.username = user.username
    request.state.role = user.role.value
    return user


def require_roles(*roles: Role):
    allowed = set(roles)

    def guard(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed and user.role != Role.ADMIN:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Requires one of roles: {sorted(r.value for r in allowed)}",
            )
        return user

    return guard


def any_authenticated(user: User = Depends(get_current_user)) -> User:
    return user


def client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    return fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "")


def roles_csv(roles: Iterable[Role]) -> str:
    return ",".join(r.value for r in roles)
